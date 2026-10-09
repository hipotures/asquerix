"""Tests for compressed experiment persistence and legacy path resolution."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import struct

import pytest

from asquerix.persistence import (
    open_jsonl_writer,
    pose_paths,
    read_json,
    read_jsonl,
    resolve_path,
    write_json,
)


def test_write_json_uses_deterministic_gzip_and_round_trips(tmp_path: Path) -> None:
    value = {"z": [3, 2, 1], "a": {"answer": 42}}
    path = write_json(tmp_path / "summary.json", value)

    assert path == tmp_path / "summary.json.gz"
    assert path.exists()
    assert read_json(tmp_path / "summary.json") == value
    first = path.read_bytes()
    assert gzip.decompress(first).decode("utf-8") == json.dumps(
        value, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"

    assert write_json(tmp_path / "summary.json", value) == path
    assert path.read_bytes() == first


def test_read_json_prefers_explicit_existing_path_and_supports_legacy_plain_json(
    tmp_path: Path,
) -> None:
    plain = tmp_path / "config.json"
    plain.write_text('{"source": "legacy"}\n', encoding="utf-8")
    assert resolve_path(plain) == plain
    assert read_json(plain) == {"source": "legacy"}

    compressed = write_json(tmp_path / "other.json", {"source": "gzip"})
    assert resolve_path(compressed.with_suffix("")) == compressed
    assert read_json(compressed.with_suffix("")) == {"source": "gzip"}


def test_jsonl_streaming_writer_and_reader_support_plain_legacy_files(tmp_path: Path) -> None:
    records = [{"trial_id": index, "side": 4.0 + index} for index in range(3)]
    with open_jsonl_writer(tmp_path / "trials.jsonl") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

    assert (tmp_path / "trials.jsonl.gz").exists()
    assert list(read_jsonl(tmp_path / "trials.jsonl")) == records

    legacy = tmp_path / "legacy.jsonl"
    legacy.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")
    assert list(read_jsonl(legacy)) == records


def test_jsonl_writer_publishes_flushed_partial_records_after_exception(tmp_path: Path) -> None:
    path = tmp_path / "partial.jsonl"
    with pytest.raises(RuntimeError, match="stop"):
        with open_jsonl_writer(path) as stream:
            stream.write('{"trial_id": 1}\n')
            stream.flush()
            raise RuntimeError("stop")

    assert list(read_jsonl(path)) == [{"trial_id": 1}]


def test_pose_paths_deduplicate_plain_and_compressed_spellings(tmp_path: Path) -> None:
    poses = tmp_path / "poses"
    poses.mkdir()
    (poses / "trial-2.json").write_text("{}\n", encoding="utf-8")
    write_json(poses / "trial-2.json", {"trial_id": 2, "source": "gzip"})
    (poses / "trial-10.json").write_text("{}\n", encoding="utf-8")

    paths = pose_paths(poses)
    assert [path.name for path in paths] == ["trial-10.json", "trial-2.json.gz"]



def test_atomic_json_failure_does_not_replace_complete_document(tmp_path):
    path = write_json(tmp_path / "complete.json", {"value": 1})
    original = path.read_bytes()
    with pytest.raises(ValueError):
        write_json(path, {"value": float("nan")})
    assert path.read_bytes() == original
    assert read_json(path) == {"value": 1}
    assert not list(tmp_path.glob(".*.tmp"))


def test_streaming_archive_bytes_are_deterministic(tmp_path):
    for name in ("one.jsonl", "two.jsonl"):
        with open_jsonl_writer(tmp_path / name) as stream:
            for index in range(5000):
                stream.write(json.dumps({"trial_id": index}) + "\n")
            stream.flush()
    assert (tmp_path / "one.jsonl.gz").read_bytes() == (tmp_path / "two.jsonl.gz").read_bytes()
    assert len(list(read_jsonl(tmp_path / "one.jsonl"))) == 5000


def test_explicit_compression_policy_preserves_float_bits_and_uint64(tmp_path, monkeypatch):
    from asquerix import persistence

    levels = []
    original = gzip.GzipFile

    def recording_gzip(*args, **kwargs):
        levels.append(kwargs.get("compresslevel"))
        return original(*args, **kwargs)

    monkeypatch.setattr(gzip, "GzipFile", recording_gzip)
    record = {"trial_id": 2**64 - 1, "values": [-0.0, 0.0, 1.0000000000000002, 1e-300]}
    write_json(tmp_path / "record.json", record)
    with open_jsonl_writer(tmp_path / "records.jsonl") as stream:
        stream.write(json.dumps(record) + "\n")
    assert levels == [persistence.GZIP_COMPRESSION_LEVEL] * 2
    for restored in (read_json(tmp_path / "record.json"), *read_jsonl(tmp_path / "records.jsonl")):
        assert restored["trial_id"] == 2**64 - 1
        assert type(restored["trial_id"]) is int
        assert [struct.pack("!d", x) for x in restored["values"]] == [
            struct.pack("!d", x) for x in record["values"]
        ]
