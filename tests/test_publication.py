"""Tests for isolated-index experiment publication."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from asquerix import publication


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo, text=True, capture_output=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.name", "Asquerix Test")
    _git(repo, "config", "user.email", "asquerix@example.invalid")
    (repo / "README.md").write_text("test repository\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")
    _git(repo.parent, "init", "--bare", str(remote))
    _git(repo, "remote", "add", "origin", str(remote))
    _git(repo, "push", "origin", "main")
    return repo, remote


def _write_gzip_json(path: Path, value: object) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            compressed.write(json.dumps(value, sort_keys=True).encode("utf-8"))


def _experiment(
    directory: Path,
    *,
    run_id: str = "run-1",
    trials: int = 2,
    compressed: bool = True,
    source_revision: str | None = None,
    timings: dict[str, float] | None = None,
    run_status: str = "COMPLETED",
    requested_trials: int | None = None,
    completed_trials: int | None = None,
) -> None:
    directory.mkdir(parents=True)
    requested = trials if requested_trials is None else requested_trials
    completed = trials if completed_trials is None else completed_trials
    metadata = {
        "experiment_name": "n12-s480-b8",
        "experiment_slug": "n12-s480-b8",
        "run_id": run_id,
        "run_status": run_status,
        "requested_trials": requested,
        "completed_trials": completed,
    }
    summary = {
        "record_count": completed,
        "requested_trials": requested,
        "statistics": {"numerically_validated": {"best": 4.0001}},
        "metadata": metadata,
    }
    if timings is not None:
        summary["timings"] = timings
    config = {
        "solver": {"n": 12, "seed": 123, "max_sweeps": 480},
        "runner": {"trials": requested, "batch_size": 8, "trial_offset": 100},
    }
    environment = {"gpu": "test-gpu"}
    if source_revision is not None:
        environment["source_revision"] = source_revision
    documents = {
        "summary": summary,
        "config": config,
        "environment": environment,
    }
    for stem, value in documents.items():
        if compressed:
            _write_gzip_json(directory / f"{stem}.json.gz", value)
        else:
            (directory / f"{stem}.json").write_text(json.dumps(value), encoding="utf-8")
    if compressed:
        with (directory / "trials.jsonl.gz").open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed_stream:
                for trial_id in range(100, 100 + completed):
                    compressed_stream.write((json.dumps({"trial_id": trial_id}) + "\n").encode("utf-8"))
    else:
        (directory / "trials.jsonl").write_text(
            "".join(json.dumps({"trial_id": trial_id}) + "\n" for trial_id in range(100, 100 + completed)),
            encoding="utf-8",
        )
    (directory / "report.md").write_text("# Report\n", encoding="utf-8")
    (directory / "histogram.svg").write_text("<svg/>\n", encoding="utf-8")


def _remote_results_head(remote: Path) -> str | None:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", "refs/heads/experiment-results"],
        cwd=remote,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        return None
    value = completed.stdout.strip()
    return value or None


def _git_bytes(repo: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, check=False
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    return completed.stdout


def test_publish_uses_compressed_inputs_and_isolates_active_index(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    output = tmp_path / "run"
    _experiment(output, compressed=True)
    (repo / "unrelated.txt").write_text("keep staged\n", encoding="utf-8")
    _git(repo, "add", "unrelated.txt")
    _git(repo, "checkout", "--detach")
    head_before = _git(repo, "rev-parse", "HEAD")
    staged_before = _git(repo, "diff", "--cached", "--name-only")

    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUBLISHED"
    assert result["commit_sha"] == _remote_results_head(remote)
    assert result["artifact_path"] == "experiments/n12-s480-b8/run-1"
    assert result["url"].endswith(f"/commit/{result['commit_sha']}") or result["url"].endswith(
        f"#commit/{result['commit_sha']}"
    )
    assert _git(repo, "rev-parse", "HEAD") == head_before
    assert _git(repo, "diff", "--cached", "--name-only") == staged_before
    assert _git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"

    tree = _git(remote, "ls-tree", "-r", "--name-only", result["commit_sha"]).splitlines()
    assert "experiments/n12-s480-b8/run-1/summary.json.gz" in tree
    assert "experiments/n12-s480-b8/run-1/manifest.json.gz" in tree
    assert "experiments/n12-s480-b8/run-1/publication.json.gz" not in tree
    blob = _git(remote, "rev-parse", f"{result['commit_sha']}:experiments/n12-s480-b8/run-1/summary.json.gz")
    assert _git_bytes(remote, "cat-file", "blob", blob) == (output / "summary.json.gz").read_bytes()
    manifest = publication.read_json(output / "manifest.json.gz")
    listed = {entry["path"] for entry in manifest["artifacts"]}
    assert "manifest.json.gz" not in listed
    assert "publication.json.gz" not in listed
    for entry in manifest["artifacts"]:
        local = output / entry["path"]
        remote_blob = _git(
            remote,
            "rev-parse",
            f"{result['commit_sha']}:{result['artifact_path']}/{entry['path']}",
        )
        remote_bytes = _git_bytes(remote, "cat-file", "blob", remote_blob)
        assert hashlib.sha256(local.read_bytes()).hexdigest() == entry["sha256"]
        assert remote_bytes == local.read_bytes()
    receipt = json.loads(gzip.open(output / "publication.json.gz", "rt", encoding="utf-8").read())
    assert receipt["status"] == "PUBLISHED"


def test_publish_reads_historical_plain_json_and_updates_branch(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    first = tmp_path / "first"
    second = tmp_path / "second"
    _experiment(first, run_id="run-plain", compressed=False)
    _experiment(second, run_id="run-gzip", compressed=True)

    first_result = publication.publish(first, repo=repo)
    second_result = publication.publish(second, repo=repo)

    assert first_result["status"] == second_result["status"] == "PUBLISHED"
    assert _remote_results_head(remote) == second_result["commit_sha"]
    assert _git(remote, "merge-base", "--is-ancestor", first_result["commit_sha"], second_result["commit_sha"]) == ""
    tree = _git(remote, "ls-tree", "-r", "--name-only", second_result["commit_sha"]).splitlines()
    assert "experiments/n12-s480-b8/run-plain/summary.json" in tree
    assert "experiments/n12-s480-b8/run-gzip/summary.json.gz" in tree


def test_no_push_creates_manifest_and_keeps_results_local(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    output = tmp_path / "offline"
    _experiment(output)

    result = publication.publish(output, repo=repo, push=False)

    assert result["status"] == "LOCAL_ONLY"
    assert result["commit_sha"] is None
    assert (output / "manifest.json.gz").is_file()
    assert (output / "publication.json.gz").is_file()
    assert _remote_results_head(remote) is None


def test_manifest_uses_run_start_provenance_timings_and_validated_best(git_repo, tmp_path: Path) -> None:
    repo, _remote = git_repo
    source_revision = _git(repo, "rev-parse", "HEAD")
    output = tmp_path / "provenance"
    _experiment(output, source_revision=source_revision, timings={"device_seconds": 1.25})
    (repo / "later.txt").write_text("later source\n", encoding="utf-8")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later source")

    result = publication.publish(output, repo=repo, push=False)

    assert result["status"] == "LOCAL_ONLY"
    manifest = publication.read_json(output / "manifest.json.gz")
    assert manifest["source_revision"] == source_revision
    assert manifest["source_revision_source"] == "environment.source_revision"
    assert manifest["timings"] == {"device_seconds": 1.25}
    assert manifest["best_validated_side"] == 4.0001


def test_partial_run_with_zero_completed_trials_preserves_zero_in_manifest(git_repo, tmp_path: Path) -> None:
    repo, _remote = git_repo
    output = tmp_path / "empty-partial"
    _experiment(
        output,
        trials=0,
        run_id="empty-partial",
        run_status="PARTIAL",
        requested_trials=4,
        completed_trials=0,
    )

    result = publication.publish(output, repo=repo, push=False)

    assert result["status"] == "LOCAL_ONLY"
    manifest = publication.read_json(output / "manifest.json.gz")
    assert manifest["run_status"] == "PARTIAL"
    assert manifest["requested_trials"] == 4
    assert manifest["completed_trials"] == 0
    assert manifest["trial_range"] == {"first_trial_id": 100}


def test_remote_lookup_failure_does_not_create_a_local_commit(git_repo, tmp_path: Path) -> None:
    repo, _remote = git_repo
    missing_remote = tmp_path / "missing-remote.git"
    _git(repo, "remote", "set-url", "origin", str(missing_remote))
    output = tmp_path / "remote-auth-failure"
    _experiment(output, run_id="remote-auth-failure")

    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUSH_FAILED"
    assert result["commit_sha"] is None
    assert result["local_commit_sha"] is None
    assert "git command failed" in result["error"].lower()
    assert (output / "manifest.json.gz").is_file()


def test_corrupted_gzip_is_rejected_before_publication(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    output = tmp_path / "corrupted"
    _experiment(output, run_id="corrupted")
    gzip_path = output / "trials.jsonl.gz"
    gzip_path.write_bytes(gzip_path.read_bytes()[:-4])

    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUSH_FAILED"
    assert "invalid gzip" in result["error"].lower()
    assert _remote_results_head(remote) is None


def test_missing_repository_is_a_failed_automatic_publication(tmp_path: Path) -> None:
    output = tmp_path / "outside-repository"
    _experiment(output)

    result = publication.publish(output, repo=tmp_path / "not-a-repository")

    assert result["status"] == "PUSH_FAILED"
    assert "repository" in result["error"].lower() or "git" in result["error"].lower()
    assert (output / "manifest.json.gz").is_file()
    assert (output / "publication.json.gz").is_file()


def test_symlinks_and_unknown_extensions_are_rejected(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    symlink_output = tmp_path / "symlink"
    _experiment(symlink_output)
    (symlink_output / "linked.json").symlink_to(symlink_output / "summary.json.gz")
    symlink_result = publication.publish(symlink_output, repo=repo)
    assert symlink_result["status"] == "PUSH_FAILED"
    assert "symlink" in symlink_result["error"]

    unknown_output = tmp_path / "unknown"
    _experiment(unknown_output, run_id="unknown")
    (unknown_output / "credentials.pem").write_text("secret\n", encoding="utf-8")
    unknown_result = publication.publish(unknown_output, repo=repo)
    assert unknown_result["status"] == "PUSH_FAILED"
    assert "extension" in unknown_result["error"]
    assert _remote_results_head(remote) is None


def test_oversized_artifact_is_rejected_without_data_loss(git_repo, tmp_path: Path, monkeypatch) -> None:
    repo, remote = git_repo
    output = tmp_path / "large"
    _experiment(output)
    (output / "too-large.json").write_bytes(b"x" * 32)
    monkeypatch.setattr(publication, "MAX_ARTIFACT_BYTES", 16)

    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUSH_FAILED"
    assert "safe per-file limit" in result["error"]
    assert (output / "too-large.json").read_bytes() == b"x" * 32
    assert _remote_results_head(remote) is None


def test_existing_artifact_path_is_never_overwritten(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    first = tmp_path / "first"
    duplicate = tmp_path / "duplicate"
    _experiment(first, run_id="same")
    _experiment(duplicate, run_id="same")

    first_result = publication.publish(first, repo=repo)
    duplicate_result = publication.publish(duplicate, repo=repo)

    assert first_result["status"] == "PUBLISHED"
    assert duplicate_result["status"] == "PUSH_FAILED"
    assert "already exists" in duplicate_result["error"]
    assert _remote_results_head(remote) == first_result["commit_sha"]


def test_remote_update_between_observation_and_push_is_retried(git_repo, tmp_path: Path, monkeypatch) -> None:
    repo, remote = git_repo
    output = tmp_path / "remote-race"
    _experiment(output, run_id="remote-race")
    real_git = publication._git
    state = {"moved": False}

    def flaky_git(repo_path, arguments, *, env=None, timeout=30.0):
        if arguments and arguments[0] == "push" and not state["moved"]:
            main_commit = real_git(remote, ["rev-parse", "refs/heads/main"])
            tree = real_git(remote, ["rev-parse", f"{main_commit}^{{tree}}"])
            competitor_env = os.environ.copy()
            competitor_env.update(
                GIT_AUTHOR_NAME="Concurrent publisher",
                GIT_AUTHOR_EMAIL="concurrent@example.invalid",
                GIT_COMMITTER_NAME="Concurrent publisher",
                GIT_COMMITTER_EMAIL="concurrent@example.invalid",
            )
            competitor = real_git(
                remote,
                ["commit-tree", tree, "-p", main_commit, "-m", "concurrent result"],
                env=competitor_env,
            )
            real_git(remote, ["update-ref", "refs/heads/experiment-results", competitor])
            state["moved"] = True
        return real_git(repo_path, arguments, env=env, timeout=timeout)

    monkeypatch.setattr(publication, "_git", flaky_git)
    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUBLISHED"
    assert result["commit_sha"] == _remote_results_head(remote)
    parents = _git(remote, "rev-list", "--parents", "-n", "1", result["commit_sha"]).split()
    assert len(parents) == 2
    assert state["moved"]


def test_push_failure_preserves_local_artifacts(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    hook = remote / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    output = tmp_path / "rejected"
    _experiment(output)

    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUSH_FAILED"
    assert result["commit_sha"] is None
    assert result["local_commit_sha"]
    assert result["local_commit_ref"].startswith("refs/asquerix/unpublished/")
    assert _git(repo, "rev-parse", result["local_commit_ref"]) == result["local_commit_sha"]
    assert (output / "summary.json.gz").is_file()
    assert (output / "publication.json.gz").is_file()
    assert _remote_results_head(remote) is None


def test_concurrent_publishers_serialize_and_preserve_both_runs(git_repo, tmp_path: Path) -> None:
    repo, remote = git_repo
    outputs = [tmp_path / "one", tmp_path / "two"]
    _experiment(outputs[0], run_id="one")
    _experiment(outputs[1], run_id="two")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda path: publication.publish(path, repo=repo), outputs))

    assert [result["status"] for result in results] == ["PUBLISHED", "PUBLISHED"]
    head = _remote_results_head(remote)
    tree = _git(remote, "ls-tree", "-r", "--name-only", head).splitlines()
    assert "experiments/n12-s480-b8/one/summary.json.gz" in tree
    assert "experiments/n12-s480-b8/two/summary.json.gz" in tree



def test_commit_uses_private_snapshot_instead_of_mutable_run_directory(git_repo, tmp_path, monkeypatch):
    repo, remote = git_repo
    output = tmp_path / "snapshot-run"
    _experiment(output)
    original = publication._build_commit
    calls = []
    def build(repo, base, artifact_path, files, message):
        assert all(not source.is_relative_to(output) for source, *_ in files)
        calls.append(True)
        return original(repo, base, artifact_path, files, message)
    monkeypatch.setattr(publication, "_build_commit", build)
    result = publication.publish(output, repo=repo)
    assert result["status"] == "PUBLISHED"
    assert calls == [True]


def test_publication_urls_and_errors_never_expose_url_credentials():
    remote = 'https://user:private-token@github.com/owner/project.git'
    assert publication._commit_url(remote, 'abc') == 'https://github.com/owner/project/commit/abc'
    error = publication._GitError(['git', 'push', 'origin'], 1, f'Cannot access {remote}')
    assert 'private-token' not in str(error)
    assert 'user:' not in str(error)
