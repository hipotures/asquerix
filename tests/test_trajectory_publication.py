"""Publication tests for bounded trajectory and replay collections."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import numpy as np
import pytest

from asquerix import publication
from asquerix.persistence import write_json
from asquerix.trajectory_format import encode_npz


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


def _valid_npz(directory: Path, trial_id: int = 7) -> Path:
    n = 1
    arrays = {
        "poses": np.zeros((1, n, 3), dtype="<f4"),
        "side": np.asarray([4.0], dtype="<f4"),
        "sequence": np.asarray([0], dtype="<i8"),
        "attempt": np.asarray([0], dtype="<i4"),
        "sweep": np.asarray([0], dtype="<i4"),
        "sweep_total": np.asarray([0], dtype="<i4"),
        "phase": np.asarray([0], dtype="u1"),
        "roles": np.asarray([3], dtype="u1"),
        "square_ids": np.asarray([0], dtype="<i4"),
    }
    payload = encode_npz(arrays)
    path = directory / "trajectories" / f"trial-{trial_id}.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    metadata = {
        "schema": "asquerix-trajectory-v1",
        "n": n,
        "trial_id": str(trial_id),
        "seed": "2",
        "frame_count": 1,
        "sampling": {
            "observed": 1,
            "retained": 1,
            "suppressed": 0,
            "effective_stride": 1,
            "max_frames": 256,
        },
        "comparison": {},
        "validations": [],
        "provenance": {},
        "termination_reason": "BUDGET_EXHAUSTED",
        "numeric_sha256": hashlib.sha256(payload).hexdigest(),
    }
    write_json(path.with_name(path.stem + ".meta.json.gz"), metadata)
    return path


def _valid_html(directory: Path, trial_id: int = 7) -> Path:
    path = directory / "trajectories" / f"trial-{trial_id}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<!doctype html><html><body><canvas id='viewer'></canvas>"
        "<script>const trajectory = true;</script></body></html>\n",
        encoding="utf-8",
    )
    return path


def _trace_operation(directory: Path, *, limit: int = 1 << 20) -> None:
    write_json(
        directory / "trace.json.gz",
        {
            "schema": "asquerix-trace-operation-v1",
            "collection_kind": "trajectory-replay",
            "operation_id": "trace-0123456789abcdef0123456789abcdef",
            "source_directory": "/tmp/original-run",
            "config": {"n": 1, "seed": 2},
            "replay_environment": {"device": "cuda:0", "source_revision": "abc"},
            "status": "COMPLETE",
            "requested_count": 1,
            "completed_count": 1,
            "export_limit_bytes": limit,
            "timings": {"total_seconds": 0.1},
            "source_artifacts": [{"path": "poses/trial-7.json.gz"}],
            "artifacts": [],
        },
    )


def _remote_head(remote: Path) -> str:
    return _git(remote, "rev-parse", "refs/heads/main")


def test_trajectory_files_are_published_and_unrelated_suffixes_remain_rejected(
    git_repo: tuple[Path, Path], tmp_path: Path
) -> None:
    repo, remote = git_repo
    output = tmp_path / "trace"
    _trace_operation(output)
    npz = _valid_npz(output)
    html = _valid_html(output)
    (output / "unrelated.npz").write_bytes(b"not a trajectory")

    failed = publication.publish(output, repo=repo)

    assert failed["status"] == "PUSH_FAILED"
    assert "trajectory artifact path" in failed["error"]
    assert _remote_head(remote) == _git(repo, "rev-parse", "HEAD")

    (output / "unrelated.npz").unlink()
    result = publication.publish(output, repo=repo)

    assert result["status"] == "PUBLISHED"
    tree = _git(remote, "ls-tree", "-r", "--name-only", result["commit_sha"]).splitlines()
    assert "trajectory-replays/trace-0123456789abcdef0123456789abcdef/trace-0123456789abcdef0123456789abcdef/trajectories/trial-7.npz" in tree
    assert any(item.endswith("/trajectories/trial-7.meta.json.gz") for item in tree)
    assert any(item.endswith("/trajectories/trial-7.html") for item in tree)
    assert all(not item.endswith("/unrelated.npz") for item in tree)
    manifest = publication.read_json(output / "manifest.json.gz")
    assert manifest["collection_kind"] == "trajectory-replay"
    assert manifest["source_directory"] == "/tmp/original-run"
    assert manifest["requested_count"] == 1
    assert manifest["completed_count"] == 1
    assert manifest["source_artifacts"] == [{"path": "poses/trial-7.json.gz"}]
    assert _git(remote, "log", "-1", "--format=%s", result["commit_sha"]) == "trajectory: trace-0123456789abcdef0123456789abcdef (1 replays)"
    assert npz.is_file() and html.is_file()


def test_invalid_trajectory_archive_and_external_html_are_not_published(
    git_repo: tuple[Path, Path], tmp_path: Path
) -> None:
    repo, remote = git_repo
    output = tmp_path / "invalid"
    _trace_operation(output)
    output.joinpath("trajectories").mkdir(parents=True, exist_ok=True)
    output.joinpath("trajectories/trial-7.npz").write_bytes(b"invalid")
    result = publication.publish(output, repo=repo)
    assert result["status"] == "PUSH_FAILED"
    assert "invalid trajectory NPZ" in result["error"]

    output.joinpath("trajectories/trial-7.npz").unlink()
    _valid_html(output).write_text(
        "<html><body><script src='https://cdn.invalid/viewer.js'></script></body></html>",
        encoding="utf-8",
    )
    result = publication.publish(output, repo=repo)
    assert result["status"] == "PUSH_FAILED"
    assert "self-contained" in result["error"]
    assert _remote_head(remote) == _git(repo, "rev-parse", "HEAD")


def test_trace_export_limit_fails_before_manifest_and_preserves_files(
    git_repo: tuple[Path, Path], tmp_path: Path
) -> None:
    repo, remote = git_repo
    output = tmp_path / "limited"
    _trace_operation(output, limit=1)
    _valid_npz(output)
    _valid_html(output)

    result = publication.publish(output, repo=repo, push=False)

    assert result["status"] == "LOCAL_ONLY"
    assert "trajectory export limit exceeded before manifest publication" in result["error"]
    assert not (output / "manifest.json.gz").exists()
    assert (output / "trace.json.gz").is_file()
    assert (output / "trajectories/trial-7.npz").is_file()
    assert _remote_head(remote) == _git(repo, "rev-parse", "HEAD")


def test_trace_status_maps_to_non_scientific_run_status_and_counts(
    tmp_path: Path,
) -> None:
    output = tmp_path / "operation"
    _trace_operation(output)
    operation = publication._experiment(output)

    assert operation.collection_kind == "trajectory-replay"
    assert operation.name == operation.run_id == "trace-0123456789abcdef0123456789abcdef"
    assert operation.requested_trials is None
    assert operation.completed_trials is None
    assert operation.run_status == "COMPLETED"
    assert operation.solver == {"n": 1, "seed": 2}
    assert operation.replay_requested_count == 1
    assert operation.replay_completed_count == 1


def test_publisher_rejects_trajectory_filename_with_wrong_global_id(tmp_path):
    output = tmp_path / "identity"
    _trace_operation(output)
    numeric = _valid_npz(output)
    metadata = numeric.with_name("trial-7.meta.json.gz")
    numeric.rename(numeric.with_name("trial-8.npz"))
    metadata.rename(metadata.with_name("trial-8.meta.json.gz"))
    result = publication.publish(output, push=False)
    assert "filename disagrees" in result["error"]

