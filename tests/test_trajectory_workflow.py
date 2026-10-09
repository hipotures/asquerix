"""Replay selection, honest comparisons, bounded exports and CLI integration."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import sys

import numpy as np
import pytest

from asquerix import cli, runner, trajectory
from asquerix.gpu import Config
from asquerix.persistence import read_json, write_json
from asquerix.trajectory_format import load_trajectory


def arrays(frames=2):
    return dict(poses=np.zeros((frames, 1, 3), dtype="<f4"), side=np.full(frames, 4, dtype="<f4"),
                sequence=np.arange(frames, dtype="<i8"), attempt=np.zeros(frames, dtype="<i4"),
                sweep=np.zeros(frames, dtype="<i4"), sweep_total=np.zeros(frames, dtype="<i4"),
                phase=np.array([0] + [6] * (frames - 1), dtype="u1"),
                roles=np.array([1] + [2] * (frames - 1), dtype="u1"), square_ids=np.array([0], dtype="<i4"))


def fake_replay(config, trial_id, **options):
    scalar = np.zeros(1, dtype=[(key, "<f4" if key in {"side", "min_gap", "min_wall", "max_penetration", "final_step"} else "<i4")
                               for key in ("side", "min_gap", "min_wall", "max_penetration", "termination", "feasible", "attempts", "sweeps", "accepted", "rejected", "proposals", "final_step")])
    scalar["side"] = 4
    scalar["min_gap"] = 1e20
    scalar["min_wall"] = 1.5
    scalar["final_step"] = np.float32(config.step)
    scalar["feasible"] = 1
    scalar["proposals"] = 1
    return dict(arrays=arrays(), scalars=scalar, device=dict(uuid="test-uuid", name="Test GPU", selector="cuda:0"),
                sampling=dict(observed=2, retained=2, suppressed=0, effective_stride=1, max_frames=options["max_frames"]),
                timings=dict(device_seconds=0.001, transfer_seconds=0.002, module_load_seconds=0.003))


def reference(tmp_path, *, plain=False):
    directory = tmp_path / "original"
    (directory / "poses").mkdir(parents=True)
    config = Config(n=1, seed=2**64 - 2, max_attempts=0)
    docs = []
    for trial_id in (2**64 - 3, 2**64 - 2):
        replay = fake_replay(config, trial_id, max_frames=256)
        document = runner.scalar_records(replay["scalars"], config, trial_id)[0]
        document.update(poses=[[0.0, 0.0, 0.0]], pose_dtype="float32", validation_status="NUMERICALLY_VALIDATED")
        docs.append(document)
        write_json(directory / "poses" / f"trial-{trial_id}.json", document)
    data = {"config": dict(solver=asdict(config), runner={}), "environment": dict(numerical_precision="float32"),
            "summary": dict(metadata=dict(leaderboard=[docs[1], docs[0], docs[0], {**docs[0], "trial_id": 1, "validation_status": "NOT_CHECKED"}]))}
    for name, value in data.items():
        if plain:
            (directory / f"{name}.json").write_text(json.dumps(value))
        else:
            write_json(directory / f"{name}.json", value)
    return directory, config, docs


def test_selection_is_global_validated_deduplicated_and_id_based(tmp_path):
    directory, _, docs = reference(tmp_path)
    assert [row[0] for row in trajectory.select_references(directory, best=3)] == [d["trial_id"] for d in docs]
    assert trajectory.select_references(directory, best=0) == []
    with pytest.raises(ValueError, match="REFERENCE_INCOMPLETE"):
        trajectory.select_references(directory, trial_ids=[4372])
    with pytest.raises(ValueError, match="exclusively"):
        trajectory.select_references(directory, trial_ids=[1], best=3)
    with pytest.raises(ValueError, match="16"):
        trajectory.select_references(directory, best=17)


def test_comparison_distinguishes_signed_zero_missing_dtype_and_mismatch(tmp_path):
    _, config, docs = reference(tmp_path)
    replay = fake_replay(config, docs[0]["trial_id"], max_frames=256)
    actual = runner.scalar_records(replay["scalars"], config, docs[0]["trial_id"])[0]
    assert trajectory.compare_reference(docs[0], actual, replay["arrays"], {})["status"] == "REPLAY_MATCHED"
    docs[0]["poses"][0][0] = -0.0
    outcome = trajectory.compare_reference(docs[0], actual, replay["arrays"], {})
    assert outcome["status"] == "REPLAY_MISMATCH" and "poses" in outcome["mismatches"]
    docs[0].pop("pose_dtype")
    assert trajectory.compare_reference(docs[0], actual, replay["arrays"], {})["status"] == "REFERENCE_INCOMPLETE"
    docs[0]["pose_dtype"] = "float32"
    docs[0]["side"] = 4.1
    assert "side: not a lossless FP32 value" in trajectory.compare_reference(docs[0], actual, replay["arrays"], {})["missing_fields"]


@pytest.mark.parametrize("plain", [False, True])
def test_companion_export_preserves_input_and_lossless_values(tmp_path, monkeypatch, plain):
    directory, _, docs = reference(tmp_path, plain=plain)
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob("*") if p.is_file()}
    monkeypatch.setattr(runner, "environment", lambda: dict(numerical_precision="float32"))
    output = tmp_path / "companion"
    result = trajectory.record(directory, output=output, best=3, replay_function=fake_replay)
    assert result["completed_count"] == 2 and result["requested_count"] == 3
    assert all(row["status"] == "REPLAY_MATCHED" for row in result["outcomes"])
    assert sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) < 10 * 1024**2
    numeric, meta = load_trajectory(output / "trajectories" / f"trial-{docs[0]['trial_id']}.npz")
    assert numeric["poses"].tobytes() == arrays()["poses"].tobytes()
    assert meta["trial_id"] == str(docs[0]["trial_id"])
    assert meta["comparison"]["initial_compared"] is False
    assert len(meta["validations"]) == 2
    assert before == {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob("*") if p.is_file()}


def test_actual_size_cap_discards_only_pending_export(tmp_path, monkeypatch):
    from asquerix import trajectory_viewer
    directory, _, _ = reference(tmp_path)
    monkeypatch.setattr(runner, "environment", lambda: {})
    monkeypatch.setattr(trajectory_viewer, "render_html", lambda *a: b"x" * 200000)
    output = tmp_path / "limited"
    result = trajectory.record(directory, output=output, best=2, max_mib=0.1, replay_function=fake_replay)
    assert result["status"] == "EXPORT_LIMIT" and result["completed_count"] == 0
    assert list((output / "trajectories").iterdir()) == []
    assert sum(p.stat().st_size for p in output.rglob("*") if p.is_file()) <= int(0.1 * 1024**2)


@pytest.mark.parametrize("failed_write", [2, 3])
def test_partial_trial_group_is_removed_without_losing_prior_exports(tmp_path, monkeypatch, failed_write):
    from asquerix import trajectory_format
    directory, _, docs = reference(tmp_path)
    monkeypatch.setattr(runner, "environment", lambda: {})
    actual = trajectory_format.write_bytes
    output = tmp_path / "failed-copy"
    count = 0
    def write(path, payload):
        nonlocal count
        if Path(path).is_relative_to(output):
            count += 1
            if count == 3 + failed_write:
                raise OSError("injected export write failure")
        return actual(path, payload)
    monkeypatch.setattr(trajectory_format, "write_bytes", write)
    result = trajectory.record(directory, output=output, best=2, replay_function=fake_replay)
    assert result["status"] == "REPLAY_ERROR" and result["completed_count"] == 1
    assert len(list((output / "trajectories").iterdir())) == 3
    assert all(str(docs[0]["trial_id"]) in p.name for p in (output / "trajectories").iterdir())


def test_device_provenance_populates_driver_for_selected_uuid():
    env = dict(device_uuid="uuid-b", gpu_query=dict(stdout="name, uuid, driver\nA, uuid-a, 1\nB, uuid-b, 2\n"))
    actual = trajectory._device_provenance(env)
    assert actual["driver_version"] == "2" and actual["device_name"] == "B"


def test_stop_drains_one_replay_and_schedules_no_more(tmp_path, monkeypatch):
    directory, _, _ = reference(tmp_path)
    monkeypatch.setattr(runner, "environment", lambda: {})
    calls = []
    def replay(*args, **kwargs):
        calls.append(args[1])
        signal.raise_signal(signal.SIGINT)
        return fake_replay(*args, **kwargs)
    result = trajectory.record(directory, output=tmp_path / "stopped", best=2, replay_function=replay)
    assert len(calls) == 1 and result["completed_count"] == 1 and result["status"] == "INTERRUPTED"


def test_solver_overrides_and_output_inside_original_are_rejected(tmp_path):
    directory, _, _ = reference(tmp_path)
    with pytest.raises(ValueError, match="outside"):
        trajectory.record(directory, output=directory / "new", best=1)
    config = read_json(directory / "config.json")
    config["solver"].pop("guard")
    write_json(directory / "config.json", config)
    with pytest.raises(ValueError, match="no defaults"):
        trajectory.record(directory, output=tmp_path / "new", best=1)
    assert not (tmp_path / "new").exists()


def test_offline_render_does_not_initialize_cuda_or_use_rich(tmp_path, monkeypatch):
    directory, _, docs = reference(tmp_path)
    monkeypatch.setattr(runner, "environment", lambda: {})
    trajectory.record(directory, output=tmp_path / "trace", best=1, replay_function=fake_replay)
    path = tmp_path / "trace" / "trajectories" / f"trial-{docs[0]['trial_id']}.npz"
    code = "import warp as wp; wp.init=lambda: (_ for _ in ()).throw(AssertionError('CUDA context requested')); from asquerix.cli import main; import sys; rc=main(sys.argv[1:]); assert 'rich' not in sys.modules; raise SystemExit(rc)"
    result = subprocess.run([sys.executable, "-c", code, "trace-render", str(path), "--json", "--output", str(tmp_path / "offline.html")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "HTML:" in result.stdout and '"poses"' not in result.stdout


def test_default_cli_does_not_schedule_traces(tmp_path, monkeypatch):
    from asquerix import publication
    from test_runner import _factory
    actual = runner.run
    monkeypatch.setattr(runner, "environment", lambda: {})
    monkeypatch.setattr(runner, "run", lambda config, **options: actual(config, **options, batch_factory=_factory()))
    monkeypatch.setattr(trajectory, "record", lambda *a, **k: pytest.fail("default trace allocated/scheduled"))
    monkeypatch.setattr(publication, "publish", lambda *a, **k: dict(status="LOCAL_ONLY", seconds=0))
    assert cli.main(["run", "--n", "1", "--max-attempts", "0", "--trials", "1", "--json", "--no-push", "--output", str(tmp_path / "ordinary")]) == 0
    assert not (tmp_path / "ordinary" / "trajectories").exists()


def test_provenance_and_result_equality_are_independent():
    assert trajectory.provenance({"source_revision": "old"}, {"source_revision": "new"})["status"] == "PROVENANCE_DIFFERENT"
    assert trajectory.provenance({}, {})["status"] == "PROVENANCE_INCOMPLETE"


def test_final_cli_receipt_keeps_the_publication_byte_reserve(tmp_path):
    from asquerix.publication import save_receipt, TRACE_RECEIPT_RESERVE_BYTES
    write_json(tmp_path / "trace.json", {"schema": trajectory.OPERATION_SCHEMA})
    noise = np.random.default_rng(12).bytes(100000).hex()
    path = save_receipt(tmp_path, dict(status="PUSH_FAILED", error=noise, total_end_to_end_seconds=1))
    assert path.stat().st_size <= TRACE_RECEIPT_RESERVE_BYTES
    assert read_json(path)["receipt_truncated"] is True
