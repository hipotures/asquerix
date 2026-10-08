"""The minimum compression step must be tried before floor termination.

These tests launch the production kernel on seeded, one-square states. The
CPU cases exercise Warp's CPU backend, not a CPU fallback in the GPU runner.
"""
import numpy as np
import pytest

wp = pytest.importorskip("warp", reason="Warp is required for kernel regression tests")

from asquerix.geometry import validate_pose
from asquerix.gpu import Config, Result, parameters, simulate


@wp.kernel
def _seed_centered_square(poses: wp.array2d(dtype=wp.vec3),
                          results: wp.array(dtype=Result), side: float, step: float):
    poses[0, 0] = wp.vec3(0.0, 0.0, 0.0)
    result = Result()
    result.side = side
    result.final_step = step
    result.termination = 0
    result.feasible = 1
    results[0] = result


@pytest.fixture(params=["cpu", pytest.param("cuda", marks=pytest.mark.gpu)])
def backend(request):
    wp.init()
    if request.param == "cuda":
        devices = wp.get_cuda_devices()
        if not devices:
            pytest.skip("No CUDA device is available")
        return devices[0]
    return wp.get_device("cpu")


def _resume(backend, side, step, attempts):
    cfg = Config(n=1, max_attempts=attempts)
    poses = wp.zeros((1, 1), dtype=wp.vec3, device=backend)
    work = wp.zeros_like(poses)
    results = wp.zeros(1, dtype=Result, device=backend)
    trace = wp.zeros((attempts, 1), dtype=float, device=backend)
    wp.launch(_seed_centered_square, dim=1, inputs=[poses, results, side, step], device=backend)
    # stage=1 resumes a saved feasible state without random initialization.
    wp.launch(simulate, dim=1, inputs=[parameters(cfg), wp.uint64(0), poses, work,
              results, trace, 1, 1, attempts], device=backend, block_dim=32)
    if backend.is_cuda:
        wp.synchronize_device(backend)
    result = results.numpy()[0].copy()
    pose = poses.numpy()[:, 0, :].copy()
    assert validate_pose(pose, float(result["side"]))["status"] == "NUMERICALLY_VALIDATED"
    assert int(result["feasible"]) == 1
    # No accepted step in these fixtures needs to move the centered square;
    # all changes made during an infeasible attempt must have been rolled back.
    np.testing.assert_array_equal(pose, np.zeros((1, 3), dtype=np.float32))
    return result


def test_non_dyadic_floor_is_attempted_and_can_succeed(backend):
    # At the larger step L < 1: impossible for a unit square. At the floor,
    # L = 1.00008: feasible with the unchanged guard and acceptance tolerance.
    result = _resume(backend, 1.00018, 0.0001953125, attempts=2)
    assert int(result["attempts"]) == 2
    assert int(result["accepted"]) == 1
    assert int(result["rejected"]) == 1
    assert int(result["termination"]) == 0  # budget, not failed floor
    assert float(result["side"]) == pytest.approx(1.00008, abs=2e-7)
    assert float(result["final_step"]) == float(np.float32(0.0001))


def test_exhausted_budget_does_not_claim_an_untried_floor_failed(backend):
    result = _resume(backend, 1.00018, 0.0001953125, attempts=1)
    assert int(result["attempts"]) == 1
    assert int(result["accepted"]) == 0
    assert int(result["rejected"]) == 1
    assert int(result["termination"]) == 0
    assert float(result["side"]) == pytest.approx(1.00018, abs=2e-7)
    assert float(result["final_step"]) == float(np.float32(0.0001))


def test_failed_floor_stops_once_and_preserves_the_feasible_state(backend):
    result = _resume(backend, 1.00005, 0.0001, attempts=8)
    assert int(result["attempts"]) == 1
    assert int(result["accepted"]) == 0
    assert int(result["rejected"]) == 1
    assert int(result["termination"]) == 1
    assert float(result["side"]) == pytest.approx(1.00005, abs=2e-7)
    assert float(result["final_step"]) == float(np.float32(0.0001))


def test_successful_floor_steps_continue_until_a_floor_attempt_fails(backend):
    result = _resume(backend, 1.0004, 0.0001, attempts=8)
    assert int(result["attempts"]) == 4
    assert int(result["accepted"]) == 3
    assert int(result["rejected"]) == 1
    assert int(result["termination"]) == 1
    assert float(result["side"]) == pytest.approx(1.0001, abs=2e-7)
    assert float(result["final_step"]) == float(np.float32(0.0001))
