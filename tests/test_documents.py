"""Tests for strict validation of persisted pose documents."""

from __future__ import annotations

import json
from types import MappingProxyType

import pytest

from asquerix.geometry import validate_document


def valid_document() -> dict:
    poses = [
        ((column - 1.5) * 1.4, (row - 1.0) * 1.4, 0.0)
        for row in range(3)
        for column in range(4)
    ]
    return {"n": 12, "side": 10.0, "poses": poses}


def test_valid_document_uses_exact_pose_count_and_validates_geometry() -> None:
    result = validate_document(MappingProxyType(valid_document()))

    assert result["status"] == "NUMERICALLY_VALIDATED"
    assert result["nonfinite"] is False
    assert "error" not in result
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("delta", (-1, 1), ids=("removed-pose", "extra-pose"))
def test_document_rejects_removed_or_extra_poses(delta: int) -> None:
    document = valid_document()
    if delta < 0:
        document["poses"] = document["poses"][:-1]
    else:
        document["poses"] = document["poses"] + [(0.0, 0.0, 0.0)]

    result = validate_document(document)

    assert result["status"] == "INVALID"
    assert result["min_pair_separation"] is None
    assert result["min_wall_clearance"] is None
    assert "poses" in result["error"]
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("declared_n", (True, False, 12.0, 0, 33, "12"))
def test_document_rejects_non_integer_boolean_or_out_of_range_n(declared_n) -> None:
    document = valid_document()
    document["n"] = declared_n

    result = validate_document(document)

    assert result["status"] == "INVALID"
    assert "n" in result["error"]


def test_document_rejects_nonfinite_pose_with_diagnostic() -> None:
    document = valid_document()
    document["poses"][0] = (float("nan"), 0.0, 0.0)

    result = validate_document(document)

    assert result["status"] == "INVALID"
    assert result["nonfinite"] is True
    assert "non-finite" in result["error"]
    json.dumps(result, allow_nan=False)


def test_document_rejects_malformed_mapping_and_missing_fields() -> None:
    non_mapping = validate_document([("n", 1)])
    missing_poses = validate_document({"n": 1, "side": 2.0})
    malformed_pose = validate_document({"n": 1, "side": 2.0, "poses": [[0.0, 0.0]]})

    assert non_mapping["status"] == "INVALID"
    assert "mapping" in non_mapping["error"]
    assert missing_poses["status"] == "INVALID"
    assert "poses" in missing_poses["error"]
    assert malformed_pose["status"] == "INVALID"
    assert "shape" in malformed_pose["error"]
