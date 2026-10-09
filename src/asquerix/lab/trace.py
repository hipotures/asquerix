"""Selected strategy replays with exact endpoint references and the existing viewer."""

from __future__ import annotations

import copy
from pathlib import Path
from time import perf_counter

import numpy as np

from ..geometry import validate_pose
from ..persistence import read_json, write_json
from ..trajectory_format import ARRAY_DTYPES, atomic_write_bytes, validate_arrays
from ..trajectory_viewer import render_html
from .config import Campaign, digest, uint64
from .storage import check_quota, load_npz, primitive_scalar, sha256, write_npz
from .strategy import compile_program

SCHEMA = "asquerix-strategy-trace-v1"
EXTRA_DTYPES = {"best_side": "<f4", "pc": "<i4", "flags": "<i4", "mask": "<u4",
                "work": "<u8", "rng_draws": "<u8", "outcome": "<i4", "vm_sequence": "<u8"}


def load_trace(path: Path) -> tuple[dict, dict]:
    metadata = read_json(path.with_suffix(".meta.json.gz"))
    if metadata.get("schema") != SCHEMA or not 3 <= metadata.get("frame_count", 0) <= 256 or not 1 <= metadata.get("n", 0) <= 32:
        raise ValueError("Invalid strategy trace metadata bounds")
    uint64(metadata["trial_id"])
    uint64(metadata["seed"])
    if metadata.get("numeric_sha256") != sha256(path):
        raise ValueError("Strategy trace checksum mismatch")
    frames, n = metadata["frame_count"], metadata["n"]
    expected = {name: (dtype, (frames,)) for name, dtype in ARRAY_DTYPES.items()}
    expected["poses"] = (np.dtype("<f4"), (frames, n, 3))
    expected["square_ids"] = (np.dtype("<i4"), (n,))
    expected.update({name: (np.dtype(dtype), (frames,)) for name, dtype in EXTRA_DTYPES.items()})
    arrays = load_npz(path, expected=expected)
    program = compile_program(metadata["strategy"]["program"]["authored"])
    if program.program_hash != metadata["strategy"]["program"]["hash"]:
        raise ValueError("Trace program hash mismatch")
    if np.any(arrays["pc"] < -1) or np.any(arrays["pc"] >= len(program.code)):
        raise ValueError("Trace instruction index out of range")
    if np.any(arrays["mask"].astype(np.uint64) >= 2**n):
        raise ValueError("Trace mask exceeds square IDs")
    if np.any(arrays["flags"] < 0) or np.any(arrays["flags"] > 511):
        raise ValueError("Trace role flags invalid")
    viewer_metadata = {**metadata, "schema": "asquerix-trajectory-v1"}
    validate_arrays({name: arrays[name] for name in ARRAY_DTYPES}, viewer_metadata)
    return arrays, metadata


def replay(campaign: Campaign, directory: Path, *, candidate: dict, row: dict, bank: dict,
           reference_arrays: dict, reference_index: int, provenance: dict,
           cancelled=lambda: False) -> dict:
    from .gpu import OUTCOMES, StrategyBatch, defined_fields
    program = compile_program(candidate["program"]["authored"])
    index = np.flatnonzero(bank["ids"] == np.uint64(int(row["initial_id"])))
    if len(index) != 1:
        raise ValueError("Replay initial identity is not in the frozen bank")
    slot = int(index[0])
    batch = StrategyBatch(campaign, [program], bank["poses"][[slot]], bank["initial_results"][[slot]],
                          bank["ids"][[slot]], np.asarray([int(row["replicate"])], dtype=np.uint64),
                          np.asarray([0], dtype=np.int32), recording=True)
    while not batch.advance(cancel=cancelled()):
        pass
    states, best, current = batch.collect()
    mismatches = []
    compared = []
    for name, array in defined_fields(states).items():
        expected = reference_arrays["state_" + name][reference_index:reference_index + 1]
        compared.append(name)
        if array.dtype != expected.dtype or array.shape != expected.shape or array.tobytes() != expected.tobytes():
            mismatches.append(name)
    for name, actual in (("best_poses", best), ("current_poses", current)):
        expected = reference_arrays[name][reference_index:reference_index + 1]
        compared.append(name)
        if actual.dtype != expected.dtype or actual.shape != expected.shape or actual.tobytes() != expected.tobytes():
            mismatches.append(name)
    comparison = {"status": "REPLAY_MATCHED" if not mismatches else "REPLAY_MISMATCH",
                  "scope": "All saved defined VM/result fields, exact best/current FP32 arrays, RNG state and counters; no intermediate-state proof.",
                  "compared_fields": compared, "mismatches": mismatches, "missing_fields": []}
    geometry, captured_frames, events, capture = batch.trace()
    count = len(geometry)
    roles = np.zeros(count, dtype=np.uint8)
    roles[0], roles[-1] = 1, 2
    arrays = {"poses": geometry.astype("<f4", copy=False), "side": captured_frames["side"].copy(),
              # Several records (best snapshot, finalization) share one VM step, so the
              # viewer sequence is the strictly increasing record order; the VM counter
              # is retained separately as vm_sequence.
              "sequence": np.arange(count, dtype="<i8"), "vm_sequence": captured_frames["sequence"].astype("<u8"),
              "attempt": captured_frames["attempt"].copy(), "sweep": captured_frames["sweep"].copy(),
              "sweep_total": captured_frames["sweep_total"].copy(), "phase": captured_frames["phase"].astype("u1"),
              "roles": roles, "square_ids": np.arange(campaign.n, dtype=np.int32)}
    arrays.update({name: captured_frames[name].astype(dtype) for name, dtype in EXTRA_DTYPES.items() if name != "vm_sequence"})
    # Best final snapshot refers to its actual logical location; terminal current is separate.
    arrays["pc"][-2] = int(states["best_pc"][0])
    arrays["attempt"][0] = -1
    arrays["sweep"][0] = -1
    arrays["attempt"][-2] = max(0, int(states["best_attempt"][0]))
    arrays["sweep"][-2] = max(0, int(states["best_sweep"][0]))
    viewer_frames = []
    for index in range(count):
        values = {name: primitive_scalar(arrays[name][index]) for name in EXTRA_DTYPES}
        values.update({name: primitive_scalar(arrays[name][index]) for name in ("side", "attempt", "sweep", "sweep_total")})
        values["outcome_name"] = OUTCOMES.get(values["outcome"], "UNKNOWN")
        viewer_frames.append(values)
    metadata = {"schema": SCHEMA, "n": campaign.n, "trial_id": row["initial_id"], "seed": campaign.operator_seed,
                "episode_key": row["episode_key"], "frame_count": count,
                "initial_identity": {"bank_hash": bank["hash"], "initial_id": row["initial_id"], "replicate": row["replicate"]},
                "sampling": {"observed": capture["observed"], "retained": count,
                             "suppressed": max(0, capture["observed"] - count), "effective_stride": capture["stride"],
                             "max_frames": campaign.recording.max_frames_per_trace, "mode": campaign.recording.mode},
                "comparison": comparison, "provenance": provenance, "evaluation_profile": campaign.profile(),
                "profile_hash": digest(campaign.profile()), "termination_reason": row["termination"],
                "replay_termination": int(states["termination"][0]), "timings": batch.timings,
                "validations": [{"frame": index, "validation": validate_pose(geometry[index], float(arrays["side"][index]), 1e-9)}
                                for index in (0, count - 2, count - 1)],
                "strategy": {"program": program.document(), "frames": viewer_frames, "best_frame": count - 2,
                             "events": [{name: primitive_scalar(event[name]) for name in event.dtype.names} for event in events],
                             "event_policy": "All bounded semantic boundaries; sampled sweeps; start/best/final geometry reserved."}}
    stem = directory / "trajectories" / ("episode-" + row["episode_key"])
    stem.parent.mkdir(parents=True, exist_ok=True)
    check_quota(campaign, directory, reserve=sum(a.nbytes for a in arrays.values()) * 3 + 100000)
    native = write_npz(stem.with_suffix(".npz"), arrays)
    metadata["numeric_sha256"] = sha256(native)
    meta_path = write_json(stem.with_suffix(".meta.json.gz"), metadata)
    viewer_metadata = {**metadata, "schema": "asquerix-trajectory-v1"}
    html = render_html({name: arrays[name] for name in ARRAY_DTYPES}, viewer_metadata)
    html_path = atomic_write_bytes(stem.with_suffix(".html"), html)
    artifacts = [native, meta_path, html_path]
    return {"episode_key": row["episode_key"], "status": comparison["status"], "frames": count,
            "best_frame": count - 2, "candidate_id": candidate["id"], "initial_identity": metadata["initial_identity"],
            "comparison": comparison, "timings": batch.timings,
            "artifacts": [{"path": str(path.relative_to(directory)), "size_bytes": path.stat().st_size,
                           "sha256": sha256(path)} for path in artifacts]}
