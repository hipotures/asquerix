"""Bounded real-CUDA regression against the original scientific workload."""
from dataclasses import asdict
from pathlib import Path

import pytest

from asquerix.gpu import Config
from asquerix.persistence import read_json, read_jsonl
from asquerix.runner import run


@pytest.mark.gpu
def test_compressed_progress_runs_preserve_archived_search_and_partitioning(tmp_path, cuda_device):
    baseline = Path(__file__).parents[1] / "artifacts/pilot/extended/repeat-0"
    config = Config()
    assert asdict(config) == read_json(baseline / "config.json")["solver"]
    original = list(read_jsonl(baseline / "trials.jsonl"))[:4]
    def search(records):
        return [{key: value for key, value in record.items()
                 if key not in ("validation_status", "independent_validation")}
                for record in records]
    events = []
    for batch_size, progress in ((2, None), (4, events.append)):
        directory = tmp_path / f"batch-{batch_size}"
        result = run(config, trials=4, batch_size=batch_size, device=str(cuda_device), output=directory,
                     retain_all=True, keep_best=2, audit_size=4, sample_every=0, max_images=0,
                     max_seconds=30, progress=progress)
        records = list(read_jsonl(directory / "trials.jsonl"))
        assert search(records) == search(original)
        assert all(record["validation_status"] == "NUMERICALLY_VALIDATED" for record in records)
        assert result["summary"]["timings"]["device_seconds"] > 0
    assert [event["completed"] for event in events if event["event"] == "batch-completed"] == [4]
    assert events[-1]["best_validated_L"] is not None
