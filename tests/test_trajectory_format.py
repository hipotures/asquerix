"""Focused tests for the bounded trajectory archive format."""

from __future__ import annotations

import gzip
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest

from asquerix.trajectory_format import (
    SCHEMA,
    TrajectoryFormatError,
    atomic_write_bytes,
    encode_npz,
    load_trajectory,
    metadata_json_bytes,
    validate_arrays,
)


def arrays(frame_count: int = 3, n: int = 2) -> dict[str, np.ndarray]:
    poses = np.zeros((frame_count, n, 3), dtype="<f4")
    poses[0, 0, 2] = np.float32(-0.0)
    poses[-1, 0, 0] = np.float32(0.25)
    roles = np.zeros(frame_count, dtype="u1")
    roles[0] |= 1
    roles[-1] |= 2
    return {
        "poses": poses,
        "side": np.linspace(3.0, 2.0, frame_count, dtype="<f4"),
        "sequence": np.arange(frame_count, dtype="<i8"),
        "attempt": np.arange(frame_count, dtype="<i4"),
        "sweep": np.arange(frame_count, dtype="<i4"),
        "sweep_total": np.full(frame_count, frame_count - 1, dtype="<i4"),
        "phase": np.asarray([0] + [3] * (frame_count - 1), dtype="u1"),
        "roles": roles,
        "square_ids": np.asarray([2_147_483_646, 2_147_483_647][:n], dtype="<i4"),
    }


def metadata(frame_count: int = 3, n: int = 2) -> dict:
    return {
        "schema": SCHEMA,
        "n": n,
        "trial_id": "18446744073709551615",
        "seed": "9223372036854775809",
        "frame_count": frame_count,
        "sampling": {
            "observed": frame_count,
            "retained": frame_count,
            "suppressed": 0,
            "effective_stride": 1,
            "max_frames": 256,
        },
        "comparison": {
            "status": "REPLAY_MATCHED",
            "scope": "defined endpoint fields",
            "compared_fields": ["poses", "side"],
            "mismatches": [],
            "missing_fields": [],
        },
        "validations": [],
        "provenance": {"replay_revision": "test"},
        "termination_reason": "BUDGET_EXHAUSTED",
    }


def write_pair(directory: Path, values: dict[str, np.ndarray] | None = None, info: dict | None = None) -> Path:
    values = values or arrays()
    info = info or metadata()
    numeric = encode_npz(values)
    npz_path = directory / "trial-4372.npz"
    atomic_write_bytes(npz_path, numeric)
    info = dict(info)
    info["numeric_sha256"] = hashlib.sha256(numeric).hexdigest()
    meta_path = directory / "trial-4372.meta.json.gz"
    atomic_write_bytes(meta_path, gzip.compress(metadata_json_bytes(info), compresslevel=3, mtime=0))
    return npz_path


def test_npz_and_metadata_round_trip_preserves_signed_zero_and_uint64_strings(tmp_path: Path) -> None:
    path = write_pair(tmp_path)

    restored, info = load_trajectory(path)

    assert restored["poses"].dtype.str == "<f4"
    assert restored["poses"].shape == (3, 2, 3)
    assert np.signbit(restored["poses"][0, 0, 2])
    np.testing.assert_array_equal(restored["poses"], arrays()["poses"])
    assert info["trial_id"] == "18446744073709551615"
    assert info["seed"] == "9223372036854775809"


def test_validate_arrays_rejects_object_arrays_and_wrong_shapes() -> None:
    invalid = arrays()
    invalid["side"] = np.asarray([1, 2, 3], dtype=object)
    with pytest.raises(TrajectoryFormatError, match="object|dtype"):
        validate_arrays(invalid, metadata())

    invalid = arrays()
    invalid["poses"] = np.ascontiguousarray(invalid["poses"][:, :, :2])
    with pytest.raises(TrajectoryFormatError, match="shape"):
        validate_arrays(invalid, metadata())


def test_loader_rejects_large_directory_before_member_allocation(tmp_path, monkeypatch):
    import asquerix.trajectory_format as module
    path = tmp_path / "too-many.npz"
    with zipfile.ZipFile(path, "w") as archive:
        for index in range(1000):
            archive.writestr(f"member-{index}.npy", b"")
    (tmp_path / "too-many.meta.json.gz").write_bytes(gzip.compress(b"{}"))
    monkeypatch.setattr(module.zipfile, "ZipFile", lambda *a, **k: pytest.fail("allocated malicious ZIP directory"))
    with pytest.raises(TrajectoryFormatError, match="nine array members"):
        load_trajectory(path)

def test_validate_arrays_requires_endpoint_roles_and_unique_square_ids() -> None:
    invalid = arrays()
    invalid["roles"] = np.zeros(3, dtype="u1")
    with pytest.raises(TrajectoryFormatError, match="INITIAL role"):
        validate_arrays(invalid, metadata())

    invalid = arrays()
    invalid["square_ids"] = np.asarray([9, 9], dtype="<i4")
    with pytest.raises(TrajectoryFormatError, match="unique"):
        validate_arrays(invalid, metadata())


def test_truncated_npz_is_rejected_before_decode(tmp_path: Path) -> None:
    path = write_pair(tmp_path)
    raw = path.read_bytes()
    path.write_bytes(raw[:-19])

    with pytest.raises(TrajectoryFormatError, match="invalid|read|truncated|ZIP"):
        load_trajectory(path)


def test_checksum_and_metadata_limits_are_checked(tmp_path: Path) -> None:
    path = write_pair(tmp_path)
    meta_path = tmp_path / "trial-4372.meta.json.gz"
    info = json.loads(gzip.decompress(meta_path.read_bytes()).decode("utf-8"))
    info["numeric_sha256"] = "0" * 64
    atomic_write_bytes(meta_path, gzip.compress(metadata_json_bytes(info), compresslevel=3, mtime=0))
    with pytest.raises(TrajectoryFormatError, match="numeric_sha256"):
        load_trajectory(path)

    too_large = dict(metadata())
    too_large["comparison"] = dict(too_large["comparison"])
    too_large["comparison"]["mismatches"] = ["x" * (2 * 1024 * 1024)]
    with pytest.raises(TrajectoryFormatError, match="metadata|serializable"):
        metadata_json_bytes(too_large)


def test_plain_metadata_spelling_remains_resolvable(tmp_path: Path) -> None:
    values = arrays()
    numeric = encode_npz(values)
    path = tmp_path / "trial-4372.npz"
    atomic_write_bytes(path, numeric)
    info = metadata()
    info["numeric_sha256"] = hashlib.sha256(numeric).hexdigest()
    # resolve_path intentionally keeps historical plain JSON readable.
    atomic_write_bytes(tmp_path / "trial-4372.meta.json", metadata_json_bytes(info))

    restored, _ = load_trajectory(path)
    np.testing.assert_array_equal(restored["sequence"], values["sequence"])
