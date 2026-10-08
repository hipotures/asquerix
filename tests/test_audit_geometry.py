"""Adversarial regression tests collected during the implementation audit."""

from __future__ import annotations

import json
from math import pi

import numpy as np
import pytest

from asquerix.geometry import VALIDATOR_VERSION, validate_document, validate_pose, vertices


def test_corner_contact_is_not_mistaken_for_aabb_overlap() -> None:
    """Axis-aligned squares touching at one vertex have zero SAT clearance."""

    poses = np.asarray(((0.0, 0.0, 0.0), (1.0, 1.0, 0.0)), dtype=np.float64)

    result = validate_pose(poses, side=5.0)

    assert result["status"] == "INDETERMINATE"
    assert result["min_pair_separation"] == pytest.approx(0.0, abs=1e-14)
    assert result["max_penetration"] == 0.0


def test_coincident_centers_with_different_angles_are_invalid_but_finite() -> None:
    """Coincident polygons must remain an explicit overlap, without NaNs."""

    poses = np.asarray(((0.0, 0.0, 0.0), (0.0, 0.0, pi / 4.0)), dtype=np.float64)

    result = validate_pose(poses, side=5.0)

    assert result["status"] == "INVALID"
    assert result["min_pair_separation"] < 0.0
    assert result["max_penetration"] > 0.0
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("side", "expected"),
    ((1.0 - 2e-9, "INDETERMINATE"), (1.0 - 3e-8, "INVALID")),
    ids=("wall-violation-within-tolerance", "wall-violation-outside-tolerance"),
)
def test_wall_uncertainty_boundaries_are_classified_honestly(side: float, expected: str) -> None:
    """A tiny wall violation is ambiguous only inside the declared tolerance."""

    result = validate_pose(np.asarray(((0.0, 0.0, 0.0),), dtype=np.float64), side=side)

    assert result["status"] == expected
    assert result["min_wall_clearance"] == pytest.approx((side - 1.0) / 2.0, abs=1e-15)
    assert result["max_penetration"] == pytest.approx(max(0.0, (1.0 - side) / 2.0), abs=1e-15)


def test_quarter_turn_wrap_and_nearly_parallel_vertices_round_trip() -> None:
    """Angles near a square's quarter-turn period preserve unit edges."""

    epsilon = 1e-13
    poses = np.asarray(
        (
            (0.0, 0.0, -epsilon),
            (1.2, 1.3, pi / 2.0 + epsilon),
            (-1.4, 0.7, pi / 2.0 + 2.0 * pi),
        ),
        dtype=np.float64,
    )

    square_vertices = vertices(poses)
    edge_lengths = np.linalg.norm(np.roll(square_vertices, -1, axis=1) - square_vertices, axis=2)
    result = validate_pose(poses, side=8.0)

    np.testing.assert_allclose(edge_lengths, 1.0, atol=1e-14)
    assert result["status"] == "NUMERICALLY_VALIDATED"
    assert np.isfinite(square_vertices).all()


def test_finite_but_unrepresentable_centers_cannot_emit_infinite_metrics() -> None:
    """Float64 center offsets that erase unit edges must be rejected safely."""

    poses = np.asarray(((1e16, 0.0, 0.0), (1e16, 0.0, pi / 4.0)), dtype=np.float64)

    result = validate_pose(poses, side=1e308)

    assert result["status"] == "INVALID"
    assert result["min_pair_separation"] is None
    assert result["max_penetration"] is None
    assert result["min_wall_clearance"] is None
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("value", (True, False, "2.0", b"2.0"))
def test_non_numeric_length_scalars_are_not_schema_coerced(value: object) -> None:
    """Booleans and textual numbers are malformed length values."""

    result = validate_pose(np.asarray(((0.0, 0.0, 0.0),), dtype=np.float64), side=value)

    assert result["status"] == "INVALID"
    json.dumps(result, allow_nan=False)


def test_document_rejects_textual_side_and_boolean_tolerance() -> None:
    document = {"n": 1, "side": "2.0", "poses": [[0.0, 0.0, 0.0]]}

    side_result = validate_document(document)
    tolerance_result = validate_document(
        {"n": 1, "side": 2.0, "poses": [[0.0, 0.0, 0.0]]}, tolerance=True
    )

    assert side_result["status"] == "INVALID"
    assert "side" in side_result["error"]
    assert tolerance_result["status"] == "INVALID"
    assert "tolerance" in tolerance_result["error"]
    json.dumps(side_result, allow_nan=False)
    json.dumps(tolerance_result, allow_nan=False)


def test_result_and_pose_json_round_trip_preserve_numeric_geometry() -> None:
    poses = np.asarray(((0.125, -0.375, 0.1234567890123456),), dtype=np.float64)
    document = {
        "n": 1,
        "side": 3.75,
        "poses": json.loads(json.dumps(poses.tolist(), allow_nan=False)),
    }

    result = validate_document(document)

    assert result["status"] == "NUMERICALLY_VALIDATED"
    assert result["validator_version"] == VALIDATOR_VERSION
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("coordinate", [10**400, "0.0", True, False])
def test_malformed_or_overflowing_pose_coordinates_return_json_invalid(coordinate):
    result = validate_document({"n": 1, "side": 4, "poses": [[coordinate, 0.0, 0.0]]})
    assert result["status"] == "INVALID"
    json.dumps(result, allow_nan=False)

