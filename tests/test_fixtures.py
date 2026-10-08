"""Offline known-packing fixtures and independent reconstruction checks."""

from __future__ import annotations

import json
import math
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import pytest

from asquerix.geometry import validate_pose, vertices


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "trump11.json"
EXPECTED_SOURCE_COMMIT = "176e8ad14d5b93f3a1f3d5a9e04ab1dfdb8c704b"
EXPECTED_SOURCE_SHA256 = "3b4eae938c37c13af6252ac5d83fa99aa95f6b1627b99920c5df8be94c56bea9"


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as stream:
        return json.load(stream)


def _evaluate_polynomial(coefficients: tuple[int, ...], value: Decimal) -> Decimal:
    result = Decimal(0)
    for coefficient in coefficients:
        result = result * value + Decimal(coefficient)
    return result


def _bisect_u(coefficients: tuple[int, ...], interval: tuple[str, str]) -> Decimal:
    """Recover the intended algebraic root without importing source code."""

    with localcontext() as context:
        context.prec = 120
        lower = Decimal(interval[0])
        upper = Decimal(interval[1])
        lower_value = _evaluate_polynomial(coefficients, lower)
        upper_value = _evaluate_polynomial(coefficients, upper)
        assert lower_value * upper_value < 0
        for _ in range(400):
            midpoint = (lower + upper) / 2
            midpoint_value = _evaluate_polynomial(coefficients, midpoint)
            if midpoint_value == 0:
                return midpoint
            if lower_value * midpoint_value < 0:
                upper = midpoint
                upper_value = midpoint_value
            else:
                lower = midpoint
                lower_value = midpoint_value
        return (lower + upper) / 2


def _reconstruct_trump11(fixture: dict) -> tuple[np.ndarray, float]:
    """Rebuild centers and angles from the fixture's published equations."""

    construction = fixture["construction"]
    coefficients = tuple(construction["u_minimal_polynomial_coefficients_high_to_low"])
    interval = tuple(construction["u_isolating_interval"])
    root = _bisect_u(coefficients, interval)
    u = float(root)

    # The root is recovered with Decimal; trigonometric evaluation and the
    # geometric reconstruction intentionally use ordinary float64 math.
    angle = 2.0 * math.atan(u)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    side = (6.0 * u + 4.0) / (1.0 + 2.0 * u - u * u)

    r1 = 1.0 - (side - 3.0) * cos_angle
    u1 = ((1.0 + r1) * cos_angle - 1.0) / sin_angle
    v1 = cos_angle - sin_angle
    v2 = (side - 1.0) / sin_angle - r1 - (3.0 + u1) * (cos_angle / sin_angle)
    x0 = 1.0 + 2.0 / cos_angle - (side - 2.0) * (sin_angle / cos_angle)

    def axis_aligned(x: float, y: float) -> list[tuple[float, float]]:
        return [(x, y), (x + 1.0, y), (x + 1.0, y + 1.0), (x, y + 1.0)]

    def tilted(offset_x: float, offset_y: float) -> list[tuple[float, float]]:
        corners = []
        for dx, dy in ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)):
            px = offset_x + dx
            py = offset_y + dy - r1
            corners.append(
                (
                    1.0 + cos_angle * px - sin_angle * py,
                    1.0 + sin_angle * px + cos_angle * py,
                )
            )
        return corners

    squares = [
        axis_aligned(0.0, 0.0),
        axis_aligned(side - 1.0, 0.0),
        axis_aligned(x0, side - 1.0),
        axis_aligned(0.0, side - 1.0),
        axis_aligned(1.0, side - 1.0),
        axis_aligned(0.0, side - 2.0),
        tilted(0.0, 0.0),
        tilted(u1, -1.0),
        tilted(1.0, v1),
        tilted(u1 + 1.0, v1 - 1.0),
        tilted(u1 + 2.0, -v2),
    ]

    poses = []
    for index, square in enumerate(squares):
        center = np.mean(np.asarray(square, dtype=np.float64), axis=0) - side / 2.0
        poses.append((float(center[0]), float(center[1]), angle if index >= 6 else 0.0))
    return np.asarray(poses, dtype=np.float64), float(side)


def test_trump11_metadata_is_pinned_and_construction_scoped() -> None:
    fixture = _load_fixture()

    assert fixture["fixture_id"] == "trump11"
    assert fixture["n"] == 11
    assert len(fixture["poses"]) == 11
    assert fixture["provenance"]["source_commit"] == EXPECTED_SOURCE_COMMIT
    assert fixture["provenance"]["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert fixture["provenance"]["source_license"] == "MIT"
    assert fixture["provenance"]["retrieved_on"] == "2026-10-08"
    assert fixture["proof_status"]["case_record_status"] == "V3/C3/S5"
    assert fixture["proof_status"]["review_status"] == "review pending"
    assert "no global optimality assertion" in fixture["proof_status"]["fixture_scope"]


def test_trump11_reconstructs_from_decimal_root_and_float64_equations() -> None:
    fixture = _load_fixture()
    reconstructed_poses, reconstructed_side = _reconstruct_trump11(fixture)
    stored_poses = np.asarray(fixture["poses"], dtype=np.float64)

    assert reconstructed_poses.shape == (11, 3)
    assert np.isfinite(reconstructed_poses).all()
    assert reconstructed_side == pytest.approx(float(fixture["side"]), abs=5e-15)
    np.testing.assert_allclose(stored_poses, reconstructed_poses, rtol=0.0, atol=5e-15)


def test_exact_rounded_trump11_pose_is_indeterminate_at_contacts() -> None:
    fixture = _load_fixture()
    poses = np.asarray(fixture["poses"], dtype=np.float64)
    result = validate_pose(poses, float(fixture["side"]))

    assert result["status"] == "INDETERMINATE"
    assert result["nonfinite"] is False
    assert result["min_pair_separation"] >= -1e-8
    assert result["min_wall_clearance"] >= -1e-8
    assert result["max_penetration"] <= 1e-8


def test_derived_trump11_pose_has_positive_clearance_without_resizing_squares() -> None:
    fixture = _load_fixture()
    poses = np.asarray(fixture["poses"], dtype=np.float64)
    side = float(fixture["side"])
    scale = 1.0 + 1e-5

    derived_poses = poses.copy()
    derived_poses[:, :2] *= scale
    result = validate_pose(derived_poses, side * scale)

    assert result["status"] == "NUMERICALLY_VALIDATED"
    assert result["min_pair_separation"] > result["tolerance"]
    assert result["min_wall_clearance"] > result["tolerance"]
    assert result["max_penetration"] == 0.0

    # Scaling centers and the container leaves the mathematical square side at
    # one; only the pose and the container side are derived artifacts.
    derived_vertices = vertices(derived_poses)
    edge_lengths = np.linalg.norm(
        np.roll(derived_vertices, -1, axis=1) - derived_vertices,
        axis=2,
    )
    np.testing.assert_allclose(edge_lengths, 1.0, rtol=0.0, atol=1e-14)
