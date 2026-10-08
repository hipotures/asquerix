#!/usr/bin/env python3
"""Reproduce the prior artifact audit without importing the production oracle.

The checker is intentionally self-contained.  It reads saved JSON/JSONL and
SVG files, reconstructs summary statistics, and implements a small float64
polygon projection check locally.  It does not import ``asquerix.geometry``
or execute any source code from a fixture.

Usage::

    python artifacts/audit/prior-evidence/check.py artifacts/pilot \
        --output /tmp/asquerix-audit.json

The positional directory may also be a new, partial campaign directory.  A
run is any descendant containing ``summary.json`` and a JSONL (possibly gzip)
trial stream.  Missing optional reports are recorded rather than invented.
"""

from __future__ import annotations

import argparse
import collections
import decimal
import hashlib
import html
import json
import math
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable, Iterator
import gzip


AUDITED_STATUSES = {"NUMERICALLY_VALIDATED", "INDETERMINATE", "INVALID"}
DEFAULT_TOLERANCE = 1.0e-8
SVG_EPSILON = 3.0e-12
UNIT_EDGE_EPSILON = 1.0e-12


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def quantile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def numeric_stats(values: Iterable[Any]) -> dict[str, Any]:
    finite = [float(value) for value in values if finite_float(value) is not None]
    if not finite:
        return {
            "count": 0,
            "best": None,
            "worst": None,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "q05": None,
            "q25": None,
            "q75": None,
            "q95": None,
            "quantiles": {"q05": None, "q25": None, "q50": None, "q75": None, "q95": None},
        }
    result = {
        "count": len(finite),
        "best": min(finite),
        "worst": max(finite),
        "min": min(finite),
        "max": max(finite),
        "mean": statistics.fmean(finite),
        "median": statistics.median(finite),
        "q05": quantile(finite, 0.05),
        "q25": quantile(finite, 0.25),
        "q75": quantile(finite, 0.75),
        "q95": quantile(finite, 0.95),
    }
    result["quantiles"] = {
        "q05": result["q05"],
        "q25": result["q25"],
        "q50": result["median"],
        "q75": result["q75"],
        "q95": result["q95"],
    }
    return result


def walk_local_name(element: ET.Element, name: str) -> Iterator[ET.Element]:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] == name:
            yield child


def _vector_length(vector: tuple[float, float]) -> float:
    return math.hypot(vector[0], vector[1])


def square_vertices(pose: Any) -> list[tuple[float, float]] | None:
    """Construct unit-square vertices in the saved SVG/validator order."""

    if not isinstance(pose, (list, tuple)) or len(pose) != 3:
        return None
    values = [finite_float(value) for value in pose]
    if any(value is None for value in values):
        return None
    x, y, theta = values
    cosine = math.cos(theta)
    sine = math.sin(theta)
    unit_u = (cosine, sine)
    unit_v = (-sine, cosine)
    signs = ((1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0))
    return [
        (
            x + 0.5 * (sx * unit_u[0] + sy * unit_v[0]),
            y + 0.5 * (sx * unit_u[1] + sy * unit_v[1]),
        )
        for sx, sy in signs
    ]


def edge_normals(polygon: list[tuple[float, float]]) -> list[tuple[float, float]] | None:
    normals: list[tuple[float, float]] = []
    for index, point in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        edge = (following[0] - point[0], following[1] - point[1])
        length = _vector_length(edge)
        if not math.isfinite(length) or length <= 0.0:
            return None
        normals.append((-edge[1] / length, edge[0] / length))
    return normals


def polygon_separation(first: list[tuple[float, float]], second: list[tuple[float, float]]) -> float | None:
    axes_first = edge_normals(first)
    axes_second = edge_normals(second)
    if axes_first is None or axes_second is None:
        return None
    best_gap = -math.inf
    for axis in axes_first + axes_second:
        first_projection = [point[0] * axis[0] + point[1] * axis[1] for point in first]
        second_projection = [point[0] * axis[0] + point[1] * axis[1] for point in second]
        if not all(math.isfinite(value) for value in first_projection + second_projection):
            return None
        gap = max(
            min(second_projection) - max(first_projection),
            min(first_projection) - max(second_projection),
        )
        best_gap = max(best_gap, gap)
    return best_gap


def independent_validate(poses: Any, side: Any, tolerance: Any = DEFAULT_TOLERANCE) -> dict[str, Any]:
    """Validate saved poses through an independent vertex/SAT implementation."""

    tolerance_value = finite_float(tolerance)
    if tolerance_value is None or tolerance_value < 0.0:
        return {
            "status": "INVALID",
            "min_pair_separation": None,
            "max_penetration": None,
            "min_wall_clearance": None,
            "nonfinite": False,
            "tolerance": None,
        }
    side_value = finite_float(side)
    if side_value is None or side_value <= 0.0 or not isinstance(poses, list):
        return {
            "status": "INVALID",
            "min_pair_separation": None,
            "max_penetration": None,
            "min_wall_clearance": None,
            "nonfinite": False,
            "tolerance": tolerance_value,
        }
    polygons: list[list[tuple[float, float]]] = []
    nonfinite = False
    edge_error = 0.0
    for pose in poses:
        polygon = square_vertices(pose)
        if polygon is None:
            nonfinite = True
            continue
        polygons.append(polygon)
        for index, point in enumerate(polygon):
            following = polygon[(index + 1) % 4]
            edge_error = max(edge_error, abs(_vector_length((following[0] - point[0], following[1] - point[1])) - 1.0))
    if nonfinite or len(polygons) != len(poses):
        return {
            "status": "INVALID",
            "min_pair_separation": None,
            "max_penetration": None,
            "min_wall_clearance": None,
            "nonfinite": True,
            "tolerance": tolerance_value,
        }
    half_side = side_value / 2.0
    min_wall = min(
        half_side - max(abs(point[coordinate]) for point in polygon for coordinate in (0, 1))
        for polygon in polygons
    ) if polygons else None
    min_pair: float | None = None
    for first_index, first in enumerate(polygons):
        for second in polygons[first_index + 1 :]:
            separation = polygon_separation(first, second)
            if separation is None:
                return {
                    "status": "INVALID",
                    "min_pair_separation": None,
                    "max_penetration": None,
                    "min_wall_clearance": None,
                    "nonfinite": True,
                    "tolerance": tolerance_value,
                }
            min_pair = separation if min_pair is None else min(min_pair, separation)
    if not polygons:
        min_wall = None
    max_penetration = max(
        [0.0]
        + ([-min_pair] if min_pair is not None and min_pair < 0.0 else [])
        + ([-min_wall] if min_wall is not None and min_wall < 0.0 else [])
    )
    if edge_error > UNIT_EDGE_EPSILON:
        status = "INVALID"
    elif min_wall is None:
        status = "INVALID"
    elif (min_pair is not None and min_pair < -tolerance_value) or min_wall < -tolerance_value:
        status = "INVALID"
    elif (min_pair is not None and min_pair <= tolerance_value) or min_wall <= tolerance_value:
        status = "INDETERMINATE"
    else:
        status = "NUMERICALLY_VALIDATED"
    return {
        "status": status,
        "min_pair_separation": min_pair,
        "max_penetration": max_penetration,
        "min_wall_clearance": min_wall,
        "nonfinite": False,
        "tolerance": tolerance_value,
        "edge_length_error": edge_error,
    }


def iter_trial_records(run: Path) -> tuple[list[dict[str, Any]], str | None, str | None]:
    plain = run / "trials.jsonl"
    compressed = run / "trials.jsonl.gz"
    if plain.exists():
        stream = plain.open("rt", encoding="utf-8")
        source = "trials.jsonl"
    elif compressed.exists():
        stream = gzip.open(compressed, "rt", encoding="utf-8")
        source = "trials.jsonl.gz"
    else:
        return [], None, "missing trials.jsonl or trials.jsonl.gz"
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_number}: {exc}")
                continue
            if not isinstance(value, dict):
                errors.append(f"line {line_number}: record is not an object")
                continue
            records.append(value)
    return records, source, "; ".join(errors) if errors else None


def discover_runs(root: Path) -> list[Path]:
    runs: list[Path] = []
    for summary in root.rglob("summary.json"):
        run = summary.parent
        if (run / "trials.jsonl").exists() or (run / "trials.jsonl.gz").exists():
            runs.append(run)
    return sorted(set(runs))


def close_enough(first: Any, second: Any, *, absolute: float = 1.0e-11) -> bool:
    if first is None or second is None:
        return first is None and second is None
    if isinstance(first, bool) or isinstance(second, bool):
        return first == second
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return math.isclose(float(first), float(second), rel_tol=1.0e-11, abs_tol=absolute)
    return first == second


def compare_stat_fields(expected: Any, actual: Any, path: str, mismatches: list[str]) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in expected:
            if key in actual:
                compare_stat_fields(expected[key], actual[key], f"{path}.{key}", mismatches)
        return
    if not close_enough(expected, actual):
        mismatches.append(f"{path}: persisted={expected!r}, reconstructed={actual!r}")


def histogram_counts(values: list[float], edges: list[float]) -> list[int]:
    counts = [0] * max(0, len(edges) - 1)
    if len(edges) < 2:
        return counts
    for value in values:
        if value < edges[0] or value > edges[-1]:
            continue
        index = len(edges) - 2 if value == edges[-1] else next(
            (candidate for candidate in range(len(edges) - 1) if edges[candidate] <= value < edges[candidate + 1]),
            None,
        )
        if index is not None:
            counts[index] += 1
    return counts


def reconstructed_statistics(records: list[dict[str, Any]]) -> dict[str, Any]:
    side_values = [record.get("side") for record in records]
    gpu_sides = [record.get("side") for record in records if record.get("gpu_status") == "GPU_FEASIBLE"]
    validated_sides = [
        record.get("side")
        for record in records
        if record.get("gpu_status") == "GPU_FEASIBLE" and record.get("validation_status") == "NUMERICALLY_VALIDATED"
    ]
    return {
        "record_count": len(records),
        "side": numeric_stats(side_values),
        "gpu_accepted": numeric_stats(gpu_sides),
        "numerically_validated": numeric_stats(validated_sides),
        "attempts": numeric_stats(record.get("attempts") for record in records),
        "sweeps": numeric_stats(record.get("sweeps") for record in records),
        "termination_counts": dict(sorted(collections.Counter(record.get("termination_reason") for record in records).items())),
        "gpu_status_counts": dict(sorted(collections.Counter(record.get("gpu_status") for record in records).items())),
        "validation_status_counts": dict(sorted(collections.Counter(record.get("validation_status") for record in records).items())),
    }


def pose_documents(run: Path) -> tuple[dict[int, dict[str, Any]], list[str]]:
    directory = run / "poses"
    documents: dict[int, dict[str, Any]] = {}
    errors: list[str] = []
    if not directory.exists():
        return documents, errors
    for path in sorted(directory.glob("trial-*.json")):
        try:
            document = load_json(path)
            trial_id = int(document["trial_id"])
            if trial_id in documents:
                errors.append(f"duplicate pose trial_id {trial_id}")
            documents[trial_id] = document
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
    return documents, errors


def compare_diagnostic(saved: Any, independent: dict[str, Any]) -> bool:
    if not isinstance(saved, dict):
        return False
    for key in ("status", "nonfinite"):
        if saved.get(key) != independent.get(key):
            return False
    for key in ("min_pair_separation", "max_penetration", "min_wall_clearance"):
        if not close_enough(saved.get(key), independent.get(key), absolute=5.0e-11):
            return False
    return True


def audit_run(run: Path, root: Path) -> dict[str, Any]:
    records, record_source, stream_error = iter_trial_records(run)
    reconstructed = reconstructed_statistics(records)
    trial_ids = [record.get("trial_id") for record in records]
    integer_ids = [value for value in trial_ids if isinstance(value, int) and not isinstance(value, bool)]
    expected_ids = list(range(min(integer_ids), max(integer_ids) + 1)) if integer_ids else []
    poses, pose_errors = pose_documents(run)
    record_by_id = {
        record["trial_id"]: record
        for record in records
        if isinstance(record.get("trial_id"), int) and not isinstance(record.get("trial_id"), bool)
    }
    audited_without_pose = [
        record.get("trial_id")
        for record in records
        if record.get("validation_status") in AUDITED_STATUSES and record.get("trial_id") not in poses
    ]
    geometry = {
        "saved_pose_documents": len(poses),
        "nonempty_pose_documents": 0,
        "empty_init_failed_documents": 0,
        "independent_status_counts": {},
        "status_or_metric_mismatches": [],
        "row_pose_mismatches": [],
    }
    for trial_id, document in sorted(poses.items()):
        row = record_by_id.get(trial_id, {})
        pose_values = document.get("poses")
        if pose_values == [] and document.get("termination_reason") == "INIT_FAILED":
            geometry["empty_init_failed_documents"] += 1
            continue
        geometry["nonempty_pose_documents"] += 1
        independent = independent_validate(
            pose_values,
            document.get("side"),
            document.get("validation", {}).get("tolerance", DEFAULT_TOLERANCE)
            if isinstance(document.get("validation"), dict)
            else DEFAULT_TOLERANCE,
        )
        status = independent["status"]
        geometry["independent_status_counts"][status] = geometry["independent_status_counts"].get(status, 0) + 1
        saved_diagnostic = document.get("independent_validation") or document.get("validation")
        if not compare_diagnostic(saved_diagnostic, independent):
            geometry["status_or_metric_mismatches"].append(trial_id)
        if row and (
            row.get("validation_status") != status
            or row.get("gpu_status") != document.get("gpu_status")
            or not close_enough(row.get("side"), document.get("side"))
        ):
            geometry["row_pose_mismatches"].append(trial_id)
    geometry["status_or_metric_mismatch_count"] = len(geometry["status_or_metric_mismatches"])
    geometry["row_pose_mismatch_count"] = len(geometry["row_pose_mismatches"])
    geometry["audited_scalar_rows_without_saved_pose"] = len(audited_without_pose)
    geometry["audited_scalar_trial_ids_without_saved_pose"] = audited_without_pose[:20]

    summary_path = run / "summary.json"
    summary = load_json(summary_path) if summary_path.exists() else {}
    summary_mismatches: list[str] = []
    expected_trial_count = len(records)
    expected_accepted_count = reconstructed["gpu_status_counts"].get("GPU_FEASIBLE", 0)
    for field, expected_value in (
        ("record_count", expected_trial_count),
        ("attempted_trials", expected_trial_count),
        ("accepted_trials", expected_accepted_count),
    ):
        if field in summary and summary[field] != expected_value:
            summary_mismatches.append(f"summary.{field}: persisted={summary[field]!r}, reconstructed={expected_value!r}")
    for field in ("termination_counts", "gpu_status_counts", "validation_status_counts"):
        if field in summary and summary[field] != reconstructed[field]:
            summary_mismatches.append(f"summary.{field}: persisted={summary[field]!r}, reconstructed={reconstructed[field]!r}")
    persisted_statistics = summary.get("statistics", {})
    for population in ("gpu_accepted", "numerically_validated"):
        if population in persisted_statistics:
            compare_stat_fields(persisted_statistics[population], reconstructed[population], f"summary.statistics.{population}", summary_mismatches)
    persisted_iteration = summary.get("iteration_statistics", {})
    for population in ("attempts", "sweeps"):
        if population in persisted_iteration:
            compare_stat_fields(persisted_iteration[population], reconstructed[population], f"summary.iteration_statistics.{population}", summary_mismatches)
    coverage = summary.get("audit_coverage", {})
    if coverage:
        expected_coverage = {
            "total_trials": len(records),
            "audited_trials": len(records) - reconstructed["validation_status_counts"].get("NOT_CHECKED", 0),
            "not_checked_trials": reconstructed["validation_status_counts"].get("NOT_CHECKED", 0),
            "numerically_validated_trials": reconstructed["validation_status_counts"].get("NUMERICALLY_VALIDATED", 0),
            "indeterminate_trials": reconstructed["validation_status_counts"].get("INDETERMINATE", 0),
            "invalid_trials": reconstructed["validation_status_counts"].get("INVALID", 0),
        }
        expected_coverage["coverage_fraction"] = expected_coverage["audited_trials"] / len(records) if records else 0.0
        for key, value in expected_coverage.items():
            if key in coverage and not close_enough(coverage[key], value):
                summary_mismatches.append(f"summary.audit_coverage.{key}: persisted={coverage[key]!r}, reconstructed={value!r}")

    svg_result = audit_svgs(run, poses, summary)
    return {
        "path": str(run.relative_to(root)) if run.is_relative_to(root) else str(run),
        "record_source": record_source,
        "record_stream_error": stream_error,
        "records": len(records),
        "global_id_count": len(integer_ids),
        "global_id_unique": len(set(integer_ids)) == len(integer_ids),
        "global_id_contiguous": bool(integer_ids) and sorted(set(integer_ids)) == expected_ids,
        "global_id_range": [min(integer_ids), max(integer_ids)] if integer_ids else [],
        "reconstructed": reconstructed,
        "summary_mismatches": summary_mismatches,
        "summary_mismatch_count": len(summary_mismatches),
        "geometry": geometry,
        "svg": svg_result,
        "config": load_json(run / "config.json") if (run / "config.json").exists() else None,
        "pose_parse_errors": pose_errors,
    }


def parse_svg_points(text: str) -> list[tuple[float, float]] | None:
    points: list[tuple[float, float]] = []
    try:
        values = text.split()
        for value in values:
            x, y = value.split(",", 1)
            points.append((float(x), float(y)))
    except (AttributeError, TypeError, ValueError):
        return None
    return points


def polygon_error(actual: list[tuple[float, float]], expected: list[tuple[float, float]]) -> float:
    if len(actual) != len(expected):
        return math.inf
    errors: list[float] = []
    for reversed_order in (False, True):
        candidate = list(reversed(expected)) if reversed_order else expected
        for offset in range(len(expected)):
            rotated = candidate[offset:] + candidate[:offset]
            errors.append(max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(actual, rotated)))
    return min(errors, default=math.inf)


def audit_svgs(run: Path, poses: dict[int, dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    directory = run / "svg"
    paths = sorted(directory.glob("*.svg")) if directory.exists() else []
    result = {
        "svg_files": len(paths),
        "metadata_mismatches": [],
        "container_mismatches": [],
        "polygon_mismatches": [],
        "histogram_count_mismatches": [],
    }
    for path in paths:
        match = re.search(r"trial-(\d+)\.svg$", path.name)
        if match is None:
            result["metadata_mismatches"].append(path.name)
            continue
        trial_id = int(match.group(1))
        document = poses.get(trial_id)
        if document is None:
            result["metadata_mismatches"].append(f"{path.name}: no pose document")
            continue
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except (OSError, ET.ParseError) as exc:
            result["metadata_mismatches"].append(f"{path.name}: {exc}")
            continue
        metadata_nodes = list(walk_local_name(root, "metadata"))
        metadata: dict[str, Any] | None = None
        if metadata_nodes and metadata_nodes[0].text:
            try:
                metadata = json.loads(html.unescape(metadata_nodes[0].text))
            except json.JSONDecodeError:
                metadata = None
        if not isinstance(metadata, dict):
            result["metadata_mismatches"].append(f"{path.name}: invalid metadata")
            continue
        for key in ("n", "trial_id", "side", "validation_status", "poses"):
            if key not in metadata or not close_enough(metadata.get(key), document.get(key)):
                result["metadata_mismatches"].append(f"{path.name}: metadata.{key}")
        container_nodes = [node for node in walk_local_name(root, "rect") if "container" in node.attrib.get("class", "").split()]
        if len(container_nodes) != 1:
            result["container_mismatches"].append(f"{path.name}: expected one container rect")
        else:
            container = container_nodes[0]
            try:
                container_values = tuple(float(container.attrib[key]) for key in ("x", "y", "width", "height"))
            except (KeyError, ValueError):
                container_values = None
            if container_values is None or any(
                not math.isclose(actual, expected, rel_tol=0.0, abs_tol=SVG_EPSILON)
                for actual, expected in zip(container_values or (), (76.0, 76.0, 748.0, 748.0))
            ):
                result["container_mismatches"].append(f"{path.name}: container geometry")
            else:
                cx, cy, width, height = container_values
                side = finite_float(document.get("side"))
                world_poses = document.get("poses")
                if world_poses == [] and document.get("termination_reason") == "INIT_FAILED":
                    polygons = [node for node in walk_local_name(root, "polygon") if "square" in node.attrib.get("class", "").split()]
                    if polygons:
                        result["polygon_mismatches"].append(f"{path.name}: unexpected polygons for INIT_FAILED")
                elif side is None or not isinstance(world_poses, list):
                    result["polygon_mismatches"].append(f"{path.name}: malformed numeric pose")
                else:
                    polygons = [node for node in walk_local_name(root, "polygon") if "square" in node.attrib.get("class", "").split()]
                    if len(polygons) != len(world_poses):
                        result["polygon_mismatches"].append(f"{path.name}: polygon count")
                    for index, (node, pose) in enumerate(zip(polygons, world_poses)):
                        expected_world = square_vertices(pose)
                        actual_svg = parse_svg_points(node.attrib.get("points", ""))
                        if expected_world is None or actual_svg is None:
                            result["polygon_mismatches"].append(f"{path.name}: square {index} malformed")
                            continue
                        expected_svg = [
                            (
                                cx + (point[0] + side / 2.0) * width / side,
                                cy + (side / 2.0 - point[1]) * height / side,
                            )
                            for point in expected_world
                        ]
                        if polygon_error(actual_svg, expected_svg) > SVG_EPSILON:
                            result["polygon_mismatches"].append(f"{path.name}: square {index}")
    histogram_path = run / "histogram.svg"
    if histogram_path.exists() and isinstance(summary.get("histogram"), dict):
        try:
            histogram_root = ET.parse(histogram_path).getroot()
            panels = {node.attrib.get("id"): node for node in walk_local_name(histogram_root, "g")}
            for population, expected in summary["histogram"].items():
                panel = panels.get(population)
                if panel is None:
                    result["histogram_count_mismatches"].append(population)
                    continue
                actual = [
                    int(node.attrib["data-count"])
                    for node in walk_local_name(panel, "rect")
                    if "bar" in node.attrib.get("class", "").split() and "data-count" in node.attrib
                ]
                if actual != expected.get("counts", []):
                    result["histogram_count_mismatches"].append(population)
        except (OSError, ET.ParseError, KeyError, ValueError) as exc:
            result["histogram_count_mismatches"].append(str(exc))
    for key in ("metadata_mismatches", "container_mismatches", "polygon_mismatches", "histogram_count_mismatches"):
        result[f"{key}_count"] = len(result[key])
    result["total_mismatches"] = sum(
        len(result[key]) for key in ("metadata_mismatches", "container_mismatches", "polygon_mismatches", "histogram_count_mismatches")
    )
    return result


def audit_manifest(root: Path) -> dict[str, Any] | None:
    path = root / "manifest.json"
    if not path.exists():
        return None
    manifest = load_json(path)
    expected = manifest.get("files", {}) if isinstance(manifest, dict) else {}
    actual_paths = {
        str(file.relative_to(root))
        for file in root.rglob("*")
        if file.is_file() and file.relative_to(root).as_posix() != "manifest.json"
    }
    expected_paths = set(expected)
    mismatches: list[dict[str, Any]] = []
    for relative in sorted(expected_paths | actual_paths):
        path_value = root / relative
        entry = expected.get(relative)
        if entry is None:
            mismatches.append({"path": relative, "kind": "unlisted_file"})
            continue
        if not path_value.exists():
            mismatches.append({"path": relative, "kind": "missing_file"})
            continue
        size = path_value.stat().st_size
        digest = sha256_file(path_value)
        if size != entry.get("bytes") or digest != entry.get("sha256"):
            mismatches.append({
                "path": relative,
                "kind": "size_or_sha256",
                "expected_bytes": entry.get("bytes"),
                "actual_bytes": size,
                "expected_sha256": entry.get("sha256"),
                "actual_sha256": digest,
            })
    source_results: dict[str, Any] = {}
    project_root = root.parent.parent
    for relative, expected_hash in (manifest.get("source_sha256", {}) if isinstance(manifest, dict) else {}).items():
        source_path = project_root / relative
        if source_path.exists():
            actual_hash = sha256_file(source_path)
            source_results[relative] = {"expected": expected_hash, "actual": actual_hash, "match": expected_hash == actual_hash}
        else:
            source_results[relative] = {"expected": expected_hash, "actual": None, "match": False, "missing": True}
    return {
        "manifest_entries": len(expected_paths),
        "actual_files_excluding_manifest": len(actual_paths),
        "names_equal": expected_paths == actual_paths,
        "file_hash_mismatch_count": len(mismatches),
        "file_hash_mismatches": mismatches[:20],
        "source_hashes": source_results,
        "implementation_commit": manifest.get("implementation_commit") if isinstance(manifest, dict) else None,
    }


def audit_archives(root: Path) -> list[dict[str, Any]]:
    measurements_path = root / "extended" / "measurements.json"
    if not measurements_path.exists():
        return []
    measurements = load_json(measurements_path)
    results: list[dict[str, Any]] = []
    for entry in measurements.get("runs", []):
        repeat = entry.get("repeat")
        archive = root / "extended" / f"repeat-{repeat}"
        archive_file = archive / "trials.jsonl.gz"
        if not archive_file.exists():
            results.append({"repeat": repeat, "error": "missing compressed archive"})
            continue
        compressed = archive_file.read_bytes()
        raw = gzip.decompress(compressed)
        results.append({
            "repeat": repeat,
            "compressed_bytes": len(compressed),
            "raw_bytes": len(raw),
            "raw_lines": raw.count(b"\n"),
            "compressed_sha256_matches_measurement": sha256_bytes(compressed) == entry.get("scalar_compressed_sha256"),
            "raw_sha256_matches_measurement": sha256_bytes(raw) == entry.get("scalar_uncompressed_sha256"),
        })
    return results


def audit_fixture(path: Path, source_path: Path | None = None) -> dict[str, Any] | None:
    if not path.exists():
        return None
    fixture = load_json(path)
    construction = fixture.get("construction", {})
    coefficients = construction.get("u_minimal_polynomial_coefficients_high_to_low")
    expected_coefficients = [5, -10, -2, 14, 12, -6, 2, 2, -1]
    decimal.getcontext().prec = 180
    low = decimal.Decimal(construction.get("u_isolating_interval", ["0.36", "0.37"])[0])
    high = decimal.Decimal(construction.get("u_isolating_interval", ["0.36", "0.37"])[1])
    decimal_coefficients = [decimal.Decimal(value) for value in coefficients or []]

    def polynomial(value: decimal.Decimal) -> decimal.Decimal:
        result = decimal.Decimal(0)
        for coefficient in decimal_coefficients:
            result = result * value + coefficient
        return result

    low_sign = polynomial(low)
    high_sign = polynomial(high)
    sign_bracketed = (low_sign < 0 < high_sign) or (high_sign < 0 < low_sign)
    for _ in range(560):
        midpoint = (low + high) / 2
        midpoint_value = polynomial(midpoint)
        if midpoint_value == 0:
            low = high = midpoint
            break
        if (low_sign < 0 < midpoint_value) or (midpoint_value < 0 < low_sign):
            high = midpoint
            high_sign = midpoint_value
        else:
            low = midpoint
            low_sign = midpoint_value
    root = (low + high) / 2
    exact_side = (decimal.Decimal(6) * root + decimal.Decimal(4)) / (decimal.Decimal(1) + decimal.Decimal(2) * root - root * root)
    side = finite_float(fixture.get("side"))
    poses = fixture.get("poses")
    geometry = independent_validate(poses, side, DEFAULT_TOLERANCE)
    construction_labels = {
        "parameter": "u = tan(a/2)",
        "angle": "a = 2 atan(u)",
        "side": "s = (6u + 4) / (1 + 2u - u^2) = 2 + (2 + sin(a)) / (cos(a) + sin(a))",
    }
    labels_match = all(construction.get(key) == value for key, value in construction_labels.items())
    result: dict[str, Any] = {
        "path": str(path),
        "fixture_id": fixture.get("fixture_id"),
        "n": fixture.get("n"),
        "pose_count": len(poses) if isinstance(poses, list) else None,
        "polynomial_coefficients_match": coefficients == expected_coefficients,
        "polynomial_interval_signs": [str(low_sign), str(high_sign)],
        "isolating_interval_bracketed": sign_bracketed,
        "recovered_u": str(root),
        "polynomial_residual": str(polynomial(root)),
        "recovered_side": str(exact_side),
        "stored_side": side,
        "stored_side_error": abs(float(exact_side) - side) if side is not None else None,
        "construction_labels_match": labels_match,
        "geometry": geometry,
        "provenance": fixture.get("provenance", {}),
        "proof_status": fixture.get("proof_status", {}),
    }
    if source_path is not None:
        expected_hash = fixture.get("provenance", {}).get("source_sha256")
        result["source_file"] = str(source_path)
        result["source_sha256"] = sha256_file(source_path) if source_path.exists() else None
        result["source_sha256_matches_fixture"] = source_path.exists() and result["source_sha256"] == expected_hash
    return result


def audit_root(root: Path, fixture: Path | None, fixture_source: Path | None) -> dict[str, Any]:
    runs = discover_runs(root)
    report: dict[str, Any] = {
        "audit_scope": {
            "source_artifact": str(root),
            "run_directories": len(runs),
            "independent_geometry_method": "float64 unit-square vertices, edge normals, and pairwise polygon projections; no production geometry import",
        },
        "artifact_integrity": {
            "manifest": audit_manifest(root),
            "extended_archives": audit_archives(root),
        },
        "runs": [audit_run(run, root) for run in runs],
    }
    pose_totals = collections.Counter()
    scalar_totals = collections.Counter()
    for run in report["runs"]:
        reconstructed = run["reconstructed"]
        for key, value in reconstructed["validation_status_counts"].items():
            scalar_totals[key] += value
        pose_totals["saved_pose_documents"] += run["geometry"]["saved_pose_documents"]
        pose_totals["nonempty_pose_documents"] += run["geometry"]["nonempty_pose_documents"]
        pose_totals["empty_init_failed_documents"] += run["geometry"]["empty_init_failed_documents"]
        pose_totals["status_or_metric_mismatch_count"] += run["geometry"]["status_or_metric_mismatch_count"]
        pose_totals["audited_scalar_rows_without_saved_pose"] += run["geometry"]["audited_scalar_rows_without_saved_pose"]
    report["aggregate"] = {
        "records": sum(run["records"] for run in report["runs"]),
        "gpu_status_counts": dict(sorted(collections.Counter(
            key
            for run in report["runs"]
            for key, value in run["reconstructed"]["gpu_status_counts"].items()
            for _ in range(value)
        ).items())),
        "validation_status_counts": dict(sorted(scalar_totals.items())),
        **dict(pose_totals),
        "svg_files": sum(run["svg"]["svg_files"] for run in report["runs"]),
        "svg_mismatch_count": sum(run["svg"]["total_mismatches"] for run in report["runs"]),
    }
    if fixture is not None:
        report["fixture"] = audit_fixture(fixture, fixture_source)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_root", type=Path, nargs="?", default=Path("artifacts/pilot"))
    parser.add_argument("--output", type=Path, help="write the JSON report to this path")
    parser.add_argument("--fixture", type=Path, default=Path("tests/fixtures/trump11.json"))
    parser.add_argument("--fixture-source", type=Path, help="optional local source copy to hash; never executed")
    args = parser.parse_args(argv)
    report = audit_root(args.artifact_root.resolve(), args.fixture.resolve() if args.fixture else None, args.fixture_source.resolve() if args.fixture_source else None)
    encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    aggregate = report["aggregate"]
    print(
        "checked runs={} records={} poses={} geometry_mismatches={} svg_mismatches={} summary_mismatches={}".format(
            len(report["runs"]),
            aggregate["records"],
            aggregate["saved_pose_documents"],
            aggregate["status_or_metric_mismatch_count"],
            aggregate["svg_mismatch_count"],
            sum(run["summary_mismatch_count"] for run in report["runs"]),
        ),
        file=sys.stderr,
    )
    manifest = report["artifact_integrity"].get("manifest")
    failed = (aggregate["status_or_metric_mismatch_count"] > 0
              or aggregate["svg_mismatch_count"] > 0
              or any(run["summary_mismatch_count"] for run in report["runs"]))
    if manifest:
        failed = failed or manifest["file_hash_mismatch_count"] > 0 or not manifest["names_equal"]
    for archive in report["artifact_integrity"].get("extended_archives", []):
        failed = failed or not archive["compressed_sha256_matches_measurement"] or not archive["raw_sha256_matches_measurement"]
    fixture = report.get("fixture", {})
    if "source_sha256_matches_fixture" in fixture:
        failed = failed or not fixture["source_sha256_matches_fixture"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
