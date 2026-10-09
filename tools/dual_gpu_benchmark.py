"""Measure identical independent trials on two physical GPUs with spawned workers.

No publication or solver scheduling changes occur here. Workers retain separate
Batch storage for each assigned chunk, so pose readback and archival happen only
after the coordinator has received every device-completion acknowledgement.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import math
import multiprocessing as mp
from multiprocessing.connection import wait
from numbers import Integral
import os
from pathlib import Path
import platform
import signal
import statistics
import subprocess
import sys
from time import perf_counter, perf_counter_ns
import traceback

import numpy as np

from asquerix.persistence import read_json, write_json, read_jsonl, open_binary

ROOT = Path(__file__).resolve().parents[1]
ARRAYS = ("results", "poses", "initial_results", "initial_poses", "trace")


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=30)
    return dict(command=args, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)


def chunks(count, offset, capacity):
    for value, label in ((count, "count"), (offset, "offset"), (capacity, "batch size")):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError(f"{label} must be an integer")
    if not 1 <= capacity <= 1048576 or count < 1 or not 0 <= offset <= 2**64 - count:
        raise ValueError("invalid count, batch size, or unsigned-64 trial range")
    return [dict(offset=offset + start, count=min(capacity, count - start))
            for start in range(0, count, capacity)]


def partition(mode, count, offset, capacity):
    full = chunks(count, offset, capacity)
    if mode == "A":
        return [full, []]
    if mode == "B":
        return [[], full]
    if mode != "dual":
        raise ValueError("mode must be A, B, or dual")
    first = (count + 1) // 2
    return [chunks(first, offset, capacity),
            chunks(count - first, offset + first, capacity) if count > first else []]


def select_devices(requested, inventory):
    if len(requested) != 2 or len(set(requested)) != 2:
        raise ValueError("two distinct physical GPU UUIDs are required")
    known = {row["uuid"]: row for row in inventory}
    if any(uuid not in known for uuid in requested):
        raise ValueError("devices must be complete physical GPU UUIDs from nvidia-smi")
    return [known[uuid] for uuid in requested]


def inventory():
    query = command(["nvidia-smi", "--query-gpu=index,name,uuid,pci.bus_id,memory.total,driver_version",
                     "--format=csv,noheader,nounits"])
    if query["exit_code"]:
        raise RuntimeError(query["stderr"])
    return [dict(zip(("index", "name", "uuid", "pci_bus_id", "memory_mib", "driver_version"),
                     (part.strip() for part in line.split(","))))
            for line in query["stdout"].splitlines() if line.strip()]


def exact(actual, expected, label):
    if actual.dtype != expected.dtype or actual.shape != expected.shape:
        raise AssertionError(f"{label}: dtype or shape mismatch")
    a = np.ascontiguousarray(actual).view(np.uint8)
    b = np.ascontiguousarray(expected).view(np.uint8)
    if not np.array_equal(a, b):
        raise AssertionError(f"{label}: bytewise mismatch")


def merge_archives(entries, count, offset):
    """Sort by global ID without changing the per-ID square ordering."""
    parts = []
    for entry in entries:
        path = Path(entry["path"])
        if sha256(path) != entry["sha256"]:
            raise AssertionError(f"archive hash mismatch: {path}")
        with np.load(path, allow_pickle=False) as archive:
            parts.append({name: archive[name].copy() for name in ("ids", *ARRAYS)})
    if not parts:
        raise AssertionError("no completed archives")
    merged = {name: np.concatenate([part[name] for part in parts], axis=0)
              for name in ("ids", *ARRAYS)}
    order = np.argsort(merged["ids"])
    merged = {name: array[order] for name, array in merged.items()}
    expected_ids = np.arange(count, dtype=np.uint64) + np.uint64(offset)
    exact(merged["ids"], expected_ids, "complete unique global IDs")
    return merged


def compare_merged(actual, expected):
    for name in ("ids", *ARRAYS):
        exact(actual[name], expected[name], name)


def merge_pipeline(entries, count, offset):
    """Compare decompressed per-trial schema and values, independent of gzip level."""
    rows = []
    for entry in entries:
        path = Path(entry["path"]) / "trials.jsonl.gz"
        if sha256(path) != entry["trials_sha256"]:
            raise AssertionError(f"pipeline archive changed: {path}")
        with open_binary(path) as stream:
            for line in stream:
                import json
                record = json.loads(line)
                tid = record["trial_id"]
                if isinstance(tid, bool) or not isinstance(tid, int):
                    raise AssertionError("trial IDs must retain integer representation")
                rows.append((tid, line))
    rows.sort(key=lambda row: row[0])
    if len(rows) != count or any(tid != offset + i for i, (tid, _) in enumerate(rows)):
        raise AssertionError("pipeline IDs are missing, duplicated, or outside the workload")
    digest = hashlib.sha256()
    for _, payload in rows:
        digest.update(payload)
    return dict(count=count, decompressed_sorted_jsonl_sha256=digest.hexdigest())


def validate_archives(entry):
    from asquerix.geometry import validate_pose
    started = perf_counter()
    checks = []
    for archive in entry["archives"]:
        with np.load(archive["path"], allow_pickle=False) as data:
            # NpzFile does not cache decoded members. Load once rather than
            # decompressing the full batch for each independently checked ID.
            results, poses, ids = (data[name] for name in ("results", "poses", "ids"))
            indices = np.unique(np.linspace(0, archive["count"] - 1,
                                archive["count"] if archive["count"] <= 64 else 32, dtype=int))
            for index in indices:
                result = results[index]
                status = "INIT_FAILED_NO_COMPLETE_GEOMETRY" if int(result["termination"]) == 3 else validate_pose(poses[index], float(result["side"]))["status"]
                checks.append(dict(uuid=archive["uuid"], trial_id=int(ids[index]), status=status))
    entry["cpu_validation"] = checks
    entry["validation_seconds"] = perf_counter() - started
    if any(c["status"] not in ("NUMERICALLY_VALIDATED", "INIT_FAILED_NO_COMPLETE_GEOMETRY") for c in checks):
        raise AssertionError("independent CPU validation failed")


def worker(pipe, start, stop, uuid, label, sources, ns, capacity, debug, output, timeout):
    """CUDA is first imported and initialized inside a spawned process."""
    os.environ["CUDA_VISIBLE_DEVICES"] = uuid
    os.environ["ASQUERIX_WARP_CACHE"] = str(Path(output) / "cache" / label)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    log = (Path(output) / f"worker-{label}.log").open("w", buffering=1)
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    # These imports must remain local: the coordinator never owns CUDA state.
    import warp as wp
    from kernel_benchmark import clear_scratch, load_source
    wp.config.quiet = True
    wp.init()
    device = wp.get_device("cuda:0")
    completed = []
    intervals = []
    task = None
    pipeline_result = None
    try:
        if not device.is_cuda or device.uuid != uuid or len(wp.get_cuda_devices()) != 1:
            raise RuntimeError(f"visibility mismatch: expected {uuid}, got {device.uuid}")
        started = perf_counter()
        modules = {variant: load_source(path, f"asquerix_dual_{variant}_{sha256(path)[:12]}")
                   for variant, path in sources.items()}
        configurations = {}
        batches = {}
        initial = {}
        properties = {}
        warmup_seconds = 0.0
        for variant, module in modules.items():
            for n in ns:
                config = module.Config(n=n, max_sweeps=480)
                configurations[variant, n] = config
                batches[variant, n] = []
                initial[variant, n] = module.Batch(replace(config, max_attempts=0), capacity, device=device)
                # Compile and prewarm full production submissions, not just initialization.
                batch = module.Batch(config, capacity, device=device, debug=debug)
                clear_scratch(batch)
                warm = perf_counter()
                batch.run(min(32, capacity), 0)
                batch.get_poses(np.arange(min(32, capacity), dtype=np.int32))
                warmup_seconds += perf_counter() - warm
                batches[variant, n].append(batch)
                properties[f"{variant}-n{n}"] = batch.kernel_properties
        pipe.send(dict(event="ready", label=label, uuid=device.uuid, pci_bus_id=device.pci_bus_id,
                       local_device=str(device), cuda_visible_devices=os.environ["CUDA_VISIBLE_DEVICES"],
                       prepare_seconds=perf_counter() - started, warmup_seconds=warmup_seconds,
                       kernel_properties=properties, sm_count=device.sm_count,
                       configs={f"{v}-n{n}": asdict(c) for (v, n), c in configurations.items()}))

        def archive_completed():
            if task.get("pipeline") == "ordinary":
                if pipeline_result is None:
                    return []
                directory = Path(pipeline_result["directory"])
                return [dict(path=str(directory), uuid=uuid,
                             trials_sha256=sha256(directory / "trials.jsonl.gz"),
                             count=pipeline_result["metadata"]["completed_trials"],
                             offset=task["chunks"][0]["offset"],
                             summary=pipeline_result["summary"],
                             gzip_level=task["gzip_level"])]
            archives = []
            for slot, specification, results, timing in completed:
                variant, n = task["variant"], task["n"]
                batch = batches[variant, n][slot]
                count, offset = specification["count"], specification["offset"]
                transfer_started = perf_counter()
                poses, _ = batch.get_poses(np.arange(count, dtype=np.int32))
                trace = batch.trace.numpy()[:, :count].T.copy()
                final_transfer_seconds = perf_counter() - transfer_started
                init = initial[variant, n]
                clear_scratch(init)
                init_started = perf_counter()
                initial_results, init_timing = init.run(count, offset)
                initial_poses, _ = init.get_poses(np.arange(count, dtype=np.int32))
                initialization_check_seconds = perf_counter() - init_started
                path = Path(task["archive_directory"]) / f"{label}-slot{slot}-id{offset}.npz"
                path.parent.mkdir(parents=True, exist_ok=True)
                persistence_started = perf_counter()
                np.savez_compressed(path, ids=np.arange(count, dtype=np.uint64) + np.uint64(offset),
                                    results=results, poses=poses, trace=trace,
                                    initial_results=initial_results, initial_poses=initial_poses)
                archives.append(dict(path=str(path), size_bytes=path.stat().st_size, sha256=sha256(path),
                                     uuid=uuid, **specification, timing=timing,
                                     final_transfer_seconds=final_transfer_seconds,
                                     initialization_check_seconds=initialization_check_seconds,
                                     initialization_timing=init_timing,
                                     persistence_seconds=perf_counter() - persistence_started))
            return archives

        while True:
            instruction = pipe.recv()
            if instruction["command"] == "shutdown":
                break
            if instruction["command"] == "collect":
                pipe.send(dict(event="archives", uuid=uuid, archives=archive_completed()))
                completed = []
                continue
            if instruction["command"] != "prepare":
                raise ValueError("unknown worker command")
            task = instruction
            completed = []
            pipeline_result = None
            variant, n = task["variant"], task["n"]
            if sha256(sources[variant]) != task["source_sha256"]:
                raise RuntimeError("source changed during benchmark")
            module = modules[variant]
            storage = batches[variant, n]
            slots = 1 if task.get("pipeline") == "ordinary" else len(task["chunks"])
            while len(storage) < slots:
                storage.append(module.Batch(configurations[variant, n], capacity, device=device, debug=debug))
            for batch in storage[:len(task["chunks"])]:
                clear_scratch(batch)
                batch.trace.zero_()
            wp.synchronize_device(device)
            pipe.send(dict(event="prepared", uuid=uuid))
            if not start.wait(timeout):
                raise TimeoutError("coordinator start barrier timed out")
            began = perf_counter_ns()
            intervals = []
            if task.get("pipeline") == "ordinary":
                if task["chunks"] and not stop.is_set():
                    from asquerix import runner
                    import gzip
                    from pipeline_observer import observe
                    original_gzip = gzip.GzipFile
                    original_level = runner.GZIP_COMPRESSION_LEVEL
                    runner.GZIP_COMPRESSION_LEVEL = task["gzip_level"]

                    class SelectedGzipFile(original_gzip):
                        def __init__(self, *args, **kwargs):
                            kwargs["compresslevel"] = task["gzip_level"]
                            super().__init__(*args, **kwargs)

                    gzip.GzipFile = SelectedGzipFile
                    batch = storage[0]
                    original_run = batch.run
                    pipeline_directory = Path(task["archive_directory"]) / label
                    diagnostic_directory = Path(task["archive_directory"]) / f"diagnostic-{label}"
                    diagnostic_directory.mkdir(parents=True, exist_ok=True)

                    def measured_run(count, offset):
                        before = perf_counter_ns()
                        results, timing = original_run(count, offset)
                        intervals.append(dict(count=count, offset=offset, started_ns=before,
                                              finished_ns=perf_counter_ns(), timing=timing,
                                              warmup=not intervals))
                        return results, timing

                    def progress(event):
                        if event["event"] == "batch-completed":
                            pipe.send(dict(event="batch", uuid=uuid, count=event["current_batch_trials"],
                                           offset=task["chunks"][0]["offset"] + event["completed"] - event["current_batch_trials"]))
                            if stop.is_set():
                                os.kill(os.getpid(), signal.SIGINT)

                    batch.run = measured_run
                    try:
                        with observe(runner, wp, batch, diagnostic_directory, task["diagnose"]):
                            pipeline_result = runner.run(configurations[variant, n],
                                trials=sum(c["count"] for c in task["chunks"]),
                                trial_offset=task["chunks"][0]["offset"], batch_size=capacity,
                                device=str(device), output=pipeline_directory, experiment=f"benchmark-n{n}",
                                run_id=f"{Path(task['archive_directory']).name}-{label}",
                                # A fixed global-ID audit set gives identical validation
                                # coverage across partitions and host variants.
                                sample_every=4096, audit_size=0, keep_best=0, max_images=0,
                                failure_examples=0, max_seconds=task["max_seconds"],
                                batch_factory=lambda *_: batch, progress=progress)
                    finally:
                        batch.run = original_run
                        gzip.GzipFile = original_gzip
                        runner.GZIP_COMPRESSION_LEVEL = original_level
                pipe.send(dict(event="complete", uuid=uuid, started_ns=began,
                               finished_ns=perf_counter_ns(), intervals=intervals,
                               completed_unique=pipeline_result["metadata"]["completed_trials"] if pipeline_result else 0))
                continue
            for slot, specification in enumerate(task["chunks"]):
                if stop.is_set():
                    break
                before = perf_counter_ns()
                results, timing = storage[slot].run(specification["count"], specification["offset"])
                after = perf_counter_ns()
                completed.append((slot, specification, results, timing))
                intervals.append(dict(**specification, started_ns=before, finished_ns=after, timing=timing))
                pipe.send(dict(event="batch", uuid=uuid, count=specification["count"], offset=specification["offset"]))
            pipe.send(dict(event="complete", uuid=uuid, started_ns=began, finished_ns=perf_counter_ns(),
                           intervals=intervals, completed_unique=sum(item[1]["count"] for item in completed)))
    except BaseException as exc:
        stop.set()
        if task and task.get("pipeline") == "ordinary" and pipeline_result is None:
            # The ordinary runner finalizes partial evidence in its finally
            # block before propagating an error. Recover that durable result.
            directory = Path(task["archive_directory"]) / label
            try:
                saved_metadata = read_json(directory / "environment.json")
                if saved_metadata["completed_trials"]:
                    pipeline_result = dict(directory=str(directory), metadata=saved_metadata,
                                           summary=read_json(directory / "summary.json"))
            except (OSError, KeyError, ValueError):
                pass
        done = (pipeline_result["metadata"]["completed_trials"] if pipeline_result else
                sum(item[1]["count"] for item in completed))
        detail = dict(event="error", uuid=uuid, error=f"{type(exc).__name__}: {exc}",
                      traceback=traceback.format_exc(), task=task,
                      completed_ranges=[item[1] for item in completed],
                      completed_unique=done, intervals=intervals,
                      finished_ns=perf_counter_ns())
        try:
            detail["archives"] = archive_completed() if completed or pipeline_result else []
        except BaseException:
            detail["archival_error"] = traceback.format_exc()
        write_json(Path(output) / f"failure-{label}.json", detail)
        try:
            pipe.send(detail)
        except (BrokenPipeError, OSError):
            pass
    finally:
        pipe.close()
        log.close()


class Display:
    def __init__(self, enabled, devices):
        self.progress = None
        self.devices = devices
        if enabled:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
            self.console = Console()
            self.progress = Progress(SpinnerColumn(), TextColumn("{task.description}"),
                                     TextColumn("{task.completed:.0f}/{task.total:.0f}"),
                                     TimeElapsedColumn(), console=self.console, refresh_per_second=2)
            self.tasks = [self.progress.add_task(f"{label}: {device['uuid']} preparing", total=0)
                          for label, device in zip(("A", "B"), devices)]
            self.combined = self.progress.add_task("Combined: preparing", total=0)
            self.progress.start()

    def update(self, assignments, phase, counts=None):
        if self.progress:
            counts = counts or [0, 0]
            for i, assignment in enumerate(assignments):
                self.progress.update(self.tasks[i], description=f"{'AB'[i]} {self.devices[i]['uuid']}: {phase}",
                                     total=sum(c["count"] for c in assignment), completed=counts[i])
            self.progress.update(self.combined, description=f"Combined: {phase}",
                                 total=sum(c["count"] for a in assignments for c in a), completed=sum(counts))

    def close(self):
        if self.progress:
            self.progress.stop()

    def summary(self, rows):
        if self.progress:
            from rich.table import Table
            table = Table(title="Measured common execution throughput")
            for column in ("N", "Variant", "Mode", "Trials/s median", "Range", "Repeats"):
                table.add_column(column)
            for row in rows:
                table.add_row(str(row["n"]), row["variant"], row["mode"], f"{row['median_rate']:.2f}",
                              f"{row['min_rate']:.2f}–{row['max_rate']:.2f}", str(row["repeats"]))
            self.console.print(table)


def receive(pipes, processes, event, timeout, stop, display=None, assignments=None, deadline=None, thread_samples=None):
    pending = set(range(len(pipes)))
    replies = {}
    expires = perf_counter() + timeout
    counts = [0] * len(pipes)
    next_sample = 0.0
    while pending:
        now = perf_counter()
        if thread_samples is not None and now >= next_sample:
            for process in processes:
                for path in Path(f"/proc/{process.pid}/task").glob("*/stat"):
                    try:
                        value = path.read_text()
                        fields = value.rsplit(")", 1)[1].split()
                        thread_samples.append(dict(timestamp_ns=perf_counter_ns(), pid=process.pid,
                                              uuid=process.name, tid=int(path.parent.name),
                                              state=fields[0], user_ticks=int(fields[11]),
                                              system_ticks=int(fields[12]), cpu=int(fields[36])))
                    except (OSError, IndexError, ValueError):
                        pass
            next_sample = now + 0.5
        if deadline is not None and now >= deadline:
            stop.set()
        if now >= expires:
            stop.set()
            raise TimeoutError(f"workers {sorted(pending)} did not report {event} within {timeout}s")
        for pipe in wait([pipes[i] for i in pending], timeout=min(0.2, expires - now)):
            i = pipes.index(pipe)
            try:
                message = pipe.recv()
            except EOFError:
                message = dict(event="error", uuid=processes[i].name,
                               error=f"worker exited with code {processes[i].exitcode}")
            if message["event"] == "batch":
                counts[i] += message["count"]
                if display:
                    display.update(assignments, "executing", counts)
                continue
            if message["event"] not in (event, "error"):
                raise RuntimeError(f"unexpected worker event: {message['event']}")
            message["received_ns"] = perf_counter_ns()
            replies[i] = message
            pending.remove(i)
            if message["event"] == "error":
                stop.set()
    return replies


def summarize(measurements):
    groups = {}
    for entry in measurements:
        if entry["status"] != "COMPLETE":
            continue
        groups.setdefault((entry["n"], entry["variant"], entry["mode"]), []).append(entry)
    rows = []
    for (n, variant, mode), entries in sorted(groups.items()):
        rates = [e["completed_unique"] / e["common_execution_seconds"] for e in entries]
        rows.append(dict(n=n, variant=variant, mode=mode, repeats=len(entries),
                         median_rate=statistics.median(rates), min_rate=min(rates), max_rate=max(rates),
                         relative_range=(max(rates) - min(rates)) / statistics.median(rates),
                         rate_cv=statistics.pstdev(rates) / statistics.mean(rates),
                         median_common_seconds=statistics.median(e["common_execution_seconds"] for e in entries)))
    scaling = []
    for n, variant in sorted({(r["n"], r["variant"]) for r in rows}):
        modes = {r["mode"]: r for r in rows if (r["n"], r["variant"]) == (n, variant)}
        if set(modes) == {"A", "B", "dual"}:
            a, b, dual = (modes[m]["median_rate"] for m in ("A", "B", "dual"))
            scaling.append(dict(n=n, variant=variant, a_rate=a, b_rate=b, dual_rate=dual,
                                dual_vs_a=dual / a, dual_vs_b=dual / b, capacity_efficiency=dual / (a + b)))
    return rows, scaling


def replay(manifest_path, output):
    manifest = read_json(manifest_path)
    references = {}
    checks = []
    for entry in manifest["measurements"]:
        if entry["status"] != "COMPLETE":
            continue
        ordinary = manifest.get("pipeline") == "ordinary"
        actual = (merge_pipeline(entry["archives"], manifest["count"], manifest["offset"])
                  if ordinary else merge_archives(entry["archives"], manifest["count"], manifest["offset"]))
        n = entry["n"]
        if n not in references:
            if entry["variant"] != "baseline":
                raise AssertionError("first complete output must use baseline")
            references[n] = actual
            scope = "BASELINE_CAPTURE"
        else:
            if ordinary:
                if actual != references[n]:
                    raise AssertionError("decompressed pipeline schema or values differ")
            else:
                compare_merged(actual, references[n])
            scope = "BASELINE_BYTEWISE_MATCH"
        checks.append(dict(measurement=entry["measurement"], n=n, comparison=scope, ids_complete=True))
    if not checks:
        raise AssertionError("no complete measurements to replay")
    write_json(output, dict(exact=True, comparisons=checks, scope="Archived bytes; no new CUDA execution."))


def run(args):
    operation_started = perf_counter()
    device_list = select_devices(args.devices, inventory())
    chunks(args.count, args.offset, args.batch_size)
    if (args.count < 2 or args.repeats < 1
            or not math.isfinite(args.timeout) or args.timeout <= 0
            or not math.isfinite(args.max_seconds) or args.max_seconds <= 0):
        raise ValueError("count >= 2 and positive repeats/time limits are required")
    if len(set(args.n)) != len(args.n) or any(n < 1 or n > 32 for n in args.n):
        raise ValueError("n must contain distinct values in [1,32]")
    if len(set(args.modes)) != len(args.modes) or any(m not in ("A", "B", "dual") for m in args.modes):
        raise ValueError("modes must contain distinct values from A,B,dual")
    sources = {"baseline": str(args.baseline_source.resolve())}
    if args.candidate_source:
        sources["candidate"] = str(args.candidate_source.resolve())
    if args.pipeline == "ordinary":
        if args.candidate_source:
            raise ValueError("ordinary host comparisons require a fixed kernel")
        if len(args.gzip_levels) not in (1, 2) or any(level not in (1, 3, 6, 9) for level in args.gzip_levels):
            raise ValueError("provide one or two gzip levels from 1,3,6,9")
        if len(args.gzip_levels) == 2:
            sources["host"] = sources["baseline"]
    levels = dict(zip(sources, args.gzip_levels)) if args.pipeline == "ordinary" else {}
    hashes = {variant: sha256(source) for variant, source in sources.items()}
    args.output.mkdir(parents=True, exist_ok=False)
    args.archives.mkdir(parents=True, exist_ok=False)
    # Worker caches stay local with the large arrays, not in published evidence.
    worker_output = args.archives.resolve()
    metadata = dict(started_utc=datetime.now(timezone.utc).isoformat(), devices=device_list,
                    coordinator_cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
                    sources=sources, source_sha256=hashes, count=args.count, offset=args.offset,
                    batch_size=args.batch_size, n=args.n, repeats=args.repeats, modes=args.modes,
                    debug=args.debug, arrays=ARRAYS, measurements=[],
                    pipeline=args.pipeline, gzip_levels=levels, diagnose=args.diagnose,
                    python=platform.python_version(), platform=platform.platform(),
                    dependencies={name: importlib.metadata.version(name)
                                  for name in ("warp-lang", "numpy", "rich", "pytest")},
                    source_commit=command(["git", "rev-parse", "HEAD"]),
                    tool_sha256={name: sha256(ROOT / "tools" / name) for name in
                                 ("dual_gpu_benchmark.py", "pipeline_observer.py", "kernel_benchmark.py")},
                    host_source_sha256={name: sha256(ROOT / "src/asquerix" / name) for name in
                                        ("runner.py", "persistence.py", "output.py", "geometry.py")},
                    git_status=command(["git", "status", "--porcelain"]),
                    lockfile_sha256=sha256(ROOT / "uv.lock"),
                    timing_scope={"cuda": "Per-device Batch.run CUDA events, summed only for serial chunks on that device.",
                                  "common": "Coordinator barrier release through receipt of all completion acknowledgements; includes Batch.run scalar transfers and IPC. Excludes preparation and pose archival.",
                                  "end_to_end": "run() entry through worker shutdown and telemetry closure; includes discovery, startup, prewarm, all runs, equality, CPU validation, archives and intermediate metadata. Excludes final summary manifest serialization, terminal summary and publication. External CLI process lifetime covers those final outputs."})
    if args.pipeline == "ordinary":
        metadata["timing_scope"]["common"] = "Coordinator release through all ordinary runner finalizations and completion acknowledgements, including warm-up, host work, gzip, reports and durable files; excludes initial worker/JIT setup and publication."
        metadata["persistence_policy"] = dict(sample_every=4096, audit_size=0, keep_best=0,
                                               failure_examples=0, max_images=0,
                                               rationale="Fixed periodic global-ID audits, all scalar records, no leaderboard or rendering in this controlled pipeline comparison. CLI defaults unchanged.")
    context = mp.get_context("spawn")
    start, stop = context.Event(), context.Event()
    pipes, processes = [], []
    display = Display(not args.json, device_list)
    deadline = operation_started + args.max_seconds
    old_handlers = {}
    reason = None

    def request_stop(signum, _frame):
        nonlocal reason
        reason = f"SIGNAL_{signum}"
        stop.set()

    for signum in (signal.SIGINT, signal.SIGTERM):
        old_handlers[signum] = signal.signal(signum, request_stop)
    telemetry = (args.output / "gpu-monitor.csv").open("w")
    monitor = subprocess.Popen(["nvidia-smi", "--query-gpu=timestamp,index,uuid,utilization.gpu,utilization.memory,temperature.gpu,clocks.sm,clocks.mem,power.draw,power.limit,memory.used", "--format=csv", "-l", "1"], stdout=telemetry, stderr=subprocess.STDOUT)
    references = {}
    thread_samples = [] if args.diagnose else None
    try:
        for label, device in zip(("A", "B"), device_list):
            parent, child = context.Pipe()
            process = context.Process(name=device["uuid"], target=worker, args=(child, start, stop, device["uuid"], label,
                                      sources, args.n, args.batch_size, args.debug, str(worker_output), args.timeout))
            process.start()
            child.close()
            pipes.append(parent)
            processes.append(process)
        ready = receive(pipes, processes, "ready", args.timeout, stop, deadline=deadline, thread_samples=thread_samples)
        metadata["workers"] = list(ready.values())
        if any(reply["event"] == "error" for reply in ready.values()):
            raise RuntimeError("worker preparation failed; see worker failure evidence")
        metadata["startup_and_prewarm_seconds"] = perf_counter() - operation_started
        metadata["status"] = "READY"
        write_json(args.output / "measurements.json", metadata)
        print("Workers ready: " + ", ".join(d["uuid"] for d in device_list), flush=True)
        measurement = 0
        for n in args.n:
            for repeat in range(args.repeats):
                modes = args.modes[repeat % len(args.modes):] + args.modes[:repeat % len(args.modes)]
                variants = list(sources) if repeat % 2 == 0 else list(reversed(sources))
                for mode in modes:
                    for variant in variants:
                        if perf_counter() >= deadline:
                            reason = "DEADLINE"
                            stop.set()
                        if stop.is_set():
                            break
                        assignment = partition(mode, args.count, args.offset, args.batch_size)
                        measurement += 1
                        directory = worker_output / f"m{measurement:03d}-n{n}-{variant}-{mode}-r{repeat}"
                        entry = dict(measurement=measurement, n=n, variant=variant, mode=mode, repeat=repeat,
                                     assignments=assignment, started_utc=datetime.now(timezone.utc).isoformat(),
                                     processes_before=command(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv"]))
                        preparation_started = perf_counter()
                        start.clear()
                        display.update(assignment, "preparing")
                        for i, pipe in enumerate(pipes):
                            pipe.send(dict(command="prepare", n=n, variant=variant, chunks=assignment[i],
                                           archive_directory=str(directory), source_sha256=hashes[variant],
                                           pipeline=args.pipeline, gzip_level=levels.get(variant),
                                           diagnose=args.diagnose, max_seconds=args.timeout))
                        prepared = receive(pipes, processes, "prepared", args.timeout, stop, deadline=deadline, thread_samples=thread_samples)
                        if any(r["event"] == "error" for r in prepared.values()):
                            entry.update(status="FAILED", errors=list(prepared.values()), archives=[])
                            metadata["measurements"].append(entry)
                            break
                        entry["preparation_seconds"] = perf_counter() - preparation_started
                        display.update(assignment, "executing")
                        print(f"N={n} {variant} {mode}: executing {args.count} unique trials", flush=True)
                        release_ns = perf_counter_ns()
                        start.set()
                        completed = receive(pipes, processes, "complete", args.timeout, stop, display, assignment, deadline, thread_samples)
                        end_ns = max(r["received_ns"] for r in completed.values())
                        entry.update(release_ns=release_ns, end_ns=end_ns,
                                     common_execution_seconds=(end_ns - release_ns) / 1e9,
                                     worker_completion=list(completed.values()),
                                     completed_unique=sum(r.get("completed_unique", 0) for r in completed.values()))
                        complete = entry["completed_unique"] == args.count and all(r["event"] == "complete" for r in completed.values())
                        entry["status"] = ("FAILED" if any(r["event"] == "error" for r in completed.values())
                                           else "COMPLETE" if complete else "PARTIAL")
                        display.update(assignment, "archiving", [r.get("completed_unique", 0) for r in completed.values()])
                        collect_started = perf_counter()
                        active = [i for i, r in completed.items() if r["event"] == "complete"]
                        for i in active:
                            pipes[i].send(dict(command="collect"))
                        archived = receive([pipes[i] for i in active], [processes[i] for i in active],
                                           "archives", args.timeout, stop) if active else {}
                        entries = list(archived.values()) + [r for r in completed.values() if r["event"] == "error"]
                        entry["archives"] = [a for r in entries for a in r.get("archives", [])]
                        entry["collection_seconds"] = perf_counter() - collect_started
                        entry["incomplete_ranges"] = []
                        for i, assigned in enumerate(assignment):
                            done = [dict(count=c["count"], offset=c["offset"])
                                    for c in completed[i].get("intervals", []) if not c.get("warmup")]
                            entry["incomplete_ranges"].extend(c for c in assigned if c not in done)
                        if any(r["event"] == "error" for r in archived.values()):
                            entry["status"] = "FAILED"
                            complete = False
                            stop.set()
                        # Preserve measurement and archive paths even if a later
                        # equality or validation gate fails.
                        metadata["measurements"].append(entry)
                        write_json(args.output / "measurements.json", metadata)
                        if complete:
                            comparison_started = perf_counter()
                            actual = (merge_pipeline(entry["archives"], args.count, args.offset)
                                      if args.pipeline == "ordinary" else
                                      merge_archives(entry["archives"], args.count, args.offset))
                            if n not in references:
                                if variant != "baseline":
                                    raise AssertionError("baseline must establish the first reference")
                                references[n] = actual
                                entry["comparison"] = "BASELINE_CAPTURE"
                            else:
                                if args.pipeline == "ordinary":
                                    if actual != references[n]:
                                        raise AssertionError("decompressed per-trial pipeline schema or values changed")
                                else:
                                    compare_merged(actual, references[n])
                                entry["comparison"] = "BASELINE_BYTEWISE_MATCH"
                            entry["comparison_seconds"] = perf_counter() - comparison_started
                            if args.pipeline == "ordinary":
                                entry["pipeline_equality"] = actual
                                entry["cpu_validation"] = [a["summary"]["audit_coverage"] for a in entry["archives"]]
                                entry["validation_seconds"] = 0.0  # included before worker acknowledgement
                            else:
                                validate_archives(entry)
                        entry["processes_after"] = command(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv"])
                        write_json(args.output / "measurements.json", metadata)
                        print(f"N={n} {variant} {mode} repeat={repeat}: {entry['status']}, {entry['completed_unique']} unique trials, {entry['common_execution_seconds']:.6f}s", flush=True)
                    if stop.is_set():
                        break
                if stop.is_set():
                    break
            if stop.is_set():
                break
        failed = any(m["status"] == "FAILED" for m in metadata["measurements"])
        metadata["status"] = "FAILED" if failed else "PARTIAL" if stop.is_set() else "COMPLETE"
        if failed and reason is None:
            reason = "WORKER_FAILURE"
    except BaseException as exc:
        stop.set()
        metadata.update(status="FAILED", error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
        raise
    finally:
        shutdown_started = perf_counter()
        stop.set()
        start.set()
        for pipe, process in zip(pipes, processes):
            if process.is_alive():
                try:
                    pipe.send(dict(command="shutdown"))
                except (BrokenPipeError, OSError):
                    pass
        for process in processes:
            process.join(timeout=args.timeout)
            if process.is_alive():
                metadata.setdefault("forced_shutdown_pids", []).append(process.pid)
                process.kill()
                process.join(timeout=5)
        for pipe in pipes:
            pipe.close()
        monitor.terminate()
        monitor.wait(timeout=10)
        telemetry.close()
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        metadata.update(stop_reason=reason, shutdown_seconds=perf_counter() - shutdown_started,
                        finished_utc=datetime.now(timezone.utc).isoformat(),
                        full_end_to_end_seconds=perf_counter() - operation_started)
        if thread_samples is not None:
            write_json(args.output / "thread-activity.json", dict(clock_ticks_per_second=os.sysconf("SC_CLK_TCK"),
                       logical_cpu_count=os.cpu_count(), samples=thread_samples,
                       scope="Only benchmark worker threads; per-thread 100% means one logical CPU."))
        rows, scaling = summarize(metadata["measurements"])
        metadata["summary"] = rows
        metadata["scaling"] = scaling
        write_json(args.output / "measurements.json", metadata)
        display.close()
        display.summary(rows)
    print(f"Saved {metadata['status']}: {args.output / 'measurements.json.gz'}; arrays: {args.archives}")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    benchmark = commands.add_parser("run")
    benchmark.add_argument("--baseline-source", type=Path, required=True)
    benchmark.add_argument("--candidate-source", type=Path)
    benchmark.add_argument("--devices", nargs=2, required=True, metavar=("GPU_A_UUID", "GPU_B_UUID"))
    benchmark.add_argument("--n", type=int, nargs="+", default=[12, 16])
    benchmark.add_argument("--count", type=int, default=262144)
    benchmark.add_argument("--offset", type=int, default=0)
    benchmark.add_argument("--batch-size", type=int, default=131072)
    benchmark.add_argument("--repeats", type=int, default=3)
    benchmark.add_argument("--modes", nargs="+", default=["A", "B", "dual"])
    benchmark.add_argument("--timeout", type=float, default=180)
    benchmark.add_argument("--max-seconds", type=float, default=1800)
    benchmark.add_argument("--output", type=Path, required=True)
    benchmark.add_argument("--archives", type=Path, required=True)
    benchmark.add_argument("--debug", action="store_true")
    benchmark.add_argument("--pipeline", choices=("compute", "ordinary"), default="compute")
    benchmark.add_argument("--gzip-levels", type=int, nargs="+", default=[9])
    benchmark.add_argument("--diagnose", action="store_true")
    benchmark.add_argument("--json", action="store_true")
    check = commands.add_parser("replay")
    check.add_argument("--manifest", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "replay":
        replay(args.manifest, args.output)
        print(f"Exact archived comparisons saved: {args.output}")
    else:
        result = run(args)
        if result["status"] != "COMPLETE":
            raise SystemExit(2)


if __name__ == "__main__":
    main()
