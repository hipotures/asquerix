"""Bounded real-CUDA regression against the current production search."""

import numpy as np
import pytest

from asquerix.gpu import Batch, Config
from asquerix.persistence import pose_paths, read_json, read_jsonl
from asquerix.runner import run, scalar_records


@pytest.mark.gpu
def test_compressed_progress_runs_preserve_current_search_and_partitioning(tmp_path, cuda_device):
    config = Config()
    # Historical pilot scalars predate the corrected step-floor behavior.
    # Compare the workflow with a direct full-budget production submission.
    batch = Batch(config, 4, device=cuda_device)
    scalars, _ = batch.run(4, 0)
    expected = scalar_records(scalars, config, 0)
    expected_poses, _ = batch.get_poses([0, 1, 2, 3])

    def search(records):
        return [{key: value for key, value in record.items()
                 if key not in ("validation_status", "independent_validation")}
                for record in records]

    for batch_size in (2, 4):
        for with_progress in (False, True):
            events = []
            directory = tmp_path / f"batch-{batch_size}-progress-{with_progress}"
            result = run(config, trials=4, batch_size=batch_size, device=str(cuda_device), output=directory,
                         retain_all=True, keep_best=2, audit_size=4, sample_every=0, max_images=0,
                         max_seconds=30, progress=events.append if with_progress else None)
            records = list(read_jsonl(directory / "trials.jsonl"))
            assert search(records) == search(expected)
            assert all(record["validation_status"] == "NUMERICALLY_VALIDATED" for record in records)
            assert len(pose_paths(directory / "poses")) == 4
            for trial_id, expected_pose in enumerate(expected_poses):
                document = read_json(directory / "poses" / f"trial-{trial_id}.json")
                np.testing.assert_array_equal(document["poses"], expected_pose)
            assert result["summary"]["timings"]["device_seconds"] > 0
            if with_progress:
                assert [event["completed"] for event in events
                        if event["event"] == "batch-completed"] == list(range(batch_size, 5, batch_size))
                assert events[-1]["best_validated_L"] is not None
