"""The vectorized pair check must reproduce the per-pair SAT validator bit for bit."""

import glob
from pathlib import Path

import numpy as np
import pytest

from asquerix import geometry
from asquerix.geometry import _pair_separation, validate_pose, vertices


def reference(poses, side, tolerance):
    """The earlier per-pair implementation of validate_pose's pair stage, for comparison."""
    square_vertices = vertices(np.asarray(poses, dtype=np.float64))
    separations = []
    for first in range(len(square_vertices) - 1):
        for second in range(first + 1, len(square_vertices)):
            separations.append(_pair_separation(square_vertices[first], square_vertices[second]))
    return separations


def poses_to_check():
    rng = np.random.default_rng(20261009)
    cases = []
    for n in (2, 3, 5, 11, 16, 32):
        for scale in (0.6, 1.0, 1.4, 3.0):  # overlapping, touching-ish and separated arrangements
            for _ in range(60):
                side = scale * np.sqrt(n) + 1.0
                centers = rng.uniform(-side / 2 + 0.5, side / 2 - 0.5, size=(n, 2))
                angles = rng.uniform(-np.pi, np.pi, size=(n, 1)) * rng.choice([0.0, 1.0])
                cases.append((np.concatenate((centers, angles), axis=1).astype(np.float32), side))
    grid = np.array([[x + 0.5, y + 0.5, 0.0] for x in range(-2, 2) for y in range(-2, 2)], dtype=np.float32)
    cases.append((grid, 4.0))  # exact contacts
    for path in sorted(glob.glob(str(Path(__file__).resolve().parents[1] / "artifacts/lab/baseline/*.npz")))[:6]:
        with np.load(path) as archive:
            for pose in archive["poses"][:4]:
                cases.append((pose, 20.0))
    return cases


def test_vectorized_pairs_are_bit_identical_to_the_per_pair_validator():
    for poses, side in poses_to_check():
        expected = reference(poses, side, 1e-9)
        actual = list(geometry._pair_separations(vertices(np.asarray(poses, dtype=np.float64)))) if len(poses) > 1 else []
        assert np.array_equal(np.asarray(actual).view(np.uint64), np.asarray(expected).view(np.uint64))
        result = validate_pose(poses, side, 1e-9)
        if expected:
            assert result["min_pair_separation"] == min(expected)


@pytest.mark.parametrize("n", [1, 2])
def test_small_counts_and_non_finite_input_keep_their_results(n):
    assert validate_pose(np.zeros((n, 3)) + np.arange(n)[:, None] * 2, 10.0, 1e-9)["status"] == "NUMERICALLY_VALIDATED"
    broken = np.zeros((2, 3)); broken[1, 0] = np.inf
    assert validate_pose(broken, 10.0, 1e-9)["status"] == "INVALID"
