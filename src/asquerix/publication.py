"""Safe publication of finalized experiment artifacts to remote main.

Publication deliberately uses Git's plumbing commands with a temporary index.
It never creates a branch or changes the caller's active checkout or index.
The local experiment directory is the source of truth: any
publication failure leaves it intact and is recorded in ``publication.json.gz``.
"""

from __future__ import annotations

import fcntl
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

from .persistence import GZIP_COMPRESSION_LEVEL, read_json, write_json

PUBLICATION_BRANCH = "main"
MAX_ARTIFACT_BYTES = 95 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 500 * 1024 * 1024
PUBLICATION_SCHEMA = "asquerix-publication-v1"
_ARTIFACT_SUFFIXES = (".json", ".json.gz", ".jsonl", ".jsonl.gz", ".md", ".svg", ".csv")
_TRACE_OPERATION_SCHEMA = "asquerix-trace-operation-v1"
_TRACE_COLLECTION_KIND = "trajectory-replay"
_TRACE_OPERATION_ID = re.compile(r"^trace-[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_TRAJECTORY_PATH = re.compile(r"^trajectories/trial-([0-9]+)\.(npz|html)$")
_LAB_NATIVE_PATH = re.compile(r"^(?:initial-bank\.npz|evaluations/part-[0-9a-f]{16}-[0-9]{4}\.npz|evaluations/top-(?:random_program_search|one_plus_lambda)\.npz|(?:collections/[0-9a-f]{32}/)?trajectories/episode-[0-9a-f]{64}\.(?:npz|html)|report\.html)$")
_UINT64_MAX = (1 << 64) - 1
# Trace creation leaves this amount unconsumed for publication.  The receipt
# itself is much smaller in normal operation; reserve a separate conservative
# amount while measuring the manifest before writing it.
TRACE_PUBLICATION_RESERVE_BYTES = 64 * 1024
TRACE_RECEIPT_RESERVE_BYTES = 8 * 1024


class PublicationError(RuntimeError):
    """A publication could not be completed safely."""


def _public_url(url: str) -> str:
    """Remove URL credentials before persisting or presenting remote metadata."""
    if "://" in url:
        parsed = urlsplit(url)
        return urlunsplit((parsed.scheme, parsed.netloc.rsplit("@", 1)[-1], parsed.path, "", ""))
    return url


def _public_diagnostic(value: str) -> str:
    return re.sub(r"(?:https?|ssh)://[^\s]+", lambda match: _public_url(match.group()), value)


@dataclass(frozen=True)
class _Experiment:
    directory: Path
    name: str
    slug: str
    run_id: str
    run_status: str
    requested_trials: int | None
    completed_trials: int | None
    seed: int | None
    trial_offset: int | None
    solver: Mapping[str, Any]
    runner: Mapping[str, Any]
    summary: Mapping[str, Any]
    config: Mapping[str, Any]
    environment: Mapping[str, Any]
    collection_kind: str | None = None
    source_directory: str | None = None
    replay_requested_count: int | None = None
    replay_completed_count: int | None = None
    export_limit_bytes: int | None = None
    trace_operation: Mapping[str, Any] | None = None


class _GitError(PublicationError):
    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stderr = _public_diagnostic(stderr.strip())
        rendered = " ".join(command)
        detail = self.stderr or f"exit code {returncode}"
        super().__init__(f"git command failed ({rendered}): {detail}")


def _json_read(path: Path) -> Any:
    """Read one JSON document through the shared persistence helper."""

    return read_json(path)


def _json_candidate(directory: Path, stem: str) -> Path | None:
    for suffix in (".json.gz", ".json"):
        candidate = directory / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def _read_optional(directory: Path, stem: str) -> Mapping[str, Any]:
    path = _json_candidate(directory, stem)
    if path is None:
        return {}
    value = _json_read(path)
    return value if isinstance(value, Mapping) else {}


def _nested(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key, {})
    return value if isinstance(value, Mapping) else {}


def _string(value: Any, fallback: str) -> str:
    return value if isinstance(value, str) and value.strip() else fallback


_SAFE_PART = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_part(value: Any, fallback: str) -> str:
    text = _string(value, fallback).strip()
    text = _SAFE_PART.sub("-", text).strip(".-")
    if not text:
        text = fallback
    if text in {".", ".."}:
        text = fallback
    return text[:128]


def _optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        try:
            return int(value, 10)
        except ValueError:
            return None
    return None


def _trace_int(value: Any, field: str, *, positive: bool = False) -> int:
    converted = _optional_int(value)
    if converted is None or converted < (1 if positive else 0):
        requirement = "a positive integer" if positive else "a non-negative integer"
        raise PublicationError(f"trace operation field '{field}' must be {requirement}")
    return converted


def _trace_operation(directory: Path) -> Mapping[str, Any] | None:
    """Read and validate a trace-operation document when one is present.

    A trace operation is intentionally a small companion collection.  It has
    no scientific ``summary.json.gz``, ``config.json.gz`` or
    ``environment.json.gz`` documents, so publication must classify it before
    deriving ordinary experiment fields.
    """

    path = _json_candidate(directory, "trace")
    if path is None:
        return None
    value = _json_read(path)
    if not isinstance(value, Mapping):
        raise PublicationError("trace operation document must be a JSON object")
    if value.get("schema") != _TRACE_OPERATION_SCHEMA:
        raise PublicationError(
            f"trace operation schema must be {_TRACE_OPERATION_SCHEMA!r}"
        )
    if value.get("collection_kind") != _TRACE_COLLECTION_KIND:
        raise PublicationError(
            f"trace operation collection_kind must be {_TRACE_COLLECTION_KIND!r}"
        )
    operation_id = value.get("operation_id")
    if not isinstance(operation_id, str) or _TRACE_OPERATION_ID.fullmatch(operation_id) is None:
        raise PublicationError("trace operation operation_id must be a safe trace-<uuid> value")
    source_directory = value.get("source_directory")
    if not isinstance(source_directory, str) or not source_directory.strip():
        raise PublicationError("trace operation source_directory must be a non-empty string")
    status = value.get("status")
    if status not in {"COMPLETE", "INTERRUPTED", "EXPORT_LIMIT", "REPLAY_ERROR"}:
        raise PublicationError(
            "trace operation status must be COMPLETE, INTERRUPTED, EXPORT_LIMIT, or REPLAY_ERROR"
        )
    _trace_int(value.get("requested_count"), "requested_count")
    _trace_int(value.get("completed_count"), "completed_count")
    _trace_int(value.get("export_limit_bytes"), "export_limit_bytes", positive=True)
    if not isinstance(value.get("config"), Mapping):
        raise PublicationError("trace operation config must be a JSON object")
    if not isinstance(value.get("replay_environment"), Mapping):
        raise PublicationError("trace operation replay_environment must be a JSON object")
    if not isinstance(value.get("timings", {}), Mapping):
        raise PublicationError("trace operation timings must be a JSON object")
    artifacts = value.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise PublicationError("trace operation artifacts must be a JSON array")
    source_artifacts = value.get("source_artifacts", [])
    if not isinstance(source_artifacts, list):
        raise PublicationError("trace operation source_artifacts must be a JSON array")
    return value


def _trace_status(status: str) -> str:
    if status == "COMPLETE":
        return "COMPLETED"
    if status in {"INTERRUPTED", "EXPORT_LIMIT"}:
        return "PARTIAL"
    return "ERROR"


def _trace_operation_artifacts(operation: Mapping[str, Any]) -> list[Any]:
    value = operation.get("source_artifacts")
    if isinstance(value, list):
        return list(value)
    value = operation.get("artifacts")
    return list(value) if isinstance(value, list) else []


def _trace_solver(config: Mapping[str, Any]) -> Mapping[str, Any]:
    nested = _nested(config, "solver")
    return nested if nested else config


def _experiment(directory: Path) -> _Experiment:
    if (directory / "campaign.json.gz").is_file():
        from .lab.config import Campaign
        from .lab.storage import bounded_json
        campaign = bounded_json(directory / "campaign.json.gz")
        spec = Campaign.model_validate(campaign["spec"])
        summary = bounded_json(directory / "summaries.json.gz")
        if (campaign.get("id") != summary.get("id") or not re.fullmatch(r"[0-9a-f]{32}", str(campaign.get("id")))
                or summary.get("schema") != "asquerix-lab-summary-v1" or summary.get("state") not in ("COMPLETED", "PARTIAL")):
            raise PublicationError("Laboratory campaign is not a finalized matching collection")
        return _Experiment(directory=directory, name=spec.name, slug=_safe_part(spec.name, "campaign"),
                           run_id=campaign["id"], run_status=summary["state"], requested_trials=None,
                           completed_trials=None, seed=None, trial_offset=None, solver=campaign["profile"],
                           runner=campaign["plan"], summary=summary, config=spec.document(),
                           environment=bounded_json(directory / "environment.json.gz"),
                           collection_kind="strategy-campaign", export_limit_bytes=int(spec.limits.max_artifact_mib * 1024**2))
    summary = _read_optional(directory, "summary")
    config = _read_optional(directory, "config")
    environment = _read_optional(directory, "environment")
    trace_operation = _trace_operation(directory)

    if trace_operation is not None and not any((summary, config, environment)):
        operation_id = str(trace_operation["operation_id"])
        trace_config = _nested(trace_operation, "config")
        replay_environment = _nested(trace_operation, "replay_environment")
        requested = _trace_int(trace_operation.get("requested_count"), "requested_count")
        completed = _trace_int(trace_operation.get("completed_count"), "completed_count")
        status = str(trace_operation["status"])
        return _Experiment(
            directory=directory,
            name=operation_id,
            slug=_safe_part(operation_id, "trace"),
            run_id=operation_id,
            run_status=_trace_status(status),
            requested_trials=None,
            completed_trials=None,
            seed=None,
            trial_offset=None,
            solver=_trace_solver(trace_config),
            runner={},
            summary={
                "collection_kind": _TRACE_COLLECTION_KIND,
                "metadata": dict(trace_operation),
                "timings": dict(_nested(trace_operation, "timings")),
            },
            config=trace_config,
            environment=replay_environment,
            collection_kind=_TRACE_COLLECTION_KIND,
            source_directory=str(trace_operation["source_directory"]),
            replay_requested_count=requested,
            replay_completed_count=completed,
            export_limit_bytes=_trace_int(
                trace_operation.get("export_limit_bytes"), "export_limit_bytes", positive=True
            ),
            trace_operation=trace_operation,
        )

    metadata = _nested(summary, "metadata")
    solver = _nested(config, "solver")
    runner = _nested(config, "runner")

    name = _string(
        metadata.get("experiment_name", summary.get("experiment_name")),
        directory.name,
    )
    slug = _safe_part(
        metadata.get("experiment_slug", summary.get("experiment_slug")),
        _safe_part(name, "experiment"),
    )
    run_id = _safe_part(
        metadata.get("run_id", summary.get("run_id")),
        _safe_part(directory.name, "run"),
    )
    requested = _first_int(
        metadata.get("requested_trials"), summary.get("requested_trials"), runner.get("trials")
    )
    completed = _first_int(
        metadata.get("completed_trials"), summary.get("completed_trials"), summary.get("record_count")
    )
    stop_reason = _string(metadata.get("stop_reason"), "")
    run_status = _string(
        metadata.get("run_status", summary.get("run_status")),
        "COMPLETED" if requested is not None and completed == requested else "PARTIAL",
    ).upper()
    if run_status not in {"COMPLETED", "PARTIAL", "ERROR"}:
        run_status = "PARTIAL"
    if stop_reason == "ERROR":
        run_status = "ERROR"

    seed = _optional_int(solver.get("seed"))
    trial_offset = _optional_int(runner.get("trial_offset"))
    return _Experiment(
        directory=directory,
        name=name,
        slug=slug,
        run_id=run_id,
        run_status=run_status,
        requested_trials=requested,
        completed_trials=completed,
        seed=seed,
        trial_offset=trial_offset,
        solver=solver,
        runner=runner,
        summary=summary,
        config=config,
        environment=environment,
        source_directory=(
            str(trace_operation.get("source_directory"))
            if trace_operation is not None and isinstance(trace_operation.get("source_directory"), str)
            else None
        ),
        replay_requested_count=(
            _trace_int(trace_operation.get("requested_count"), "requested_count")
            if trace_operation is not None
            else None
        ),
        replay_completed_count=(
            _trace_int(trace_operation.get("completed_count"), "completed_count")
            if trace_operation is not None
            else None
        ),
        export_limit_bytes=(
            _trace_int(trace_operation.get("export_limit_bytes"), "export_limit_bytes", positive=True)
            if trace_operation is not None
            else None
        ),
        trace_operation=trace_operation,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_gzip(path: Path) -> None:
    try:
        with gzip.open(path, "rb") as stream:
            while stream.read(1024 * 1024):
                pass
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise PublicationError(f"invalid gzip artifact {path}: {exc}") from exc


def _trajectory_kind(relative: Path) -> str | None:
    match = _TRAJECTORY_PATH.fullmatch(relative.as_posix())
    if match is None:
        return None
    try:
        trial_id = int(match.group(1), 10)
    except ValueError:  # pragma: no cover - the regular expression is decimal-only
        return None
    if trial_id > _UINT64_MAX:
        return None
    return match.group(2)


def _validate_trajectory_npz(path: Path, relative: Path) -> None:
    """Validate a trajectory archive through the shared bounded loader."""

    if _trajectory_kind(relative) != "npz":
        raise PublicationError(f"trajectory NPZ has an invalid path: {relative}")
    try:
        from .trajectory_format import load_trajectory

        _, metadata = load_trajectory(path)
        match = _TRAJECTORY_PATH.fullmatch(relative.as_posix())
        if metadata["trial_id"] != str(int(match.group(1))):
            raise ValueError("trajectory filename disagrees with metadata trial identity")
    except Exception as exc:
        # A malformed or incomplete trajectory must never enter a publication
        # snapshot.  Keep the original exception as diagnostic context while
        # presenting a stable publication-level error to callers.
        raise PublicationError(f"invalid trajectory NPZ {relative}: {exc}") from exc


def _validate_trajectory_html(path: Path, relative: Path) -> None:
    """Require a self-contained HTML document for a selected trajectory."""

    if _trajectory_kind(relative) != "html":
        raise PublicationError(f"trajectory HTML has an invalid path: {relative}")
    _validate_selfcontained_html(path, relative)


def _validate_selfcontained_html(path: Path, relative: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PublicationError(f"invalid trajectory HTML {relative}: {exc}") from exc
    normalized = text.lstrip("\ufeff").lower()
    if "<html" not in normalized or "</html>" not in normalized:
        raise PublicationError(f"trajectory HTML is not a complete HTML document: {relative}")
    # A local viewer may use inline scripts and styles, but it must not depend
    # on a server, CDN, browser extension, or another local file.
    resource_attribute = re.compile(r"(?is)\b(?:src|href)\s*=\s*(['\"])(.*?)\1")
    for match in resource_attribute.finditer(text):
        target = match.group(2).strip().lower()
        if target and not target.startswith(("#", "data:", "blob:")):
            raise PublicationError(f"trajectory HTML is not self-contained: {relative}")
    external_request = re.compile(r"(?is)\b(?:fetch|importScripts|XMLHttpRequest)\s*\(")
    if external_request.search(text):
        raise PublicationError(f"trajectory HTML requests a network resource: {relative}")


def _collect_files(directory: Path, *, include_manifest: bool = True) -> list[tuple[Path, str, int, str]]:
    files: list[tuple[Path, str, int, str]] = []
    total = 0
    laboratory = _experiment(directory) if (directory / "campaign.json.gz").is_file() else None
    ignored_directories = {"__pycache__", ".pytest_cache", ".warp-cache"}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory)
        # Check this before is_file(): a symlink to a directory can otherwise
        # be traversed or silently skipped by pathlib.
        if path.is_symlink():
            raise PublicationError(f"symlink artifacts are not publishable: {relative}")
        if any(part.startswith(".") for part in relative.parts):
            raise PublicationError(f"hidden or temporary artifact path is not publishable: {relative}")
        if any(part in ignored_directories for part in relative.parts):
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            raise PublicationError(f"special artifact path is not publishable: {relative}")
        if relative == Path("publication.json.gz") or (
            relative == Path("manifest.json.gz") and not include_manifest
        ):
            continue
        if any(part in {".", ".."} for part in relative.parts):
            raise PublicationError(f"invalid artifact path: {relative}")
        size = path.stat().st_size
        if size > MAX_ARTIFACT_BYTES:
            raise PublicationError(
                f"artifact {relative} is {size} bytes; the safe per-file limit is {MAX_ARTIFACT_BYTES}"
            )
        trajectory_kind = _trajectory_kind(relative)
        if relative.suffix in {".npz", ".html"}:
            if laboratory and _LAB_NATIVE_PATH.fullmatch(relative.as_posix()):
                try:
                    if relative.suffix == ".html":
                        _validate_selfcontained_html(path, relative)
                    elif relative.parent.name == "trajectories":
                        from .lab.trace import load_trace
                        load_trace(path)
                    else:
                        from .lab.storage import load_npz
                        load_npz(path)
                except (ValueError, OSError, KeyError) as error:
                    raise PublicationError(f"Invalid laboratory artifact {relative}: {error}") from error
            elif trajectory_kind is None:
                raise PublicationError(f"unsupported trajectory artifact path: {relative}")
            elif trajectory_kind == "npz":
                _validate_trajectory_npz(path, relative)
            else:
                _validate_trajectory_html(path, relative)
        elif not relative.name.endswith(_ARTIFACT_SUFFIXES):
            raise PublicationError(f"unsupported artifact extension: {relative}")
        if path.name.endswith(".gz"):
            _validate_gzip(path)
        total += size
        if total > MAX_TOTAL_ARTIFACT_BYTES:
            raise PublicationError(
                f"artifacts total {total} bytes; the safe total limit is {MAX_TOTAL_ARTIFACT_BYTES}"
            )
        if laboratory and total > laboratory.export_limit_bytes:
            raise PublicationError("Laboratory publication exceeds its declared campaign artifact quota")
        files.append((path, relative.as_posix(), size, _sha256(path)))
    return files


def _freeze_files(
    files: list[tuple[Path, str, int, str]], root: Path
) -> list[tuple[Path, str, int, str]]:
    """Copy finalized files to a private snapshot and verify every digest."""

    frozen: list[tuple[Path, str, int, str]] = []
    for source, relative, size, digest in files:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied_size = target.stat().st_size
        copied_digest = _sha256(target)
        current_size = source.stat().st_size
        current_digest = _sha256(source)
        if (copied_size, copied_digest) != (size, digest) or (current_size, current_digest) != (size, digest):
            raise PublicationError(f"artifact changed while being finalized: {relative}")
        frozen.append((target, relative, size, digest))
    return frozen


def _assert_files_unchanged(directory: Path, original: list[tuple[Path, str, int, str]]) -> None:
    current = _collect_files(directory, include_manifest=False)
    expected = [(relative, size, digest) for _path, relative, size, digest in original]
    observed = [(relative, size, digest) for _path, relative, size, digest in current]
    if observed != expected:
        raise PublicationError("experiment artifacts changed after the publication snapshot was taken")


def _source_revision(environment: Mapping[str, Any]) -> str | None:
    direct = environment.get("source_revision")
    if isinstance(direct, str) and direct:
        return direct
    git_revision = environment.get("git_revision")
    if isinstance(git_revision, Mapping):
        value = git_revision.get("stdout")
        if isinstance(value, str) and value.strip():
            return value.strip().splitlines()[0]
    return None


def _source_revision_info(environment: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """Return run-start provenance and the field that supplied it."""

    direct = environment.get("source_revision")
    if isinstance(direct, str) and direct.strip():
        return direct.strip(), "environment.source_revision"
    git_revision = environment.get("git_revision")
    if isinstance(git_revision, Mapping):
        value = git_revision.get("stdout")
        if isinstance(value, str) and value.strip():
            return value.strip().splitlines()[0], "environment.git_revision.stdout"
    return None, None


def _first_int(*values: Any) -> int | None:
    """Return the first present integer, preserving a legitimate zero."""

    for value in values:
        converted = _optional_int(value)
        if converted is not None:
            return converted
    return None


def _best_side(summary: Mapping[str, Any]) -> Any:
    return _nested(_nested(summary, "statistics"), "numerically_validated").get("best")


def _trace_manifest_fields(experiment: _Experiment) -> dict[str, Any]:
    if experiment.collection_kind == "strategy-campaign":
        return {"collection_kind": experiment.collection_kind,
                "profile_hash": experiment.summary["profile_hash"],
                "executable_hash": experiment.summary["executable_hash"],
                "completed_candidates": experiment.summary["completed_candidates"],
                "completed_episode_executions": experiment.summary["completed_episode_executions"],
                "submitted_episode_attempts": experiment.summary["submitted_episode_attempts"],
                "diagnostic_replay_executions": experiment.summary["replay_executions"]}
    operation = experiment.trace_operation
    if operation is None:
        return {}
    fields: dict[str, Any] = {
        "collection_kind": _TRACE_COLLECTION_KIND,
        "source_directory": experiment.source_directory,
        "requested_count": experiment.replay_requested_count,
        "completed_count": experiment.replay_completed_count,
        "trace_status": operation.get("status"),
        "export_limit_bytes": experiment.export_limit_bytes,
        "source_artifacts": _trace_operation_artifacts(operation),
    }
    if experiment.collection_kind is None:
        return {"trajectory": fields}
    return fields


def _manifest(
    experiment: _Experiment,
    *,
    source_revision: str | None,
    source_revision_source: str,
    artifact_path: str,
    files: list[tuple[Path, str, int, str]],
) -> dict[str, Any]:
    trial_range: dict[str, int] = {}
    if experiment.trial_offset is not None:
        trial_range["first_trial_id"] = experiment.trial_offset
        if experiment.completed_trials:
            trial_range["last_trial_id"] = experiment.trial_offset + experiment.completed_trials - 1
    manifest = {
        "schema": PUBLICATION_SCHEMA,
        "experiment_name": experiment.name,
        "experiment_slug": experiment.slug,
        "run_id": experiment.run_id,
        "run_status": experiment.run_status,
        "artifact_path": artifact_path,
        "source_revision": source_revision,
        "code_revision": source_revision,
        "source_revision_source": source_revision_source,
        "publication_branch": PUBLICATION_BRANCH,
        "seed": experiment.seed,
        "trial_range": trial_range,
        "requested_trials": experiment.requested_trials,
        "completed_trials": experiment.completed_trials,
        "solver": dict(experiment.solver),
        "runner": dict(experiment.runner),
        "best_validated_side": _best_side(experiment.summary),
        "timings": dict(_nested(experiment.summary, "timings")),
        "environment": dict(experiment.environment),
        "artifacts": [
            {"path": relative, "size_bytes": size, "sha256": digest}
            for _path, relative, size, digest in files
        ],
        "excluded_from_artifact_hashes": ["manifest.json.gz", "publication.json.gz"],
    }
    manifest.update(_trace_manifest_fields(experiment))
    return manifest


def _git(repo: Path, arguments: list[str], *, env: Mapping[str, str] | None = None, timeout: float = 30.0) -> str:
    command = ["git", *arguments]
    try:
        completed = subprocess.run(
            command,
            cwd=repo,
            env=dict(env) if env is not None else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublicationError(f"git command failed ({' '.join(command)}): {exc}") from exc
    if completed.returncode:
        raise _GitError(command, completed.returncode, completed.stderr)
    return completed.stdout.strip()


def _resolve_repo(directory: Path, repo: Path | str | None) -> Path:
    if repo is not None:
        candidates = [Path(repo).resolve()]
    else:
        project_root = Path(__file__).resolve().parents[2]
        candidates = [directory, project_root, Path.cwd()]
    errors: list[str] = []
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            root = _git(candidate, ["rev-parse", "--show-toplevel"])
        except PublicationError as exc:
            errors.append(str(exc))
            continue
        return Path(root).resolve()
    detail = errors[-1] if errors else "no repository candidates"
    raise PublicationError(f"Git repository could not be discovered: {detail}")


def _common_git_dir(repo: Path) -> Path:
    value = _git(repo, ["rev-parse", "--git-common-dir"])
    path = Path(value)
    if not path.is_absolute():
        path = (repo / path).resolve()
    return path


@contextmanager
def _publication_lock(git_dir: Path, timeout: float = 30.0) -> Iterator[None]:
    lock_path = git_dir / "asquerix-publication.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    deadline = monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if monotonic() >= deadline:
                    raise PublicationError("timed out waiting for the repository publication lock")
                import time

                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _remote(repo: Path) -> tuple[str, str] | None:
    names = _git(repo, ["remote"]).splitlines()
    if not names:
        return None
    name = "origin" if "origin" in names else names[0]
    url = _git(repo, ["remote", "get-url", name])
    return name, _public_url(url)


def _remote_head(repo: Path, remote: str) -> str | None:
    output = _git(repo, ["ls-remote", "--heads", remote, f"refs/heads/{PUBLICATION_BRANCH}"])
    if not output:
        return None
    first = output.splitlines()[0].split()
    if len(first) != 2 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", first[0]):
        raise PublicationError(f"unexpected remote branch response for {PUBLICATION_BRANCH}")
    return first[0]


def _fetch_base(repo: Path, remote: str, sha: str | None, namespace: str) -> str | None:
    if sha is None:
        return None
    ref = f"refs/asquerix/publication/{namespace}"
    try:
        _git(repo, ["fetch", "--no-tags", remote, f"+refs/heads/{PUBLICATION_BRANCH}:{ref}"])
        fetched = _git(repo, ["rev-parse", ref])
        if fetched != sha:
            # The remote could have moved between ls-remote and fetch.  The
            # caller will compare the new head on the next retry.
            return fetched
        return fetched
    finally:
        try:
            _git(repo, ["update-ref", "-d", ref])
        except PublicationError:
            pass


def _remote_contains(repo: Path, base: str | None, artifact_path: str) -> bool:
    if base is None:
        return False
    prefix = artifact_path.rstrip("/") + "/"
    output = _git(repo, ["ls-tree", "-r", "--name-only", base, "--", artifact_path])
    return any(line == artifact_path or line.startswith(prefix) for line in output.splitlines())


def _remote_contains_commit(repo: Path, remote: str, commit: str, observed: str | None) -> bool:
    """Confirm that a pushed commit remains reachable from the remote head."""

    if observed == commit:
        return True
    if observed is None:
        return False
    fetched = _fetch_base(repo, remote, observed, f"confirmation-{os.getpid()}-{uuid4().hex}")
    if fetched is None:
        return False
    try:
        _git(repo, ["merge-base", "--is-ancestor", commit, fetched])
    except PublicationError:
        return False
    return True


def _build_commit(
    repo: Path,
    base: str | None,
    artifact_path: str,
    files: list[tuple[Path, str, int, str]],
    message: str,
) -> tuple[str, Path]:
    temporary_directory = Path(tempfile.mkdtemp(prefix="asquerix-publication-"))
    index = temporary_directory / "index"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(index)
    try:
        if base is None:
            _git(repo, ["read-tree", "--empty"], env=environment)
        else:
            _git(repo, ["read-tree", base], env=environment)
        for source, relative, _size, _digest in files:
            destination = f"{artifact_path}/{relative}"
            blob = _git(
                repo,
                ["hash-object", "--no-filters", "-w", str(source)],
                env=environment,
            )
            _git(repo, ["update-index", "--add", "--cacheinfo", "100644", blob, destination], env=environment)
        tree = _git(repo, ["write-tree"], env=environment)
        arguments = ["commit-tree", tree]
        if base is not None:
            arguments.extend(["-p", base])
        arguments.extend(["-m", message])
        commit = _git(repo, arguments, env=environment)
        return commit, index
    finally:
        shutil.rmtree(temporary_directory, ignore_errors=True)


def _anchor_unpublished_commit(repo: Path, commit: str) -> str:
    """Keep an unpublished commit reachable without touching active HEAD."""

    reference = f"refs/asquerix/unpublished/{uuid4().hex}"
    _git(repo, ["update-ref", reference, commit])
    return reference


def _delete_ref(repo: Path, reference: str | None) -> None:
    if reference is None:
        return
    try:
        _git(repo, ["update-ref", "-d", reference])
    except PublicationError:
        # A failed cleanup must never erase the original publication result.
        pass


def _commit_url(remote_url: str, commit: str) -> str:
    url = _public_url(remote_url.strip())
    if url.startswith("git@") and ":" in url:
        host, path = url.split(":", 1)
        url = f"https://{host[4:]}/{path}"
    elif url.startswith("ssh://"):
        parsed = urlsplit(url)
        url = f"https://{parsed.hostname}{parsed.path}"
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("http://") or url.startswith("https://"):
        return f"{url.rstrip('/')}/commit/{commit}"
    return f"{url}#commit/{commit}"


def _bounded_receipt(result: Mapping[str, Any], max_bytes: int) -> dict[str, Any]:
    document = dict(result)
    if _gzip_json_size(document) <= max_bytes:
        return document
    error = document.get("error")
    document["error"] = str(error)[:2048] if error is not None else None
    document["receipt_truncated"] = True
    if _gzip_json_size(document) <= max_bytes:
        return document
    # Keep the publication state and its location even if a remote diagnostic
    # or future extension added an unexpectedly large field.
    compact = {
        key: document[key]
        for key in (
            "status",
            "commit_sha",
            "local_commit_sha",
            "url",
            "error",
            "seconds",
            "artifact_path",
            "directory",
            "experiment_name",
            "run_status",
            "receipt_truncated",
        )
        if key in document
    }
    return compact


def _write_receipt(
    directory: Path, result: Mapping[str, Any], *, max_bytes: int | None = None
) -> None:
    try:
        document = dict(result)
        if max_bytes is not None:
            document = _bounded_receipt(document, max_bytes)
        write_json(directory / "publication.json.gz", document)
    except OSError:
        # A receipt cannot make a successfully finalized experiment look like
        # a failed computation.  The returned result still contains the error.
        pass


def save_receipt(directory: Path | str, result: Mapping[str, Any]) -> Path:
    """Save final CLI timing through the same bounded publication serializer."""
    directory = Path(directory)
    maximum = TRACE_RECEIPT_RESERVE_BYTES if _json_candidate(directory, "trace") else None
    _write_receipt(directory, result, max_bytes=maximum)
    return directory / "publication.json.gz"


def _base_result(directory: Path, experiment: _Experiment, started: float) -> dict[str, Any]:
    if experiment.collection_kind == _TRACE_COLLECTION_KIND:
        artifact_path = f"trajectory-replays/{experiment.slug}/{experiment.run_id}"
    else:
        artifact_path = f"experiments/{experiment.slug}/{experiment.run_id}"
    return {
        "status": "LOCAL_ONLY",
        "commit_sha": None,
        "local_commit_sha": None,
        "url": None,
        "error": None,
        "seconds": 0.0,
        "artifact_path": artifact_path,
        "directory": str(directory),
        "experiment_name": experiment.name,
        "run_status": experiment.run_status,
    }


def _gzip_json_size(value: Mapping[str, Any]) -> int:
    """Measure the deterministic gzip representation written by ``write_json``."""

    payload = json.dumps(
        dict(value), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    stream = io.BytesIO()
    with gzip.GzipFile(
        fileobj=stream,
        mode="wb",
        filename="",
        mtime=0,
        compresslevel=GZIP_COMPRESSION_LEVEL,
    ) as compressed:
        compressed.write(payload)
    return len(stream.getvalue())


def _trace_budget_bytes(
    experiment: _Experiment,
    files: list[tuple[Path, str, int, str]],
) -> int:
    """Return the bytes covered by a trace export budget.

    A standalone companion contains only replay artifacts, so all finalized
    files count.  An ordinary run may also contain the scientific campaign;
    its trace budget covers the trace operation document and trajectory
    directory without charging the original experiment evidence twice.
    """

    if experiment.trace_operation is None:
        return 0
    if experiment.collection_kind == _TRACE_COLLECTION_KIND:
        return sum(size for _path, _relative, size, _digest in files)
    return sum(
        size
        for _path, relative, size, _digest in files
        if relative == "trace.json.gz" or relative.startswith("trajectories/")
    )


def _check_trace_export_budget(
    experiment: _Experiment,
    files: list[tuple[Path, str, int, str]],
    manifest: Mapping[str, Any],
) -> None:
    limit = experiment.export_limit_bytes
    if limit is None:
        return
    trace_bytes = _trace_budget_bytes(experiment, files)
    manifest_bytes = _gzip_json_size(manifest)
    publication_bytes = manifest_bytes + TRACE_RECEIPT_RESERVE_BYTES
    projected = trace_bytes + publication_bytes
    if publication_bytes > TRACE_PUBLICATION_RESERVE_BYTES:
        raise PublicationError(
            "trajectory export limit exceeded before manifest publication: "
            f"manifest plus receipt reserve is {publication_bytes} bytes, above the "
            f"{TRACE_PUBLICATION_RESERVE_BYTES}-byte publication reserve"
        )
    if projected > limit:
        raise PublicationError(
            "trajectory export limit exceeded before manifest publication: "
            f"{trace_bytes} bytes of trace files + {manifest_bytes} bytes of manifest + "
            f"{TRACE_RECEIPT_RESERVE_BYTES} bytes reserved for publication receipt "
            f"= {projected} > {limit} bytes (publication reserve: "
            f"{TRACE_PUBLICATION_RESERVE_BYTES} bytes)"
        )


def publish(directory: Path | str, *, repo: Path | str | None = None, push: bool = True) -> dict[str, Any]:
    """Finalize and publish an experiment directory without changing its worktree.

    ``push=False`` is the explicit offline escape hatch.  It still creates a
    manifest and a local receipt, but it does not create a Git commit or alter
    any refs.  All publication failures are returned as a structured result;
    finalized experiment files are never removed.
    """

    started = monotonic()
    output = Path(directory).resolve()
    if not output.is_dir():
        raise ValueError(f"experiment directory does not exist: {output}")
    experiment = _experiment(output)
    result = _base_result(output, experiment, started)
    artifact_path = result["artifact_path"]
    source_revision, source_revision_source = _source_revision_info(experiment.environment)
    remote_url: str | None = None
    repo_root: Path | None = None
    repo_error: str | None = None
    snapshot_directory: Path | None = None
    unpublished_ref: str | None = None
    try:
        # The environment document is captured at run start.  Never replace
        # that provenance with the current checkout's HEAD.  Old artifacts
        # without a recorded revision receive an explicit fallback label.
        try:
            repo_root = _resolve_repo(output, repo)
        except PublicationError as exc:
            repo_error = str(exc)
        if source_revision is None and repo_root is not None:
            try:
                source_revision = _git(repo_root, ["rev-parse", "HEAD"])
                source_revision_source = "head-fallback-missing-artifact-provenance"
            except PublicationError as exc:
                repo_error = repo_error or str(exc)
        if source_revision is None:
            source_revision_source = "unavailable-missing-artifact-provenance"
        elif source_revision_source is None:
            source_revision_source = "head-fallback-missing-artifact-provenance"

        # Freeze the source files before writing the manifest.  The commit is
        # built exclusively from this snapshot, so a concurrent writer cannot
        # make the manifest hashes disagree with committed bytes.
        files_without_manifest = _collect_files(output, include_manifest=False)
        snapshot_directory = Path(tempfile.mkdtemp(prefix="asquerix-artifacts-"))
        frozen_without_manifest = _freeze_files(files_without_manifest, snapshot_directory)
        manifest = _manifest(
            experiment,
            source_revision=source_revision,
            source_revision_source=source_revision_source or "unavailable-missing-artifact-provenance",
            artifact_path=artifact_path,
            files=frozen_without_manifest,
        )
        _check_trace_export_budget(experiment, files_without_manifest, manifest)
        write_json(output / "manifest.json.gz", manifest)
        manifest_file = [item for item in _collect_files(output) if item[1] == "manifest.json.gz"]
        if len(manifest_file) != 1:
            raise PublicationError("final manifest was not written exactly once")
        frozen_manifest = _freeze_files(manifest_file, snapshot_directory)
        _assert_files_unchanged(output, files_without_manifest)
        files = [*frozen_without_manifest, *frozen_manifest]
        result["source_revision"] = source_revision
        result["source_revision_source"] = source_revision_source
        result["remote_url"] = remote_url

        if not push:
            result["error"] = "Publication disabled by push=False."
            return result
        if repo_root is None:
            result["status"] = "PUSH_FAILED"
            result["error"] = repo_error or "Git repository could not be discovered."
            return result

        try:
            remote_info = _remote(repo_root)
        except PublicationError as exc:
            result["status"] = "PUSH_FAILED"
            result["error"] = str(exc)
            return result
        if remote_info is None:
            result["status"] = "PUSH_FAILED"
            result["error"] = "No Git remote is configured."
            return result
        remote_url = remote_info[1]
        result["remote_url"] = remote_url
        git_dir = _common_git_dir(repo_root)
        with _publication_lock(git_dir):
            remote, remote_url = remote_info
            last_error = ""
            for attempt in range(3):
                remote_sha = _remote_head(repo_root, remote)
                base = _fetch_base(repo_root, remote, remote_sha, f"{os.getpid()}-{uuid4().hex}")
                if base != remote_sha:
                    # Fetch observed a newer head.  Re-evaluate the branch and
                    # continue the normal ancestry-preserving attempt.
                    remote_sha = base
                if base is None:
                    # Initial publication includes committed source, never an
                    # orphan artifact-only tree or unrelated staged changes.
                    base = _git(repo_root, ["rev-parse", "HEAD"])
                if _remote_contains(repo_root, base, artifact_path):
                    result["status"] = "PUSH_FAILED"
                    result["error"] = f"artifact path already exists on {PUBLICATION_BRANCH}: {artifact_path}"
                    return result
                _assert_files_unchanged(output, files_without_manifest)
                if experiment.collection_kind == _TRACE_COLLECTION_KIND:
                    completed_text = experiment.replay_completed_count or 0
                    message = f"trajectory: {experiment.name} ({completed_text} replays)"
                elif experiment.collection_kind == "strategy-campaign":
                    episodes = experiment.summary["completed_episode_executions"]
                    message = f"lab campaign: {experiment.name} ({experiment.run_status}, {episodes} episodes)"
                else:
                    message_side = _best_side(experiment.summary)
                    side_text = f", best L={message_side:.9g}" if isinstance(message_side, (int, float)) else ""
                    completed_text = experiment.completed_trials if experiment.completed_trials is not None else 0
                    message = f"experiment: {experiment.name} ({completed_text} trials{side_text})"
                commit, _index = _build_commit(repo_root, base, artifact_path, files, message)
                _delete_ref(repo_root, unpublished_ref)
                unpublished_ref = _anchor_unpublished_commit(repo_root, commit)
                result["local_commit_sha"] = commit
                result["local_commit_ref"] = unpublished_ref
                try:
                    _git(repo_root, ["push", "--porcelain", remote, f"{commit}:refs/heads/{PUBLICATION_BRANCH}"])
                except PublicationError as exc:
                    last_error = str(exc)
                    newer = _remote_head(repo_root, remote)
                    if attempt < 2 and newer != remote_sha:
                        continue
                    result["status"] = "PUSH_FAILED"
                    result["error"] = last_error
                    return result
                confirmed = _remote_head(repo_root, remote)
                if not _remote_contains_commit(repo_root, remote, commit, confirmed):
                    last_error = f"remote did not confirm commit {commit} on {PUBLICATION_BRANCH}"
                    if attempt < 2 and confirmed != remote_sha:
                        continue
                    result["status"] = "PUSH_FAILED"
                    result["error"] = last_error
                    return result
                result["status"] = "PUBLISHED"
                result["commit_sha"] = commit
                result["url"] = _commit_url(remote_url, commit)
                result["remote_url"] = remote_url
                result["local_commit_sha"] = None
                result.pop("local_commit_ref", None)
                _delete_ref(repo_root, unpublished_ref)
                unpublished_ref = None
                return result
            result["status"] = "PUSH_FAILED"
            result["error"] = last_error or "remote branch changed during publication"
            return result
    except (_GitError, PublicationError, OSError, ValueError) as exc:
        result["error"] = str(exc)
        result["status"] = "PUSH_FAILED" if push else "LOCAL_ONLY"
        return result
    finally:
        result["seconds"] = monotonic() - started
        _write_receipt(
            output,
            result,
            max_bytes=TRACE_RECEIPT_RESERVE_BYTES if experiment.trace_operation is not None else None,
        )
        if snapshot_directory is not None:
            shutil.rmtree(snapshot_directory, ignore_errors=True)
