"""Deterministic, atomic persistence for experiment JSON artifacts.

New experiment JSON and JSONL artifacts are gzip-compressed.  Readers resolve
both the new compressed spelling and the historical uncompressed spelling so
that old evidence remains usable without rewriting it.
"""

from __future__ import annotations

from contextlib import contextmanager
import gzip
import io
import json
import os
from pathlib import Path
import tempfile
from collections.abc import Iterator
from typing import Any


_JSON_SUFFIXES = (".json", ".jsonl")
_GZIP_SUFFIX = ".gz"
# Explicit lossless compression policy; benchmarked independently of the solver.
GZIP_COMPRESSION_LEVEL = 3


def _compressed_path(path: Path) -> Path:
    """Return the canonical compressed destination for a JSON path."""

    if path.name.endswith((".json.gz", ".jsonl.gz")):
        return path
    if path.suffix in _JSON_SUFFIXES:
        return path.with_name(path.name + _GZIP_SUFFIX)
    return path


def _alternate_path(path: Path) -> Path:
    if path.name.endswith((".json.gz", ".jsonl.gz")):
        return path.with_name(path.name[:-len(_GZIP_SUFFIX)])
    if path.suffix in _JSON_SUFFIXES:
        return path.with_name(path.name + _GZIP_SUFFIX)
    return path.with_name(path.name + _GZIP_SUFFIX)


def resolve_path(path: str | os.PathLike[str]) -> Path:
    """Resolve a JSON/JSONL path while preferring an explicit existing path.

    If ``path`` exists it is returned unchanged.  Otherwise the compressed or
    uncompressed spelling is tried.  This explicit-first behavior lets callers
    inspect a historical plain artifact even when a similarly named compressed
    artifact is present.
    """

    requested = Path(path)
    if requested.exists():
        return requested
    alternate = _alternate_path(requested)
    if alternate.exists():
        return alternate
    return requested


def _json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def write_json(path: str | os.PathLike[str], value: Any) -> Path:
    """Atomically write deterministic JSON, gzip-compressed for JSON paths.

    ``path`` may use either the historical plain spelling (``summary.json``)
    or the canonical compressed spelling (``summary.json.gz``).  Plain
    ``.json`` and ``.jsonl`` names are converted to their ``.gz`` destination;
    the returned path is the path that was written.
    """

    requested = Path(path)
    target = _compressed_path(requested)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_text(value).encode("utf-8")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as raw:
            temporary = Path(raw.name)
            if target.name.endswith(_GZIP_SUFFIX):
                with gzip.GzipFile(
                    fileobj=raw,
                    mode="wb",
                    filename="",
                    mtime=0,
                    compresslevel=GZIP_COMPRESSION_LEVEL,
                ) as compressed:
                    compressed.write(payload)
            else:
                raw.write(payload)
            raw.flush()
            os.fsync(raw.fileno())
        os.replace(temporary, target)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        raise
    return target


def _open_json_text(path: str | os.PathLike[str], mode: str = "rt"):
    resolved = resolve_path(path)
    if resolved.name.endswith(_GZIP_SUFFIX):
        return gzip.open(resolved, mode, encoding="utf-8", newline="")
    return resolved.open(mode, encoding="utf-8", newline="")


def read_json(path: str | os.PathLike[str]) -> Any:
    """Load JSON from either a plain or gzip-compressed artifact."""

    with _open_json_text(path, "rt") as stream:
        return json.load(stream)


def read_jsonl(path: str | os.PathLike[str]) -> Iterator[Any]:
    """Yield JSONL records from either a plain or gzip-compressed artifact."""

    with _open_json_text(path, "rt") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


@contextmanager
def open_binary(path: str | os.PathLike[str], mode: str = "rb") -> Iterator[Any]:
    """Open a resolved artifact as binary data.

    This helper is intended for streaming hashes or archive copies where the
    uncompressed bytes matter.  Read modes resolve plain/gzip spellings using
    the same rules as :func:`read_json`; write modes use the exact path given
    by the caller and do not provide atomic replacement.
    """

    requested = Path(path)
    resolved = resolve_path(requested) if "r" in mode else requested
    if resolved.name.endswith(_GZIP_SUFFIX):
        with gzip.open(resolved, mode) as stream:
            yield stream
    else:
        with resolved.open(mode) as stream:
            yield stream


@contextmanager
def open_jsonl_writer(path: str | os.PathLike[str]) -> Iterator[io.TextIOBase]:
    """Stream JSONL to an atomic deterministic gzip artifact.

    The target is replaced only after the stream is closed.  A caller that is
    interrupted after completed records have been flushed still gets a valid,
    readable partial JSONL archive because the temporary stream is finalized
    and published on both normal and exceptional context exit.
    """

    requested = Path(path)
    target = _compressed_path(requested)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    raw = None
    text_stream: io.TextIOWrapper | None = None
    try:
        raw = tempfile.NamedTemporaryFile(
            mode="w+b",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        )
        temporary = Path(raw.name)
        if target.name.endswith(_GZIP_SUFFIX):
            compressed = gzip.GzipFile(
                fileobj=raw,
                mode="wb",
                filename="",
                mtime=0,
                compresslevel=GZIP_COMPRESSION_LEVEL,
            )
            text_stream = io.TextIOWrapper(compressed, encoding="utf-8", newline="")
        else:
            text_stream = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        yield text_stream
    finally:
        if text_stream is not None:
            try:
                text_stream.flush()
            finally:
                text_stream.close()
        elif raw is not None:
            raw.close()
        if raw is not None and not raw.closed:
            raw.close()
        if temporary is not None:
            if temporary.exists():
                with temporary.open("ab") as completed:
                    completed.flush()
                    os.fsync(completed.fileno())
                os.replace(temporary, target)


def pose_paths(directory: str | os.PathLike[str]) -> list[Path]:
    """Return de-duplicated retained pose paths in deterministic order.

    Both ``trial-<id>.json`` and ``trial-<id>.json.gz`` are accepted.  When
    both spellings exist for one trial, the compressed artifact is preferred
    because it is the canonical spelling produced by new runs.
    """

    root = Path(directory)
    selected: dict[str, Path] = {}
    for path in root.glob("trial-*.json.gz"):
        selected[path.name[:-len(_GZIP_SUFFIX)]] = path
    for path in root.glob("trial-*.json"):
        selected.setdefault(path.name, path)
    return [selected[key] for key in sorted(selected)]
