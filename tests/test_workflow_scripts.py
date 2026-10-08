"""Offline smoke tests for maintained experiment workflow scripts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from asquerix.persistence import open_binary, open_jsonl_writer, read_json, read_jsonl, write_json


ROOT = Path(__file__).parents[1]


def load_tool(name: str) -> ModuleType:
    path = ROOT / "tools" / name
    spec = importlib.util.spec_from_file_location(f"asquerix_test_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record() -> dict:
    return {
        "trial_id": 0,
        "n": 1,
        "side": 2.0,
        "termination_reason": "STEP_FLOOR_REACHED",
        "gpu_status": "GPU_FEASIBLE",
        "validation_status": "NUMERICALLY_VALIDATED",
        "attempts": 1,
        "sweeps": 1,
    }


def _pose() -> dict:
    return {
        **_record(),
        "poses": [[0.0, 0.0, 0.0]],
        "validation": {
            "status": "NUMERICALLY_VALIDATED",
            "min_pair_separation": None,
            "max_penetration": 0.0,
            "min_wall_clearance": 0.5,
            "nonfinite": False,
            "tolerance": 1e-8,
            "edge_length_error": 0.0,
        },
    }


def make_run(root: Path, *, compressed: bool) -> Path:
    run = root / ("compressed" if compressed else "plain")
    (run / "poses").mkdir(parents=True)
    record = _record()
    pose = _pose()
    summary = {"record_count": 1, "attempted_trials": 1, "accepted_trials": 1}
    if compressed:
        write_json(run / "summary.json", summary)
        write_json(run / "config.json", {"runner": {"batch_size": 1}})
        write_json(run / "poses" / "trial-0.json", pose)
        with open_jsonl_writer(run / "trials.jsonl") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
    else:
        (run / "summary.json").write_text(json.dumps(summary) + "\n", encoding="utf-8")
        (run / "config.json").write_text('{"runner": {"batch_size": 1}}\n', encoding="utf-8")
        (run / "poses" / "trial-0.json").write_text(json.dumps(pose) + "\n", encoding="utf-8")
        (run / "trials.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    return run


def test_checker_reads_historical_plain_and_new_gzip_runs(tmp_path: Path) -> None:
    checker = load_tool("check_artifacts.py")
    plain = make_run(tmp_path, compressed=False)
    compressed = make_run(tmp_path, compressed=True)

    report = checker.audit_root(tmp_path, None, None)
    by_name = {Path(item["path"]).name: item for item in report["runs"]}
    assert by_name[plain.name]["record_source"] == "trials.jsonl"
    assert by_name[compressed.name]["record_source"] == "trials.jsonl.gz"
    assert all(item["records"] == 1 for item in report["runs"])
    assert all(item["geometry"]["status_or_metric_mismatch_count"] == 0 for item in report["runs"])

    output = tmp_path / "checker-report.json"
    assert checker.main(
        [str(tmp_path), "--fixture", str(tmp_path / "missing-fixture.json"), "--output", str(output)]
    ) == 0
    assert output.with_name("checker-report.json.gz").exists()
    assert read_json(output)["aggregate"]["records"] == 2


@pytest.mark.parametrize("source_compressed", [False, True])
def test_reproduce_archive_streams_plain_and_gzip_sources(tmp_path: Path, source_compressed: bool) -> None:
    reproduce = load_tool("reproduce_audit.py")
    source = make_run(tmp_path / "source", compressed=source_compressed)
    target = tmp_path / "archive"

    with open_binary(source / "trials.jsonl", "rb") as stream:
        expected_raw = stream.read()
    expected_sha = hashlib.sha256(expected_raw).hexdigest()
    assert reproduce.archive_run(source, target) == expected_sha
    assert list(read_jsonl(target / "trials.jsonl")) == [_record()]
    assert (target / "trials.jsonl.gz").exists()


def test_maintained_script_defaults_do_not_target_historical_artifacts() -> None:
    for name in ("reproduce_audit.py", "extended_benchmark.py", "check_stop.py", "check_artifacts.py"):
        text = (ROOT / "tools" / name).read_text(encoding="utf-8")
        assert "artifacts/pilot/stop-sigint" not in text
    assert "runs/audit-archive" in (ROOT / "tools/reproduce_audit.py").read_text(encoding="utf-8")
    assert "runs/extended-archive" in (ROOT / "tools/extended_benchmark.py").read_text(encoding="utf-8")

