"""Regression test for durable audit status and pose retention."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from asquerix import runner
from asquerix.cli import main as cli_main
from asquerix.gpu import Config


_RESULT_DTYPE = np.dtype(
    [
        ("side", "<f8"),
        ("min_gap", "<f8"),
        ("min_wall", "<f8"),
        ("max_penetration", "<f8"),
        ("termination", "<i4"),
        ("feasible", "<i4"),
        ("attempts", "<i4"),
        ("sweeps", "<i4"),
        ("accepted", "<i4"),
        ("rejected", "<i4"),
        ("proposals", "<i4"),
        ("final_step", "<f8"),
    ]
)


class DescendingBatch:
    """A deterministic batch double whose later worlds always rank better."""

    def __init__(self, config: Config, capacity: int, device: str) -> None:
        self.config = config
        self.capacity = capacity
        self.device = f"fake:{device}"
        self.module_load_seconds = 0.0
        self.offset = 0

    def run(self, count: int, offset: int):
        self.offset = offset
        values = np.zeros(count, dtype=_RESULT_DTYPE)
        for index in range(count):
            trial_id = offset + index
            values[index]["side"] = 4.0 - 0.1 * trial_id
            values[index]["min_gap"] = 1.0
            values[index]["min_wall"] = 1.0
            values[index]["termination"] = 1
            values[index]["feasible"] = 1
            values[index]["final_step"] = 0.1
        return values, {"simulation_seconds": 0.0, "device_seconds": 0.0, "transfer_seconds": 0.0}

    def get_poses(self, indices):
        poses = np.zeros((len(indices), self.config.n, 3), dtype=np.float64)
        return poses, 0.0


def test_audited_scalar_records_have_durable_pose_evidence(tmp_path: Path, monkeypatch) -> None:
    """A candidate dropped by a later leaderboard update cannot stay audited alone."""

    monkeypatch.setattr(
        runner,
        "environment",
        lambda: {"python": "test", "gpu_query": {"exit_code": 0}, "dependencies": {}},
    )
    output = tmp_path / "retention"
    runner.run(
        Config(n=1, initial_side=10.0, max_attempts=0),
        trials=6,
        batch_size=2,
        output=output,
        sample_every=0,
        keep_best=1,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        max_seconds=30.0,
        batch_factory=DescendingBatch,
    )

    records = [json.loads(line) for line in (output / "trials.jsonl").read_text().splitlines()]
    saved_ids = {json.loads(path.read_text())["trial_id"] for path in (output / "poses").glob("*.json")}
    audited_ids = {record["trial_id"] for record in records if record["validation_status"] != "NOT_CHECKED"}

    assert audited_ids <= saved_ids


def test_validate_cli_does_not_relabel_initialization_failure_as_geometry_invalid(
    tmp_path: Path, capsys
) -> None:
    """An exhausted initializer has no pose to validate and remains NOT_CHECKED."""

    run = tmp_path / "init-failed"
    poses = run / "poses"
    poses.mkdir(parents=True)
    (poses / "trial-0.json").write_text(
        json.dumps(
            {
                "n": 2,
                "side": None,
                "poses": [],
                "trial_id": 0,
                "termination_reason": "INIT_FAILED",
                "gpu_status": "NO_ACCEPTED_POSE",
                "validation_status": "NOT_CHECKED",
                "validation": {"status": "NOT_CHECKED"},
            }
        ),
        encoding="utf-8",
    )

    assert cli_main(["validate", str(run)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output[0]["status"] == "NOT_CHECKED"

