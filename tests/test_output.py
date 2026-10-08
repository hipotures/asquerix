"""Tests for sparse pose output and factual run reporting."""

from __future__ import annotations

import json
from pathlib import Path

from asquerix.output import render_pose, render_selected, summarize, write_report


def pose_document(trial_id: int, side: float, status: str = "NOT_CHECKED") -> dict:
    return {
        "trial_id": trial_id,
        "n": 1,
        "side": side,
        "poses": [[0.0, 0.0, 0.0]],
        "validation": {"status": status},
    }


def test_render_pose_uses_actual_square_and_labels_invalid_debug(tmp_path: Path) -> None:
    path = render_pose(
        {
            "trial_id": 7,
            "n": 1,
            "side": 1.0,
            "poses": [[0.0, 0.0, 0.0]],
            "validation": {"status": "INVALID"},
        },
        tmp_path / "pose.svg",
    )

    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "validation=INVALID DEBUG" in text
    assert 'data-pose="0 0 0"' in text
    assert 'width="748" height="748"' in text
    assert text.count("class=\"square\"") == 1


def test_render_selected_deduplicates_sorts_by_side_then_trial_and_caps(tmp_path: Path) -> None:
    documents = [
        pose_document(9, 4.0),
        pose_document(3, 2.0),
        pose_document(9, 1.5),  # Same trial: the lower-side document wins.
        pose_document(2, 3.0),
    ]

    paths = render_selected(documents, tmp_path, max_images=2)

    assert [path.name for path in paths] == ["trial-9.svg", "trial-3.svg"]
    assert len(list(tmp_path.glob("*.svg"))) == 2
    assert "side=1.5" in paths[0].read_text(encoding="utf-8")


def test_render_selected_preserves_full_width_trial_ids(tmp_path: Path) -> None:
    first = 2**63 + 1
    second = 2**63 + 2

    paths = render_selected(
        [pose_document(first, 2.0), pose_document(second, 2.0)],
        tmp_path,
        max_images=2,
    )

    assert [path.name for path in paths] == [f"trial-{first}.svg", f"trial-{second}.svg"]
    assert f"trial_id={first}" in paths[0].read_text(encoding="utf-8")
    assert f"trial_id={second}" in paths[1].read_text(encoding="utf-8")


def test_summarize_separates_gpu_acceptance_validation_and_failures() -> None:
    records = [
        {
            "trial_id": 0,
            "n": 12,
            "side": 4.2,
            "termination_reason": "STEP_FLOOR_REACHED",
            "gpu_status": "GPU_FEASIBLE",
            "validation_status": "NUMERICALLY_VALIDATED",
            "attempts": 4,
            "sweeps": 20,
            "rejected": 1,
            "accepted": 3,
        },
        {
            "trial_id": 1,
            "n": 12,
            "side": 4.8,
            "termination_reason": "BUDGET_EXHAUSTED",
            "gpu_status": "GPU_FEASIBLE",
            "validation_status": "INDETERMINATE",
            "attempts": 5,
            "sweeps": 30,
            "rejected": 2,
            "accepted": 3,
        },
        {
            "trial_id": 2,
            "n": 12,
            "side": None,
            "termination_reason": "INIT_FAILED",
            "gpu_status": "NO_ACCEPTED_POSE",
            "validation_status": "NOT_CHECKED",
            "attempts": 1,
            "sweeps": 0,
            "rejected": 0,
            "accepted": 0,
        },
        {
            "trial_id": 3,
            "n": 12,
            "side": 5.0,
            "termination_reason": "NUMERICAL_FAILURE",
            "gpu_status": "NO_ACCEPTED_POSE",
            "validation_status": "INVALID",
            "attempts": 2,
            "sweeps": 4,
            "rejected": 1,
            "accepted": 0,
        },
    ]

    result = summarize(
        records,
        {
            "simulation_seconds": 1.25,
            "device_seconds": 2.0,
            "end_to_end_seconds": 4.0,
        },
    )

    assert result["accepted_trials"] == 2
    assert result["no_accepted_pose_trials"] == 2
    assert result["failure_counts"] == {
        "total": 2,
        "no_accepted_pose": 2,
        "initialization_failed": 1,
        "numerical_failure": 1,
        "budget_exhausted": 1,
    }
    assert result["statistics"]["gpu_accepted"]["count"] == 2
    assert result["statistics"]["gpu_accepted"]["best"] == 4.2
    assert result["statistics"]["numerically_validated"]["count"] == 1
    assert result["histogram"]["gpu_accepted"]["counts"] == [1, 1]
    assert result["audit_coverage"]["audited_trials"] == 3
    assert result["audit_coverage"]["coverage_fraction"] == 0.75
    assert result["counters"] == {"attempts": 12, "sweeps": 54, "rejected": 4, "accepted": 6}
    assert result["iteration_statistics"]["attempts"]["min"] == 1.0
    assert result["iteration_statistics"]["attempts"]["median"] == 3.0
    assert result["iteration_statistics"]["attempts"]["max"] == 5.0
    assert result["iteration_statistics"]["sweeps"]["min"] == 0.0
    assert result["iteration_statistics"]["sweeps"]["max"] == 30.0
    assert result["throughput"]["simulation_seconds"]["attempted_trials_per_second"] == 3.2
    assert result["throughput"]["simulation_seconds"]["gpu_feasible_trials_per_second"] == 1.6
    assert result["throughput"]["device_seconds"]["attempted_trials_per_second"] == 2.0
    assert result["throughput"]["end_to_end_seconds"]["gpu_feasible_trials_per_second"] == 0.5
    assert "not individual-trial latency" in result["throughput"]["simulation_seconds"]["meaning"]


def test_write_report_contains_observed_histogram_and_machine_summary(tmp_path: Path) -> None:
    records = [
        {
            "trial_id": 4,
            "n": 4,
            "side": 2.0,
            "termination_reason": "STEP_FLOOR_REACHED",
            "gpu_status": "GPU_FEASIBLE",
            "validation_status": "NUMERICALLY_VALIDATED",
            "attempts": 1,
            "sweeps": 2,
            "rejected": 0,
            "accepted": 1,
        },
        {
            "trial_id": 5,
            "n": 4,
            "side": None,
            "termination_reason": "INIT_FAILED",
            "gpu_status": "NO_ACCEPTED_POSE",
            "validation_status": "NOT_CHECKED",
            "attempts": 1,
            "sweeps": 0,
            "rejected": 0,
            "accepted": 0,
        },
    ]

    summary = write_report(tmp_path, records, {"end_to_end_seconds": 0.5}, {"seed": 123})

    assert summary["metadata"] == {"seed": 123}
    for name in ("summary.json", "report.md", "histogram.svg"):
        assert (tmp_path / name).exists()
    loaded = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    histogram = (tmp_path / "histogram.svg").read_text(encoding="utf-8")
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert loaded["histogram"]["gpu_accepted"]["count"] == 1
    assert histogram.count('class="bar"') == 2
    assert "GPU-feasible trials: 1" in report
    assert "Trials without an accepted pose: 1" in report
