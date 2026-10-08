"""Sparse offline output and reporting for compression experiments.

The functions in this module consume compact trial records and retained pose
documents.  They do not run a search or repair a pose.  In particular, a
rendered image is a view of the coordinates supplied by the caller: the
square side remains one and the container side is taken from the document.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import html
import json
import math
from pathlib import Path
import re
from typing import Any
from time import perf_counter

import numpy as np

from .geometry import vertices
from .persistence import write_json


_SVG_WIDTH = 900
_SVG_HEIGHT = 900
_SVG_MARGIN = 76
_VALIDATION_STATUSES = {
    "NUMERICALLY_VALIDATED",
    "INDETERMINATE",
    "INVALID",
    "NOT_CHECKED",
}


def _json_value(value: Any) -> Any:
    """Convert common NumPy/path values to strict-JSON-compatible values."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return _json_value(value.tolist())
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def _as_finite_float(value: Any) -> float | None:
    """Return a finite scalar as a Python float, or ``None``."""

    try:
        converted = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return converted if math.isfinite(converted) else None


def _exact_integer(value: Any) -> int | None:
    """Return an integer identifier without passing it through ``float``.

    Trial identifiers are global stream keys and may use the full range of a
    signed or unsigned 64-bit value (or a larger Python integer).  Converting
    one of those values to float would collapse distinct IDs above 2**53.
    Integer strings are accepted because JSON/configuration loaders sometimes
    preserve a large identifier as text.
    """

    if isinstance(value, (bool, np.bool_)):
        return None
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if re.fullmatch(r"[+-]?\d+", text):
            try:
                return int(text, 10)
            except ValueError:
                return None
    return None


def _positive_side(value: Any) -> float | None:
    converted = _as_finite_float(value)
    return converted if converted is not None and converted > 0.0 else None


def _format_number(value: Any) -> str:
    """Format a scalar without making SVG labels appear artificially exact."""

    converted = _as_finite_float(value)
    if converted is None:
        return str(value)
    return format(converted, ".17g")


def _trial_id(document: Mapping[str, Any], fallback: Any = None) -> Any:
    return document.get("trial_id", fallback)


def _id_token(value: Any) -> tuple[str, Any]:
    """Return a stable, hashable identifier token for selection deduplication."""

    integer = _exact_integer(value)
    if integer is not None:
        return ("integer", integer)
    number = _as_finite_float(value)
    if number is not None and number.is_integer():
        return ("integer", int(number))
    if value is None:
        return ("missing", "")
    return ("text", str(value))


def _sort_trial(value: Any) -> tuple[int, Any]:
    integer = _exact_integer(value)
    if integer is not None:
        return (0, integer)
    number = _as_finite_float(value)
    if number is not None:
        if number.is_integer():
            return (0, int(number))
        return (1, number)
    return (2, str(value))


def _safe_filename_id(value: Any) -> str:
    integer = _exact_integer(value)
    if integer is not None:
        label = str(integer)
    else:
        number = _as_finite_float(value)
        if number is not None and number.is_integer():
            label = str(int(number))
        elif value is None:
            label = "unknown"
        else:
            label = str(value)
    label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("._")
    return label or "unknown"


def _document_status(document: Mapping[str, Any]) -> str:
    validation = document.get("validation")
    if isinstance(validation, Mapping) and validation.get("status") is not None:
        raw = validation.get("status")
    else:
        raw = document.get("validation_status", "NOT_CHECKED")
    if raw is None:
        return "NOT_CHECKED"
    status = str(raw).upper()
    return status if status in _VALIDATION_STATUSES else "INVALID"


def _pose_array(document: Mapping[str, Any]) -> np.ndarray | None:
    """Return a finite ``(n, 3)`` pose array for rendering, if possible."""

    try:
        array = np.asarray(document.get("poses"), dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if array.ndim != 2 or array.shape[1] != 3 or not np.isfinite(array).all():
        return None
    return array


def _xml_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_pose(document: dict, path: Path) -> Path:
    """Render one retained pose document as an equal-scale offline SVG.

    ``document`` must contain ``poses`` as ``[[x, y, theta], ...]`` and a
    positive ``side`` for a geometrically meaningful drawing.  Malformed or
    independently invalid documents still produce an explicitly labelled
    ``INVALID DEBUG`` view, which is useful when inspecting failed trials.
    """

    if not isinstance(document, Mapping):
        raise TypeError("document must be a mapping")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_side = document.get("side")
    side = _positive_side(raw_side)
    pose_array = _pose_array(document)
    status = _document_status(document)
    invalid_debug = (status == "INVALID" or side is None or pose_array is None
                     or document.get("n") != (pose_array.shape[0] if pose_array is not None else None))
    display_status = "INVALID DEBUG" if invalid_debug else status
    drawing_side = side if side is not None else 1.0
    scale = (_SVG_WIDTH - 2.0 * _SVG_MARGIN) / drawing_side

    trial = _trial_id(document, "unknown")
    n_value = document.get("n", pose_array.shape[0] if pose_array is not None else 0)
    side_label = _format_number(raw_side) if side is not None else "invalid"
    status_class = {
        "NUMERICALLY_VALIDATED": "validated",
        "INDETERMINATE": "indeterminate",
        "INVALID": "invalid",
        "NOT_CHECKED": "unchecked",
    }.get(status, "unknown")

    def map_point(point: Sequence[float]) -> tuple[float, float]:
        return (
            _SVG_MARGIN + (float(point[0]) + drawing_side / 2.0) * scale,
            _SVG_MARGIN + (drawing_side / 2.0 - float(point[1])) * scale,
        )

    body: list[str] = []
    body.append(f'<rect width="{_SVG_WIDTH}" height="{_SVG_HEIGHT}" fill="white"/>')
    body.append(
        f'<rect class="container" x="{_SVG_MARGIN:g}" y="{_SVG_MARGIN:g}" '
        f'width="{_SVG_WIDTH - 2 * _SVG_MARGIN:g}" '
        f'height="{_SVG_HEIGHT - 2 * _SVG_MARGIN:g}"/>'
    )

    if pose_array is not None and side is not None:
        square_vertices = vertices(pose_array)
        for index, polygon in enumerate(square_vertices):
            points = " ".join(
                f"{x:.17g},{y:.17g}" for x, y in (map_point(point) for point in polygon)
            )
            raw_pose = " ".join(_format_number(item) for item in pose_array[index])
            body.append(
                f'<polygon class="square" id="square-{index}" points="{points}" '
                f'data-pose="{_xml_text(raw_pose)}"/>'
            )

    # Keep the machine-readable pose values in the SVG metadata as well as in
    # the polygon transform.  This does not replace the durable pose document;
    # it makes a capped, offline artifact auditable on its own.
    metadata = {
        "trial_id": _json_value(trial),
        "n": _json_value(n_value),
        "side": _json_value(raw_side),
        "poses": _json_value(document.get("poses")),
        "validation_status": status,
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    body.append(f"<metadata>{_xml_text(metadata_json)}</metadata>")
    body.append(
        f'<text class="title" x="{_SVG_MARGIN:g}" y="28">'
        f"trial_id={_xml_text(trial)} | n={_xml_text(n_value)} | side={_xml_text(side_label)}</text>"
    )
    body.append(
        f'<text class="status {status_class}" x="{_SVG_MARGIN:g}" '
        f'y="{_SVG_HEIGHT - 32:g}">validation={_xml_text(display_status)}</text>'
    )

    svg = "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{_SVG_WIDTH}" '
            f'height="{_SVG_HEIGHT}" viewBox="0 0 {_SVG_WIDTH} {_SVG_HEIGHT}" '
            'preserveAspectRatio="xMidYMid meet">',
            "<title>Asquerix square compression pose</title>",
            "<style>",
            ".container{fill:none;stroke:#222;stroke-width:2}",
            ".square{fill:#4e79a7;fill-opacity:.32;stroke:#174a7e;stroke-width:1.25}",
            ".title,.status{font-family:monospace;font-size:16px;fill:#111}",
            ".status.validated{fill:#18794e}.status.indeterminate{fill:#9a6700}",
            ".status.invalid{fill:#b42318;font-weight:bold}.status.unchecked{fill:#555}",
            ".status.unknown{fill:#b42318;font-weight:bold}",
            "</style>",
            *body,
            "</svg>",
        )
    )
    output_path.write_text(svg + "\n", encoding="utf-8")
    return output_path


def render_selected(documents: list[dict], directory: Path, max_images: int) -> list[Path]:
    """Render a deterministic, de-duplicated, capped set of pose documents.

    Selection order is ascending ``(side, trial_id)``.  When a trial is
    present more than once, the first item in that order is retained, so a
    smaller actual side wins ties between selection rules.  The input
    documents are never modified.
    """

    if isinstance(max_images, bool) or not isinstance(max_images, (int, np.integer)):
        raise TypeError("max_images must be an integer")
    if max_images < 0:
        raise ValueError("max_images must be non-negative")
    output_directory = Path(directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    indexed: list[tuple[tuple[Any, ...], int, Mapping[str, Any]]] = []
    for index, document in enumerate(documents):
        if not isinstance(document, Mapping):
            raise TypeError("documents must contain mappings")
        side = _positive_side(document.get("side"))
        side_key = (0, side) if side is not None else (1, math.inf)
        trial = _trial_id(document, index)
        indexed.append((side_key + (_sort_trial(trial), index), index, document))
    indexed.sort(key=lambda item: item[0])

    paths: list[Path] = []
    seen: set[tuple[str, Any]] = set()
    used_filenames: set[str] = set()
    for _, fallback_index, document in indexed:
        trial = _trial_id(document, None)
        token = _id_token(trial) if trial is not None else ("missing", fallback_index)
        if token in seen:
            continue
        seen.add(token)
        if len(paths) >= int(max_images):
            break
        filename_stem = _safe_filename_id(trial if trial is not None else fallback_index)
        filename = f"trial-{filename_stem}.svg"
        suffix = 2
        while filename in used_filenames:
            filename = f"trial-{filename_stem}-{suffix}.svg"
            suffix += 1
        used_filenames.add(filename)
        paths.append(render_pose(dict(document), output_directory / filename))
    return paths


def _record_validation_status(record: Mapping[str, Any]) -> str:
    raw = record.get("validation_status")
    if raw is None and isinstance(record.get("validation"), Mapping):
        raw = record["validation"].get("status")
    if raw is None:
        return "NOT_CHECKED"
    status = str(raw).upper()
    return status if status in _VALIDATION_STATUSES else "INVALID"


def _record_side(record: Mapping[str, Any]) -> float | None:
    side = _positive_side(record.get("side"))
    return side


def _record_counter(record: Mapping[str, Any], key: str) -> float:
    value = _as_finite_float(record.get(key, 0.0))
    return value if value is not None else 0.0


def _side_statistics(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        empty = {
            "count": 0,
            "best": None,
            "min": None,
            "max": None,
            "worst": None,
            "mean": None,
            "median": None,
            "q05": None,
            "q25": None,
            "q75": None,
            "q95": None,
        }
        empty["quantiles"] = {key: None for key in ("q05", "q25", "q50", "q75", "q95")}
        return empty
    array = np.asarray(values, dtype=np.float64)
    quantiles = np.quantile(array, (0.05, 0.25, 0.50, 0.75, 0.95))
    q05, q25, q50, q75, q95 = (float(item) for item in quantiles)
    return {
        "count": int(array.size),
        "best": float(array.min()),
        "min": float(array.min()),
        "max": float(array.max()),
        "worst": float(array.max()),
        "mean": float(array.mean()),
        "median": q50,
        "q05": q05,
        "q25": q25,
        "q75": q75,
        "q95": q95,
        "quantiles": {"q05": q05, "q25": q25, "q50": q50, "q75": q75, "q95": q95},
    }


def _histogram(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "edges": [], "counts": []}
    array = np.asarray(values, dtype=np.float64)
    if np.all(array == array[0]):
        half_width = max(abs(float(array[0])) * 1e-6, 1e-6)
        edges = np.asarray((array[0] - half_width, array[0] + half_width), dtype=np.float64)
    else:
        bin_count = max(1, min(20, int(math.ceil(math.log2(array.size) + 1.0))))
        _, edges = np.histogram(array, bins=bin_count)
    counts, edges = np.histogram(array, bins=edges)
    return {
        "count": int(array.size),
        "edges": [float(item) for item in edges],
        "counts": [int(item) for item in counts],
    }


def _throughput_metrics(
    seconds_value: Any,
    attempted_trials: int,
    gpu_feasible_trials: int,
    interval_description: str,
) -> dict[str, Any]:
    """Calculate amortized rates for one measured timing interval."""

    seconds = _as_finite_float(seconds_value)
    if seconds is None or seconds <= 0.0:
        attempted_rate = None
        feasible_rate = None
    else:
        attempted_rate = float(attempted_trials / seconds)
        feasible_rate = float(gpu_feasible_trials / seconds)
    return {
        "seconds": seconds,
        "attempted_trials_per_second": attempted_rate,
        "gpu_feasible_trials_per_second": feasible_rate,
        "meaning": (
            f"Amortized throughput over the {interval_description}; "
            "not individual-trial latency."
        ),
    }


def summarize(records: list[dict], timings: dict) -> dict:
    """Summarize real trial records without conflating acceptance and audit."""

    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not isinstance(timings, Mapping):
        raise TypeError("timings must be a mapping")

    gpu_status_counts: dict[str, int] = {}
    validation_status_counts: dict[str, int] = {}
    termination_counts: dict[str, int] = {}
    gpu_sides: list[float] = []
    validated_sides: list[float] = []
    counters = {key: 0.0 for key in ("attempts", "sweeps", "rejected", "accepted")}
    iteration_values = {key: [] for key in ("attempts", "sweeps")}

    for record in records:
        if not isinstance(record, Mapping):
            raise TypeError("records must contain mappings")
        gpu_status = str(record.get("gpu_status", "NO_ACCEPTED_POSE")).upper()
        validation_status = _record_validation_status(record)
        termination = str(record.get("termination_reason", "UNKNOWN")).upper()
        gpu_status_counts[gpu_status] = gpu_status_counts.get(gpu_status, 0) + 1
        validation_status_counts[validation_status] = validation_status_counts.get(validation_status, 0) + 1
        termination_counts[termination] = termination_counts.get(termination, 0) + 1
        side = _record_side(record)
        if gpu_status == "GPU_FEASIBLE" and side is not None:
            gpu_sides.append(side)
        if (
            gpu_status == "GPU_FEASIBLE"
            and validation_status == "NUMERICALLY_VALIDATED"
            and side is not None
        ):
            validated_sides.append(side)
        for key in counters:
            counters[key] += _record_counter(record, key)
        for key, values in iteration_values.items():
            if key in record:
                metric = _as_finite_float(record[key])
                if metric is not None:
                    values.append(metric)

    total = len(records)
    gpu_feasible = gpu_status_counts.get("GPU_FEASIBLE", 0)
    no_accepted = gpu_status_counts.get("NO_ACCEPTED_POSE", 0)
    not_checked = validation_status_counts.get("NOT_CHECKED", 0)
    audited = total - not_checked
    budget_exhausted = termination_counts.get("BUDGET_EXHAUSTED", 0)
    init_failed = termination_counts.get("INIT_FAILED", 0)
    numerical_failed = termination_counts.get("NUMERICAL_FAILURE", 0)

    histogram_gpu = _histogram(gpu_sides)
    histogram_gpu["population"] = "GPU_FEASIBLE"
    histogram_validated = _histogram(validated_sides)
    histogram_validated["population"] = "GPU_FEASIBLE + NUMERICALLY_VALIDATED"
    throughput: dict[str, Any] = {}
    timing_intervals = (
        ("simulation_seconds", "synchronized simulation interval"),
        ("device_seconds", "synchronized device timing interval"),
        ("end_to_end_seconds", "end-to-end wall-clock interval"),
    )
    for timing_key, interval_description in timing_intervals:
        if timing_key in timings:
            throughput[timing_key] = _throughput_metrics(
                timings[timing_key], total, gpu_feasible, interval_description
            )

    summary = {
        "record_count": total,
        "attempted_trials": total,
        "gpu_status_counts": dict(sorted(gpu_status_counts.items())),
        "validation_status_counts": dict(sorted(validation_status_counts.items())),
        "termination_counts": dict(sorted(termination_counts.items())),
        "accepted_trials": gpu_feasible,
        "no_accepted_pose_trials": no_accepted,
        "failure_counts": {
            "total": no_accepted,
            "no_accepted_pose": no_accepted,
            "initialization_failed": init_failed,
            "numerical_failure": numerical_failed,
            "budget_exhausted": budget_exhausted,
        },
        "audit_coverage": {
            "total_trials": total,
            "audited_trials": audited,
            "not_checked_trials": not_checked,
            "coverage_fraction": float(audited / total) if total else 0.0,
            "numerically_validated_trials": validation_status_counts.get("NUMERICALLY_VALIDATED", 0),
            "indeterminate_trials": validation_status_counts.get("INDETERMINATE", 0),
            "invalid_trials": validation_status_counts.get("INVALID", 0),
        },
        "counters": {key: int(value) if value.is_integer() else value for key, value in counters.items()},
        "iteration_statistics": {
            "attempts": _side_statistics(iteration_values["attempts"]),
            "sweeps": _side_statistics(iteration_values["sweeps"]),
        },
        "statistics": {
            "gpu_accepted": _side_statistics(gpu_sides),
            "numerically_validated": _side_statistics(validated_sides),
        },
        "histogram": {
            "gpu_accepted": histogram_gpu,
            "numerically_validated": histogram_validated,
        },
        "throughput": throughput,
        "timings": _json_value(timings),
    }
    return _json_value(summary)


def _report_number(value: Any) -> str:
    if value is None:
        return "—"
    converted = _as_finite_float(value)
    return format(converted, ".12g") if converted is not None else str(value)


def _histogram_svg(histograms: Mapping[str, Any]) -> str:
    width, height = 1100, 610
    panels = (
        ("gpu_accepted", "GPU-accepted final sides"),
        (
            "numerically_validated",
            "Independently validated selected subset",
        ),
    )
    fragments: list[str] = []
    for panel_index, (key, title) in enumerate(panels):
        histogram = histograms.get(key, {})
        edges = histogram.get("edges", [])
        counts = histogram.get("counts", [])
        left = 45 + panel_index * 535
        plot_left, plot_top = left + 58, 92
        plot_width, plot_height = 430, 400
        fragments.append(f'<g class="panel" id="{key}">')
        fragments.append(f'<text class="panel-title" x="{left + 8}" y="48">{_xml_text(title)}</text>')
        predicate = "GPU_FEASIBLE" if key == "gpu_accepted" else "GPU_FEASIBLE + NUMERICALLY_VALIDATED"
        fragments.append(f'<text class="predicate" x="{left + 8}" y="70">{predicate}</text>')
        fragments.append(
            f'<line class="axis" x1="{plot_left}" y1="{plot_top + plot_height}" '
            f'x2="{plot_left + plot_width}" y2="{plot_top + plot_height}"/>'
        )
        fragments.append(
            f'<line class="axis" x1="{plot_left}" y1="{plot_top}" '
            f'x2="{plot_left}" y2="{plot_top + plot_height}"/>'
        )
        if edges and counts:
            minimum, maximum = float(edges[0]), float(edges[-1])
            span = maximum - minimum
            if span <= 0.0:
                span = 1.0
            top_count = max(int(item) for item in counts) or 1
            fragments.append(f'<text class="tick" text-anchor="end" x="{plot_left - 8}" y="{plot_top + 8}">{top_count}</text>')
            fragments.append(f'<text class="tick" text-anchor="end" x="{plot_left - 8}" y="{plot_top + plot_height}">0</text>')
            for index, count in enumerate(counts):
                x0 = plot_left + (float(edges[index]) - minimum) / span * plot_width
                x1 = plot_left + (float(edges[index + 1]) - minimum) / span * plot_width
                bar_height = int(count) / top_count * plot_height
                y = plot_top + plot_height - bar_height
                fragments.append(
                    f'<rect class="bar" x="{x0:.6g}" y="{y:.6g}" '
                    f'width="{max(x1 - x0, 0.5):.6g}" height="{bar_height:.6g}" '
                    f'data-count="{int(count)}"/>'
                )
            fragments.append(
                f'<text class="tick" x="{plot_left}" y="{plot_top + plot_height + 24}">'
                f"{_xml_text(_report_number(minimum))}</text>"
            )
            fragments.append(
                f'<text class="tick" text-anchor="end" x="{plot_left + plot_width}" '
                f'y="{plot_top + plot_height + 24}">{_xml_text(_report_number(maximum))}</text>'
            )
            fragments.append(
                f'<text class="count" x="{left + 8}" y="{plot_top + plot_height + 58}">'
                f'n={int(histogram.get("count", sum(counts)))}</text>'
            )
        else:
            fragments.append(
                f'<text class="empty" x="{plot_left + plot_width / 2:g}" '
                f'y="{plot_top + plot_height / 2:g}" text-anchor="middle">No values</text>'
            )
        fragments.append("</g>")
    return "\n".join(
        (
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
            "<title>Final accepted container-side histograms</title>",
            f'<rect width="{width}" height="{height}" fill="white"/>',
            "<style>.axis{stroke:#444}.bar{fill:#4e79a7;fill-opacity:.78}.panel-title,.tick,.count,.empty,.predicate{font-family:monospace;font-size:16px;fill:#111}.predicate{font-size:12px}.empty{fill:#777}.panel-title{font-weight:bold}</style>",
            *fragments,
            "</svg>",
        )
    ) + "\n"


def _report_markdown(summary: Mapping[str, Any], metadata: Any = None) -> str:
    statistics = summary["statistics"]
    iteration_statistics = summary["iteration_statistics"]
    coverage = summary["audit_coverage"]
    failure = summary["failure_counts"]
    report_name = None
    if isinstance(metadata, Mapping):
        report_name = metadata.get("experiment") or metadata.get("experiment_name")
    title = f"# {report_name} compression run report" if report_name else "# Compression run report"
    lines = [
        title,
        "",
        "This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.",
        "",
        "## Outcome",
        "",
        f"- Attempted trials: {summary['attempted_trials']}",
        f"- GPU-feasible trials: {summary['accepted_trials']}",
        f"- Trials without an accepted pose: {summary['no_accepted_pose_trials']}",
        f"- Budget-exhausted trials: {failure['budget_exhausted']}",
        f"- Other initialization failures: {failure['initialization_failed']}",
        f"- Numerical failures: {failure['numerical_failure']}",
        "",
        "## Container-side statistics",
        "",
        "| subset | count | best | median | q05 | q95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, key in (
        ("GPU accepted", "gpu_accepted"),
        ("Independently numerically validated", "numerically_validated"),
    ):
        stats = statistics[key]
        lines.append(
            f"| {label} | {stats['count']} | {_report_number(stats['best'])} | "
            f"{_report_number(stats['median'])} | {_report_number(stats['q05'])} | "
            f"{_report_number(stats['q95'])} |"
        )
    lines.extend(
        (
            "",
            "## Solver iteration statistics",
            "",
            "| metric | count | min | median | q95 | max |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        )
    )
    for label, key in (("Attempts", "attempts"), ("Sweeps", "sweeps")):
        stats = iteration_statistics[key]
        lines.append(
            f"| {label} | {stats['count']} | {_report_number(stats['min'])} | "
            f"{_report_number(stats['median'])} | {_report_number(stats['q95'])} | "
            f"{_report_number(stats['max'])} |"
        )
    lines.extend(
        (
            "",
            "## Independent validation coverage",
            "",
            f"- Audited trials: {coverage['audited_trials']} / {coverage['total_trials']} ({coverage['coverage_fraction']:.3f})",
            f"- Numerically validated: {coverage['numerically_validated_trials']}",
            f"- Indeterminate: {coverage['indeterminate_trials']}",
            f"- Invalid: {coverage['invalid_trials']}",
            f"- Not checked: {coverage['not_checked_trials']}",
            "",
            "## Termination reasons",
            "",
        )
    )
    for reason, count in summary["termination_counts"].items():
        lines.append(f"- `{reason}`: {count}")
    lines.extend(("", "## Timing", ""))
    if summary["timings"]:
        for key, value in summary["timings"].items():
            lines.append(f"- `{key}`: {_report_number(value)}")
    else:
        lines.append("- No timing fields were supplied.")
    if summary["throughput"]:
        lines.extend(("", "## Amortized throughput", ""))
        for timing_key, metrics in summary["throughput"].items():
            lines.append(
                f"- `{timing_key}`: attempted {_report_number(metrics['attempted_trials_per_second'])} trials/s; "
                f"GPU-feasible {_report_number(metrics['gpu_feasible_trials_per_second'])} trials/s. "
                f"{metrics['meaning']}"
            )
    lines.extend(
        (
            "",
            "The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.",
            "",
        )
    )
    if metadata is not None:
        lines.extend(("## Metadata", "", "```json", json.dumps(_json_value(metadata), indent=2, sort_keys=True), "```", ""))
    return "\n".join(lines)


def write_report(
    directory: Path,
    records: list[dict],
    timings: dict,
    metadata: Any = None,
    *,
    started_at: float | None = None,
) -> dict:
    """Write strict JSON, Markdown, and an observed-data histogram SVG."""

    output_directory = Path(directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    report_started = perf_counter()
    # The Markdown is written before its own elapsed time exists. The final
    # summary is the canonical timing record and is serialized only once.
    report_timings = dict(timings)
    if started_at is not None:
        report_timings.pop("report_seconds", None)
        report_timings.pop("end_to_end_seconds", None)
    summary = summarize(records, report_timings)
    if metadata is not None:
        summary["metadata"] = _json_value(metadata)
    summary["artifacts"] = {
        "summary": "summary.json.gz",
        "report": "report.md",
        "histogram": "histogram.svg",
    }

    histogram_path = output_directory / "histogram.svg"
    histogram_path.write_text(_histogram_svg(summary["histogram"]), encoding="utf-8")
    report_path = output_directory / "report.md"
    markdown = _report_markdown(summary, metadata)
    if started_at is not None:
        markdown += ("\nFinal report and end-to-end timings are in `summary.json.gz`. "
                     "Their boundary includes this report and histogram; it excludes "
                     "the final summary's own serialization.\n")
    report_path.write_text(markdown, encoding="utf-8")
    if started_at is not None:
        completed = perf_counter()
        timings["report_seconds"] = completed - report_started
        timings["end_to_end_seconds"] = completed - started_at
        summary["timings"] = _json_value(timings)
        summary["timing_boundary"] = "Includes report and histogram; excludes final summary JSON serialization."
        summary["throughput"]["end_to_end_seconds"] = _throughput_metrics(
            timings["end_to_end_seconds"], summary["attempted_trials"], summary["accepted_trials"],
            "End-to-end through report/histogram persistence; excludes final summary serialization.")
    write_json(output_directory / "summary.json", summary)
    return summary
