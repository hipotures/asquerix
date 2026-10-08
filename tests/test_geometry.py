"""Tests for the independent float64 square-geometry validator."""

from __future__ import annotations

import json
from math import pi, sqrt

import numpy as np
import pytest

from asquerix.geometry import VALIDATOR_VERSION, validate_pose, vertices


def grid_fixture(rows: int, columns: int) -> tuple[np.ndarray, float]:
    """Return an aligned grid centred at the origin and its container side."""

    poses = [
        (column - (columns - 1) / 2.0, row - (rows - 1) / 2.0, 0.0)
        for row in range(rows)
        for column in range(columns)
    ]
    return np.asarray(poses, dtype=np.float64), float(max(rows, columns))


@pytest.mark.parametrize(
    ("rows", "columns"),
    ((1, 1), (2, 2), (3, 3), (3, 4), (4, 4)),
    ids=("n1", "n4", "n9", "n12", "n16"),
)
def test_known_grid_fixtures_are_contained_and_contacting(rows: int, columns: int) -> None:
    poses, side = grid_fixture(rows, columns)

    result = validate_pose(poses, side)

    assert result["status"] == "INDETERMINATE"
    assert result["nonfinite"] is False
    assert result["max_penetration"] == 0.0
    assert result["min_wall_clearance"] == pytest.approx(0.0, abs=1e-12)
    if len(poses) == 1:
        assert result["min_pair_separation"] is None
    else:
        assert result["min_pair_separation"] == pytest.approx(0.0, abs=1e-12)


def five_square_fixture() -> tuple[np.ndarray, float]:
    """Analytic four-corner plus central 45-degree five-square construction."""

    side = 2.0 + sqrt(2.0) / 2.0
    corner_offset = (side - 1.0) / 2.0
    poses = np.asarray(
        (
            (-corner_offset, -corner_offset, 0.0),
            (-corner_offset, corner_offset, 0.0),
            (corner_offset, -corner_offset, 0.0),
            (corner_offset, corner_offset, 0.0),
            (0.0, 0.0, pi / 4.0),
        ),
        dtype=np.float64,
    )
    return poses, side


def test_five_square_rotated_fixture_has_only_numerical_contacts() -> None:
    poses, side = five_square_fixture()

    result = validate_pose(poses, side, tolerance=1e-8)

    assert result["status"] == "INDETERMINATE"
    assert result["nonfinite"] is False
    assert result["max_penetration"] == pytest.approx(0.0, abs=1e-12)
    assert result["min_wall_clearance"] == pytest.approx(0.0, abs=1e-12)
    assert result["min_pair_separation"] == pytest.approx(0.0, abs=1e-12)


def test_vertices_have_unit_edges_and_expected_shape() -> None:
    poses = np.asarray(((0.2, -0.3, 0.37), (-0.4, 0.8, -1.2)), dtype=np.float64)

    result = vertices(poses)

    assert result.shape == (2, 4, 2)
    assert result.dtype == np.float64
    edge_lengths = np.linalg.norm(np.roll(result, -1, axis=1) - result, axis=2)
    np.testing.assert_allclose(edge_lengths, 1.0, atol=1e-14)
    assert np.isfinite(result).all()


def test_aabb_overlap_does_not_replace_polygon_sat() -> None:
    # The two 45-degree squares have overlapping axis-aligned bounding boxes,
    # but their diagonal support intervals are separated.
    poses = np.asarray(((0.0, 0.0, pi / 4.0), (1.2, 1.2, pi / 4.0)), dtype=np.float64)

    result = validate_pose(poses, side=6.0)

    assert result["status"] == "NUMERICALLY_VALIDATED"
    assert result["min_pair_separation"] > 0.6
    assert result["max_penetration"] == 0.0


def test_near_parallel_edges_and_quarter_turn_periodicity_are_finite() -> None:
    near_parallel = np.asarray(((0.0, 0.0, 1e-12), (1.1, 0.0, pi / 2.0 - 1e-12)), dtype=np.float64)
    quarter_turn = np.asarray(((0.0, 0.0, 0.0), (1.1, 0.0, pi / 2.0)), dtype=np.float64)
    periodic = np.asarray(((0.0, 0.0, 0.0), (1.1, 0.0, pi / 2.0 + 2.0 * pi)), dtype=np.float64)

    near_result = validate_pose(near_parallel, side=4.0)
    quarter_result = validate_pose(quarter_turn, side=4.0)
    periodic_result = validate_pose(periodic, side=4.0)

    assert near_result["status"] == "NUMERICALLY_VALIDATED"
    assert quarter_result["status"] == "NUMERICALLY_VALIDATED"
    assert periodic_result["status"] == "NUMERICALLY_VALIDATED"
    assert near_result["min_pair_separation"] == pytest.approx(0.1, abs=1e-10)
    assert periodic_result["min_pair_separation"] == pytest.approx(
        quarter_result["min_pair_separation"], abs=1e-12
    )


def test_exact_contact_is_indeterminate_and_clearance_perturbations_change_verdict() -> None:
    touching = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)), dtype=np.float64)
    separated = touching.copy()
    separated[1, 0] += 2e-7
    overlapping = touching.copy()
    overlapping[1, 0] -= 2e-7

    touching_result = validate_pose(touching, side=4.0)
    separated_result = validate_pose(separated, side=4.0)
    overlapping_result = validate_pose(overlapping, side=4.0)

    assert touching_result["status"] == "INDETERMINATE"
    assert touching_result["min_pair_separation"] == pytest.approx(0.0, abs=1e-14)
    assert separated_result["status"] == "NUMERICALLY_VALIDATED"
    assert separated_result["min_pair_separation"] == pytest.approx(2e-7, abs=1e-12)
    assert overlapping_result["status"] == "INVALID"
    assert overlapping_result["max_penetration"] == pytest.approx(2e-7, abs=1e-12)


@pytest.mark.parametrize(
    ("poses", "side"),
    (
        (np.asarray(((0.0, 0.0, 0.0),), dtype=np.float64), 2.0 + 2e-7),
        (np.asarray(((0.0, 0.0, 0.0),), dtype=np.float64), 1.0),
    ),
    ids=("positive-wall-clearance", "wall-contact"),
)
def test_containment_is_measured_from_all_vertices(poses: np.ndarray, side: float) -> None:
    result = validate_pose(poses, side)

    assert result["min_pair_separation"] is None
    assert result["min_wall_clearance"] == pytest.approx((side - 1.0) / 2.0, abs=1e-14)
    expected_status = "NUMERICALLY_VALIDATED" if side > 2.0 else "INDETERMINATE"
    assert result["status"] == expected_status


def test_each_wall_contact_is_retained_as_indeterminate() -> None:
    poses = np.asarray(
        (
            (0.5, 0.0, 0.0),
            (-0.5, 0.0, 0.0),
            (0.0, 0.5, 0.0),
            (0.0, -0.5, 0.0),
        ),
        dtype=np.float64,
    )

    for pose in poses:
        result = validate_pose(pose[None, :], side=2.0)
        assert result["status"] == "INDETERMINATE"
        assert result["min_wall_clearance"] == pytest.approx(0.0, abs=1e-14)


def test_nonfinite_and_malformed_inputs_are_invalid() -> None:
    nonfinite = validate_pose(np.asarray(((np.nan, 0.0, 0.0),)), side=2.0)
    malformed = validate_pose(np.asarray((0.0, 0.0, 0.0)), side=2.0)
    bad_side = validate_pose(np.asarray(((0.0, 0.0, 0.0),)), side=0.0)
    bad_tolerance = validate_pose(np.asarray(((0.0, 0.0, 0.0),)), side=2.0, tolerance=-1.0)

    assert nonfinite["status"] == "INVALID"
    assert nonfinite["nonfinite"] is True
    assert malformed["status"] == "INVALID"
    assert malformed["nonfinite"] is False
    assert bad_side["status"] == "INVALID"
    assert bad_tolerance["status"] == "INVALID"


def test_json_serialization_has_no_nonstandard_float_values() -> None:
    poses, side = grid_fixture(2, 2)
    result = validate_pose(poses, side)

    encoded = json.dumps(result, allow_nan=False, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["validator_version"] == VALIDATOR_VERSION
    assert decoded["status"] == "INDETERMINATE"
    assert isinstance(decoded["nonfinite"], bool)


def test_vertices_reject_malformed_shapes_but_preserve_nonfinite_diagnostics() -> None:
    with pytest.raises(ValueError, match=r"shape \(n, 3\)"):
        vertices(np.zeros((3, 2), dtype=np.float64))

    nonfinite_vertices = vertices(np.asarray(((0.0, 0.0, np.inf),), dtype=np.float64))
    assert nonfinite_vertices.shape == (1, 4, 2)
    assert not np.isfinite(nonfinite_vertices).all()
