"""Regression checks for production residual reporting and GPU readback bounds."""
import numpy as np
import pytest
import warp as wp

from asquerix.gpu import Batch, Config, Result, parameters, simulate
from asquerix.geometry import validate_pose


@pytest.mark.parametrize("changes", [
    {"step": 1e40}, {"motion_tolerance": 1e-50},
    {"step_reduction": 1 - 1e-10},
    {"guard": 2e-5, "acceptance_tolerance": 2e-5 - 1e-14},
])
def test_configuration_contract_survives_fp32_conversion(changes):
    with pytest.raises(ValueError, match="FP32"):
        Config(**changes).validate()


@pytest.mark.gpu
def test_production_finalizer_reports_wall_penetration(cuda_device):
    # Inject an invalid accepted state to exercise the production finalizer;
    # zero attempts in this diagnostic must leave all coordinates unchanged.
    config = Config(n=1, max_attempts=1)
    poses = wp.array(np.asarray([[[5.0, 0.0, 0.0]]], dtype=np.float32),
                     dtype=wp.vec3, device=cuda_device)
    work = wp.empty_like(poses)
    state = Result()
    state.side = 10.0
    state.final_step = config.step
    results = wp.array([state], dtype=Result, device=cuda_device)
    trace = wp.zeros((1, 1), dtype=float, device=cuda_device)
    wp.launch(simulate, dim=1, inputs=[parameters(config), wp.uint64(0), poses,
              work, results, trace, 0, 1, 0], device=cuda_device, block_dim=32)
    wp.synchronize_device(cuda_device)
    result = results.numpy()[0]
    assert result["min_wall"] == pytest.approx(-0.5)
    assert result["max_penetration"] == pytest.approx(0.5)
    assert result["feasible"] == 0
    np.testing.assert_array_equal(poses.numpy(), [[[5.0, 0.0, 0.0]]])


@pytest.mark.gpu
def test_batch_rejects_noninteger_ids_and_out_of_batch_gather(cuda_device):
    batch = Batch(Config(n=1, max_attempts=0), 4, cuda_device)
    for count, offset in [(1, 1.5), (1, True), (True, 0), (1.5, 0),
                          (1, -1), (2, 2**64 - 1)]:
        with pytest.raises(ValueError, match="trial range"):
            batch.run(count, offset)
    with pytest.raises(ValueError, match="pose indices"):
        batch.get_poses([0])
    batch.run(4, 9)
    batch.run(1, 13)
    for indices in [[1], [-1], [0.0], [True], [2**64 - 1], [[0]], [0] * 5]:
        with pytest.raises(ValueError, match="pose indices"):
            batch.get_poses(indices)
    assert batch.get_poses([0])[0].shape == (1, 1, 3)
    assert batch.get_poses([])[0].shape == (0, 1, 3)


@pytest.mark.gpu
def test_gpu_sat_matches_independent_vertex_projection_on_adversarial_pairs(cuda_device):
    from asquerix.gpu import contact_diagnostic
    cases = [
        ((0, 0, 0), (1, 0, 0)),                 # edge contact
        ((0, 0, 0), (1, 1, 0)),                 # vertex contact
        ((0, 0, 0), (1 - 1e-4, 0, 0)),          # overlap
        ((0, 0, 0), (1 + 1e-4, 0, 0)),          # separation
        ((0, 0, 0.31), (0, 0, -0.27)),          # coincident centers
        ((0, 0, 1e-7), (1.01, 0, -1e-7)),       # nearly parallel
        ((0, 0, np.pi / 2 - 1e-7), (1.01, 0, -1e-7)),
        ((0, 0, np.pi / 4), (1.0, 1.0, np.pi / 4)),  # AABB false positive
    ]
    p_host = np.asarray([a for a, _ in cases], dtype=np.float32)
    q_host = np.asarray([b for _, b in cases], dtype=np.float32)
    p = wp.array(p_host, dtype=wp.vec3, device=cuda_device)
    q = wp.array(q_host, dtype=wp.vec3, device=cuda_device)
    values = wp.zeros((len(cases), 7), dtype=float, device=cuda_device)
    wp.launch(contact_diagnostic, len(cases), inputs=[p, q, parameters(Config()), 10.0, 0, values],
              device=cuda_device)
    wp.synchronize_device(cuda_device)
    gaps = values.numpy()[:, 0]
    for index in range(len(cases)):
        # Validate the exact saved FP32 inputs, rather than unrounded originals.
        validation = validate_pose([p_host[index], q_host[index]], 10)
        assert gaps[index] == pytest.approx(validation["min_pair_separation"], abs=5e-7)
