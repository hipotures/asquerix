"""Safe publication of finalized experiment artifacts to remote main.

Publication deliberately uses Git's plumbing commands with a temporary index.
It never creates a branch or changes the caller's active checkout or index.
The local experiment directory is the source of truth: any
publication failure leaves it intact and is recorded in ``publication.json.gz``.
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from time import monotonic
from typing import Any, Iterator
from uuid import uuid4
from urllib.parse import urlsplit, urlunsplit

from .persistence import read_json, write_json


PUBLICATION_BRANCH = "main"
MAX_ARTIFACT_BYTES = 95 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 500 * 1024 * 1024
PUBLICATION_SCHEMA = "asquerix-publication-v1"
_ARTIFACT_SUFFIXES = (".json", ".json.gz", ".jsonl", ".jsonl.gz", ".md", ".svg", ".csv")


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


def _experiment(directory: Path) -> _Experiment:
    summary = _read_optional(directory, "summary")
    config = _read_optional(directory, "config")
    environment = _read_optional(directory, "environment")
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


def _collect_files(directory: Path, *, include_manifest: bool = True) -> list[tuple[Path, str, int, str]]:
    files: list[tuple[Path, str, int, str]] = []
    total = 0
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
        if not relative.name.endswith(_ARTIFACT_SUFFIXES):
            raise PublicationError(f"unsupported artifact extension: {relative}")
        size = path.stat().st_size
        if size > MAX_ARTIFACT_BYTES:
            raise PublicationError(
                f"artifact {relative} is {size} bytes; the safe per-file limit is {MAX_ARTIFACT_BYTES}"
            )
        if path.name.endswith(".gz"):
            _validate_gzip(path)
        total += size
        if total > MAX_TOTAL_ARTIFACT_BYTES:
            raise PublicationError(
                f"artifacts total {total} bytes; the safe total limit is {MAX_TOTAL_ARTIFACT_BYTES}"
            )
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
    return {
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


def _write_receipt(directory: Path, result: Mapping[str, Any]) -> None:
    try:
        write_json(directory / "publication.json.gz", dict(result))
    except OSError:
        # A receipt cannot make a successfully finalized experiment look like
        # a failed computation.  The returned result still contains the error.
        pass


def _base_result(directory: Path, experiment: _Experiment, started: float) -> dict[str, Any]:
    return {
        "status": "LOCAL_ONLY",
        "commit_sha": None,
        "local_commit_sha": None,
        "url": None,
        "error": None,
        "seconds": 0.0,
        "artifact_path": f"experiments/{experiment.slug}/{experiment.run_id}",
        "directory": str(directory),
        "experiment_name": experiment.name,
        "run_status": experiment.run_status,
    }


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
        _write_receipt(output, result)
        if snapshot_directory is not None:
            shutil.rmtree(snapshot_directory, ignore_errors=True)
