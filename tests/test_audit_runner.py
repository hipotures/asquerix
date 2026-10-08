"""Regression checks derived from the independent runner/output audit."""

from __future__ import annotations

from pathlib import Path

from asquerix.output import summarize
from asquerix.persistence import read_json, read_jsonl


def test_saved_campaign_scalar_records_match_summary_counts() -> None:
    root = Path(__file__).parents[1] / "artifacts" / "pilot" / "campaign" / "repeat-0"
    records = list(read_jsonl(root / "trials.jsonl"))
    summary = read_json(root / "summary.json")

    assert summary["record_count"] == len(records) == 512
    assert summary["attempted_trials"] == len(records)
    assert sum(summary["gpu_status_counts"].values()) == len(records)
    assert sum(summary["validation_status_counts"].values()) == len(records)
    assert summary["accepted_trials"] == sum(record["gpu_status"] == "GPU_FEASIBLE" for record in records)
    assert summary["statistics"]["gpu_accepted"]["count"] == summary["accepted_trials"]
    assert summary["audit_coverage"]["audited_trials"] == sum(
        record["validation_status"] != "NOT_CHECKED" for record in records
    )


def test_summary_recomputation_preserves_pilot_populations() -> None:
    root = Path(__file__).parents[1] / "artifacts" / "pilot" / "campaign" / "repeat-0"
    records = list(read_jsonl(root / "trials.jsonl"))
    persisted = read_json(root / "summary.json")
    recomputed = summarize(records, persisted["timings"])

    assert recomputed["statistics"] == persisted["statistics"]
    assert recomputed["histogram"] == persisted["histogram"]
    assert recomputed["audit_coverage"] == persisted["audit_coverage"]
    assert recomputed["termination_counts"] == persisted["termination_counts"]
