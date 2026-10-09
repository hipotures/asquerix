"""CUDA checks for the bounded, isolated trajectory replay kernel."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

wp = pytest.importorskip("warp", reason="Warp is required for CUDA trajectory tests")

from asquerix.gpu import Batch, Config, Result, parameters, simulate
from asquerix.trace_gpu import (
    MODE_ACCEPTED,
    MODE_SWEEPS,
    PHASE_FINAL,
    PHASE_INITIAL,
    PHASE_REJECTED,
    PHASE_ROLLBACK,
    PHASE_RELAXING,
    PHASE_TRIAL,
    ROLE_FINAL,
    ROLE_INITIAL,
    replay,
    trace_finalize,
    trace_simulate,
)


pytestmark = pytest.mark.gpu


def _assert_result_bytes_equal(actual: np.ndarray, expected: np.ndarray) -> None:
    assert actual.dtype == expected.dtype
    assert actual.shape == expected.shape
    for field in actual.dtype.names or ():
        assert actual[field].tobytes() == expected[field].tobytes(), field


def _assert_array_bytes_equal(actual: np.ndarray, expected: np.ndarray) -> None:
    assert actual.dtype == expected.dtype
    assert actual.shape == expected.shape
    assert actual.tobytes() == expected.tobytes()


def _device_name(cuda_device) -> str:
    return str(getattr(cuda_device, "alias", None) or "cuda:0")


def _production(config: Config, trial_id: int, cuda_device):
    batch = Batch(config, capacity=1, device=_device_name(cuda_device))
    results, _timing = batch.run(1, offset=trial_id)
    poses, _transfer = batch.get_poses([0])
    return results, poses


@pytest.mark.parametrize("every", (0, 2**31))
def test_sweep_interval_is_bounded_before_cuda_setup(every: int) -> None:
    config = Config(n=1, max_attempts=0)
    with pytest.raises(ValueError, match="every"):
        replay(config, 0, device="cpu", mode=MODE_SWEEPS, every=every)


def test_accepted_replay_matches_production_result_and_endpoint(cuda_device) -> None:
    config = Config(n=4, seed=12345, max_attempts=5, max_sweeps=2)
    trial_id = 2**64 - 17
    production_result, production_pose = _production(config, trial_id, cuda_device)
    trace = replay(
        config,
        trial_id,
        device=_device_name(cuda_device),
        mode=MODE_ACCEPTED,
        max_frames=256,
    )

    arrays = trace["arrays"]
    _assert_result_bytes_equal(trace["scalars"], production_result)
    _assert_array_bytes_equal(arrays["poses"][-1], production_pose[0])
    assert arrays["poses"].dtype == np.float32
    assert arrays["poses"].shape[1:] == (config.n, 3)
    assert arrays["roles"][0] & ROLE_INITIAL
    assert arrays["roles"][-1] & ROLE_FINAL
    assert arrays["phase"][0] == PHASE_INITIAL
    assert arrays["phase"][-1] == PHASE_FINAL
    assert np.all(np.diff(arrays["sequence"]) > 0)
    assert trace["sampling"]["retained"] <= 256
    assert trace["device"]["uuid"] == cuda_device.uuid


def test_sweep_replay_preserves_proposal_before_rollback(cuda_device) -> None:
    config = Config(
        n=4,
        seed=987654321,
        step=20.0,
        max_attempts=1,
        max_sweeps=1,
    )
    trace = replay(
        config,
        17,
        device=_device_name(cuda_device),
        mode=MODE_SWEEPS,
        every=1,
        max_frames=32,
    )

    arrays = trace["arrays"]
    phases = arrays["phase"].tolist()
    assert phases[0] == PHASE_INITIAL
    assert PHASE_TRIAL in phases
    assert PHASE_RELAXING in phases
    assert PHASE_REJECTED in phases
    assert PHASE_ROLLBACK in phases
    assert arrays["roles"][-1] & ROLE_FINAL
    rejected = phases.index(PHASE_REJECTED)
    rollback = phases.index(PHASE_ROLLBACK)
    assert rejected < rollback
    assert arrays["side"][rejected] < arrays["side"][rollback]
    _assert_array_bytes_equal(arrays["poses"][rollback], arrays["poses"][0])


def test_frame_cap_is_device_bounded_and_endpoint_preserving(cuda_device) -> None:
    config = Config(n=1, seed=55, max_attempts=32, max_sweeps=1)
    trace = replay(
        config,
        4,
        device=_device_name(cuda_device),
        mode=MODE_ACCEPTED,
        max_frames=2,
    )

    arrays = trace["arrays"]
    assert 1 <= len(arrays["poses"]) <= 2
    assert arrays["roles"][0] & ROLE_INITIAL
    assert arrays["roles"][-1] & ROLE_FINAL
    assert trace["sampling"]["max_frames"] == 2
    assert trace["sampling"]["suppressed"] >= 0
    assert trace["sampling"]["effective_stride"] >= 1


def test_sweep_cap_two_marks_reused_accepted_endpoint_final(cuda_device) -> None:
    config = Config(n=1, seed=55, step=0.1, max_attempts=1, max_sweeps=1)
    production_result, production_pose = _production(config, 4, cuda_device)
    trace = replay(config, 4, device=_device_name(cuda_device), mode=MODE_SWEEPS,
                   every=1, max_frames=2)

    arrays = trace["arrays"]
    assert int(production_result[0]["accepted"]) == 1
    assert arrays["phase"][-1] == PHASE_FINAL
    assert arrays["roles"][-1] & ROLE_FINAL
    _assert_array_bytes_equal(arrays["poses"][-1], production_pose[0])


def test_initialization_failure_has_no_unwritten_frames(cuda_device) -> None:
    config = Config(n=2, initial_side=1.5, seed=123, max_attempts=0, proposals_per_square=1)
    trace = replay(config, 0, device=_device_name(cuda_device), max_frames=8)

    arrays = trace["arrays"]
    assert int(trace["scalars"][0]["termination"]) == 3
    assert arrays["poses"].shape == (0, config.n, 3)
    assert arrays["side"].size == 0
    assert trace["sampling"]["retained"] == 0


@pytest.mark.parametrize("n", (1, 4, 11, 12, 16, 32))
def test_initial_rng_and_zero_attempt_endpoint_for_supported_n(n: int, cuda_device) -> None:
    config = Config(n=n, seed=2**64 - 123, max_attempts=0)
    production_result, production_pose = _production(config, 2**64 - 8, cuda_device)
    trace = replay(config, 2**64 - 8, device=_device_name(cuda_device), max_frames=8)

    arrays = trace["arrays"]
    _assert_result_bytes_equal(trace["scalars"], production_result)
    if int(production_result[0]["termination"]) == 3:
        assert arrays["poses"].shape == (0, n, 3)
        return
    _assert_array_bytes_equal(arrays["poses"][0], production_pose[0])
    assert len(arrays["poses"]) == 1
    assert arrays["roles"][0] == (ROLE_INITIAL | ROLE_FINAL)


@pytest.mark.parametrize("n", (1, 4, 11, 12, 16, 32))
@pytest.mark.parametrize("seed", (20261008, 987654321))
def test_bounded_nonzero_replay_matches_production_for_supported_n(
    n: int, seed: int, cuda_device
) -> None:
    config = Config(n=n, initial_side=15.0, seed=seed, max_attempts=2, max_sweeps=1)
    production_result, production_pose = _production(config, 4096, cuda_device)
    trace = replay(config, 4096, device=_device_name(cuda_device), max_frames=8)

    _assert_result_bytes_equal(trace["scalars"], production_result)
    assert int(production_result[0]["termination"]) != 3
    assert trace["arrays"]["poses"].shape[1:] == (n, 3)
    assert trace["arrays"]["square_ids"].dtype == np.dtype("<i4")
    _assert_array_bytes_equal(trace["arrays"]["poses"][0], production_pose[0])
    _assert_array_bytes_equal(trace["arrays"]["poses"][-1], production_pose[0])
    assert trace["sampling"]["retained"] <= 8


def test_repeated_compaction_keeps_temporal_coverage_and_exact_result(cuda_device) -> None:
    config = Config(n=1, seed=55, max_attempts=128, max_sweeps=8)
    full = replay(config, 4, device=_device_name(cuda_device), max_frames=256)
    compact = replay(config, 4, device=_device_name(cuda_device), max_frames=8)

    _assert_result_bytes_equal(compact["scalars"], full["scalars"])
    compact_arrays = compact["arrays"]
    full_arrays = full["arrays"]
    assert len(compact_arrays["poses"]) <= 8
    assert compact_arrays["roles"][0] & ROLE_INITIAL
    assert compact_arrays["roles"][-1] & ROLE_FINAL
    assert np.all(np.diff(compact_arrays["sequence"]) > 0)
    assert compact_arrays["sequence"][0] == full_arrays["sequence"][0]
    assert compact_arrays["sequence"][-1] >= full_arrays["sequence"][-1]
    span = int(full_arrays["sequence"][-1] - full_arrays["sequence"][0])
    middle = compact_arrays["sequence"][1:-1]
    assert np.any((middle > full_arrays["sequence"][0] + span // 4)
                  & (middle < full_arrays["sequence"][0] + (3 * span) // 4))
    assert compact["sampling"]["observed"] >= compact["sampling"]["retained"]
    assert compact["sampling"]["suppressed"] > 0
    assert compact["sampling"]["effective_stride"] > 1


def test_recording_cap_does_not_change_final_outcome(cuda_device) -> None:
    config = Config(n=4, seed=20261008, max_attempts=16, max_sweeps=2)
    small = replay(config, 7, device=_device_name(cuda_device), max_frames=2)
    large = replay(config, 7, device=_device_name(cuda_device), max_frames=256)

    _assert_result_bytes_equal(small["scalars"], large["scalars"])
    assert len(small["arrays"]["poses"]) <= 2
    assert small["arrays"]["roles"][0] & ROLE_INITIAL
    assert small["arrays"]["roles"][-1] & ROLE_FINAL


def test_resumed_numerical_failure_preserves_nan_diagnostic_frames(cuda_device) -> None:
    """A test-only resumed launch keeps NaNs visible and matches production counters."""

    device_name = _device_name(cuda_device)
    initial_config = Config(n=1, seed=77, max_attempts=0, max_sweeps=1)
    resumed_config = Config(n=1, seed=77, max_attempts=1, max_sweeps=1)
    params_initial = parameters(initial_config)
    params_resumed = parameters(resumed_config)
    nan_pose = wp.array(np.asarray(((np.nan, np.nan, np.nan),), dtype=np.float32),
                        dtype=wp.vec3, device="cpu")

    production_pose = wp.empty((1, 1), dtype=wp.vec3, device=device_name)
    production_work = wp.empty_like(production_pose)
    production_results = wp.empty(1, dtype=Result, device=device_name)
    production_trace = wp.zeros((1, 1), dtype=float, device=device_name)
    wp.launch(simulate, dim=1, inputs=[params_initial, wp.uint64(9), production_pose,
                                       production_work, production_results, production_trace,
                                       0, 0, 16], device=device_name, block_dim=32)
    wp.copy(production_pose, nan_pose)
    wp.launch(simulate, dim=1, inputs=[params_resumed, wp.uint64(9), production_pose,
                                       production_work, production_results, production_trace,
                                       0, 1, 16], device=device_name, block_dim=32)

    frame_capacity = 16
    trace_pose = wp.empty((1, 1), dtype=wp.vec3, device=device_name)
    trace_work = wp.empty_like(trace_pose)
    trace_results = wp.empty(1, dtype=Result, device=device_name)
    frame_count = wp.zeros(1, dtype=int, device=device_name)
    event_count = wp.zeros(1, dtype=wp.int64, device=device_name)
    suppressed_count = wp.zeros(1, dtype=wp.int64, device=device_name)
    compaction_count = wp.zeros(1, dtype=int, device=device_name)
    effective_stride = wp.ones(1, dtype=wp.int64, device=device_name)
    sequence_counter = wp.zeros(1, dtype=wp.int64, device=device_name)
    last_attempt = wp.full(1, -1, dtype=int, device=device_name)
    last_sweep = wp.full(1, -1, dtype=int, device=device_name)
    trace_poses = wp.empty((1, frame_capacity), dtype=wp.vec3, device=device_name)
    trace_side = wp.empty(frame_capacity, dtype=float, device=device_name)
    trace_sequence = wp.empty(frame_capacity, dtype=wp.int64, device=device_name)
    trace_attempt = wp.empty(frame_capacity, dtype=int, device=device_name)
    trace_sweep = wp.empty(frame_capacity, dtype=int, device=device_name)
    trace_sweep_total = wp.empty(frame_capacity, dtype=int, device=device_name)
    trace_phase = wp.empty(frame_capacity, dtype=wp.uint8, device=device_name)
    trace_roles = wp.empty(frame_capacity, dtype=wp.uint8, device=device_name)
    wp.load_module(module="asquerix.trace_gpu", device=device_name, block_dim=32)
    trace_inputs = [params_initial, wp.uint64(9), trace_pose, trace_work, trace_results, 1, 1,
                    frame_capacity, frame_count, event_count, suppressed_count, compaction_count,
                    effective_stride, sequence_counter, last_attempt, last_sweep, trace_poses,
                    trace_side, trace_sequence, trace_attempt, trace_sweep, trace_sweep_total,
                    trace_phase, trace_roles]
    wp.launch(trace_simulate, dim=1, inputs=trace_inputs + [0, 16], device=device_name, block_dim=32)
    wp.copy(trace_pose, nan_pose)
    trace_inputs[0] = params_resumed
    wp.launch(trace_simulate, dim=1, inputs=trace_inputs + [1, 16], device=device_name, block_dim=32)
    finalize_inputs = [params_resumed, trace_pose, trace_results, frame_count, sequence_counter,
                       last_attempt, last_sweep, frame_capacity, event_count, suppressed_count,
                       compaction_count, effective_stride, trace_poses, trace_side, trace_sequence,
                       trace_attempt, trace_sweep, trace_sweep_total, trace_phase, trace_roles]
    wp.launch(trace_finalize, dim=1, inputs=finalize_inputs, device=device_name, block_dim=32)
    wp.synchronize_device(device_name)

    production_result = production_results.numpy().copy()
    trace_result = trace_results.numpy().copy()
    _assert_result_bytes_equal(trace_result, production_result)
    assert int(trace_result[0]["termination"]) == 4
    assert int(trace_result[0]["attempts"]) == 1
    assert int(trace_result[0]["rejected"]) == 1
    assert int(trace_result[0]["sweeps"]) == 1
    assert np.isnan(production_pose.numpy()).all()
    count = int(frame_count.numpy()[0])
    recorded = trace_poses.numpy()[:, :count, :].transpose(1, 0, 2)
    assert count >= 2
    assert np.isfinite(recorded[0]).all()
    assert np.isnan(recorded[1:]).all()
    assert int(trace_roles.numpy()[count - 1]) & ROLE_FINAL


@pytest.mark.parametrize("trial_id", (4124, 4372))
def test_historical_n11_diagnostics_match_frozen_cuda_reference(trial_id: int, cuda_device) -> None:
    reference = (
        Path(__file__).parents[1]
        / "artifacts"
        / "performance"
        / "cuda-20261009"
        / "corpus"
        / f"n11-seed20261008-id{trial_id}.npz"
    )
    if not reference.exists():
        pytest.skip("frozen trajectory baseline corpus is unavailable")
    expected = np.load(reference, allow_pickle=False)
    config = Config(n=11, seed=20261008, max_sweeps=480)
    trace = replay(config, trial_id, device=_device_name(cuda_device), max_frames=256)

    _assert_result_bytes_equal(trace["scalars"], expected["results"])
    _assert_array_bytes_equal(trace["arrays"]["poses"][0], expected["initial_poses"][0])
    _assert_array_bytes_equal(trace["arrays"]["poses"][-1], expected["poses"][0])
