"""Independent float64 geometry checks for unit squares.

The production search may use support-function calculations on the GPU.  This
module deliberately takes a separate route for validation: it reconstructs the
four vertices in float64 and projects those vertices onto normals of the
polygon edges.  The implementation is intended to be an oracle for saved
poses, rather than a second simulation backend.

Coordinates use a container centred at the origin.  A pose is ``(x, y,
theta)`` and every square has mathematical side length one.  The vertex
construction and all reported distances are floating-point numerical checks;
``NUMERICALLY_VALIDATED`` is not an exact or rigorous certificate.
"""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Integral, Real
from typing import Any

import numpy as np


VALIDATOR_VERSION = "cpu-f64-projection-v2"
_VERTEX_COUNT = 4
_POSE_WIDTH = 3
_UNIT_EDGE_TOLERANCE = 1e-12


def _pose_array(poses: Any) -> np.ndarray:
    """Return poses as float64, rejecting malformed dimensions.

    Non-finite values are intentionally allowed here.  ``validate_pose`` must
    report them as ``INVALID`` instead of failing before it can produce its
    JSON-serializable diagnostic.  The public ``vertices`` helper follows the
    same rule and therefore returns non-finite vertices for non-finite poses.
    """

    try:
        raw = np.asarray(poses, dtype=object)
        if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) for value in raw.flat):
            raise ValueError("pose coordinates must be numeric, non-boolean scalars")
        array = np.asarray(raw, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("poses must be convertible to a numeric float64 array") from exc
    if array.ndim != 2 or array.shape[1] != _POSE_WIDTH:
        raise ValueError("poses must have shape (n, 3)")
    return array


def vertices(poses: Any) -> np.ndarray:
    """Construct the four vertices of each unit square.

    Parameters
    ----------
    poses:
        An array-like object with shape ``(n, 3)`` containing ``x``, ``y``,
        and an angle in radians for each square.

    Returns
    -------
    numpy.ndarray
        A float64 array with shape ``(n, 4, 2)``.  Vertices are ordered around
        each square.  The first vertex is ``center + 0.5*u + 0.5*v`` where
        ``u=(cos(theta), sin(theta))`` and ``v=(-sin(theta), cos(theta))``.

    Raises
    ------
    ValueError
        If ``poses`` is not convertible to shape ``(n, 3)``.
    """

    array = _pose_array(poses)
    centers = array[:, :2]
    angles = array[:, 2]

    with np.errstate(invalid="ignore"):
        cosine = np.cos(angles)
        sine = np.sin(angles)
    u = np.stack((cosine, sine), axis=-1)
    v = np.stack((-sine, cosine), axis=-1)

    # This order winds around the square and makes the edge normals easy to
    # derive independently in the SAT validator below.
    signs = np.asarray(
        (
            (1.0, 1.0),
            (-1.0, 1.0),
            (-1.0, -1.0),
            (1.0, -1.0),
        ),
        dtype=np.float64,
    )
    return centers[:, None, :] + 0.5 * (
        signs[None, :, 0, None] * u[:, None, :]
        + signs[None, :, 1, None] * v[:, None, :]
    )


def _invalid_result(tolerance: float | None, nonfinite: bool = False) -> dict[str, Any]:
    """Build the stable result shape used for malformed input."""

    return {
        "status": "INVALID",
        "min_pair_separation": None,
        "max_penetration": None,
        "min_wall_clearance": None,
        "nonfinite": bool(nonfinite),
        "tolerance": tolerance,
        "validator_version": VALIDATOR_VERSION,
    }


def _scalar(value: Any) -> float | None:
    """Convert a numeric scalar without accepting schema-coercing values.

    JSON documents use numeric values for lengths and tolerances.  In
    particular, accepting ``"2.0"`` or ``True`` here would make malformed
    persisted documents appear valid after an implicit conversion.
    """

    try:
        array = np.asarray(value)
        if array.ndim != 0:
            return None
        if array.dtype.kind not in "iuf":
            return None
        result = float(array)
    except (TypeError, ValueError, OverflowError):
        return None
    return result


def _edge_normals(polygon: np.ndarray) -> np.ndarray:
    """Return unit normals for all four edges of one polygon."""

    edges = np.roll(polygon, -1, axis=0) - polygon
    # A valid square has unit-length edges.  Keep the normalization explicit so
    # the SAT path is independent of the vertex scale and ordering.
    normals = np.stack((-edges[:, 1], edges[:, 0]), axis=-1)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        lengths = np.linalg.norm(normals, axis=1)
        normalized = normals / lengths[:, None]
    if not bool(np.isfinite(lengths).all()) or not bool(np.isfinite(normalized).all()):
        raise ValueError("polygon edge normals are not finite")
    if bool((lengths <= 0.0).any()):
        raise ValueError("polygon edge normals are degenerate")
    return normalized


def _pair_separation(first: np.ndarray, second: np.ndarray) -> float:
    """Return the signed polygon SAT separation for one pair.

    On each candidate edge-normal axis, the interval gap is positive for a
    separating interval, zero for contact, and negative for overlap.  The
    maximum over all axes is the SAT signed separation: non-negative means the
    polygon interiors are disjoint, while a negative value estimates the
    shallowest penetration depth as viewed by this SAT test.
    """

    axes = np.concatenate((_edge_normals(first), _edge_normals(second)), axis=0)
    if not bool(np.isfinite(axes).all()):
        raise ValueError("polygon separating axes are not finite")
    best_gap = -np.inf
    for axis in axes:
        with np.errstate(over="ignore", invalid="ignore"):
            first_projection = first @ axis
            second_projection = second @ axis
        if not bool(np.isfinite(first_projection).all()) or not bool(np.isfinite(second_projection).all()):
            raise ValueError("polygon projections are not finite")
        gap = max(
            float(second_projection.min() - first_projection.max()),
            float(first_projection.min() - second_projection.max()),
        )
        if not np.isfinite(gap):
            raise ValueError("polygon separation is not finite")
        if gap > best_gap:
            best_gap = gap
    return float(best_gap)


def validate_pose(poses: Any, side: Any, tolerance: float = 1e-8) -> dict[str, Any]:
    """Validate unit-square containment and pairwise separation in float64.

    ``side`` is the side length of the centred square container.  Every
    returned value is composed of Python scalars, ``None``, booleans, or
    strings, so the dictionary can be passed directly to ``json.dumps``.

    Status policy:

    * ``NUMERICALLY_VALIDATED`` requires every pair SAT separation and wall
      clearance to be strictly greater than ``tolerance``.
    * ``INDETERMINATE`` means all clearances are at least ``-tolerance`` but
      at least one is at or below ``tolerance``.  Exact contacts therefore
      remain visibly distinct from positive-clearance poses.
    * ``INVALID`` covers larger violations, non-finite data, malformed poses,
      non-positive/non-finite side lengths, and invalid tolerances.

    The pair metric is computed from projections of reconstructed vertices on
    edge-normal axes.  ``max_penetration`` is the largest of the SAT overlap
    estimate and any wall violation; the wall clearance remains available
    separately in ``min_wall_clearance``.
    """

    tolerance_value = _scalar(tolerance)
    if tolerance_value is None:
        return _invalid_result(None)

    # Keep the caller's numeric tolerance in the result even when it is
    # invalid, while avoiding NaN/Inf in a JSON record.
    if not np.isfinite(tolerance_value):
        return _invalid_result(None)

    try:
        pose_array = _pose_array(poses)
    except ValueError:
        return _invalid_result(tolerance_value)

    has_nonfinite = not bool(np.isfinite(pose_array).all())
    if has_nonfinite:
        return _invalid_result(tolerance_value, nonfinite=True)
    if tolerance_value < 0.0 or pose_array.shape[0] < 1:
        return _invalid_result(tolerance_value)

    side_value = _scalar(side)
    if side_value is None or not np.isfinite(side_value) or side_value <= 0.0:
        return _invalid_result(tolerance_value)

    square_vertices = vertices(pose_array)
    if not bool(np.isfinite(square_vertices).all()):
        # This is defensive for unusual NumPy/platform behavior in trig
        # evaluation; it also guarantees that no non-finite metric escapes.
        return _invalid_result(tolerance_value, nonfinite=True)

    # At sufficiently large offsets, adding the half-unit vertex offsets to a
    # float64 center rounds them away.  Such a pose still has finite input
    # fields, but its reconstructed polygon no longer represents a unit square.
    # Reject it before the SAT path can normalize zero/overflowed edges.
    with np.errstate(over="ignore", invalid="ignore"):
        edges = np.roll(square_vertices, -1, axis=1) - square_vertices
        edge_lengths = np.linalg.norm(edges, axis=2)
    if not bool(np.isfinite(edge_lengths).all()):
        return _invalid_result(tolerance_value, nonfinite=True)
    if not bool(np.all(np.isclose(edge_lengths, 1.0,
                                  rtol=_UNIT_EDGE_TOLERANCE,
                                  atol=_UNIT_EDGE_TOLERANCE))):
        return _invalid_result(tolerance_value)

    half_side = 0.5 * side_value
    wall_clearances = half_side - np.abs(square_vertices)
    if not bool(np.isfinite(wall_clearances).all()):
        return _invalid_result(tolerance_value, nonfinite=True)
    min_wall_clearance = float(wall_clearances.min())

    pair_separations: list[float] = []
    for first_index in range(square_vertices.shape[0] - 1):
        first = square_vertices[first_index]
        for second_index in range(first_index + 1, square_vertices.shape[0]):
            try:
                separation = _pair_separation(first, square_vertices[second_index])
            except ValueError:
                return _invalid_result(tolerance_value, nonfinite=True)
            pair_separations.append(separation)

    if pair_separations:
        min_pair_separation: float | None = float(min(pair_separations))
        pair_penetration = max(0.0, -min_pair_separation)
    else:
        min_pair_separation = None
        pair_penetration = 0.0

    wall_penetration = max(0.0, -min_wall_clearance)
    max_penetration = float(max(pair_penetration, wall_penetration))

    clearances = pair_separations + [min_wall_clearance]
    if any(clearance < -tolerance_value for clearance in clearances):
        status = "INVALID"
    elif all(clearance > tolerance_value for clearance in clearances):
        status = "NUMERICALLY_VALIDATED"
    else:
        status = "INDETERMINATE"

    return {
        "status": status,
        "min_pair_separation": min_pair_separation,
        "max_penetration": max_penetration,
        "min_wall_clearance": min_wall_clearance,
        "nonfinite": False,
        "tolerance": float(tolerance_value),
        "validator_version": VALIDATOR_VERSION,
    }


def validate_document(document: Any, tolerance: float = 1e-8) -> dict[str, Any]:
    """Validate a persisted pose document without trusting its declared ``n``.

    A document must be a mapping with an integer, non-boolean ``n`` from 1
    through 32, a ``poses`` value whose outer length is exactly ``n``, and a
    ``side`` value.  The length check happens before the geometry validator is
    called, so a document cannot silently validate a prefix or ignore extra
    poses.  Malformed documents use the normal diagnostic fields and add a
    JSON-serializable ``error`` string.
    """

    tolerance_value = _scalar(tolerance)
    if tolerance_value is None or not np.isfinite(tolerance_value):
        result = _invalid_result(None)
        result["error"] = "tolerance must be a finite scalar"
        return result

    def invalid(error: str, *, nonfinite: bool = False) -> dict[str, Any]:
        result = _invalid_result(float(tolerance_value), nonfinite=nonfinite)
        result["error"] = error
        return result

    if not isinstance(document, Mapping):
        return invalid("document must be a mapping")

    if "n" not in document:
        return invalid("document is missing required field 'n'")
    declared_n = document["n"]
    if isinstance(declared_n, bool) or not isinstance(declared_n, Integral):
        return invalid("document field 'n' must be an integer in [1, 32]")
    n = int(declared_n)
    if not 1 <= n <= 32:
        return invalid("document field 'n' must be an integer in [1, 32]")

    if "poses" not in document:
        return invalid("document is missing required field 'poses'")
    poses = document["poses"]
    try:
        pose_count = len(poses)
    except (TypeError, ValueError):
        return invalid("document field 'poses' must have length n")
    if pose_count != n:
        return invalid(f"document field 'poses' length {pose_count} does not match n={n}")

    if "side" not in document:
        return invalid("document is missing required field 'side'")

    result = validate_pose(poses, document["side"], tolerance=float(tolerance_value))
    if result["status"] == "INVALID":
        if result["nonfinite"]:
            result["error"] = "document poses contain non-finite values"
        else:
            try:
                _pose_array(poses)
            except ValueError as exc:
                result["error"] = str(exc)
            else:
                side_value = _scalar(document["side"])
                if side_value is None or not np.isfinite(side_value) or side_value <= 0.0:
                    result["error"] = "document field 'side' must be positive and finite"
                else:
                    result["error"] = "document geometry or tolerance is invalid"
    return result
