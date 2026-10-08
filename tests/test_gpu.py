"""Bounded CUDA correctness tests for the one-world-per-thread baseline."""

from __future__ import annotations

import numpy as np
import pytest

wp = pytest.importorskip("warp", reason="Warp is required for CUDA correctness tests")

from asquerix.geometry import validate_pose
from asquerix.gpu import (
    TERMINATIONS,
    Batch,
    Config,
    contact_diagnostic,
    parameters,
)


pytestmark = pytest.mark.gpu


def _batch(config: Config, capacity: int, cuda_device, *, debug: bool = False) -> Batch:
    return Batch(config, capacity=capacity, device=cuda_device, debug=debug)


def _diagnostic(
    cuda_device,
    config: Config,
    p_values: np.ndarray,
    q_values: np.ndarray,
    side: float,
    *,
    wall_mode: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run the device contact diagnostic and read back one compact result."""

    p_host = np.asarray(p_values, dtype=np.float32).reshape(-1, 3)
    q_host = np.asarray(q_values, dtype=np.float32).reshape(-1, 3)
    if p_host.shape != q_host.shape:
        raise ValueError("diagnostic p and q arrays must have the same shape")
    p = wp.array(p_host, dtype=wp.vec3, device=cuda_device)
    q = wp.array(q_host, dtype=wp.vec3, device=cuda_device)
    values = wp.zeros((len(p_host), 7), dtype=float, device=cuda_device)
    wp.launch(
        contact_diagnostic,
        dim=len(p_host),
        inputs=[p, q, parameters(config), float(side), int(wall_mode), values],
        device=cuda_device,
    )
    wp.synchronize_device(cuda_device)
    return p.numpy().copy(), q.numpy().copy(), values.numpy().copy()


@pytest.mark.parametrize("n", (1, 11, 12, 16, 32), ids=("n1", "n11", "n12", "n16", "n32"))
def test_initializer_audit_supports_required_n_values(n: int, cuda_device) -> None:
    """The conservative initializer succeeds at a loose side for each supported n."""

    config = Config(n=n, initial_side=10.0, seed=20261008, max_attempts=0)
    batch = _batch(config, capacity=1, cuda_device=cuda_device)
    results, _timing = batch.run(1, offset=0)

    result = results[0]
    assert int(result["termination"]) in TERMINATIONS
    assert int(result["termination"]) != 3
    assert int(result["attempts"]) == 0
    assert int(result["sweeps"]) == 0
    assert float(result["side"]) == pytest.approx(10.0)
    assert int(result["feasible"]) == 1

    poses, _ = batch.get_poses([0])
    validation = validate_pose(poses[0], float(result["side"]))
    assert validation["status"] in {"NUMERICALLY_VALIDATED", "INDETERMINATE"}
    assert validation["nonfinite"] is False
    assert float(validation["max_penetration"]) <= 1e-7


def test_global_uint64_ids_are_reproducible_distinct_and_partition_invariant(cuda_device) -> None:
    """Trial identifiers remain global across high-ID and partitioned launches."""

    config = Config(n=4, initial_side=10.0, seed=2**64 - 123, max_attempts=0)
    offset = 2**64 - 8

    repeated_batch = _batch(config, capacity=8, cuda_device=cuda_device)
    first_results, _ = repeated_batch.run(8, offset=offset)
    first_poses, _ = repeated_batch.get_poses(np.arange(8, dtype=np.int32))
    second_results, _ = repeated_batch.run(8, offset=offset)
    second_poses, _ = repeated_batch.get_poses(np.arange(8, dtype=np.int32))

    np.testing.assert_array_equal(first_results, second_results)
    np.testing.assert_array_equal(first_poses, second_poses)
    assert len(np.unique(first_poses.reshape(8, -1), axis=0)) == 8

    full_batch = _batch(config, capacity=8, cuda_device=cuda_device)
    full_results, _ = full_batch.run(8, offset=offset)
    full_poses, _ = full_batch.get_poses(np.arange(8, dtype=np.int32))

    partition_batch = _batch(config, capacity=4, cuda_device=cuda_device)
    first_partition_results, _ = partition_batch.run(4, offset=offset)
    first_partition_poses, _ = partition_batch.get_poses(np.arange(4, dtype=np.int32))
    second_partition_results, _ = partition_batch.run(4, offset=offset + 4)
    second_partition_poses, _ = partition_batch.get_poses(np.arange(4, dtype=np.int32))

    partition_results = np.concatenate((first_partition_results, second_partition_results))
    partition_poses = np.concatenate((first_partition_poses, second_partition_poses))
    np.testing.assert_array_equal(full_results, partition_results)
    np.testing.assert_array_equal(full_poses, partition_poses)


def test_off_center_wall_and_pair_contacts_translate_and_rotate(cuda_device) -> None:
    """Asymmetric contacts produce both translational and angular response."""

    config = Config(n=1, initial_side=10.0, max_attempts=1)
    wall_initial = np.asarray(((0.1, 0.23, 0.3),), dtype=np.float32)
    wall_p, _wall_q, _wall_values = _diagnostic(
        cuda_device,
        config,
        wall_initial,
        np.zeros_like(wall_initial),
        side=1.0,
        wall_mode=1,
    )
    assert np.isfinite(wall_p).all()
    assert abs(float(wall_p[0, 0] - wall_initial[0, 0])) > 1e-5
    assert abs(float(wall_p[0, 2] - wall_initial[0, 2])) > 1e-5
    assert float(wall_p[0, 1]) == pytest.approx(float(wall_initial[0, 1]), abs=1e-7)

    pair_p_initial = np.asarray(((0.0, 0.0, 0.3),), dtype=np.float32)
    pair_q_initial = np.asarray(((0.7, 0.2, -0.2),), dtype=np.float32)
    pair_p, pair_q, values = _diagnostic(
        cuda_device,
        config,
        pair_p_initial,
        pair_q_initial,
        side=10.0,
    )
    assert np.isfinite(pair_p).all() and np.isfinite(pair_q).all()
    assert np.isfinite(values).all()
    assert float(values[0, 0]) < 0.0
    assert np.linalg.norm(pair_p[0, :2] - pair_p_initial[0, :2]) > 1e-5
    assert np.linalg.norm(pair_q[0, :2] - pair_q_initial[0, :2]) > 1e-5
    assert max(
        abs(float(pair_p[0, 2] - pair_p_initial[0, 2])),
        abs(float(pair_q[0, 2] - pair_q_initial[0, 2])),
    ) > 1e-5


def test_aligned_symmetric_contacts_have_zero_torque(cuda_device) -> None:
    """Symmetric aligned contacts still translate but do not invent torque."""

    config = Config(n=1, initial_side=10.0, max_attempts=1)
    wall_initial = np.asarray(((0.0, 0.0, 0.0),), dtype=np.float32)
    wall_p, _wall_q, _wall_values = _diagnostic(
        cuda_device,
        config,
        wall_initial,
        np.zeros_like(wall_initial),
        side=1.0,
        wall_mode=1,
    )
    assert abs(float(wall_p[0, 0] - wall_initial[0, 0])) > 1e-5
    assert float(wall_p[0, 1]) == pytest.approx(0.0, abs=1e-7)
    assert float(wall_p[0, 2]) == pytest.approx(0.0, abs=1e-7)

    pair_p_initial = np.asarray(((0.0, 0.0, 0.0),), dtype=np.float32)
    pair_q_initial = np.asarray(((0.7, 0.0, 0.0),), dtype=np.float32)
    pair_p, pair_q, values = _diagnostic(
        cuda_device,
        config,
        pair_p_initial,
        pair_q_initial,
        side=10.0,
    )
    assert np.isfinite(values).all()
    assert abs(float(pair_p[0, 0] - pair_p_initial[0, 0])) > 1e-5
    assert abs(float(pair_q[0, 0] - pair_q_initial[0, 0])) > 1e-5
    assert float(pair_p[0, 2]) == pytest.approx(0.0, abs=1e-7)
    assert float(pair_q[0, 2]) == pytest.approx(0.0, abs=1e-7)


def test_coincident_pair_contact_stays_finite(cuda_device) -> None:
    config = Config(n=1, initial_side=10.0, max_attempts=1)
    coincident = np.asarray(((0.0, 0.0, 0.31),), dtype=np.float32)
    other_orientation = np.asarray(((0.0, 0.0, -0.27),), dtype=np.float32)

    p, q, values = _diagnostic(cuda_device, config, coincident, other_orientation, side=10.0)

    assert np.isfinite(p).all()
    assert np.isfinite(q).all()
    assert np.isfinite(values).all()
    assert float(values[0, 0]) < 0.0


@pytest.mark.parametrize(
    ("p_values", "q_values"),
    (
        ((0.0, 0.0, 0.3), (0.7, 0.2, -0.2)),
        # Here the strongest separating-axis candidate is q's edge axis;
        # this exercises the opposite orientation branch of the derivative.
        ((0.0, 0.0, 0.0), (0.4, 0.3, 0.2)),
    ),
    ids=("p_axis", "q_axis"),
)
def test_sat_gradient_matches_finite_difference(
    cuda_device, p_values: tuple[float, float, float], q_values: tuple[float, float, float]
) -> None:
    """The diagnostic's analytic gradient agrees away from axis ties."""

    config = Config(n=1, initial_side=10.0, max_attempts=1)
    p0 = np.asarray(p_values, dtype=np.float32)
    q0 = np.asarray(q_values, dtype=np.float32)
    _p, _q, base_values = _diagnostic(
        cuda_device,
        config,
        p0[None, :],
        q0[None, :],
        side=10.0,
    )
    values = base_values[0]
    assert np.isfinite(values).all()
    assert values[0] < -0.1
    np.testing.assert_allclose(values[1], -values[4], atol=1e-6)
    np.testing.assert_allclose(values[2], -values[5], atol=1e-6)

    def gap_at(p: np.ndarray, q: np.ndarray) -> float:
        _p, _q, diagnostic_values = _diagnostic(
            cuda_device,
            config,
            p[None, :],
            q[None, :],
            side=10.0,
        )
        return float(diagnostic_values[0, 0])

    epsilon = 1e-3
    finite_difference = []
    for index in range(6):
        p_plus, p_minus = p0.copy(), p0.copy()
        q_plus, q_minus = q0.copy(), q0.copy()
        if index < 3:
            p_plus[index] += epsilon
            p_minus[index] -= epsilon
        else:
            q_plus[index - 3] += epsilon
            q_minus[index - 3] -= epsilon
        finite_difference.append((gap_at(p_plus, q_plus) - gap_at(p_minus, q_minus)) / (2.0 * epsilon))

    # The diagnostic columns are exactly [gap, -nx, -ny, gp, nx, ny, gq],
    # which maps to [p_x, p_y, p_theta, q_x, q_y, q_theta].
    analytic = np.asarray(values[1:7])
    np.testing.assert_allclose(finite_difference, analytic, rtol=2e-2, atol=2e-3)


def test_rejected_impossible_step_restores_every_pose_component(cuda_device) -> None:
    """A rejected proposal leaves the accepted pose bitwise equal to initialization."""

    seed = 987654321
    offset = 17
    initial_config = Config(n=4, initial_side=10.0, seed=seed, max_attempts=0)
    initial_batch = _batch(initial_config, capacity=1, cuda_device=cuda_device)
    initial_results, _ = initial_batch.run(1, offset=offset)
    initial_poses, _ = initial_batch.get_poses([0])

    impossible_config = Config(
        n=4,
        initial_side=10.0,
        seed=seed,
        step=20.0,
        max_attempts=1,
        max_sweeps=1,
    )
    impossible_batch = _batch(impossible_config, capacity=1, cuda_device=cuda_device)
    results, _ = impossible_batch.run(1, offset=offset)
    poses, _ = impossible_batch.get_poses([0])
    result = results[0]

    assert int(result["attempts"]) == 1
    assert int(result["accepted"]) == 0
    assert int(result["rejected"]) == 1
    assert int(result["termination"]) == 0
    assert float(result["side"]) == pytest.approx(float(initial_results[0]["side"]))
    np.testing.assert_array_equal(poses, initial_poses)


def test_accepted_side_trace_is_monotonic_and_auditable(cuda_device) -> None:
    """A tiny full-budget n=12 search has monotonic accepted sides and valid audits."""

    config = Config(n=12, initial_side=10.0, seed=20261008)
    batch = _batch(config, capacity=8, cuda_device=cuda_device, debug=True)
    results, _ = batch.run(8, offset=0)
    poses, _ = batch.get_poses(np.arange(8, dtype=np.int32))
    trace = batch.trace.numpy().copy()

    for world, result in enumerate(results):
        assert int(result["termination"]) in TERMINATIONS
        assert 0 <= int(result["attempts"]) <= config.max_attempts
        attempts = int(result["attempts"])
        if attempts:
            world_trace = trace[:attempts, world]
            assert np.all(np.diff(world_trace) <= 1e-5)
            assert float(result["side"]) == pytest.approx(float(world_trace[-1]), abs=2e-5)
        if int(result["termination"]) == 3:
            assert float(result["side"]) == 0.0
            continue

        validation = validate_pose(poses[world], float(result["side"]))
        assert validation["status"] == "NUMERICALLY_VALIDATED"
        assert validation["nonfinite"] is False


def test_budget_exhaustion_and_initialization_failure_are_explicit(cuda_device) -> None:
    """Bounded budgets terminate cleanly without inventing a final pose."""

    failure_config = Config(
        n=2,
        initial_side=1.5,
        seed=123,
        max_attempts=0,
        proposals_per_square=1,
    )
    failure_batch = _batch(failure_config, capacity=1, cuda_device=cuda_device)
    failure_results, _ = failure_batch.run(1, offset=0)
    failure = failure_results[0]
    assert int(failure["termination"]) == 3
    assert float(failure["side"]) == 0.0
    assert int(failure["feasible"]) == 0
    assert int(failure["accepted"]) == 0
    assert int(failure["sweeps"]) == 0

    exhaustion_config = Config(
        n=1,
        initial_side=10.0,
        seed=123,
        max_attempts=1,
        max_sweeps=1,
    )
    exhaustion_batch = _batch(exhaustion_config, capacity=1, cuda_device=cuda_device)
    exhaustion_results, _ = exhaustion_batch.run(1, offset=0)
    exhaustion = exhaustion_results[0]
    assert int(exhaustion["termination"]) == 0
    assert int(exhaustion["attempts"]) == 1
    assert int(exhaustion["sweeps"]) <= 1
    assert int(exhaustion["accepted"]) + int(exhaustion["rejected"]) == 1
    assert np.isfinite(
        np.asarray(
            (
                exhaustion["side"],
                exhaustion["min_gap"],
                exhaustion["min_wall"],
                exhaustion["max_penetration"],
                exhaustion["final_step"],
            ),
            dtype=np.float64,
        )
    ).all()
