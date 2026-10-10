"""Bounded, lossless storage for selected Asquerix trajectories.

The recorder writes one compressed NumPy archive and one small gzip JSON
document per selected trial.  This module deliberately has no CUDA or Warp
imports: it is also used by the offline viewer and by artifact validation.

The binary schema is versioned by :data:`SCHEMA`.  All numeric arrays use
little-endian dtypes and the archive is loaded with ``allow_pickle=False``.
The loader inspects the ZIP central directory and every NPY header before
letting NumPy allocate an array.  This is important because a trajectory is
an externally persisted diagnostic artifact, not trusted in-process state.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import struct
import tempfile
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from numpy.lib import format as npy_format

from .persistence import resolve_path

SCHEMA = "asquerix-trajectory-v1"

PHASE_INITIAL = 0
PHASE_TRIAL = 1
PHASE_RELAXING = 2
PHASE_ACCEPTED = 3
PHASE_REJECTED = 4
PHASE_ROLLBACK = 5
PHASE_FINAL = 6

ROLE_INITIAL = 1
ROLE_FINAL = 2

MAX_FRAMES = 4096
MIN_FRAMES = 1
MAX_SQUARES = 1000
MIN_SQUARES = 1
MAX_METADATA_BYTES = 2 * 1024 * 1024
MAX_METADATA_COMPRESSED_BYTES = 4 * 1024 * 1024
# The largest valid v1 numeric payload is below two MiB.  The larger bounds
# leave room for NPY headers and ZIP bookkeeping while rejecting archive bombs.
MAX_NPZ_BYTES = 16 * 1024 * 1024
MAX_NUMERIC_BYTES = 8 * 1024 * 1024
MAX_NPY_HEADER_BYTES = 64 * 1024

_U64_MAX = (1 << 64) - 1
_DECIMAL_U64 = re.compile(r"(?:0|[1-9][0-9]*)\Z")

ARRAY_DTYPES: dict[str, np.dtype[Any]] = {
    "poses": np.dtype("<f4"),
    "side": np.dtype("<f4"),
    "sequence": np.dtype("<i8"),
    "attempt": np.dtype("<i4"),
    "sweep": np.dtype("<i4"),
    "sweep_total": np.dtype("<i4"),
    "phase": np.dtype("u1"),
    "roles": np.dtype("u1"),
    "square_ids": np.dtype("<i4"),
}

_ARRAY_ORDER = tuple(ARRAY_DTYPES)
_PHASES = frozenset(
    {
        PHASE_INITIAL,
        PHASE_TRIAL,
        PHASE_RELAXING,
        PHASE_ACCEPTED,
        PHASE_REJECTED,
        PHASE_ROLLBACK,
        PHASE_FINAL,
    }
)
_PHASE_NAMES = {
    PHASE_INITIAL: "INITIAL",
    PHASE_TRIAL: "TRIAL",
    PHASE_RELAXING: "RELAXING",
    PHASE_ACCEPTED: "ACCEPTED",
    PHASE_REJECTED: "REJECTED",
    PHASE_ROLLBACK: "ROLLBACK",
    PHASE_FINAL: "FINAL",
}


class TrajectoryFormatError(ValueError):
    """Raised when a trajectory does not conform to the v1 format."""


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_))


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TrajectoryFormatError(f"{label} must be a JSON object")
    return value


def _validate_decimal_u64(value: Any, label: str) -> str:
    if not isinstance(value, str) or _DECIMAL_U64.fullmatch(value) is None:
        raise TrajectoryFormatError(f"metadata field '{label}' must be a decimal uint64 string")
    try:
        integer = int(value, 10)
    except ValueError as exc:  # pragma: no cover - regex already excludes this
        raise TrajectoryFormatError(f"metadata field '{label}' is not a decimal uint64") from exc
    if integer > _U64_MAX:
        raise TrajectoryFormatError(f"metadata field '{label}' is outside uint64 range")
    return value


def _validate_array_dtype(name: str, array: Any) -> np.ndarray:
    if not isinstance(array, np.ndarray):
        raise TrajectoryFormatError(f"array '{name}' must be a NumPy ndarray")
    expected = ARRAY_DTYPES[name]
    if array.dtype != expected:
        raise TrajectoryFormatError(
            f"array '{name}' must have dtype {expected.str}, got {array.dtype.str}"
        )
    if array.dtype.hasobject:
        raise TrajectoryFormatError(f"array '{name}' must not have object dtype")
    return array


def _checked_nbytes(shape: tuple[int, ...], dtype: np.dtype[Any], label: str) -> int:
    count = 1
    for dimension in shape:
        if not isinstance(dimension, (int, np.integer)) or int(dimension) < 0:
            raise TrajectoryFormatError(f"{label} has an invalid shape")
        count *= int(dimension)
        if count > MAX_NUMERIC_BYTES // max(1, dtype.itemsize):
            raise TrajectoryFormatError(f"{label} is larger than the trajectory limit")
    return count * dtype.itemsize


def validate_metadata(metadata: Mapping[str, Any], *, frame_count: int | None = None,
                      square_count: int | None = None) -> Mapping[str, Any]:
    """Validate the JSON companion document and return it unchanged.

    The validator requires the stable top-level fields used by the recorder,
    but permits additional provenance and timing fields so future diagnostics
    can extend the document without changing the numeric schema.
    """

    document = _require_mapping(metadata, "metadata")
    if document.get("schema") != SCHEMA:
        raise TrajectoryFormatError(
            f"metadata schema must be {SCHEMA!r}, got {document.get('schema')!r}"
        )
    n = document.get("n")
    if not _is_exact_int(n) or not MIN_SQUARES <= int(n) <= MAX_SQUARES:
        raise TrajectoryFormatError(f"metadata field 'n' must be an integer in [{MIN_SQUARES}, {MAX_SQUARES}]")
    if square_count is not None and int(n) != square_count:
        raise TrajectoryFormatError("metadata field 'n' does not match square_ids")
    _validate_decimal_u64(document.get("trial_id"), "trial_id")
    _validate_decimal_u64(document.get("seed"), "seed")

    declared_frames = document.get("frame_count")
    if not _is_exact_int(declared_frames) or not MIN_FRAMES <= int(declared_frames) <= MAX_FRAMES:
        raise TrajectoryFormatError(
            f"metadata field 'frame_count' must be an integer in [{MIN_FRAMES}, {MAX_FRAMES}]"
        )
    if frame_count is not None and int(declared_frames) != frame_count:
        raise TrajectoryFormatError("metadata field 'frame_count' does not match poses")

    sampling = _require_mapping(document.get("sampling"), "metadata sampling")
    for key in ("observed", "retained", "suppressed", "effective_stride", "max_frames"):
        if key in sampling and not _is_exact_int(sampling[key]):
            raise TrajectoryFormatError(f"metadata sampling field '{key}' must be an integer")
    if "retained" in sampling and int(sampling["retained"]) != int(declared_frames):
        raise TrajectoryFormatError("metadata sampling retained count does not match frame_count")
    if "max_frames" in sampling and not MIN_FRAMES <= int(sampling["max_frames"]) <= MAX_FRAMES:
        raise TrajectoryFormatError("metadata sampling max_frames is outside the supported range")
    if "effective_stride" in sampling and int(sampling["effective_stride"]) < 1:
        raise TrajectoryFormatError("metadata sampling effective_stride must be positive")

    comparison = _require_mapping(document.get("comparison"), "metadata comparison")
    if "status" in comparison and not isinstance(comparison["status"], str):
        raise TrajectoryFormatError("metadata comparison status must be a string")
    if "compared_fields" in comparison and not isinstance(comparison["compared_fields"], list):
        raise TrajectoryFormatError("metadata comparison compared_fields must be a list")
    if "mismatches" in comparison and not isinstance(comparison["mismatches"], list):
        raise TrajectoryFormatError("metadata comparison mismatches must be a list")
    if "missing_fields" in comparison and not isinstance(comparison["missing_fields"], list):
        raise TrajectoryFormatError("metadata comparison missing_fields must be a list")

    validations = document.get("validations")
    if not isinstance(validations, list):
        raise TrajectoryFormatError("metadata field 'validations' must be a list")
    for index, item in enumerate(validations):
        if not isinstance(item, Mapping):
            raise TrajectoryFormatError(f"metadata validations[{index}] must be an object")

    _require_mapping(document.get("provenance"), "metadata provenance")
    termination = document.get("termination_reason")
    if not isinstance(termination, str) or not termination:
        raise TrajectoryFormatError("metadata field 'termination_reason' must be a non-empty string")

    checksum = document.get("numeric_sha256")
    if checksum is not None and (
        not isinstance(checksum, str) or re.fullmatch(r"[0-9a-fA-F]{64}", checksum) is None
    ):
        raise TrajectoryFormatError("metadata numeric_sha256 must be a SHA-256 hexadecimal string")
    return document


def validate_arrays(arrays: Mapping[str, Any], metadata: Mapping[str, Any] | None = None) -> dict[str, np.ndarray]:
    """Validate the complete v1 numeric array set.

    Arrays are returned in schema order.  The returned mapping contains the
    original ndarray objects and is safe for callers to pass to
    :func:`encode_npz`; no lossy conversion or dtype coercion is performed.
    """

    mapping = _require_mapping(arrays, "arrays")
    keys = set(mapping)
    expected_keys = set(_ARRAY_ORDER)
    if keys != expected_keys:
        missing = sorted(expected_keys - keys)
        extra = sorted(keys - expected_keys)
        detail: list[str] = []
        if missing:
            detail.append(f"missing {missing}")
        if extra:
            detail.append(f"unexpected {extra}")
        raise TrajectoryFormatError("trajectory arrays have the wrong fields: " + ", ".join(detail))

    checked = {name: _validate_array_dtype(name, mapping[name]) for name in _ARRAY_ORDER}
    poses = checked["poses"]
    if poses.ndim != 3 or poses.shape[2] != 3:
        raise TrajectoryFormatError("array 'poses' must have shape (F, N, 3)")
    frame_count, square_count, _ = poses.shape
    if not MIN_FRAMES <= frame_count <= MAX_FRAMES:
        raise TrajectoryFormatError(f"poses frame count must be in [{MIN_FRAMES}, {MAX_FRAMES}]")
    if not MIN_SQUARES <= square_count <= MAX_SQUARES:
        raise TrajectoryFormatError(f"poses square count must be in [{MIN_SQUARES}, {MAX_SQUARES}]")
    _checked_nbytes(poses.shape, poses.dtype, "poses")

    one_dimensional = ("side", "sequence", "attempt", "sweep", "sweep_total", "phase", "roles")
    for name in one_dimensional:
        array = checked[name]
        if array.ndim != 1 or array.shape[0] != frame_count:
            raise TrajectoryFormatError(f"array '{name}' must have shape ({frame_count},)")
        _checked_nbytes(array.shape, array.dtype, name)
    ids = checked["square_ids"]
    if ids.ndim != 1 or ids.shape[0] != square_count:
        raise TrajectoryFormatError(f"array 'square_ids' must have shape ({square_count},)")
    _checked_nbytes(ids.shape, ids.dtype, "square_ids")

    phase_values = checked["phase"]
    if phase_values.size and not bool(np.isin(phase_values, tuple(_PHASES)).all()):
        raise TrajectoryFormatError("array 'phase' contains an unknown phase code")
    role_values = checked["roles"]
    if role_values.size and bool((role_values & np.uint8(~(ROLE_INITIAL | ROLE_FINAL) & 0xFF)).any()):
        raise TrajectoryFormatError("array 'roles' contains unknown role bits")
    if not (int(role_values[0]) & ROLE_INITIAL):
        raise TrajectoryFormatError("first trajectory frame must carry the INITIAL role")
    if not (int(role_values[-1]) & ROLE_FINAL):
        raise TrajectoryFormatError("last trajectory frame must carry the FINAL role")
    if frame_count > 1:
        if bool((role_values[1:] & np.uint8(ROLE_INITIAL)).any()):
            raise TrajectoryFormatError("INITIAL role is only valid on the first trajectory frame")
        if bool((role_values[:-1] & np.uint8(ROLE_FINAL)).any()):
            raise TrajectoryFormatError("FINAL role is only valid on the last trajectory frame")
    if np.unique(checked["square_ids"]).size != square_count:
        raise TrajectoryFormatError("array 'square_ids' must contain unique IDs")
    # The initial frame has no attempt or sweep yet.  The CUDA recorder uses
    # -1 for those two indices as an explicit pre-attempt sentinel; negative
    # values in every other phase would make the algorithmic coordinates
    # ambiguous and are rejected.
    initial = checked["phase"] == np.uint8(PHASE_INITIAL)
    for name in ("attempt", "sweep"):
        values = checked[name]
        invalid_negative = (values < 0) & ~initial
        if values.size and bool(invalid_negative.any()):
            raise TrajectoryFormatError(f"array '{name}' must not contain negative indices outside INITIAL")
        if values.size and bool((values < -1).any()):
            raise TrajectoryFormatError(f"array '{name}' contains an invalid negative index")
    if checked["sweep_total"].size and bool((checked["sweep_total"] < 0).any()):
        raise TrajectoryFormatError("array 'sweep_total' must not contain negative indices")
    if checked["sweep"].size and bool((checked["sweep"] > checked["sweep_total"]).any()):
        raise TrajectoryFormatError("array 'sweep' cannot exceed sweep_total")
    if frame_count > 1 and bool((checked["sequence"][1:] <= checked["sequence"][:-1]).any()):
        raise TrajectoryFormatError("array 'sequence' must increase strictly")

    if metadata is not None:
        validate_metadata(metadata, frame_count=frame_count, square_count=square_count)
    return checked


def encode_npz(arrays: Mapping[str, Any]) -> bytes:
    """Encode validated arrays as a compressed, pickle-free NPZ payload."""

    checked = validate_arrays(arrays)
    stream = io.BytesIO()
    # Supplying keyword arguments in a fixed order makes the member order
    # deterministic.  The ZIP timestamp may vary, so callers must hash the
    # emitted bytes rather than assume byte-for-byte repeatability.
    np.savez_compressed(stream, **{name: checked[name] for name in _ARRAY_ORDER})
    payload = stream.getvalue()
    if len(payload) > MAX_NPZ_BYTES:
        raise TrajectoryFormatError("encoded trajectory exceeds the NPZ size limit")
    return payload


def _parse_npy_header(raw: bytes, name: str) -> tuple[tuple[int, ...], np.dtype[Any], bool, int]:
    stream = io.BytesIO(raw)
    try:
        major, minor = npy_format.read_magic(stream)
        if (major, minor) == (1, 0):
            shape, fortran_order, dtype = npy_format.read_array_header_1_0(
                stream, max_header_size=MAX_NPY_HEADER_BYTES
            )
        elif (major, minor) == (2, 0):
            shape, fortran_order, dtype = npy_format.read_array_header_2_0(
                stream, max_header_size=MAX_NPY_HEADER_BYTES
            )
        elif (major, minor) == (3, 0):
            reader = getattr(npy_format, "read_array_header_3_0", None)
            if reader is None:
                raise TrajectoryFormatError("NumPy cannot read NPY version 3 headers")
            shape, fortran_order, dtype = reader(stream, max_header_size=MAX_NPY_HEADER_BYTES)
        else:
            raise TrajectoryFormatError(f"array '{name}' uses unsupported NPY version {major}.{minor}")
    except (ValueError, TypeError, EOFError, OSError) as exc:
        raise TrajectoryFormatError(f"array '{name}' has an invalid NPY header") from exc
    if not isinstance(shape, tuple) or any(not isinstance(item, int) for item in shape):
        raise TrajectoryFormatError(f"array '{name}' has an invalid NPY shape")
    if dtype.hasobject:
        raise TrajectoryFormatError(f"array '{name}' has a forbidden object dtype")
    offset = stream.tell()
    if offset > MAX_NPY_HEADER_BYTES:
        raise TrajectoryFormatError(f"array '{name}' has an oversized NPY header")
    expected = _checked_nbytes(shape, dtype, name)
    if len(raw) - offset != expected:
        raise TrajectoryFormatError(f"array '{name}' has truncated or trailing NPY data")
    return shape, dtype, bool(fortran_order), offset


def _check_zip_directory(path: Path, file_size: int) -> None:
    """Bound central-directory allocation before ZipFile creates member objects."""
    with path.open("rb") as stream:
        stream.seek(max(0, file_size - 65557))
        tail = stream.read(65557)
    marker = tail.rfind(b"PK\x05\x06")
    if marker < 0 or len(tail) - marker < 22:
        raise TrajectoryFormatError("trajectory ZIP end record is missing or truncated")
    _, disk, central_disk, disk_entries, entries, central_bytes, _, comment_bytes = struct.unpack_from("<4s4H2IH", tail, marker)
    if marker + 22 + comment_bytes != len(tail):
        raise TrajectoryFormatError("trajectory ZIP end record has trailing or truncated data")
    if disk or central_disk or entries != len(_ARRAY_ORDER) or disk_entries != entries:
        raise TrajectoryFormatError("trajectory ZIP must contain exactly the schema's nine array members")
    if central_bytes > 65536:
        raise TrajectoryFormatError("trajectory ZIP central directory exceeds its bounded size")


def _decode_npz(path: Path) -> dict[str, np.ndarray]:
    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise TrajectoryFormatError(f"cannot stat trajectory archive {path}") from exc
    if file_size > MAX_NPZ_BYTES:
        raise TrajectoryFormatError("trajectory archive exceeds the NPZ size limit")
    _check_zip_directory(path, file_size)
    try:
        archive = zipfile.ZipFile(path, mode="r")
    except (OSError, zipfile.BadZipFile) as exc:
        raise TrajectoryFormatError(f"invalid trajectory ZIP archive: {path}") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) != len(_ARRAY_ORDER):
            raise TrajectoryFormatError("trajectory archive has the wrong number of array members")
        seen: set[str] = set()
        total_uncompressed = 0
        decoded: dict[str, np.ndarray] = {}
        for info in infos:
            name = info.filename
            if name in seen:
                raise TrajectoryFormatError(f"trajectory archive contains duplicate member '{name}'")
            seen.add(name)
            if not name.endswith(".npy") or name[:-4] not in ARRAY_DTYPES:
                raise TrajectoryFormatError(f"trajectory archive contains unexpected member '{name}'")
            key = name[:-4]
            if info.is_dir() or info.file_size > MAX_NUMERIC_BYTES:
                raise TrajectoryFormatError(f"trajectory member '{name}' is too large")
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_NUMERIC_BYTES:
                raise TrajectoryFormatError("trajectory archive numeric payload is too large")
            try:
                raw = archive.read(info)
            except (OSError, EOFError, RuntimeError, zipfile.BadZipFile) as exc:
                raise TrajectoryFormatError(f"cannot read trajectory member '{name}'") from exc
            shape, dtype, _fortran_order, _ = _parse_npy_header(raw, key)
            if dtype != ARRAY_DTYPES[key]:
                raise TrajectoryFormatError(
                    f"array '{key}' must have dtype {ARRAY_DTYPES[key].str}, got {dtype.str}"
                )
            # NumPy already performed no data allocation while parsing the
            # header; this load is now bounded by the checked member size.
            try:
                loaded = np.load(io.BytesIO(raw), allow_pickle=False)
            except (ValueError, TypeError, OSError) as exc:
                raise TrajectoryFormatError(f"cannot decode trajectory member '{name}'") from exc
            if not isinstance(loaded, np.ndarray) or loaded.dtype.hasobject:
                raise TrajectoryFormatError(f"array '{key}' is not a primitive ndarray")
            if loaded.shape != shape or loaded.dtype != ARRAY_DTYPES[key]:
                raise TrajectoryFormatError(f"array '{key}' changed after safe header validation")
            decoded[key] = loaded
        if set(decoded) != set(_ARRAY_ORDER):
            raise TrajectoryFormatError("trajectory archive is missing one or more arrays")
    return decoded


def _read_json_bounded(path: Path) -> dict[str, Any]:
    try:
        compressed_size = path.stat().st_size
    except OSError as exc:
        raise TrajectoryFormatError(f"cannot stat metadata file {path}") from exc
    if compressed_size > MAX_METADATA_COMPRESSED_BYTES:
        raise TrajectoryFormatError("trajectory metadata archive is too large")
    try:
        if path.name.endswith(".gz"):
            with gzip.open(path, mode="rb") as stream:
                raw = stream.read(MAX_METADATA_BYTES + 1)
        else:
            raw = path.read_bytes()
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise TrajectoryFormatError(f"cannot read trajectory metadata {path}") from exc
    if len(raw) > MAX_METADATA_BYTES:
        raise TrajectoryFormatError("trajectory metadata exceeds the decompressed size limit")

    def reject_constant(value: str) -> Any:
        raise TrajectoryFormatError(f"metadata contains non-standard JSON constant {value!r}")

    try:
        decoded = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TrajectoryFormatError(f"trajectory metadata is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(decoded, dict):
        raise TrajectoryFormatError("trajectory metadata must be a JSON object")
    return decoded


def associated_metadata_path(npz_path: str | os.PathLike[str]) -> Path:
    """Return the canonical metadata path associated with an NPZ file."""

    path = Path(npz_path)
    if path.suffix != ".npz":
        raise TrajectoryFormatError("trajectory numeric path must end in .npz")
    return path.with_name(path.stem + ".meta.json.gz")


def load_trajectory(npz_path: str | os.PathLike[str]) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """Safely load a trajectory archive and its gzip metadata companion."""

    requested = Path(npz_path)
    if requested.suffix != ".npz":
        raise TrajectoryFormatError("trajectory numeric path must end in .npz")
    if not requested.is_file():
        raise FileNotFoundError(requested)
    metadata_requested = associated_metadata_path(requested)
    metadata_path = resolve_path(metadata_requested)
    if not metadata_path.is_file():
        raise FileNotFoundError(metadata_requested)

    arrays = _decode_npz(requested)
    metadata = _read_json_bounded(metadata_path)
    validate_arrays(arrays, metadata)
    checksum = metadata.get("numeric_sha256")
    if checksum is not None:
        actual = hashlib.sha256(requested.read_bytes()).hexdigest()
        if actual.lower() != str(checksum).lower():
            raise TrajectoryFormatError("trajectory numeric_sha256 does not match the NPZ bytes")
    return arrays, metadata


def atomic_write_bytes(path: str | os.PathLike[str], payload: bytes | bytearray | memoryview) -> Path:
    """Atomically publish one binary trajectory or viewer artifact."""

    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("payload must be bytes-like")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        raise
    return target


def write_bytes(path: str | os.PathLike[str], payload: bytes | bytearray | memoryview) -> Path:
    """Compatibility spelling for the public atomic binary writer."""

    return atomic_write_bytes(path, payload)


def metadata_json_bytes(metadata: Mapping[str, Any]) -> bytes:
    """Return deterministic UTF-8 JSON bytes for the gzip companion writer."""

    validate_metadata(metadata)
    try:
        payload = (
            json.dumps(
                dict(metadata), ensure_ascii=False, indent=2, sort_keys=True,
                allow_nan=False, separators=(",", ": "),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TrajectoryFormatError("metadata is not strict JSON serializable") from exc
    if len(payload) > MAX_METADATA_BYTES:
        raise TrajectoryFormatError("trajectory metadata exceeds the uncompressed size limit")
    return payload


def phase_name(code: int) -> str:
    """Return the stable display name for a phase code."""

    return _PHASE_NAMES.get(int(code), "UNKNOWN")


__all__ = [
    "ARRAY_DTYPES",
    "MAX_FRAMES",
    "MAX_SQUARES",
    "PHASE_ACCEPTED",
    "PHASE_FINAL",
    "PHASE_INITIAL",
    "PHASE_REJECTED",
    "PHASE_RELAXING",
    "PHASE_ROLLBACK",
    "PHASE_TRIAL",
    "ROLE_FINAL",
    "ROLE_INITIAL",
    "SCHEMA",
    "TrajectoryFormatError",
    "associated_metadata_path",
    "atomic_write_bytes",
    "encode_npz",
    "load_trajectory",
    "metadata_json_bytes",
    "phase_name",
    "validate_arrays",
    "validate_metadata",
    "write_bytes",
]
