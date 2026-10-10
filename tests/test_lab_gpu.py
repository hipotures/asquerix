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
    assert git(remote, "log", "-1", "--format=%s", "main") == "lab campaign: Worker publication (COMPLETED, 4 episodes)"
    published = git(remote, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert result["artifact_path"] + "/report.html" in published
    assert any(path.endswith(".npz") and "/trajectories/episode-" in path for path in published)


def _run_worker(root, identifier, spec):
    from types import SimpleNamespace
    from asquerix.lab.worker import CampaignWorker
    messages = []
    worker = CampaignWorker({"id": identifier, "spec": spec.document(), "directory": str(root / "campaigns" / identifier),
                             "checkpoint": str(root / "checkpoints" / (identifier + ".json.gz"))},
                            emit=messages.append, signal=SimpleNamespace(value=0), signal_since=SimpleNamespace(value=0.0))
    return worker.run(), worker.state, messages


def test_continuation_reproduces_a_single_campaign_with_the_larger_budget(cuda_device, tmp_path):
    from asquerix.lab.continuation import continuation_spec
    base = Campaign(name="Continuation", n=4, batch_capacity=16, controls=["legacy_compress"],
                    search={"candidate_budget_per_method": 2, "initial_pool": 1, "lambda": 1},
                    datasets={"training": {"first_id": "100", "valid_count": 2}, "holdout": {"first_id": "200", "valid_count": 2}},
                    generation={"min_nodes": 2, "max_nodes": 4}, recording={"max_traces": 2}, publication={"enabled": False})
    parent_summary, _, _ = _run_worker(tmp_path, "a" * 32, base)
    child_spec = continuation_spec({"id": "a" * 32, "spec": base.document()}, 2, {"batch_capacity": 7, "name": "Continued"})
    summary, state, messages = _run_worker(tmp_path, "b" * 32, child_spec)
    single_spec = Campaign.model_validate({**base.document(), "search": {**base.document()["search"], "candidate_budget_per_method": 4}})
    _, single, _ = _run_worker(tmp_path, "c" * 32, single_spec)

    assert summary["state"] == "COMPLETED"
    assert summary["continuation"]["parent_id"] == "a" * 32
    assert summary["continuation"]["inherited_episode_executions"] == parent_summary["completed_episode_executions"]
    def programs(identifier, method):
        records = {}
        for record in read_jsonl_all(tmp_path / "campaigns" / identifier / "candidates.jsonl.gz"):
            if record["arm"] == method and "score" in record and record["score"]:
                records[record["id"]] = record
        return sorted(records.values(), key=lambda record: record["position"])
    for method in ("random_program_search", "one_plus_lambda"):
        continued, reference = state["controllers"][method], single["controllers"][method]
        assert continued["completed"] == reference["completed"] == 4
        child, alone = programs("b" * 32, method), programs("c" * 32, method)
        assert [c["program"]["hash"] for c in child] == [c["program"]["hash"] for c in alone]
        assert [c["score"]["ranking_tuple"] for c in child] == [c["score"]["ranking_tuple"] for c in alone]
        assert continued["rng_state"] == reference["rng_state"]
        assert child[0]["id"].startswith("a" * 32) and child[-1]["id"].startswith("b" * 32)
    # Only new episodes are executed; the inherited control holdout is not repeated.
    new_episodes = summary["completed_episode_executions"] - summary["continuation"]["inherited_episode_executions"]
    holdout_runs = sum(1 for message in messages if message["type"] == "candidate" and "holdout_score" in message["candidate"]
                       and message["candidate"]["arm"] == "controls")
    assert new_episodes <= 2 * 2 * 2 + 2 * 2  # two new candidates per method on two training starts, plus up to two winners on holdout
    assert holdout_runs <= 1  # the inherited control result is only re-announced
    assert any(message["type"] == "chunk" and message.get("inherited") for message in messages)
    assert all(item["status"] == "REPLAY_MATCHED" for item in summary["replays"])


def test_parallel_validation_returns_the_serial_rows_and_holdout_is_not_repeated(cuda_device, tmp_path, monkeypatch):
    from asquerix.lab import worker as module
    from asquerix.lab.continuation import continuation_spec
    initial, poses = starts(Config(n=6), 160, 300, cuda_device)
    ids = np.arange(300, 460, dtype=np.uint64)
    _, (states, best, current) = execute(control_program("legacy_compress"), poses, initial, ids)
    campaign = Campaign(name="Rows", n=6, batch_capacity=160, publication={"enabled": False})
    items = [(states[i], best[i], current[i], "p", "b", str(int(ids[i])), "0") for i in range(len(ids))]
    worker = module.CampaignWorker.__new__(module.CampaignWorker)
    worker.campaign, worker.pool = campaign, None
    try:
        assert worker.result_rows(items) == [module._result_row(campaign, item) for item in items]
        assert worker.pool is not None
        # The campaign path validates whole chunks with the batched validator; its rows match too.
        chunk = {"states": states, "best": best, "current": current, "program_hashes": ["p"] * len(ids),
                 "candidate_ids": ["c"] * len(ids), "arms": ["a"] * len(ids), "initial_ids": ids, "replicates": np.zeros(len(ids), np.uint64), "identifier": "i", "bank": "training", "bank_hash": "b", "attempt": 1}
        rows = worker.validate_async(chunk).result()
        expected = [module._result_row(campaign, item) for item in items]
        assert [{key: row[key] for key in expected[0]} for row in rows] == expected
    finally:
        worker.close()

    monkeypatch.setattr(module, "PARALLEL_VALIDATION_MINIMUM", 1)  # exercise the pool inside real campaigns
    base = Campaign(name="Holdout once", n=4, batch_capacity=16, controls=["legacy_compress"],
                    search={"candidate_budget_per_method": 2, "initial_pool": 1, "lambda": 1},
                    datasets={"training": {"first_id": "100", "valid_count": 2}, "holdout": {"first_id": "200", "valid_count": 2}},
                    generation={"min_nodes": 2, "max_nodes": 4}, recording={"automatic": False}, publication={"enabled": False})
    _run_worker(tmp_path, "d" * 32, base)
    child = continuation_spec({"id": "d" * 32, "spec": base.document()}, 1, {})
    _, state, _ = _run_worker(tmp_path, "e" * 32, child)
    keys = [(row["candidate_id"], row["episode_key"]) for chunk in state["chunks"]
            for row in __import__("asquerix.persistence", fromlist=["read_jsonl"]).read_jsonl(tmp_path / "campaigns" / ("e" * 32) / chunk["records_path"])]
    assert len(keys) == len(set(keys)), "an episode was evaluated twice"


@pytest.mark.parametrize("evidence", ["all", "important"])
def test_search_reproduces_the_recorded_golden_programs_and_scores(cuda_device, tmp_path, evidence):
    """Grouping and storage changes must not change which programs are tried or how they score."""
    import json
    golden = json.loads((Path(__file__).parent / "data" / "lab_search_golden.json").read_text())
    spec = Campaign.model_validate({**golden["spec"], "pose_evidence": evidence})
    _, state, _ = _run_worker(tmp_path, "f" * 32, spec)
    log = {}
    for record in read_jsonl_all(tmp_path / "campaigns" / ("f" * 32) / "candidates.jsonl.gz"):
        log.setdefault(record["id"], {}).update(record)
    for method in ("random_program_search", "one_plus_lambda"):
        records = sorted((record for record in log.values() if record["arm"] == method), key=lambda record: record["position"])
        assert [(r["position"], r["program"]["hash"], r["score"]["ranking_tuple"], r["score"]["mean_best_L"]) for r in records] == \
               [(g["position"], g["program_hash"], g["ranking_tuple"], g["mean_best_L"]) for g in golden[method]]
    winners = sorted((w["arm"], w["program"]["hash"], w["score"]["ranking_tuple"]) for w in state["frozen_winners"])
    assert [list(w) for w in winners] == golden["winners"]
    holdout = sorted((c["id"].split(":", 1)[1], c["holdout_score"]["mean_best_L"]) for c in state["candidates"] if c.get("holdout_score"))
    assert [list(h) for h in holdout] == golden["holdout"]


def read_jsonl_all(path):
    from asquerix.persistence import read_jsonl
    return list(read_jsonl(path))


def test_time_budget_fills_the_gpu_keeps_important_evidence_and_still_runs_holdout(cuda_device, tmp_path):
    from asquerix.lab.config import RETAINED_PER_METHOD
    spec = Campaign(name="Timed", n=4, batch_capacity=256, controls=["legacy_compress"], pose_evidence="important",
                    search={"candidate_budget_per_method": 1_000_000, "initial_pool": 2, "lambda": 0, "time_budget_seconds": 8},
                    datasets={"training": {"first_id": "100", "valid_count": 4}, "holdout": {"first_id": "200", "valid_count": 2}},
                    generation={"min_nodes": 2, "max_nodes": 4}, recording={"automatic": False}, publication={"enabled": False},
                    limits={"max_seconds": 120})
    assert spec.effective_lambda() == 256 and spec.random_group_size() == 256
    summary, state, messages = _run_worker(tmp_path, "9" * 32, spec)
    assert summary["state"] == "COMPLETED" and summary["stop_reason"] is None
    assert {state["outcome"] for state in summary["controllers"].values()} == {"TIME_BUDGET_REACHED"}
    events = [message["payload"] for message in messages if message["type"] == "event" and message["kind"] == "TIME_BUDGET_REACHED"]
    assert len(events) == 2 and all(4 <= event["seconds"] < 30 for event in events)
    log = {}
    for record in read_jsonl_all(tmp_path / "campaigns" / ("9" * 32) / "candidates.jsonl.gz"):
        log.setdefault(record["id"], {}).update(record)
    searched = [record for record in log.values() if record["arm"] != "controls"]
    assert summary["evaluated_programs"] == len(searched) > 2 * 2 * RETAINED_PER_METHOD
    assert all(record["score"]["complete"] and record["score"]["validation_counts"] for record in searched)
    tops = summary["top_evidence"]
    rows = [row for chunk in state["chunks"] + tops for row in read_jsonl_all(tmp_path / "campaigns" / ("9" * 32) / chunk["records_path"])]
    for top in tops:  # each method's file holds exactly its best programs
        arm = [record for record in searched if record["arm"] == top["arm"] and record["score"]["eligible"]]
        best = sorted(arm, key=lambda record: tuple(record["score"]["ranking_tuple"]))[:RETAINED_PER_METHOD]
        assert top["programs"] == [record["id"] for record in best]
    with_poses = {row["candidate_id"] for row in rows if row["bank"] == "training"}
    print("searched", len(searched), "with poses", len(with_poses), {arm: sum(r["arm"] == arm for r in searched) for arm in ("random_program_search", "one_plus_lambda")}, {arm: sum(i.split(":")[1] == arm for i in with_poses) for arm in ("random_program_search", "one_plus_lambda")})
    assert len(with_poses) < 3 * RETAINED_PER_METHOD < len(searched)
    winners = {winner["id"] for winner in state["frozen_winners"]}
    assert winners <= with_poses and all(candidate.get("holdout_score") for candidate in state["candidates"] if candidate["id"] in winners)


def _mixed_programs(count, seed):
    import random
    from asquerix.lab.config import Generation
    from asquerix.lab.search import generate
    rng = random.Random(seed)
    return [compile_program(generate(rng, Generation())) for _ in range(count)]


def test_streaming_slots_give_the_same_bytes_as_one_batch(cuda_device):
    from asquerix.lab.gpu import StreamingBatch
    initial, poses = starts(Config(n=6), 20, 700, cuda_device)
    programs = _mixed_programs(6, 11)
    slots = np.tile(np.arange(20), 6)
    pids = np.repeat(np.arange(6), 20).astype(np.int32)
    ids = np.arange(700, 720, dtype=np.uint64)[slots]
    replicates = np.zeros(len(ids), dtype=np.uint64)
    spec = Campaign(name="Stream", n=6, batch_capacity=len(ids), publication={"enabled": False})
    whole = StrategyBatch(spec, programs, poses[slots], initial[slots], ids, replicates, pids)
    while not whole.advance():
        pass
    expected = whole.collect()
    narrow = Campaign.model_validate({**spec.document(), "batch_capacity": 16})
    stream = StreamingBatch(narrow, programs, poses[slots], initial[slots], ids, replicates, pids)
    while not stream.advance():
        pass
    actual = stream.collect()
    for name, array in defined_fields(expected[0]).items():
        np.testing.assert_array_equal(defined_fields(actual[0])[name].view(np.uint8), array.view(np.uint8), err_msg=name)
    np.testing.assert_array_equal(actual[1].view(np.uint8), expected[1].view(np.uint8))
    np.testing.assert_array_equal(actual[2].view(np.uint8), expected[2].view(np.uint8))


def test_streaming_keeps_slots_busy_when_program_lengths_differ(cuda_device):
    from asquerix.lab.gpu import StreamingBatch
    initial, poses = starts(Config(n=11), 32, 800, cuda_device)
    programs = _mixed_programs(64, 7)
    slots = np.tile(np.arange(32), 64)
    pids = np.repeat(np.arange(64), 32).astype(np.int32)
    ids = np.arange(800, 832, dtype=np.uint64)[slots]
    spec = Campaign(name="Load", n=11, batch_capacity=256, publication={"enabled": False})
    stream = StreamingBatch(spec, programs, poses[slots], initial[slots], ids, np.zeros(len(ids), dtype=np.uint64), pids)
    while not stream.advance():
        pass
    # 2048 episodes in 256 slots: slots stay occupied until the queue runs out; one plain batch idles most of the time.
    whole = Campaign.model_validate({**spec.document(), "batch_capacity": len(ids)})
    plain = StreamingBatch(whole, programs, poses[slots], initial[slots], ids, np.zeros(len(ids), dtype=np.uint64), pids)
    while not plain.advance():
        pass
    print(f"slot occupancy: streaming {stream.occupancy():.0%}, one batch {plain.occupancy():.0%}")
    assert stream.occupancy() > 2 * plain.occupancy()
