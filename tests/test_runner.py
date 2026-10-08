"""Runner tests using a deterministic batch double instead of CUDA."""

from __future__ import annotations

import json
import signal
from pathlib import Path

import numpy as np
import pytest

from asquerix import runner
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


class FakeBatch:
    """Small host-side stand-in with the same boundary API as ``gpu.Batch``."""

    instances: list["FakeBatch"] = []

    def __init__(
        self,
        config: Config,
        capacity: int,
        device: str,
        *,
        fail_ids: set[int] | None = None,
        interrupt_after_warmup: bool = False,
        invalid_poses: bool = False,
        raise_on_call: int | None = None,
    ) -> None:
        self.config = config
        self.capacity = capacity
        self.device = f"fake:{device}"
        self.fail_ids = fail_ids or set()
        self.interrupt_after_warmup = interrupt_after_warmup
        self.invalid_poses = invalid_poses
        self.raise_on_call = raise_on_call
        self.module_load_seconds = 0.0
        self.calls: list[tuple[int, int]] = []
        self.current_offset = 0
        self.current_results = np.empty(0, dtype=_RESULT_DTYPE)
        FakeBatch.instances.append(self)

    def run(self, count: int, offset: int):
        self.calls.append((count, offset))
        self.current_offset = offset
        if self.raise_on_call is not None and len(self.calls) == self.raise_on_call:
            raise RuntimeError("synthetic batch failure")
        results = np.zeros(count, dtype=_RESULT_DTYPE)
        for index in range(count):
            trial_id = offset + index
            failed = trial_id in self.fail_ids
            results[index]["side"] = 0.0 if failed else 4.0 + 0.001 * (trial_id % 7)
            results[index]["min_gap"] = 1.0 if not failed else 0.0
            results[index]["min_wall"] = 1.0 if not failed else 0.0
            results[index]["max_penetration"] = 0.0
            results[index]["termination"] = 3 if failed else 1
            results[index]["feasible"] = 0 if failed else 1
            results[index]["attempts"] = 2 if not failed else 0
            results[index]["sweeps"] = 3 if not failed else 0
            results[index]["accepted"] = 1 if not failed else 0
            results[index]["rejected"] = 0
            results[index]["proposals"] = self.config.n if not failed else 1
            results[index]["final_step"] = 0.1
        self.current_results = results
        if self.interrupt_after_warmup and len(self.calls) == 2:
            signal.raise_signal(signal.SIGINT)
        return results, {
            "simulation_seconds": 0.01,
            "device_seconds": 0.005,
            "transfer_seconds": 0.001,
        }

    def get_poses(self, indices):
        indices = [int(index) for index in indices]
        poses = np.zeros((len(indices), self.config.n, 3), dtype=np.float64)
        for selected, index in enumerate(indices):
            _trial_id = self.current_offset + index
            for square in range(self.config.n):
                if not self.invalid_poses:
                    poses[selected, square, 0] = (square - (self.config.n - 1) / 2.0) * 1.5
        return poses, 0.001


@pytest.fixture(autouse=True)
def reset_fake_batches() -> None:
    FakeBatch.instances.clear()


@pytest.fixture
def fake_environment(monkeypatch):
    monkeypatch.setattr(
        runner,
        "environment",
        lambda: {"python": "test", "gpu_query": {"exit_code": 0}, "dependencies": {}},
    )


def _config(n: int = 1) -> Config:
    return Config(n=n, initial_side=10.0, seed=123, max_attempts=0)


def _factory(**options):
    def factory(config, capacity, device):
        return FakeBatch(config, capacity, device, **options)

    return factory


def _read_records(directory: Path) -> list[dict]:
    path = directory / "trials.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_select_indices_uses_global_periodic_ids_fixed_audits_and_tie_breaking() -> None:
    records = [
        {"trial_id": 100, "side": 3.0, "gpu_status": "GPU_FEASIBLE"},
        {"trial_id": 101, "side": 2.0, "gpu_status": "GPU_FEASIBLE"},
        {"trial_id": 102, "side": 2.0, "gpu_status": "GPU_FEASIBLE"},
        {"trial_id": 103, "side": None, "gpu_status": "NO_ACCEPTED_POSE"},
        {"trial_id": 104, "side": None, "gpu_status": "NO_ACCEPTED_POSE"},
    ]

    reasons, candidates = runner.select_indices(
        records,
        sample_every=4,
        audit_ids={101},
        keep_best=2,
        failures=1,
    )

    assert [records[index]["trial_id"] for index in candidates] == [101, 102, 100]
    assert reasons[0] == {"periodic"}
    assert reasons[1] == {"random_audit", "best_candidate"}
    assert reasons[2] == {"best_candidate"}
    assert reasons[3] == {"failure_example"}
    assert reasons[4] == {"periodic"}

    no_periodic, no_candidates = runner.select_indices(
        records,
        sample_every=0,
        audit_ids=set(),
        keep_best=0,
        failures=0,
    )
    assert no_periodic == {}
    assert [records[index]["trial_id"] for index in no_candidates] == [101, 102, 100]


def test_run_batches_cover_each_global_trial_once_after_warmup(tmp_path: Path, fake_environment) -> None:
    output = tmp_path / "scheduled"
    runner.run(
        _config(),
        trials=5,
        batch_size=2,
        trial_offset=100,
        output=output,
        sample_every=0,
        keep_best=0,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        max_seconds=30.0,
        batch_factory=_factory(),
    )

    batch = FakeBatch.instances[0]
    assert batch.calls == [(1, 100), (2, 100), (2, 102), (1, 104)]
    records = _read_records(output)
    assert [record["trial_id"] for record in records] == list(range(100, 105))


def test_sigint_preserves_completed_batch_and_stops_new_launches(tmp_path: Path, fake_environment) -> None:
    output = tmp_path / "interrupt"
    runner.run(
        _config(),
        trials=6,
        batch_size=2,
        trial_offset=10,
        output=output,
        sample_every=0,
        keep_best=2,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        max_seconds=30.0,
        batch_factory=_factory(interrupt_after_warmup=True),
    )

    batch = FakeBatch.instances[0]
    assert batch.calls == [(1, 10), (2, 10)]
    records = _read_records(output)
    assert [record["trial_id"] for record in records] == [10, 11]
    assert len(list((output / "poses").glob("trial-*.json"))) == 2
    metadata = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    assert metadata["stop_reason"] == "SIGINT"
    assert metadata["completed_trials"] == 2
    assert metadata["stop_observed_to_batch_completion_seconds"] >= 0.0


def test_invalid_debug_examples_are_bounded_across_batches(tmp_path: Path, fake_environment) -> None:
    output = tmp_path / "invalid-debug-cap"
    runner.run(
        _config(n=2),
        trials=6,
        batch_size=2,
        output=output,
        sample_every=0,
        keep_best=1,
        max_images=0,
        audit_size=0,
        failure_examples=1,
        max_seconds=30.0,
        batch_factory=_factory(invalid_poses=True),
    )

    records = _read_records(output)
    assert len(records) == 6
    assert all(record["validation_status"] == "INVALID" for record in records)
    pose_documents = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((output / "poses").glob("trial-*.json"))
    ]
    assert len(pose_documents) <= 1
    assert all(document["validation"]["status"] == "INVALID" for document in pose_documents)


def test_batch_exception_persists_error_stop_metadata(tmp_path: Path, fake_environment) -> None:
    output = tmp_path / "batch-error"
    with pytest.raises(RuntimeError, match="synthetic batch failure"):
        runner.run(
            _config(),
            trials=5,
            batch_size=2,
            output=output,
            sample_every=0,
            keep_best=0,
            max_images=0,
            audit_size=0,
            failure_examples=0,
            max_seconds=30.0,
            batch_factory=_factory(raise_on_call=3),
        )

    records = _read_records(output)
    metadata = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    assert [record["trial_id"] for record in records] == [0, 1]
    assert metadata["stop_reason"] == "ERROR"
    assert metadata["error"] == "RuntimeError: synthetic batch failure"
    assert metadata["completed_trials"] == 2


class _Clock:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        # Use a non-zero origin so the test also exercises elapsed-time
        # bookkeeping that must distinguish None from a valid zero timestamp.
        # Start, search-start, and the first loop check fit in the budget; the
        # first completed batch then advances the clock past the limit.
        if self.calls <= 2:
            return 10.0
        return 10.1 if self.calls == 3 else 11.0


def test_max_seconds_stops_after_completed_batch_without_another_launch(
    tmp_path: Path, fake_environment, monkeypatch
) -> None:
    clock = _Clock()
    monkeypatch.setattr(runner, "perf_counter", clock)
    output = tmp_path / "wall-time"

    runner.run(
        _config(),
        trials=5,
        batch_size=2,
        output=output,
        sample_every=0,
        keep_best=0,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        max_seconds=0.5,
        batch_factory=_factory(),
    )

    batch = FakeBatch.instances[0]
    assert batch.calls == [(1, 0), (2, 0)]
    metadata = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    assert metadata["stop_reason"] == "MAX_SECONDS"
    assert metadata["completed_trials"] == 2
    assert metadata["stop_observed_to_batch_completion_seconds"] > 0.0
    assert len(_read_records(output)) == 2


def test_retain_all_keeps_small_audit_batch_even_with_zero_leaderboard(tmp_path: Path, fake_environment) -> None:
    output = tmp_path / "retain-all"
    runner.run(
        _config(),
        trials=3,
        batch_size=2,
        output=output,
        sample_every=0,
        keep_best=0,
        max_images=0,
        audit_size=0,
        failure_examples=0,
        retain_all=True,
        max_seconds=30.0,
        batch_factory=_factory(),
    )

    pose_paths = sorted((output / "poses").glob("trial-*.json"))
    assert [path.stem for path in pose_paths] == ["trial-0", "trial-1", "trial-2"]
    assert all(
        json.loads(path.read_text(encoding="utf-8"))["validation_status"] == "NUMERICALLY_VALIDATED"
        for path in pose_paths
    )


@pytest.mark.parametrize(
    "kwargs",
    (
        {"trials": 0},
        {"batch_size": 0},
        {"max_seconds": 0.0},
        {"sample_every": -1},
        {"keep_best": -1},
        {"max_images": -1},
        {"audit_size": -1},
        {"failure_examples": -1},
        {"trial_offset": 2**64},
    ),
)
def test_run_rejects_malformed_controls(tmp_path: Path, fake_environment, kwargs: dict) -> None:
    with pytest.raises(ValueError):
        runner.run(
            _config(),
            output=tmp_path / ("bad-" + "-".join(f"{key}-{value}" for key, value in kwargs.items())),
            batch_factory=_factory(),
            **kwargs,
        )
