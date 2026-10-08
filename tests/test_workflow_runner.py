"""Focused workflow tests for runner metadata, progress, and compression."""

from __future__ import annotations

from pathlib import Path

import pytest

from asquerix import runner
from asquerix.gpu import Config
from asquerix.persistence import pose_paths, read_json, read_jsonl

from test_runner import _config, _factory


@pytest.fixture
def fake_environment(monkeypatch):
    monkeypatch.setattr(
        runner,
        "environment",
        lambda: {"python": "test", "gpu_query": {"exit_code": 0}, "dependencies": {}},
    )


def test_progress_events_are_batch_accurate_and_outputs_are_compressed(
    tmp_path: Path, fake_environment
) -> None:
    events: list[dict] = []
    output = tmp_path / "experiment"

    result = runner.run(
        _config(),
        trials=5,
        batch_size=2,
        trial_offset=100,
        experiment="n1-workflow",
        run_id="run-test",
        output=output,
        sample_every=0,
        keep_best=0,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        max_seconds=30.0,
        batch_factory=_factory(),
        progress=events.append,
    )

    assert [event["event"] for event in events] == [
        "init",
        "batch-start",
        "batch-completed",
        "batch-start",
        "batch-completed",
        "batch-start",
        "batch-completed",
        "finalizing",
    ]
    assert [event["completed"] for event in events if event["event"] == "batch-start"] == [0, 2, 4]
    assert [event["completed"] for event in events if event["event"] == "batch-completed"] == [2, 4, 5]
    assert all(event["requested"] == 5 for event in events)
    assert all(event["n"] == 1 and event["batch_size"] == 2 for event in events)
    assert events[-1]["completed"] == 5
    assert result["run_status"] == "COMPLETED"

    for name in ("config.json.gz", "environment.json.gz", "audit_ids.json.gz",
                 "validation.json.gz", "trials.jsonl.gz"):
        assert (output / name).exists()
    assert not (output / "config.json").exists()
    assert not (output / "trials.jsonl").exists()
    assert pose_paths(output / "poses") == []
    assert len(list(read_jsonl(output / "trials.jsonl"))) == 5
    assert read_json(output / "environment.json")["experiment_name"] == "n1-workflow"


def test_runner_generates_unique_safe_default_experiment_directory(
    tmp_path: Path, fake_environment, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    first = runner.run(
        _config(), trials=1, batch_size=1, max_images=0, audit_size=0,
        keep_best=0, sample_every=0, failure_examples=0, batch_factory=_factory(),
    )
    second = runner.run(
        _config(), trials=1, batch_size=1, max_images=0, audit_size=0,
        keep_best=0, sample_every=0, failure_examples=0, batch_factory=_factory(),
    )

    assert first["directory"] != second["directory"]
    assert Path(first["directory"]).is_dir()
    metadata = read_json(Path(first["directory"]) / "environment.json")
    assert metadata["experiment_name"].startswith("n1-s120-b1-run-")
    assert metadata["run_id"].startswith("run-")


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a b", "é", "a" * 81])
def test_experiment_name_rejects_unsafe_values(name: str) -> None:
    with pytest.raises(ValueError):
        runner.validate_experiment_name(name)


@pytest.mark.parametrize("run_id", ["", ".", "..", "a/b", "a" * 81])
def test_run_id_rejects_unsafe_values(tmp_path: Path, fake_environment, run_id: str) -> None:
    with pytest.raises(ValueError):
        runner.run(
            _config(),
            trials=1,
            batch_size=1,
            run_id=run_id,
            output=tmp_path / "unsafe",
            max_images=0,
            audit_size=0,
            keep_best=0,
            sample_every=0,
            failure_examples=0,
            batch_factory=_factory(),
        )

