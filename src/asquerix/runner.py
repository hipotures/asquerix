"""Batch scheduling, independent audits, and durable output at batch boundaries."""
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import signal
import subprocess
from time import perf_counter

import numpy as np

from .geometry import validate_pose
from .gpu import Batch, Config, TERMINATIONS
from .output import render_selected, write_report


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def environment():
    def command(args):
        try:
            proc = subprocess.run(args, text=True, capture_output=True, check=False)
        except FileNotFoundError as exc:
            return {"command": args, "exit_code": 127, "stdout": "", "stderr": str(exc)}
        return {"command": args, "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    root = Path(__file__).resolve().parents[2]
    return {
        "python": platform.python_version(), "platform": platform.platform(),
        "dependencies": {key: importlib.metadata.version(key) for key in ("numpy", "warp-lang", "asquerix")},
        "wheel_variant": "warp-lang 1.18.0 default PyPI CUDA 13.4 wheel",
        "gpu_query": command(["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,memory.used,display_active,compute_mode", "--format=csv"]),
        "git_revision": command(["git", "rev-parse", "HEAD"]),
        "git_status": command(["git", "status", "--porcelain"]),
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


def run(config: Config, *, trials=64, batch_size=32, trial_offset=0, device="cuda:0",
        output="runs/run", sample_every=1000, keep_best=10, max_images=10,
        audit_size=16, failure_examples=3, retain_all=False, max_seconds=30.0,
        batch_factory=Batch):
    config.validate()
    if not 1 <= trials <= 2**31 - 1 or not 0 <= trial_offset <= 2**64 - trials:
        raise ValueError("trials must be in [1,2**31-1] and the global range must fit uint64")
    if not 1 <= batch_size <= 65536 or not np.isfinite(max_seconds) or max_seconds <= 0:
        raise ValueError("batch_size must be in [1,65536]; max_seconds must be positive and finite")
    if min(sample_every, keep_best, max_images, audit_size, failure_examples) < 0:
        raise ValueError("output selection counts must be non-negative")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    timings = {key: 0.0 for key in ("module_load_seconds", "warmup_seconds", "simulation_seconds",
                                   "device_seconds", "transfer_seconds", "validation_seconds",
                                   "render_seconds", "report_seconds", "persistence_seconds")}
    metadata = environment()
    options = dict(trials=trials, batch_size=batch_size, trial_offset=trial_offset, device=device,
                   sample_every=sample_every, keep_best=keep_best, max_images=max_images,
                   audit_size=audit_size, failure_examples=failure_examples, retain_all=retain_all,
                   max_seconds=max_seconds)
    write_json(output / "config.json", {"solver": asdict(config), "runner": options})
    write_json(output / "environment.json", metadata)
    audit_rng = np.random.default_rng(config.seed)
    audit_ids = {trial_offset + int(i) for i in audit_rng.choice(trials, min(trials, audit_size), replace=False)}
    write_json(output / "audit_ids.json", sorted(audit_ids))
    records, documents, leaderboard = [], {}, []
    stop = {"requested": False, "observed_at": None}
    def stop_handler(signum, frame):
        if not stop["requested"]:
            stop.update(requested=True, observed_at=perf_counter())
    old_handler = signal.signal(signal.SIGINT, stop_handler)
    search_started = None
    completed_at = None
    error = None
    try:
        batch = batch_factory(config, batch_size, device)
        timings["module_load_seconds"] = batch.module_load_seconds
        metadata["warp_device"] = str(batch.device)
        metadata["kernel_properties"] = getattr(batch, "kernel_properties", {})
        # Warm-up uses the identical production budget, and repeats ID 0 without
        # recording it as an attempted trial. Production IDs are never skipped.
        if not stop["requested"]:
            _, warm_timing = batch.run(1, trial_offset)
            timings["warmup_seconds"] = warm_timing["simulation_seconds"] + warm_timing["transfer_seconds"]
        search_started = perf_counter()
        with (output / "trials.jsonl").open("w", encoding="utf-8") as scalar_file:
            while len(records) < trials:
                if stop["requested"] or perf_counter() - search_started >= max_seconds:
                    break
                offset = trial_offset + len(records)
                count = min(batch_size, trials - len(records))
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
                            document = {**record, "poses": pose_map[i].tolist(), "validation": validation}
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
                # Keep final leaderboard plus the explicitly bounded other rules.
                leader_ids = {r["trial_id"] for r in leaderboard}
                for tid, doc in list(documents.items()):
                    if doc["selection_reasons"] == ["best_candidate"] and tid not in leader_ids:
                        if doc["validation_status"] == "INVALID" and failure_count < failure_examples:
                            doc["selection_reasons"].append("invalid_candidate")
                            failure_count += 1
                        else:
                            del documents[tid]
                begin = perf_counter()
                for record in current:
                    scalar_file.write(json.dumps(record, allow_nan=False) + "\n")
                scalar_file.flush()
                records.extend(current)
                timings["persistence_seconds"] += perf_counter() - begin
                print(f"Completed {len(records)}/{trials} trials; best numerical side="
                      f"{leaderboard[0]['side'] if leaderboard else 'none'}", flush=True)
    except BaseException as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        signal.signal(signal.SIGINT, old_handler)
        end_search = perf_counter()
        metadata["stop_reason"] = ("ERROR" if error else "SIGINT" if stop["requested"] else
                                   "MAX_SECONDS" if len(records) < trials else "TRIALS_COMPLETED")
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
        write_json(output / "environment.json", metadata)
        begin = perf_counter()
        timings["end_to_end_seconds"] = perf_counter() - started
        write_report(output, records, timings, metadata={"stop_reason": metadata["stop_reason"],
                     "requested_trials": trials, "retained_pose_count": len(documents),
                     "leaderboard": leaderboard, "solver": asdict(config)})
        timings["report_seconds"] = perf_counter() - begin
        timings["end_to_end_seconds"] = perf_counter() - started
        summary = write_report(output, records, timings, metadata={"stop_reason": metadata["stop_reason"],
                     "requested_trials": trials, "retained_pose_count": len(documents),
                     "leaderboard": leaderboard, "solver": asdict(config)})
        return_value = {"directory": str(output), "summary": summary}
    return return_value
