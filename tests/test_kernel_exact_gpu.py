"""Bitwise CUDA regression tests for the frozen kernel correctness corpus."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = REPOSITORY_ROOT / "artifacts" / "performance" / "cuda-20261009" / "corpus"
MANIFEST_PATH = CORPUS_ROOT / "corpus.json"
SOURCE_PATH = REPOSITORY_ROOT / "src" / "asquerix" / "gpu.py"
SMALL_VALIDATION_MAX_COUNT = 32


def _read_manifest() -> list[dict[str, Any]]:
    with MANIFEST_PATH.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    experiments = manifest.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        raise ValueError(f"{MANIFEST_PATH} must contain a non-empty experiments list")
    entries: list[dict[str, Any]] = []
    for entry in experiments:
        if not isinstance(entry, dict):
            raise ValueError("corpus experiment entries must be objects")
        required = {"name", "config", "count", "offset", "file"}
        missing = required.difference(entry)
        if missing:
            raise ValueError(f"corpus experiment is missing fields: {sorted(missing)}")
        entries.append(entry)
    return entries


EXPERIMENTS = _read_manifest()

# Importing Warp is intentionally delayed until a corpus exists.  The shared
# fixture in tests/conftest.py skips this module unless a real CUDA device is
# available; no CPU backend is accepted here.
wp = pytest.importorskip("warp", reason="Warp is required for exact CUDA regression tests")
pytestmark = pytest.mark.gpu

from asquerix import gpu


BASELINE_SOURCE_PATH = (
    REPOSITORY_ROOT / "artifacts" / "performance" / "cuda-20261009" / "baseline" / "gpu.py"
)


def _load_kernel_tools_module():
    """Load benchmark helpers from their repository file."""

    spec = importlib.util.spec_from_file_location(
        "asquerix_kernel_benchmark_test", REPOSITORY_ROOT / "tools" / "kernel_benchmark.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("kernel benchmark helper spec is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


KERNEL_TOOLS = _load_kernel_tools_module()
baseline_gpu = KERNEL_TOOLS.load_source(BASELINE_SOURCE_PATH, "asquerix_gpu_axes_baseline")


@wp.kernel
def _axes_baseline_probe(theta: wp.array(dtype=float), values: wp.array2d(dtype=float)):
    i = wp.tid()
    u, v = baseline_gpu.axes(theta[i])
    values[i, 0] = u[0]
    values[i, 1] = u[1]
    values[i, 2] = v[0]
    values[i, 3] = v[1]
    values[i, 4] = wp.dot(u, u)
    values[i, 5] = wp.dot(u, v)
    values[i, 6] = wp.dot(v, u)
    values[i, 7] = wp.dot(v, v)


@wp.kernel
def _axes_current_probe(theta: wp.array(dtype=float), values: wp.array2d(dtype=float)):
    i = wp.tid()
    u, v = gpu.axes(theta[i])
    values[i, 0] = u[0]
    values[i, 1] = u[1]
    values[i, 2] = v[0]
    values[i, 3] = v[1]
    values[i, 4] = wp.dot(u, u)
    values[i, 5] = wp.dot(u, v)
    values[i, 6] = wp.dot(v, u)
    values[i, 7] = wp.dot(v, v)


def _experiment_id(entry: dict[str, Any]) -> str:
    return str(entry["name"])


def _load_archive(entry: dict[str, Any]) -> dict[str, np.ndarray]:
    path = CORPUS_ROOT / str(entry["file"])
    with np.load(path, allow_pickle=False) as archive:
        return {name: archive[name].copy() for name in archive.files}


def _assert_byte_equal(actual: np.ndarray, expected: np.ndarray, label: str) -> None:
    """Compare shape, dtype, and every byte, including signed zero bits."""

    actual = np.asarray(actual)
    expected = np.asarray(expected)
    assert actual.shape == expected.shape, f"{label} shape differs"
    assert actual.dtype == expected.dtype, f"{label} dtype differs"
    actual_bytes = np.ascontiguousarray(actual).view(np.uint8)
    expected_bytes = np.ascontiguousarray(expected).view(np.uint8)
    np.testing.assert_array_equal(actual_bytes, expected_bytes, err_msg=f"{label} bytes differ")


def _run_axes_probe(kernel, theta_host: np.ndarray, device) -> np.ndarray:
    theta = wp.array(np.asarray(theta_host, dtype=np.float32), dtype=float, device=device)
    values = wp.zeros((len(theta_host), 8), dtype=float, device=device)
    wp.launch(kernel, dim=len(theta_host), inputs=[theta, values], device=device, block_dim=32)
    wp.synchronize_device(device)
    return values.numpy().copy()


@pytest.fixture(scope="session")
def kernel_tools():
    return KERNEL_TOOLS


@pytest.fixture(scope="session")
def baseline_gpu_module(kernel_tools):
    return baseline_gpu


def test_axes_and_dot_products_match_frozen_baseline(cuda_device) -> None:
    """Axis components and all four dot products remain bitwise identical."""

    theta = np.random.default_rng(20261009).uniform(-10.0, 10.0, 65536).astype(np.float32)
    baseline = _run_axes_probe(_axes_baseline_probe, theta, cuda_device)
    current = _run_axes_probe(_axes_current_probe, theta, cuda_device)
    _assert_byte_equal(current, baseline, "axes and dot-product probe")


@pytest.mark.parametrize("entry", EXPERIMENTS, ids=_experiment_id)
def test_current_batch_matches_frozen_experiment(entry, cuda_device) -> None:
    """Current simulation output must match the baseline corpus byte-for-byte."""

    module = gpu
    archive = _load_archive(entry)
    count = int(entry["count"])
    offset = int(entry["offset"])
    config_values = dict(entry["config"])
    config = module.Config(**config_values)

    batch = module.Batch(config, capacity=count, device=cuda_device)
    batch.poses.zero_()
    batch.work.zero_()
    results, _timing = batch.run(count, offset=offset)
    poses, _transfer = batch.get_poses(np.arange(count, dtype=np.int32))
    _assert_byte_equal(results, archive["results"], f"{entry['name']} results")
    _assert_byte_equal(poses, archive["poses"], f"{entry['name']} poses")

    # Re-run only initialization with the exact experiment configuration.  A
    # zero attempt budget still executes the device-resident initializer and
    # therefore checks RNG identity, global offsets, and initial pose layout.
    initial_config_values = dict(config_values)
    initial_config_values["max_attempts"] = 0
    initial_config = module.Config(**initial_config_values)
    initial_batch = module.Batch(initial_config, capacity=count, device=cuda_device)
    initial_batch.poses.zero_()
    initial_batch.work.zero_()
    initial_results, _initial_timing = initial_batch.run(count, offset=offset)
    initial_poses, _initial_transfer = initial_batch.get_poses(np.arange(count, dtype=np.int32))
    _assert_byte_equal(
        initial_results,
        archive["initial_results"],
        f"{entry['name']} initial results",
    )
    _assert_byte_equal(
        initial_poses,
        archive["initial_poses"],
        f"{entry['name']} initial poses",
    )

    if count <= SMALL_VALIDATION_MAX_COUNT:
        _validate_small_outputs(module, results, poses, initial_results, entry)


def _validate_small_outputs(
    module,
    results: np.ndarray,
    poses: np.ndarray,
    initial_results: np.ndarray,
    entry: dict[str, Any],
) -> None:
    """Run the independent float64 validator on every small final output."""

    # Importing here keeps the CUDA corpus test's validator independent from
    # the loaded production source module.
    from asquerix.geometry import validate_pose

    for index, result in enumerate(results):
        termination = int(result["termination"])
        if termination == 3:
            # Initialization failures do not have a complete final pose and
            # are checked through the initializer result instead.
            assert int(initial_results[index]["termination"]) == 3, (
                f"{entry['name']} world {index} changed initialization status"
            )
            continue

        assert int(initial_results[index]["termination"]) != 3, (
            f"{entry['name']} world {index} lost its initialized pose"
        )
        validation = validate_pose(poses[index], float(result["side"]))
        assert validation["status"] == "NUMERICALLY_VALIDATED", (
            f"{entry['name']} world {index} CPU validation: {validation}"
        )


def test_contact_diagnostics_match_frozen_outputs(kernel_tools, cuda_device) -> None:
    """Pair and wall diagnostics retain exact baseline values and pose bits."""

    diagnostic = kernel_tools.diagnostic
    contact_path = CORPUS_ROOT / "contacts.npz"
    with np.load(contact_path, allow_pickle=False) as archive:
        expected = {name: archive[name].copy() for name in archive.files}

    device = str(cuda_device)
    pair_p, pair_q, pair_values = diagnostic(
        gpu,
        expected["input_p"],
        expected["input_q"],
        wall_mode=0,
        device=device,
    )
    _assert_byte_equal(pair_p, expected["pair_p"], "pair diagnostic p")
    _assert_byte_equal(pair_q, expected["pair_q"], "pair diagnostic q")
    _assert_byte_equal(pair_values, expected["pair_values"], "pair diagnostic values")

    wall_p, wall_q, wall_values = diagnostic(
        gpu,
        expected["input_p"],
        expected["input_q"],
        wall_mode=1,
        device=device,
    )
    _assert_byte_equal(wall_p, expected["wall_p"], "wall diagnostic p")
    _assert_byte_equal(wall_q, expected["wall_q"], "wall diagnostic q")
    _assert_byte_equal(wall_values, expected["wall_values"], "wall diagnostic values")


def test_adversarial_wall_diagnostics_match_frozen_bytes(
    kernel_tools, baseline_gpu_module, cuda_device
) -> None:
    """Adversarial wall diagnostics preserve the complete output bit-for-bit."""

    guard = float(gpu.Config().guard)
    distances = np.asarray(
        (
            0.7072068 + guard - 2e-5,
            0.7072068 + guard,
            0.7072068 + guard + 2e-5,
            999.999,
            1000.0,
            1000.001,
        ),
        dtype=np.float32,
    )
    angles = np.asarray(
        (0.0, np.pi / 4, -np.pi / 3, 10000.0, -10000.0, 10001.0, np.inf, np.nan),
        dtype=np.float32,
    )
    rows = []
    for distance in distances:
        for y in (0.0, 0.25, -0.25):
            for angle in angles:
                rows.append((1.0 - distance, y, angle))
    p_host = np.asarray(rows, dtype=np.float32)
    q_host = np.zeros_like(p_host)
    device = str(cuda_device)

    current = kernel_tools.diagnostic(gpu, p_host, q_host, wall_mode=1, device=device)
    baseline = kernel_tools.diagnostic(
        baseline_gpu_module, p_host, q_host, wall_mode=1, device=device
    )
    for label, optimized, reference in zip(("p", "q", "values"), current, baseline):
        _assert_byte_equal(optimized, reference, f"wall boundary {label}")


def _resume_simulation(
    module,
    poses_host: np.ndarray,
    side: float,
    device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Resume a fixed accepted state through the complete production kernel."""

    count, n, width = poses_host.shape
    assert width == 3
    config = module.Config(
        n=n,
        initial_side=10.0,
        seed=20261008,
        max_attempts=32,
        max_sweeps=480,
    )
    # Production storage is (square, world, component), while fixtures are
    # easier to read and define as (world, square, component).
    accepted_pose = wp.array(
        np.ascontiguousarray(np.transpose(poses_host, (1, 0, 2)), dtype=np.float32),
        dtype=wp.vec3,
        device=device,
    )
    work = wp.empty_like(accepted_pose)
    result_dtype = wp.zeros(1, dtype=module.Result, device=device).numpy().dtype
    initial_results = np.zeros(count, dtype=result_dtype)
    initial_results["side"] = np.float32(side)
    initial_results["final_step"] = np.float32(config.step)
    initial_results["termination"] = 0
    initial_results["feasible"] = 1
    results = wp.array(initial_results, dtype=module.Result, device=device)
    trace = wp.zeros((config.max_attempts, count), dtype=float, device=device)
    wp.launch(
        module.simulate,
        dim=count,
        inputs=[
            module.parameters(config),
            wp.uint64(0),
            accepted_pose,
            work,
            results,
            trace,
            1,
            1,
            config.max_attempts,
        ],
        device=device,
        block_dim=32,
    )
    wp.synchronize_device(device)
    return results.numpy().copy(), accepted_pose.numpy().copy(), trace.numpy().copy()


def _seeded_contact_fixtures() -> tuple[tuple[str, np.ndarray, float], ...]:
    """Return simultaneous-contact states for both small and wall-heavy cases."""

    grid = np.asarray(
        (
            (-0.45, -0.45, 0.0),
            (0.45, -0.45, np.pi / 4),
            (-0.45, 0.45, -np.pi / 6),
            (0.45, 0.45, np.pi / 3),
        ),
        dtype=np.float32,
    )
    grid_worlds = np.stack(
        (
            grid,
            grid + np.asarray((0.02, -0.01, 0.03), dtype=np.float32),
            grid * np.asarray((1.0, -1.0, 1.0), dtype=np.float32),
        ),
        axis=0,
    ).astype(np.float32)

    near_wall = np.asarray(
        (
            (-2.35, -2.35, 0.0),
            (-1.25, -2.35, np.pi / 8),
            (-0.15, -2.35, -np.pi / 8),
            (0.95, -2.35, np.pi / 6),
            (2.05, -2.35, -np.pi / 6),
            (2.35, -1.25, np.pi / 4),
            (2.35, -0.15, -np.pi / 4),
            (2.35, 0.95, np.pi / 3),
            (2.35, 2.05, -np.pi / 3),
            (1.25, 2.35, np.pi / 5),
            (0.15, 2.35, -np.pi / 5),
        ),
        dtype=np.float32,
    )
    wall_worlds = np.stack(
        (
            near_wall,
            near_wall + np.asarray((-0.03, 0.02, 0.04), dtype=np.float32),
        ),
        axis=0,
    ).astype(np.float32)
    return (
        ("grid-n4", grid_worlds, 2.2),
        ("near-wall-n11", wall_worlds, 5.0),
    )


def test_seeded_contact_resumes_match_frozen_baseline(
    baseline_gpu_module, cuda_device
) -> None:
    """Dense contact states preserve complete resume outputs across revisions."""

    device = str(cuda_device)
    for name, poses, side in _seeded_contact_fixtures():
        current = _resume_simulation(gpu, poses, side, device)
        baseline = _resume_simulation(baseline_gpu_module, poses, side, device)
        for label, optimized, reference in zip(
            ("results", "poses", "trace"), current, baseline
        ):
            _assert_byte_equal(optimized, reference, f"{name} {label}")


def test_invalid_resume_states_match_frozen_baseline(
    baseline_gpu_module, cuda_device
) -> None:
    """Invalid centers and orientations preserve all resume bytes and statuses."""

    base = _seeded_contact_fixtures()[0][1][0]
    invalid_worlds = np.repeat(base[None, :, :], 4, axis=0).astype(np.float32)
    invalid_worlds[0, 0, 0] = np.nan
    invalid_worlds[1, 1, 1] = np.inf
    invalid_worlds[2, 2, 2] = np.nan
    invalid_worlds[3, 3, 0] = -np.inf

    device = str(cuda_device)
    current = _resume_simulation(gpu, invalid_worlds, 2.2, device)
    baseline = _resume_simulation(baseline_gpu_module, invalid_worlds, 2.2, device)
    for label, optimized, reference in zip(
        ("results", "poses", "trace"), current, baseline
    ):
        _assert_byte_equal(optimized, reference, f"invalid-resume {label}")
