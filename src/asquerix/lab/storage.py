"""Bounded primitive NPZ evidence, exact identities, and executable provenance."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import gzip
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import struct
import subprocess
from time import perf_counter
import zipfile

import numpy as np
from numpy.lib import format as npy

from ..geometry import validate_pose
from ..persistence import read_json, write_json
from ..trajectory_format import atomic_write_bytes
from .config import Campaign, digest

MAX_CHUNK_BYTES = 32 * 1024**2
MAX_JSON_BYTES = 64 * 1024**2
NUMERICAL_FILES = ("gpu.py", "geometry.py", "lab/config.py", "lab/strategy.py", "lab/gpu.py",
                   "lab/storage.py", "lab/evaluation.py", "lab/search.py", "lab/worker.py")


def sha256(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def executable_identity() -> dict:
    root = Path(__file__).resolve().parents[1]
    return {"sources": {name: sha256(root / name) for name in NUMERICAL_FILES if (root / name).is_file()},
            "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "warp-lang")},
            "python": platform.python_version()}


def environment(device=None) -> dict:
    repository = Path(__file__).resolve().parents[3]
    identity = executable_identity()
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    return {"schema": "asquerix-lab-environment-v1", "source_revision": revision,
            "executable_identity": identity, "executable_hash": digest(identity),
            "dependencies": {name: importlib.metadata.version(name) for name in ("numpy", "warp-lang", "rich", "fastapi", "uvicorn")},
            "platform": platform.platform(), "python": platform.python_version(),
            "device": {"selector": str(device), "uuid": device.uuid, "name": device.name} if device else None,
            "reproducibility_scope": "Defined bytes on this GPU architecture, locked Warp/NumPy and source/profile identity; no cross-toolchain guarantee."}


def write_npz(path: Path, arrays: dict[str, np.ndarray]) -> Path:
    if not arrays or any(array.dtype.hasobject or array.dtype.names for array in arrays.values()):
        raise ValueError("Scientific archives require primitive arrays, never object/structured arrays")
    if sum(array.nbytes for array in arrays.values()) > MAX_CHUNK_BYTES:
        raise ValueError("Numeric chunk exceeds the bounded decompressed size")
    data = io.BytesIO()
    np.savez_compressed(data, **arrays)
    if data.tell() > MAX_CHUNK_BYTES:
        raise ValueError("Numeric archive exceeds the bounded stored size")
    return atomic_write_bytes(path, data.getvalue())


def load_npz(path: Path, *, expected: dict[str, tuple[np.dtype, tuple]] | None = None) -> dict[str, np.ndarray]:
    """Check every ZIP/NPY header before NumPy is allowed to allocate arrays."""
    if path.stat().st_size > MAX_CHUNK_BYTES:
        raise ValueError("Stored archive exceeds size limit")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if not 1 <= len(names) <= 128 or len(set(names)) != len(names):
            raise ValueError("Invalid or duplicate archive entries")
        if expected is not None and set(names) != {name + ".npy" for name in expected}:
            raise ValueError("Archive has unexpected arrays")
        total = 0
        for info in infos:
            if not info.filename.endswith(".npy") or "/" in info.filename or "\\" in info.filename or info.flag_bits & 1:
                raise ValueError("Invalid archive entry")
            total += info.file_size
            if total > MAX_CHUNK_BYTES or info.file_size > MAX_CHUNK_BYTES:
                raise ValueError("Decompressed archive exceeds size limit")
            with archive.open(info) as stream:
                version = npy.read_magic(stream)
                if version == (1, 0):
                    shape, fortran, dtype = npy.read_array_header_1_0(stream, max_header_size=65536)
                elif version == (2, 0):
                    shape, fortran, dtype = npy.read_array_header_2_0(stream, max_header_size=65536)
                else:
                    raise ValueError("Unsupported NPY version")
                if dtype.hasobject or dtype.names or dtype.kind not in "fiu" or dtype.itemsize not in (1, 4, 8) or fortran:
                    raise ValueError("Archive requires allowlisted primitive C-order arrays")
                count = 1
                if not 1 <= len(shape) <= 3:
                    raise ValueError("Unsupported array dimension")
                for dimension in shape:
                    if type(dimension) is not int or not 0 <= dimension <= 1048576:
                        raise ValueError("Invalid array dimension")
                    count *= dimension
                    if count * dtype.itemsize > MAX_CHUNK_BYTES:
                        raise ValueError("Array shape exceeds size limit")
                if stream.tell() + count * dtype.itemsize != info.file_size:
                    raise ValueError("NPY size/header mismatch")
                if expected is not None:
                    wanted_dtype, wanted_shape = expected[info.filename[:-4]]
                    if dtype != np.dtype(wanted_dtype) or shape != wanted_shape:
                        raise ValueError("Array dtype/shape mismatch")
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def primitive_scalar(value):
    if isinstance(value, np.unsignedinteger) and value.dtype.itemsize == 8:
        return str(int(value))
    return value.item() if isinstance(value, np.generic) else value


def geometry_bank_hash(arrays: dict[str, np.ndarray], provenance: dict) -> str:
    h = hashlib.sha256(json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode())
    for name, array in sorted(arrays.items()):
        h.update(name.encode() + b"\0" + array.dtype.str.encode() + repr(array.shape).encode())
        h.update(np.ascontiguousarray(array).tobytes())
    return h.hexdigest()


def prepare_banks(campaign: Campaign, directory: Path, *, stop=lambda: False, progress=lambda value: None) -> tuple[dict, dict]:
    from ..gpu import Batch, Config
    config = Config(n=campaign.n, initial_side=campaign.initial_side,
                    seed=int(campaign.datasets.initializer_seed), max_attempts=0,
                    max_sweeps=480, **campaign.profile()["solver"])
    results = {}
    timings = {"initialization_seconds": 0.0, "initialization_device_seconds": 0.0,
               "initialization_transfer_seconds": 0.0, "initial_validation_seconds": 0.0}
    all_arrays = {}
    for kind in ("training", "holdout"):
        requested = getattr(campaign.datasets, kind)
        ids, poses, rows, rejected = [], [], [], []
        next_id = int(requested.first_id)
        end_id = next_id + 4 * requested.valid_count
        while len(ids) < requested.valid_count and next_id < end_id:
            if stop():
                raise InterruptedError("Bank preparation stopped before complete common inputs")
            count = min(campaign.batch_capacity, requested.valid_count - len(ids), end_id - next_id)
            batch = Batch(config, capacity=count, device=campaign.device)
            batch.poses.zero_()
            batch.work.zero_()
            records, timing = batch.run(count, next_id)
            geometry, transfer = batch.get_poses(np.arange(count, dtype=np.int32))
            timings["initialization_seconds"] += timing["simulation_seconds"]
            timings["initialization_device_seconds"] += timing["device_seconds"]
            timings["initialization_transfer_seconds"] += timing["transfer_seconds"] + transfer
            for index, (pose, row) in enumerate(zip(geometry, records, strict=True)):
                start = perf_counter()
                validation = validate_pose(pose, float(row["side"]), 1e-9) if int(row["termination"]) != 3 else {"status": "INIT_FAILED"}
                timings["initial_validation_seconds"] += perf_counter() - start
                initial_id = next_id + index
                if validation["status"] == "NUMERICALLY_VALIDATED":
                    ids.append(initial_id)
                    poses.append(pose)
                    rows.append(row)
                else:
                    rejected.append({"initial_id": str(initial_id), "validation": validation})
            next_id += count
            progress({"phase": "PREPARING", "bank": kind, "valid": len(ids), "requested": requested.valid_count,
                      "rejected": len(rejected)})
        if len(ids) != requested.valid_count:
            write_json(directory / "initialization-failure.json.gz", {"bank": kind, "rejected": rejected, "valid": len(ids)})
            raise ValueError(f"Random starts did not fit: too few of {campaign.n} squares could be placed without overlap in a "
                             f"{campaign.initial_side:g} x {campaign.initial_side:g} container. Increase the initial container side "
                             f"(for example to {max(campaign.initial_side + 2, 2 * campaign.n ** 0.5):.0f}).")
        initial_results = np.asarray(rows, dtype=rows[0].dtype)
        arrays = {"ids": np.asarray(ids, dtype=np.uint64), "poses": np.asarray(poses, dtype=np.float32)}
        arrays.update({"initial_" + name: initial_results[name].copy() for name in initial_results.dtype.names})
        provenance = {"initializer_seed": campaign.datasets.initializer_seed, "first_id": requested.first_id,
                      "replacement_policy": "Increasing IDs, at most four times the bank count, shared by all programs.",
                      "n": campaign.n, "config": asdict(config), "rejected": rejected}
        bank_hash = geometry_bank_hash(arrays, provenance)
        results[kind] = {"hash": bank_hash, "count": len(ids), "provenance": provenance}
        all_arrays.update({kind + "_" + name: array for name, array in arrays.items()})
    write_npz(directory / "initial-bank.npz", all_arrays)
    write_json(directory / "datasets.json.gz", results)
    return results, timings


def load_banks(directory: Path) -> tuple[dict, dict]:
    from ..gpu import Result
    metadata = read_json(directory / "datasets.json.gz")
    arrays = load_npz(directory / "initial-bank.npz")
    banks = {}
    for kind in ("training", "holdout"):
        count = metadata[kind]["count"]
        records = np.zeros(count, dtype=Result.numpy_dtype())
        for name in records.dtype.names:
            records[name] = arrays[kind + "_initial_" + name]
        parts = {name[len(kind) + 1:]: array for name, array in arrays.items() if name.startswith(kind + "_")}
        if geometry_bank_hash(parts, metadata[kind]["provenance"]) != metadata[kind]["hash"]:
            raise ValueError("Common input bank hash mismatch")
        banks[kind] = {"ids": parts["ids"], "poses": parts["poses"], "initial_results": records,
                       "hash": metadata[kind]["hash"]}
    return metadata, banks


def bounded_json(path: Path) -> dict:
    """Read one gzip JSON object without unbounded decompression."""
    with gzip.open(path, "rb") as stream:
        data = stream.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError(f"{path.name} exceeds the bounded decompressed JSON size")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} is not a JSON object")
    return value


def storage_bytes(directory: Path) -> int:
    return sum(path.stat().st_size for path in directory.rglob("*") if path.is_file())


def check_quota(campaign: Campaign, directory: Path, *, reserve: int = 0):
    if storage_bytes(directory) + reserve > campaign.limits.max_artifact_mib * 1024**2:
        raise OSError("Campaign artifact quota exhausted; finalized chunks are preserved")
