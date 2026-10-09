"""Actual CUDA interpreter tests; never use a CPU simulation substitute."""

from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest
import warp as wp

from asquerix.gpu import Batch, Config, Result
from asquerix.geometry import validate_pose
from asquerix.lab.config import Campaign
from asquerix.lab.gpu import StrategyBatch, defined_fields
from asquerix.lab.strategy import compile_program, control_program
from asquerix.persistence import read_json

pytestmark = pytest.mark.gpu
BASELINE = Path(__file__).resolve().parents[1] / "artifacts/lab/baseline"
REFERENCES = read_json(BASELINE / "manifest.json.gz")["experiments"]


def starts(config, count, offset, device):
    initial = Batch(Config(**{**asdict(config), "max_attempts": 0}), count, device)
    initial.poses.zero_()
    initial.work.zero_()
    results, _ = initial.run(count, offset)
    poses, _ = initial.get_poses(np.arange(count, dtype=np.int32))
    assert np.all(results["termination"] != 3), "Test starts did not initialize"
    return results, poses


def execute(program, poses, initial, ids, *, slice_sweeps=16, recording=False, limits=None):
    spec = Campaign(name="CUDA test", n=poses.shape[1], batch_capacity=len(ids),
                    slice_sweeps=slice_sweeps, publication={"enabled": False}).document()
    if limits:
        spec["work_limits"].update(limits)
    campaign = Campaign.model_validate(spec)
    batch = StrategyBatch(campaign, [compile_program(program)], poses, initial, ids,
                          np.zeros(len(ids), dtype=np.uint64), np.zeros(len(ids), dtype=np.int32), recording=recording)
    for _ in range(100000):
        if batch.advance():
            break
    else:
        pytest.fail("Bounded interpreter failed to terminate")
    return batch, batch.collect()


@pytest.mark.parametrize("entry", REFERENCES, ids=lambda e: e["file"])
def test_legacy_program_matches_current_frozen_defined_bytes(entry, cuda_device):
    with np.load(BASELINE / entry["file"], allow_pickle=False) as archive:
        initial = np.zeros(entry["count"], dtype=Result.numpy_dtype())
        for name in initial.dtype.names:
            initial[name] = archive["initial_" + name]
        keep = initial["termination"] != 3
        if not np.any(keep):
            pytest.skip("Frozen initializer exhausted on these starts; no episode exists")
        poses = archive["initial_poses"][keep].copy()
        ids = np.arange(entry["count"], dtype=np.uint64) + np.uint64(int(entry["offset"]))
        _, (states, best, current) = execute(control_program("legacy_compress"), poses, initial[keep], ids[keep])
        for name in initial.dtype.names:
            actual = np.ascontiguousarray(states["result"][name]).view(np.uint8)
            expected = np.ascontiguousarray(archive["result_" + name][keep]).view(np.uint8)
            np.testing.assert_array_equal(actual, expected, err_msg=f"Defined result field {name}")
        np.testing.assert_array_equal(best.view(np.uint8), archive["poses"][keep].view(np.uint8))
        np.testing.assert_array_equal(current.view(np.uint8), best.view(np.uint8))
        assert np.all(states["termination"] == 1)
        for pose, row in zip(best, states, strict=True):
            assert validate_pose(pose, float(row["best_side"]), 1e-9)["status"] == "NUMERICALLY_VALIDATED"


def test_no_hidden_compression_expand_restore_and_relax(cuda_device):
    initial, poses = starts(Config(n=4), 2, 7, cuda_device)
    ids = np.asarray([7, 8], dtype=np.uint64)
    program = {"schema": "asquerix-strategy-v1", "body": [
        {"op": "EXPAND", "fraction": .04}, {"op": "RELAX"}, {"op": "STOP"}]}
    _, (states, best, current) = execute(program, poses, initial, ids)
    np.testing.assert_array_equal(best.view(np.uint8), poses.view(np.uint8))
    np.testing.assert_array_equal(current.view(np.uint8), poses.view(np.uint8))
    np.testing.assert_array_equal(states["best_side"], initial["side"])
    assert np.all(states["result"]["side"] > initial["side"])
    assert np.all(states["result"]["attempts"] == 0)
    assert np.all(states["last_outcome"] == 6)
    program["body"].insert(-1, {"op": "RESTORE_BEST"})
    _, (restored, _, restored_current) = execute(program, poses, initial, ids)
    assert np.all(restored["last_outcome"] == 9)
    assert np.all(restored["result"]["side"] == initial["side"])
    np.testing.assert_array_equal(restored_current.view(np.uint8), poses.view(np.uint8))
    assert np.all(restored["work"] > states["work"])


def test_slices_and_recording_preserve_all_defined_fields(cuda_device):
    initial, poses = starts(Config(n=4), 1, 2**64 - 7, cuda_device)
    ids = np.asarray([2**64 - 7], dtype=np.uint64)
    program = control_program("pulse_rotate", attempts=12, sweeps=40)
    program["body"].insert(-1, {"op": "RESTORE_BEST"})
    baseline, reference = execute(program, poses, initial, ids, slice_sweeps=128)
    for slice_sweeps, recording in ((1, False), (7, False), (7, True)):
        batch, actual = execute(program, poses, initial, ids, slice_sweeps=slice_sweeps, recording=recording)
        for name, field in defined_fields(actual[0]).items():
            np.testing.assert_array_equal(field.view(np.uint8), defined_fields(reference[0])[name].view(np.uint8), err_msg=name)
        for left, right in zip(actual[1:], reference[1:], strict=True):
            np.testing.assert_array_equal(left.view(np.uint8), right.view(np.uint8))
        if recording:
            trace, frames, events, capture = batch.trace()
            assert len(trace) > 3
            np.testing.assert_array_equal(trace[0].view(np.uint8), poses[0].view(np.uint8))
            np.testing.assert_array_equal(trace[-1].view(np.uint8), actual[2][0].view(np.uint8))
            np.testing.assert_array_equal(trace[-2].view(np.uint8), actual[1][0].view(np.uint8))
            assert np.any(events["flags"] & 64)


def fixture(poses, side):
    geometry = np.asarray(poses, dtype=np.float32)
    rows = np.zeros(len(geometry), dtype=Result.numpy_dtype())
    rows["side"] = side
    rows["final_step"] = .2
    rows["feasible"] = 1
    return rows, geometry


def test_effective_target_floor_and_fp32_no_progress(cuda_device):
    initial, poses = fixture([[[0., 0., 0.]]], 3.)
    ids = np.asarray([9], dtype=np.uint64)
    program = {"schema": "asquerix-strategy-v1", "body": [
        {"op": "COMPRESS", "target_reduction": .00001, "attempt_limit": 1, "sweep_limit": 1}, {"op": "STOP"}]}
    _, (states, best, _) = execute(program, poses, initial, ids)
    assert states["last_outcome"][0] == 1
    assert states["result"]["attempts"][0] == 1
    assert 0 < 3. - states["best_side"][0] < .0001
    program["body"][0]["target_reduction"] = 1e-10
    _, (states, best, current) = execute(program, poses, initial, ids)
    assert states["last_outcome"][0] == 3
    assert states["result"]["attempts"][0] == 0
    assert states["best_side"][0] == 3
    np.testing.assert_array_equal(current.view(np.uint8), poses.view(np.uint8))


def test_joint_proposal_rollback_empty_selection_and_rng_not_refunded(cuda_device):
    arrangement = [[x, y, 0.] for x in (-.500025, .500025) for y in (-.500025, .500025)]
    initial, poses = fixture([arrangement], 2.00012)
    ids = np.asarray([41], dtype=np.uint64)
    program = {"schema": "asquerix-strategy-v1", "body": [
        {"op": "MOVE", "selector": {"kind": "ALL"}, "max_distance": .5, "repair_sweeps": 1},
        {"op": "STOP"}]}
    batch, (states, best, current) = execute(program, poses, initial, ids, recording=True)
    assert states["last_outcome"][0] == 4
    np.testing.assert_array_equal(current.view(np.uint8), poses.view(np.uint8))
    assert states["rng_draws"][0] == 8
    assert np.any(batch.trace()[2]["flags"] & 16)
    program["body"][0]["selector"] = {"kind": "RANDOM_K", "k": 0}
    _, (empty, _, current) = execute(program, poses, initial, ids)
    assert empty["last_outcome"][0] == 5
    assert empty["rng_draws"][0] == 0
    assert empty["work"][0] > 0


def test_wall_selection_after_expansion_per_object_rotation_and_restore(cuda_device):
    initial, poses = starts(Config(n=4), 1, 51, cuda_device)
    ids = np.asarray([51], dtype=np.uint64)
    program = {"schema": "asquerix-strategy-v1", "body": [
        {"op": "EXPAND", "fraction": .04},
        {"op": "ROTATE", "selector": {"kind": "WALL_K", "k": 3}, "max_angle_rad": .1, "repair_sweeps": 120},
        {"op": "RESTORE_BEST"}, {"op": "STOP"}]}
    batch, (states, best, current) = execute(program, poses, initial, ids, recording=True)
    assert states["proposal_count"][0] == 3
    assert states["rng_draws"][0] == 3
    np.testing.assert_array_equal(current.view(np.uint8), poses.view(np.uint8))
    np.testing.assert_array_equal(best.view(np.uint8), poses.view(np.uint8))
    assert np.any(batch.trace()[2]["mask"])


def test_budget_cancellation_and_corrupted_device_program_are_bounded(cuda_device):
    initial, poses = starts(Config(n=4), 1, 71, cuda_device)
    ids = np.asarray([71], dtype=np.uint64)
    program = control_program("legacy_compress")
    _, (states, best, current) = execute(program, poses, initial, ids, limits={"contact_sweeps": 1})
    assert states["termination"][0] == 3
    assert states["result"]["sweeps"][0] == 1
    assert validate_pose(best[0], float(states["best_side"][0]), 1e-9)["status"] == "NUMERICALLY_VALIDATED"
    campaign = Campaign(name="Cancel", n=4, batch_capacity=1)
    for corrupt in (False, True):
        batch = StrategyBatch(campaign, [compile_program(program)], poses, initial, ids,
                              np.zeros(1, dtype=np.uint64), np.zeros(1, dtype=np.int32))
        if corrupt:
            wp.copy(batch.lengths, wp.array(np.asarray([999], dtype=np.int32), dtype=int, device=batch.device))
        assert batch.advance(cancel=not corrupt)
        state, best, current = batch.collect()
        assert state["termination"][0] == (5 if corrupt else 6)
        np.testing.assert_array_equal(current.view(np.uint8), poses.view(np.uint8))


def test_replay_writes_loadable_trace_with_shared_vm_steps(cuda_device, tmp_path):
    from asquerix.lab.trace import load_trace, replay
    initial, poses = starts(Config(n=4), 1, 91, cuda_device)
    ids = np.asarray([91], dtype=np.uint64)
    program = control_program("pulse_rotate")
    _, (states, best, current) = execute(program, poses, initial, ids)
    reference = {"state_" + name: array for name, array in defined_fields(states).items()}
    reference.update(best_poses=best, current_poses=current)
    campaign = Campaign(name="Replay", n=4, batch_capacity=1, publication={"enabled": False})
    compiled = compile_program(program)
    result = replay(campaign, tmp_path, candidate={"id": "c0", "program": {"authored": compiled.document()["authored"]}},
                    row={"initial_id": "91", "replicate": "0", "episode_key": "0" * 64, "termination": "STOPPED"},
                    bank={"poses": poses, "initial_results": initial, "ids": ids, "hash": "0" * 64},
                    reference_arrays=reference, reference_index=0, provenance={})
    assert result["status"] == "REPLAY_MATCHED"
    arrays, metadata = load_trace(tmp_path / "trajectories" / ("episode-" + "0" * 64 + ".npz"))
    assert np.all(np.diff(arrays["sequence"]) > 0)
    # The best snapshot and final current state are recorded at the same VM step.
    assert arrays["vm_sequence"][-2] == arrays["vm_sequence"][-1]
    assert metadata["strategy"]["frames"][-1]["vm_sequence"] == str(arrays["vm_sequence"][-1])


def test_campaign_worker_report_and_publication_end_to_end(cuda_device, tmp_path):
    import subprocess
    from types import SimpleNamespace
    from asquerix.lab.report import generate
    from asquerix.lab.worker import CampaignWorker
    from asquerix.publication import publish

    spec = Campaign(name="Worker publication", n=4, batch_capacity=8, controls=["legacy_compress"],
                    search={"methods": []}, datasets={"training": {"first_id": "100", "valid_count": 2},
                                                      "holdout": {"first_id": "200", "valid_count": 2}},
                    recording={"max_traces": 1}, publication={"enabled": True})
    directory = tmp_path / "campaign"
    messages = []
    worker = CampaignWorker({"id": "0" * 32, "spec": spec.document(), "directory": str(directory),
                             "checkpoint": str(tmp_path / "checkpoint.json.gz")},
                            emit=messages.append, signal=SimpleNamespace(value=0), signal_since=SimpleNamespace(value=0.0))
    summary = worker.run()
    assert summary["state"] == "COMPLETED"
    assert summary["completed_episode_executions"] == 4
    assert [item["status"] for item in summary["replays"]] == ["REPLAY_MATCHED"]
    generate(directory, [], campaign=spec)

    repo, remote = tmp_path / "repo", tmp_path / "remote.git"
    git = lambda cwd, *args: subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
    repo.mkdir()
    git(repo, "init", "--initial-branch=main")
    git(repo, "config", "user.name", "Asquerix Test")
    git(repo, "config", "user.email", "asquerix@example.invalid")
    (repo / "README.md").write_text("test\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    git(tmp_path, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "origin", "main")
    result = publish(directory, repo=repo, push=True)
    assert result["status"] == "PUBLISHED", result
    assert git(remote, "rev-parse", "main") == result["commit_sha"]
    published = git(remote, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert result["artifact_path"] + "/report.html" in published
    assert any(path.endswith(".npz") and "/trajectories/episode-" in path for path in published)
