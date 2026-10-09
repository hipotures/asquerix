"""Batch scheduling, independent audits, and durable output at batch boundaries."""
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
from numbers import Real
from pathlib import Path
import platform
import re
import signal
import subprocess
from time import perf_counter, perf_counter_ns
import uuid
from datetime import datetime, timezone

import numpy as np

from .geometry import validate_pose
from .gpu import Batch, Config, TERMINATIONS
from .output import render_selected, write_report
from .persistence import GZIP_COMPRESSION_LEVEL, open_jsonl_writer, write_json


_EXPERIMENT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def validate_experiment_name(value: str) -> str:
    """Validate and return a filesystem/Git-safe experiment display name."""

    if not isinstance(value, str) or value in {".", ".."} or not _EXPERIMENT_NAME.fullmatch(value):
        raise ValueError(
            "experiment must be 1-80 ASCII characters matching [A-Za-z0-9][A-Za-z0-9._-]*"
        )
    return value


def _validate_run_id(value: str) -> str:
    """Validate a caller-supplied run identifier using the same safe slug rule."""

    try:
        return validate_experiment_name(value)
    except ValueError as exc:
        raise ValueError(
            "run_id must be 1-80 ASCII characters matching [A-Za-z0-9][A-Za-z0-9._-]*"
        ) from exc


def _default_experiment(config: Config, batch_size: int) -> tuple[str, str]:
    """Return a descriptive experiment name and unique run identifier."""

    run_id = f"run-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{uuid.uuid4().hex[:12]}"
    return f"n{config.n}-s{config.max_sweeps}-b{batch_size}-{run_id}", run_id


def environment():
    # Resolve repository provenance relative to the installed module rather
    # than the caller's shell.  Experiments are often started from another
    # working directory or a detached worktree.
    root = Path(__file__).resolve().parents[2]

    def command(args):
        try:
            proc = subprocess.run(args, cwd=root, text=True, capture_output=True, check=False)
        except FileNotFoundError as exc:
            return {"command": args, "exit_code": 127, "stdout": "", "stderr": str(exc)}
        return {"command": args, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    revision = command(["git", "rev-parse", "HEAD"])
    status = command(["git", "status", "--porcelain"])
    return {
        "python": platform.python_version(), "platform": platform.platform(),
        "numerical_precision": "float32",
        "source_root": str(root),
        "dependencies": {key: importlib.metadata.version(key) for key in ("numpy", "warp-lang", "asquerix", "rich")},
        "wheel_variant": "warp-lang 1.18.0 default PyPI CUDA 13.4 wheel",
        "gpu_query": command(["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,memory.used,display_active,compute_mode", "--format=csv"]),
        "git_revision": revision,
        "git_status": status,
        "source_revision": revision["stdout"].strip() if revision["exit_code"] == 0 else None,
        "source_dirty": bool(status["stdout"].strip()) if status["exit_code"] == 0 else None,
        "source_sha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted((root / "src").rglob("*.py"))},
    }


def scalar_records(scalars, cfg, offset):
    records = []
    for i, scalar in enumerate(scalars):
        feasible = bool(scalar["feasible"])
        initialized = int(scalar["termination"]) != 3
        record = {
            "trial_id": offset + i, "seed": cfg.seed, "rng_scheme": "splitmix64-counter-v1",
            "n": cfg.n, "side": float(scalar["side"]) if initialized else None,
            "termination_reason": TERMINATIONS[int(scalar["termination"])],
            "gpu_status": "GPU_FEASIBLE" if feasible else "NO_ACCEPTED_POSE",
            "validation_status": "NOT_CHECKED",
            "min_pair_separation_gpu": float(scalar["min_gap"]) if initialized and cfg.n > 1 else None,
            "min_wall_clearance_gpu": float(scalar["min_wall"]) if initialized else None,
            "max_penetration": float(scalar["max_penetration"]) if initialized else None,
            "final_step": float(scalar["final_step"]),
        }
        record.update({key: int(scalar[key]) for key in ("attempts", "sweeps", "accepted", "rejected", "proposals")})
        records.append(record)
    return records


def rank(record):
    return (record["side"], record["trial_id"])


def select_indices(records, *, sample_every, audit_ids, keep_best, threshold=None, retain_all=False, failures=0):
    reasons = {}
    def add(i, reason):
        reasons.setdefault(i, set()).add(reason)
    for i, record in enumerate(records):
        if retain_all:
            add(i, "all_correctness")
        if sample_every and record["trial_id"] % sample_every == 0:
            add(i, "periodic")
        if record["trial_id"] in audit_ids:
            add(i, "random_audit")
    candidates = sorted((i for i, r in enumerate(records) if r["gpu_status"] == "GPU_FEASIBLE"
                         and (threshold is None or rank(r) < threshold)), key=lambda i: rank(records[i]))
    for i in candidates[:keep_best]:
        add(i, "best_candidate")
    for i, record in enumerate(records):
        if failures and record["gpu_status"] != "GPU_FEASIBLE":
            add(i, "failure_example")
            failures -= 1
    return reasons, candidates


def _runner_integer(value, name, *, minimum, maximum):
    """Validate a bounded runner integer without accepting bool or floats."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    converted = int(value)
    if not minimum <= converted <= maximum:
        raise ValueError(f"{name} must be in [{minimum},{maximum}]")
    return converted


def _runner_seconds(value):
    """Validate a positive finite wall-time budget and return a float."""

    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError("max_seconds must be positive and finite")
    converted = float(value)
    if not math.isfinite(converted) or converted <= 0.0:
        raise ValueError("max_seconds must be positive and finite")
    return converted


def run(config: Config, *, trials=64, batch_size=32, trial_offset=0, device="cuda:0",
        output=None, experiment=None, run_id=None, sample_every=1000, keep_best=10, max_images=10,
        audit_size=16, failure_examples=3, retain_all=False, max_seconds=30.0,
        batch_factory=Batch, progress=None):
    config.validate()
    trials = _runner_integer(trials, "trials", minimum=1, maximum=2**31 - 1)
    batch_size = _runner_integer(batch_size, "batch_size", minimum=1, maximum=1048576)
    trial_offset = _runner_integer(trial_offset, "trial_offset", minimum=0, maximum=2**64 - 1)
    if trial_offset > 2**64 - trials:
        raise ValueError("trial_offset plus trials must fit unsigned 64 bits")
    sample_every = _runner_integer(sample_every, "sample_every", minimum=0, maximum=2**64 - 1)
    keep_best = _runner_integer(keep_best, "keep_best", minimum=0, maximum=2**31 - 1)
    max_images = _runner_integer(max_images, "max_images", minimum=0, maximum=2**31 - 1)
    audit_size = _runner_integer(audit_size, "audit_size", minimum=0, maximum=2**31 - 1)
    failure_examples = _runner_integer(failure_examples, "failure_examples", minimum=0, maximum=2**31 - 1)
    max_seconds = _runner_seconds(max_seconds)
    if not isinstance(retain_all, (bool, np.bool_)):
        raise ValueError("retain_all must be a boolean")
    retain_all = bool(retain_all)
    if progress is not None and not callable(progress):
        raise ValueError("progress must be callable")
    if run_id is None:
        generated_experiment, run_id = _default_experiment(config, batch_size)
        if experiment is None:
            experiment = generated_experiment
    else:
        run_id = _validate_run_id(run_id)
    if experiment is None:
        experiment = f"n{config.n}-s{config.max_sweeps}-b{batch_size}-{run_id}"
    experiment = validate_experiment_name(experiment)
    if output is None:
        output = Path("runs") / experiment / run_id
    else:
        output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    timings = {key: 0.0 for key in ("module_load_seconds", "warmup_seconds", "simulation_seconds",
                                   "device_seconds", "transfer_seconds", "validation_seconds",
                                   "render_seconds", "report_seconds", "persistence_seconds")}
    metadata = environment()
    metadata.update({
        "experiment_name": experiment,
        "experiment_slug": experiment,
        "experiment": experiment,
        "run_id": run_id,
        "n": config.n,
        "device": device,
    })
    options = dict(trials=trials, batch_size=batch_size, trial_offset=trial_offset, device=device,
                   experiment=experiment, experiment_name=experiment, experiment_slug=experiment,
                   run_id=run_id,
                   sample_every=sample_every, keep_best=keep_best, max_images=max_images,
                   audit_size=audit_size, failure_examples=failure_examples, retain_all=retain_all,
                   max_seconds=max_seconds)
    options["gzip_compression_level"] = GZIP_COMPRESSION_LEVEL
    metadata["compression"] = {"format": "gzip", "level": GZIP_COMPRESSION_LEVEL, "mtime": 0}
    initial_persistence_started = perf_counter_ns()
    write_json(output / "config.json", {"solver": asdict(config), "runner": options})
    write_json(output / "environment.json", metadata)
    audit_rng = np.random.default_rng(config.seed)
    audit_ids = {trial_offset + int(i) for i in audit_rng.choice(trials, min(trials, audit_size), replace=False)}
    write_json(output / "audit_ids.json", sorted(audit_ids))
    timings["persistence_seconds"] += (perf_counter_ns() - initial_persistence_started) / 1_000_000_000.0
    records, documents, leaderboard = [], {}, []
    batch = None
    validated_count = 0
    best_validated_L = None

    def device_label() -> str:
        """Format the configured selector together with Warp's actual device name."""

        selected = str(getattr(batch, "device", device))
        name = getattr(getattr(batch, "device", None), "name", None)
        if name:
            return f"{selected} ({name})"
        return selected

    def update_validation_progress(current: list[dict]) -> None:
        """Accumulate validation counters after a scalar batch is persisted."""

        nonlocal validated_count, best_validated_L
        for record in current:
            if (record.get("gpu_status") == "GPU_FEASIBLE"
                    and record.get("validation_status") == "NUMERICALLY_VALIDATED"
                    and record.get("side") is not None):
                validated_count += 1
                side = float(record["side"])
                if best_validated_L is None or side < best_validated_L:
                    best_validated_L = side

    def emit_progress(event: str, *, current_batch_trials: int = 0) -> None:
        """Emit one batch-boundary update without adding work when disabled."""

        if progress is None:
            return
        elapsed = perf_counter() - started
        completed = len(records)
        event_data = {
            "event": event,
            "experiment_name": experiment,
            "experiment": experiment,
            "run_id": run_id,
            "n": config.n,
            "device": device_label(),
            "device_selector": device,
            "device_name": getattr(getattr(batch, "device", None), "name", None),
            "requested": trials,
            "requested_trials": trials,
            "completed": completed,
            "completed_trials": completed,
            "current": completed,
            "current_count": completed,
            "current_batch_trials": current_batch_trials,
            "batch_size": batch_size,
            "elapsed_seconds": elapsed,
            "device_seconds": timings["device_seconds"],
            "simulation_seconds": timings["simulation_seconds"],
            "validated_count": validated_count,
            "best_validated_L": best_validated_L,
        }
        progress(event_data)

    emit_progress("init")
    stop = {"requested": False, "observed_at": None}
    def stop_handler(signum, frame):
        if not stop["requested"]:
            stop.update(requested=True, observed_at=perf_counter())
    old_handler = signal.signal(signal.SIGINT, stop_handler)
    search_started = None
    completed_at = None
    jsonl_close_reference = None
    jsonl_completed = False
    error = None
    try:
        batch = batch_factory(config, batch_size, device)
        timings["module_load_seconds"] = batch.module_load_seconds
        metadata["warp_device"] = str(batch.device)
        metadata["device"] = str(batch.device)
        metadata["device_selector"] = device
        metadata["device_name"] = getattr(batch.device, "name", None)
        metadata["device_uuid"] = getattr(batch.device, "uuid", None)
        metadata["kernel_properties"] = getattr(batch, "kernel_properties", {})
        # Warm-up uses the identical production budget, and repeats ID 0 without
        # recording it as an attempted trial. Production IDs are never skipped.
        if not stop["requested"]:
            _, warm_timing = batch.run(1, trial_offset)
            timings["warmup_seconds"] = warm_timing["simulation_seconds"] + warm_timing["transfer_seconds"]
        search_started = perf_counter()
        with open_jsonl_writer(output / "trials.jsonl") as scalar_file:
            while len(records) < trials:
                if stop["requested"]:
                    if jsonl_close_reference is None:
                        jsonl_close_reference = stop["observed_at"]
                    break
                search_elapsed = perf_counter() - search_started
                if search_elapsed >= max_seconds:
                    if jsonl_close_reference is None:
                        jsonl_close_reference = search_started + search_elapsed
                    break
                offset = trial_offset + len(records)
                count = min(batch_size, trials - len(records))
                emit_progress("batch-start", current_batch_trials=count)
                scalars, timing = batch.run(count, offset)
                completed_at = perf_counter()
                for key, value in timing.items():
                    if key == "max_stage_seconds":
                        timings[key] = max(timings.get(key, 0.0), value)
                    else:
                        timings[key] += value
                current = scalar_records(scalars, config, offset)
                threshold = rank(leaderboard[-1]) if keep_best and len(leaderboard) >= keep_best else None
                failure_count = sum(bool({"failure_example", "invalid_candidate"}.intersection(d["selection_reasons"]))
                                    for d in documents.values())
                reasons, candidates = select_indices(current, sample_every=sample_every, audit_ids=audit_ids,
                    keep_best=keep_best, threshold=threshold, retain_all=retain_all,
                    failures=max(0, failure_examples - failure_count))
                def collect(selection):
                    indices = sorted(i for i in selection if current[i]["side"] is not None)
                    poses, transfer = batch.get_poses(indices)
                    timings["transfer_seconds"] += transfer
                    pose_map = dict(zip(indices, poses))
                    for i in sorted(selection):
                        record = current[i]
                        trial_id = record["trial_id"]
                        if i in pose_map:
                            begin = perf_counter()
                            validation = validate_pose(pose_map[i], record["side"])
                            timings["validation_seconds"] += perf_counter() - begin
                            record["validation_status"] = validation["status"]
                            record["independent_validation"] = validation
                            document = {**record, "poses": pose_map[i].tolist(), "pose_dtype": "float32", "validation": validation}
                        else:
                            document = {**record, "poses": [], "validation": {"status": "NOT_CHECKED"},
                                        "diagnostic": "Initialization exhausted; no complete pose exists."}
                        document["selection_reasons"] = sorted(selection[i])
                        documents[trial_id] = document
                        if record["validation_status"] == "NUMERICALLY_VALIDATED" and record["gpu_status"] == "GPU_FEASIBLE":
                            if trial_id not in {r["trial_id"] for r in leaderboard}:
                                leaderboard.append(record)
                    leaderboard.sort(key=rank)
                    del leaderboard[keep_best:]
                collect(reasons)
                failure_count = sum(bool({"failure_example", "invalid_candidate"}.intersection(d["selection_reasons"]))
                                    for d in documents.values())
                # If candidates are independently invalid/indeterminate, audit
                # further ranked candidates before promoting a replacement.
                remaining = [i for i in candidates if i not in reasons]
                while keep_best and remaining:
                    cutoff = rank(leaderboard[-1]) if len(leaderboard) >= keep_best else None
                    worthy = [i for i in remaining if cutoff is None or rank(current[i]) < cutoff]
                    if not worthy:
                        break
                    chunk = worthy[:keep_best]
                    collect({i: {"best_candidate"} for i in chunk})
                    remaining = [i for i in remaining if i not in chunk]
                # Preserve checked valid/indeterminate candidate geometry after
                # supersession. Invalid debug examples retain their explicit cap.
                leader_ids = {r["trial_id"] for r in leaderboard}
                for tid, doc in list(documents.items()):
                    if doc["selection_reasons"] == ["best_candidate"] and tid not in leader_ids:
                        if doc["validation_status"] == "INVALID":
                            if failure_count < failure_examples:
                                doc["selection_reasons"].append("invalid_candidate")
                                failure_count += 1
                            else:
                                del documents[tid]
                        else:
                            doc["selection_reasons"].append("superseded_candidate")
                begin = perf_counter()
                for record in current:
                    scalar_file.write(json.dumps(record, allow_nan=False) + "\n")
                scalar_file.flush()
                records.extend(current)
                persisted_at = perf_counter()
                timings["persistence_seconds"] += persisted_at - begin
                jsonl_close_reference = persisted_at
                update_validation_progress(current)
                emit_progress("batch-completed", current_batch_trials=count)
        jsonl_completed = True
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.signal(signal.SIGINT, old_handler)
        end_search = perf_counter()
        if jsonl_completed and jsonl_close_reference is not None:
            # The writer closes the text wrapper, gzip footer, and fsync/rename
            # after the last scalar write.  Attribute that host-only interval
            # to persistence without another clock call that would affect the
            # bounded deadline/signal scheduling path.
            timings["persistence_seconds"] += max(0.0, end_search - jsonl_close_reference)
        metadata["stop_reason"] = ("ERROR" if error else "SIGINT" if stop["requested"] else
                                   "MAX_SECONDS" if len(records) < trials else "TRIALS_COMPLETED")
        metadata["run_status"] = (
            "FAILED" if error else "COMPLETED" if len(records) == trials else "PARTIAL"
        )
        metadata["error"] = error
        deadline = search_started + max_seconds if search_started else None
        metadata["stop_observed_to_batch_completion_seconds"] = (
            max(0.0, (completed_at or end_search) - stop["observed_at"]) if stop["requested"] else
            max(0.0, completed_at - deadline) if completed_at and deadline else 0.0)
        metadata["deadline_overrun_seconds"] = max(0.0, end_search - deadline) if deadline else 0.0
        metadata["search_elapsed_seconds"] = end_search - search_started if search_started else 0.0
        metadata["requested_trials"] = trials
        metadata["completed_trials"] = len(records)
        metadata["audit_sample_completed"] = len(audit_ids.intersection(r["trial_id"] for r in records))
        metadata["random_audit_outcomes"] = {
            status: sum(r["trial_id"] in audit_ids and r["validation_status"] == status for r in records)
            for status in ("NUMERICALLY_VALIDATED", "INDETERMINATE", "INVALID", "NOT_CHECKED")}
        metadata["leaderboard"] = leaderboard
        metadata["retained_pose_count"] = len(documents)
        metadata["reproducibility"] = "Same seed/global IDs/config/kernel/hardware: tested bitwise; no cross-device/version guarantee."
        metadata["persistence_timing_boundary"] = (
            "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, "
            "pose/validation JSON, and final environment writes; report_seconds includes "
            "report, histogram, and summary persistence."
        )
        emit_progress("finalizing")
        begin = perf_counter()
        (output / "poses").mkdir(exist_ok=True)
        for tid, document in sorted(documents.items()):
            write_json(output / "poses" / f"trial-{tid}.json", document)
        write_json(output / "validation.json", {str(tid): d["validation"] for tid, d in documents.items()})
        timings["persistence_seconds"] += perf_counter() - begin
        begin = perf_counter()
        paths = render_selected(list(documents.values()), output / "svg", max_images)
        timings["render_seconds"] = perf_counter() - begin
        metadata["svg_count"] = len(paths)
        final_environment_started = perf_counter_ns()
        write_json(output / "environment.json", metadata)
        timings["persistence_seconds"] += (perf_counter_ns() - final_environment_started) / 1_000_000_000.0
        summary = write_report(output, records, timings, metadata={
                     "experiment_name": experiment,
                     "experiment_slug": experiment,
                     "experiment": experiment,
                     "run_id": run_id,
                     "run_status": metadata["run_status"],
                     "stop_reason": metadata["stop_reason"],
                     "requested_trials": trials,
                     "completed_trials": len(records),
                     "retained_pose_count": len(documents),
                     "persistence_timing_boundary": metadata["persistence_timing_boundary"],
                     "leaderboard": leaderboard,
                     "solver": asdict(config)}, started_at=started)
        return_value = {
            "directory": str(output),
            "summary": summary,
            "experiment_name": experiment,
            "experiment_slug": experiment,
            "run_id": run_id,
            "run_status": metadata["run_status"],
            "metadata": metadata,
        }
    return return_value
