"""Selected CUDA replays, independent checks, and bounded companion exports.

This module never changes an original experiment or its scientific statistics.
The recorder is imported only when a selected replay is actually scheduled.
"""
from dataclasses import fields
import hashlib
import math
from pathlib import Path
import re
import signal
import subprocess
import tempfile
from time import perf_counter
from uuid import uuid4

import numpy as np

from .geometry import validate_pose
from .persistence import read_json, resolve_path, write_json

OPERATION_SCHEMA = "asquerix-trace-operation-v1"
PUBLICATION_RESERVE = 64 * 1024


def options_valid(mode="accepted", max_frames=256, every=16, max_mib=10, count=1):
    for name, value, low, high in (("selected trials", count, 0, 16),
                                  ("max_frames", max_frames, 2, 4096),
                                  ("every", every, 1, 2**31 - 1)):
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in [{low},{high}]")
    if mode not in {"accepted", "sweeps"}:
        raise ValueError("mode must be accepted or sweeps")
    if isinstance(max_mib, bool) or not math.isfinite(max_mib) or not 0 < max_mib <= 100:
        raise ValueError("max_mib must be positive, finite, and at most 100")
    limit = int(max_mib * 1024**2)
    if limit <= PUBLICATION_RESERVE:
        raise ValueError("export budget must exceed the 64 KiB manifest/publication reserve")
    return limit


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _browser_ids(value):
    if isinstance(value, dict):
        return {key: str(item) if key in {"seed", "trial_id", "first_trial_id", "last_trial_id"} and item is not None
                else _browser_ids(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_browser_ids(item) for item in value]
    return value


def select_references(directory, *, trial_ids=None, best=None):
    """Select the existing validated leaderboard once, using global IDs."""
    directory = Path(directory)
    if (trial_ids is None) == (best is None):
        raise ValueError("choose repeated --trial-id or --best, exclusively")
    if best is not None:
        options_valid(count=best)
        summary = read_json(directory / "summary.json")
        candidates = summary.get("metadata", {}).get("leaderboard", [])
        ordered = sorted((r for r in candidates if r.get("gpu_status") == "GPU_FEASIBLE"
                          and r.get("validation_status") == "NUMERICALLY_VALIDATED"
                          and r.get("side") is not None), key=lambda r: (r["side"], r["trial_id"]))
        identifiers = list(dict.fromkeys(r["trial_id"] for r in ordered))
    else:
        options_valid(count=len(trial_ids))
        identifiers = list(dict.fromkeys(trial_ids))
    selected = []
    for trial_id in identifiers:
        if isinstance(trial_id, bool) or not isinstance(trial_id, int) or not 0 <= trial_id < 2**64:
            raise ValueError("trial IDs must fit unsigned 64 bits")
        path = resolve_path(directory / "poses" / f"trial-{trial_id}.json")
        if not path.is_file():
            if best is not None:
                continue
            raise ValueError(f"REFERENCE_INCOMPLETE: trial {trial_id} has no retained original pose in {directory}")
        document = read_json(path)
        if not isinstance(document, dict) or document.get("trial_id") != trial_id:
            raise ValueError(f"Malformed reference identity: {path}")
        if best is not None and (document.get("validation_status") != "NUMERICALLY_VALIDATED"
                                or document.get("gpu_status") != "GPU_FEASIBLE"):
            continue
        if document.get("termination_reason") != "INIT_FAILED":
            pose = np.asarray(document.get("poses"))
            if pose.shape != (document.get("n"), 3) or pose.dtype.kind not in "iuf":
                raise ValueError(f"REFERENCE_INCOMPLETE: malformed retained pose: {path}")
        selected.append((trial_id, document, path))
        if best is not None and len(selected) >= best:
            break
    return selected[:best] if best is not None else selected


def _known_fp32(document, environment):
    if "pose_dtype" in document:
        return document["pose_dtype"] == "float32"
    if environment.get("numerical_precision") == "float32":
        return True
    # Legacy project JSON had no dtype tag. Verify its recorded source locally,
    # without executing old code or changing the checkout/dependencies.
    revision = environment.get("source_revision") or environment.get("git_revision", {}).get("stdout", "").strip()
    digest = environment.get("source_sha256", {}).get("src/asquerix/gpu.py")
    if not revision or not digest or re.fullmatch(r"[0-9a-fA-F]{40,64}", revision) is None:
        return False
    root = Path(__file__).resolve().parents[2]
    proc = subprocess.run(["git", "show", f"{revision}:src/asquerix/gpu.py"], cwd=root, capture_output=True)
    return (proc.returncode == 0 and hashlib.sha256(proc.stdout).hexdigest() == digest
            and b"dtype=wp.vec3" in proc.stdout and b"class Result:" in proc.stdout
            and b"side: float" in proc.stdout)


def compare_reference(document, replay_record, arrays, original_environment):
    """Compare defined values, including FP32 signed-zero bits; never padding."""
    compared, mismatches, missing = [], [], []
    fp32 = _known_fp32(document, original_environment)
    floats = {"side", "min_pair_separation_gpu", "min_wall_clearance_gpu", "max_penetration", "final_step"}
    required = ("n", "seed", "trial_id", "side", "gpu_status", "termination_reason", "final_step",
                "attempts", "sweeps", "accepted", "rejected", "proposals",
                "min_pair_separation_gpu", "min_wall_clearance_gpu", "max_penetration")
    for name in required:
        if name not in document:
            missing.append(name)
            continue
        expected, actual = document[name], replay_record[name]
        if name in floats and expected is not None and actual is not None:
            if not fp32:
                missing.append(f"{name}: original dtype unknown")
                continue
            old = np.asarray(expected, dtype=np.float64)
            cast = old.astype("<f4")
            if old.tobytes() != cast.astype(np.float64).tobytes():
                missing.append(f"{name}: not a lossless FP32 value")
                continue
            equal = cast.tobytes() == np.asarray(actual, dtype="<f4").tobytes()
        else:
            equal = expected == actual
        compared.append(name)
        if not equal:
            mismatches.append(name)
    if len(arrays.get("poses", [])) and document.get("poses"):
        old = np.asarray(document["poses"], dtype=np.float64)
        cast = old.astype("<f4")
        if not fp32 or old.tobytes() != cast.astype(np.float64).tobytes():
            missing.append("poses: original dtype unknown or not lossless FP32")
        else:
            compared.extend(["poses.x", "poses.y", "poses.theta", "square_ids (original array order)"])
            if cast.shape != arrays["poses"][-1].shape or cast.tobytes() != arrays["poses"][-1].tobytes():
                mismatches.append("poses")
            if "square_ids" in document and list(document["square_ids"]) != arrays["square_ids"].tolist():
                mismatches.append("square_ids")
    elif document.get("termination_reason") != "INIT_FAILED":
        missing.append("poses")
    initial_compared = False
    if "initial_poses" in document and len(arrays.get("poses", [])) and fp32:
        initial = np.asarray(document["initial_poses"], dtype=np.float64)
        cast = initial.astype("<f4")
        if initial.tobytes() == cast.astype(np.float64).tobytes():
            initial_compared = True
            compared.append("initial_poses")
            if cast.tobytes() != arrays["poses"][0].tobytes():
                mismatches.append("initial_poses")
        else:
            missing.append("initial_poses dtype")
    status = "REPLAY_MISMATCH" if mismatches else "REFERENCE_INCOMPLETE" if missing else "REPLAY_MATCHED"
    return dict(status=status, compared_fields=compared, mismatches=mismatches, missing_fields=missing,
                initial_compared=initial_compared,
                scope="Newly recorded replay. Exact endpoint and defined result fields were compared where available; matching them does not establish identity of the unrecorded intermediate history. Numerical validation is not mathematical certification.")


def provenance(original, replay):
    keys = ("source_revision", "source_sha256", "dependencies", "device_uuid", "device_name", "driver_version")
    missing = [key for key in keys if original.get(key) is None]
    differences = [key for key in keys if key not in missing and original[key] != replay.get(key)]
    return dict(status="PROVENANCE_DIFFERENT" if differences else "PROVENANCE_INCOMPLETE" if missing else "PROVENANCE_MATCHED",
                differences=differences, missing_fields=missing, original=original, replay=replay)


def _device_provenance(environment):
    """Resolve the selected original physical GPU, without guessing multi-GPU mappings."""
    import csv
    env = dict(environment)
    rows = list(csv.reader(env.get("gpu_query", {}).get("stdout", "").splitlines()))
    candidates = [row for row in rows[1:] if len(row) >= 3
                  and (row[1].strip() == env.get("device_uuid") or (not env.get("device_uuid") and len(rows) == 2))]
    if len(candidates) == 1:
        row = candidates[0]
        env.update(device_name=row[0].strip(), device_uuid=row[1].strip(), driver_version=row[2].strip())
    return env


def record(directory, *, output, trial_ids=None, best=None, mode="accepted", max_frames=256,
           every=16, max_mib=10, device="cuda:0", progress=None, companion=True,
           replay_function=None, stop_requested=None):
    """Finalize a bounded operation. Original files and rankings are read-only."""
    started = perf_counter()
    limit = options_valid(mode, max_frames, every, max_mib, best if best is not None else len(trial_ids or []))
    directory, output = Path(directory), Path(output)
    if companion and (output.resolve() == directory.resolve() or output.resolve().is_relative_to(directory.resolve())):
        raise ValueError("standalone trace output must be outside the original experiment")
    selected = select_references(directory, trial_ids=trial_ids, best=best)
    configuration = read_json(directory / "config.json")
    from .gpu import Config
    names = {f.name for f in fields(Config)}
    if set(configuration.get("solver", {})) != names:
        raise ValueError("Original solver configuration is incomplete or unsupported; no defaults or solver overrides are applied")
    config = Config(**configuration["solver"])
    config.validate()
    for trial_id, document, _ in selected:
        if document.get("n") != config.n or document.get("seed") != config.seed:
            raise ValueError(f"Original trial {trial_id} identity disagrees with saved configuration")
    original_environment = _device_provenance(read_json(directory / "environment.json"))
    if companion:
        output.mkdir(parents=True, exist_ok=False)
    elif output.resolve() != directory.resolve():
        raise ValueError("automatic recording must target its just-finalized campaign")
    trace_directory = output / "trajectories"
    trace_directory.mkdir(exist_ok=False)
    from .runner import environment, scalar_records
    from .trajectory_format import SCHEMA, encode_npz, write_bytes
    from .trajectory_viewer import render_html
    replay_environment = environment()
    operation = dict(schema=OPERATION_SCHEMA, collection_kind="trajectory-replay",
                     operation_id=f"trace-{uuid4().hex[:12]}", source_directory=str(directory),
                     config=configuration["solver"], replay_environment=replay_environment,
                     requested_count=best if best is not None else len(trial_ids), selected_count=len(selected),
                     completed_count=0, status="COMPLETE", export_limit_bytes=limit,
                     publication_reserved_bytes=PUBLICATION_RESERVE,
                     estimated_trace_memory_bytes=max_frames * (12 * config.n + 34),
                     options=dict(mode=mode, max_frames=max_frames, every=every), artifacts=[], outcomes=[],
                     source_artifacts=[dict(path=str(path), sha256=sha256(path)) for path in
                                       (resolve_path(directory / "config.json"), resolve_path(directory / "environment.json"), resolve_path(directory / "summary.json"))],
                     timings={key: 0.0 for key in ("compile_seconds", "device_seconds", "transfer_seconds", "validation_seconds", "export_seconds")})
    stop = {"requested": False, "at": None}
    def handler(signum, frame):
        stop.update(requested=True, at=perf_counter())
    previous = signal.signal(signal.SIGINT, handler)
    used = 0
    try:
        for trial_id, document, reference_path in selected:
            if stop["requested"] or (stop_requested and stop_requested()):
                operation["status"] = "INTERRUPTED"
                break
            if progress:
                progress(dict(event="replay-start", trial_id=str(trial_id), completed=operation["completed_count"], total=len(selected)))
            try:
                if replay_function is None:
                    from .trace_gpu import replay
                    replay_function = replay
                replayed = replay_function(config, trial_id, device=device, mode=mode, max_frames=max_frames, every=every)
                arrays = replayed["arrays"]
                replay_record = scalar_records(replayed["scalars"], config, trial_id)[0]
                replay_environment.update(device_uuid=replayed["device"]["uuid"], device_name=replayed["device"]["name"])
                replay_environment = _device_provenance(replay_environment)
                for key, value in replayed["timings"].items():
                    operation["timings"][key] = operation["timings"].get(key, 0.0) + value
                comparison = compare_reference(document, replay_record, arrays, original_environment)
                begin = perf_counter()
                validations = []
                for frame in range(len(arrays["side"])):
                    # Provisional geometry is measured but never receives an accepted badge.
                    provisional = int(arrays["phase"][frame]) in {1, 2, 4}
                    validations.append(dict(frame=frame, sequence=int(arrays["sequence"][frame]),
                                            phase=int(arrays["phase"][frame]), provisional=provisional,
                                            validation=validate_pose(arrays["poses"][frame], float(arrays["side"][frame]))))
                validation_seconds = perf_counter() - begin
                operation["timings"]["validation_seconds"] += validation_seconds
                metadata = dict(schema=SCHEMA, n=config.n, trial_id=str(trial_id), seed=str(config.seed),
                                frame_count=len(arrays["side"]), config={**configuration["solver"], "seed": str(config.seed)},
                                mode=mode, sampling=replayed["sampling"], comparison=comparison,
                                termination_reason=replay_record["termination_reason"],
                                replay_result={**replay_record, "trial_id": str(trial_id), "seed": str(config.seed)},
                                original_result={k: str(v) if k in {"seed", "trial_id"} else v for k, v in document.items() if k != "poses"},
                                validations=validations, provenance=provenance(original_environment, replay_environment),
                                source_artifacts={str(path): sha256(path) for path in [reference_path, resolve_path(directory / "config.json"), resolve_path(directory / "environment.json")]},
                                timings={**replayed["timings"], "validation_seconds": validation_seconds})
                metadata = _browser_ids(metadata)
                begin = perf_counter()
                # Build at most one bounded export in temporary storage, then check
                # actual bytes before any final file is made visible.
                with tempfile.TemporaryDirectory(prefix="asquerix-trace-") as temporary:
                    root = Path(temporary)
                    stem = f"trial-{trial_id}"
                    files = []
                    if len(arrays["side"]):
                        numeric = encode_npz(arrays)
                        metadata["numeric_sha256"] = hashlib.sha256(numeric).hexdigest()
                        metadata["numeric_size_bytes"] = len(numeric)
                        write_bytes(root / f"{stem}.npz", numeric)
                        write_bytes(root / f"{stem}.html", render_html(arrays, metadata))
                        files.extend([root / f"{stem}.npz", root / f"{stem}.html"])
                    else:
                        metadata["recording_status"] = "INITIALIZATION_FAILED"
                    files.append(write_json(root / f"{stem}.meta.json", metadata))
                    entries = [dict(path=f"trajectories/{path.name}", size_bytes=path.stat().st_size,
                                    sha256=sha256(path), trial_id=str(trial_id), retained_frames=len(arrays["side"])) for path in files]
                    candidate = {**operation, "artifacts": operation["artifacts"] + entries}
                    receipt = write_json(root / "trace.json", candidate)
                    new_size = sum(entry["size_bytes"] for entry in entries)
                    if used + new_size + receipt.stat().st_size + PUBLICATION_RESERVE > limit:
                        operation.update(status="EXPORT_LIMIT", error=f"Trial {trial_id} needs {new_size} export bytes; {used} bytes are finalized and limit is {limit} including operation metadata and publication reserve")
                        break
                    finalized = []
                    try:
                        for path in files:
                            target = trace_directory / path.name
                            if target.exists():
                                raise ValueError(f"Trajectory output already exists: {target}")
                            write_bytes(target, path.read_bytes())
                            finalized.append(target)
                    except BaseException:
                        # Remove only this operation's pending trial group. Earlier
                        # finalized trials remain available for safe publication.
                        for target in finalized:
                            target.unlink(missing_ok=True)
                        raise
                    used += new_size
                    operation["artifacts"].extend(entries)
                operation["timings"]["export_seconds"] += perf_counter() - begin
                operation["completed_count"] += 1
                operation["outcomes"].append(dict(trial_id=str(trial_id), status=comparison["status"],
                                                 recording_status="INITIALIZATION_FAILED" if not len(arrays["side"]) else "RECORDED",
                                                 termination_reason=replay_record["termination_reason"],
                                                 retained_frames=len(arrays["side"]), sampling=replayed["sampling"]))
                if progress:
                    progress(dict(event="replay-completed", trial_id=str(trial_id), completed=operation["completed_count"], total=len(selected), status=comparison["status"]))
            except (Exception, KeyboardInterrupt) as exc:
                operation.update(status="INTERRUPTED" if isinstance(exc, KeyboardInterrupt) else "REPLAY_ERROR", error=f"{type(exc).__name__}: {exc}"[:2048])
                break
        if stop["requested"]:
            operation["status"] = "INTERRUPTED"
        operation["stop_drain_seconds"] = max(0.0, perf_counter() - stop["at"]) if stop["at"] else 0.0
    finally:
        signal.signal(signal.SIGINT, previous)
    operation["replay_environment"] = replay_environment
    operation["timings"]["total_postprocessing_seconds"] = perf_counter() - started
    operation["artifact_bytes"] = used
    receipt = write_json(output / "trace.json", operation)
    # The publication manifest measures this operation file separately. Avoid
    # embedding its own compressed size recursively in its contents.
    operation["total_export_bytes"] = used + receipt.stat().st_size
    if used + receipt.stat().st_size + PUBLICATION_RESERVE > limit:
        raise RuntimeError("Trace metadata exceeded its reserved export budget")
    return operation
