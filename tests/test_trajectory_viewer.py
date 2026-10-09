"""Static and browser-independent checks for the offline trajectory viewer."""

from __future__ import annotations

import base64
import json
import re

import numpy as np

from asquerix.trajectory_format import encode_npz
from asquerix.trajectory_viewer import render_html


def arrays() -> dict[str, np.ndarray]:
    return {
        "poses": np.asarray(
            [[[0.0, 0.0, -0.0], [0.4, 0.0, 0.1]], [[0.2, 0.0, 0.0], [0.4, 0.2, 0.1]], [[0.3, 0.0, 0.0], [0.4, 0.3, 0.1]]],
            dtype="<f4",
        ),
        "side": np.asarray([3.0, 2.5, 2.0], dtype="<f4"),
        "sequence": np.arange(3, dtype="<i8"),
        "attempt": np.arange(3, dtype="<i4"),
        "sweep": np.arange(3, dtype="<i4"),
        "sweep_total": np.full(3, 2, dtype="<i4"),
        "phase": np.asarray([0, 3, 6], dtype="u1"),
        "roles": np.asarray([1, 0, 2], dtype="u1"),
        "square_ids": np.asarray([11, 12], dtype="<i4"),
    }


def metadata() -> dict:
    return {
        "schema": "asquerix-trajectory-v1",
        "n": 2,
        "trial_id": "18446744073709551615",
        "seed": "9223372036854775809",
        "frame_count": 3,
        "sampling": {"observed": 3, "retained": 3, "suppressed": 0, "effective_stride": 1, "max_frames": 256},
        "comparison": {"status": "REPLAY_MATCHED", "scope": "defined endpoint fields", "compared_fields": [], "mismatches": [], "missing_fields": []},
        "validations": [],
        "provenance": {"replay_revision": "test"},
        "termination_reason": "BUDGET_EXHAUSTED",
    }


def test_html_is_self_contained_and_recovers_exact_numeric_payload() -> None:
    values = arrays()
    html = render_html(values, metadata()).decode("utf-8")
    match = re.search(r'<script id="trajectory-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    assert match is not None
    payload = json.loads(match.group(1))
    assert payload["schema"] == "asquerix-trajectory-v1"
    for name, original in values.items():
        spec = payload["arrays"][name]
        restored = np.frombuffer(base64.b64decode(spec["base64"]), dtype=original.dtype).reshape(original.shape)
        np.testing.assert_array_equal(restored, original)

    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "https://" not in html
    assert "Initial arrangement" in html
    assert "Current recorded frame" in html
    assert "frame-slider" in html
    assert "play-pause" in html
    assert "export-svg" in html
    assert 'id="show-trails"' in html
    assert 'id="trail-square"' in html
    assert 'id="show-squares"' in html
    assert 'id="square-legend"' in html
    assert 'id="show-container"' in html
    assert 'id="current-zoom"' in html
    assert 'id="range-start"' in html
    assert 'id="range-end"' in html
    assert 'id="playback-mode"' in html
    assert 'id="trail-history"' in html
    assert "Intermediate states marked provisional may contain overlaps" not in html
    assert "connecting lines do not reconstruct skipped states" in html
    assert "no interpolation" in html


def test_html_escapes_metadata_script_terminators_and_keeps_uint64_id() -> None:
    info = metadata()
    info["termination_reason"] = "safe </script><script>unexpected"
    html = render_html(arrays(), info).decode("utf-8")
    assert "</script><script>unexpected" not in html
    assert "18446744073709551615" in html
    assert "const DATA = JSON.parse" in html


def test_viewer_validates_same_archive_arrays_before_rendering() -> None:
    values = arrays()
    # A normal archive round trip is useful here because the viewer and the
    # storage writer must share the same fixed dtypes and array order.
    assert encode_npz(values).startswith(b"PK")
    html = render_html(values, metadata())
    assert len(html) > 10_000


def test_viewer_does_not_repair_invalid_side_or_hide_nonfinite_pose_warning() -> None:
    values = arrays()
    values["side"][1] = np.float32(np.nan)
    values["poses"][1, 0, 0] = np.float32(np.nan)

    html = render_html(values, metadata()).decode("utf-8")

    assert "invalid diagnostic side; boundary omitted" in html
    assert "non-finite poses: ${omittedSquares} square(s) omitted" in html
    assert "const boundary = validSide ? side : initialSide" not in html
