"""Presentation contracts, compressed artifacts, and quiet publication behavior."""
from io import StringIO
from pathlib import Path
import json
import subprocess
import sys

import pytest
from rich.console import Console

from asquerix import cli, runner, publication
from asquerix.output import summarize
from asquerix.persistence import read_json, write_json
from asquerix.presentation import RunProgress
from test_runner import _factory


def experiment(directory, *, batch=2, n=1, seed=123, compressed=True, gpu="Test GPU"):
    directory.mkdir()
    records = [dict(trial_id=i, n=n, side=4.0+i/10, gpu_status="GPU_FEASIBLE",
                    validation_status="NUMERICALLY_VALIDATED" if i == 0 else "NOT_CHECKED",
                    termination_reason="BUDGET_EXHAUSTED") for i in range(2)]
    summary = summarize(records, dict(device_seconds=2.0/batch, simulation_seconds=2.0/batch,
                                     end_to_end_seconds=3.0))
    summary["metadata"] = dict(experiment_name=directory.name, solver=dict(n=n), requested_trials=2,
                               stop_reason="TRIALS_COMPLETED", run_status="COMPLETED")
    config = dict(solver=dict(n=n, seed=seed, max_sweeps=120),
                  runner=dict(batch_size=batch, trials=2, trial_offset=0, device="cuda:0"))
    env = dict(gpu_query=dict(stdout=f"name, uuid, driver\n{gpu}, UUID, driver\n"),
               dependencies={"warp-lang": "1.18.0", "numpy": "2.5.3"}, source_sha256={"gpu.py": "same"})
    for name, value in (("summary", summary), ("config", config), ("environment", env)):
        if compressed:
            write_json(directory / f"{name}.json", value)
        else:
            (directory / f"{name}.json").write_text(json.dumps(value))
    return summary


def test_compare_table_reads_both_formats_and_preserves_columns(tmp_path, capsys):
    a, b = tmp_path / "batch2", tmp_path / "batch8"
    experiment(a, compressed=False)
    experiment(b, batch=8)
    assert cli.main(["compare", str(a), str(b)]) == 0
    output = capsys.readouterr().out
    for label in ("Experiment", "GPU trials/s", "Speedup", "Best validated L", "Validated/total", "batch2", "batch8", "4.00x"):
        assert label in output
    assert "\x1b" not in output
    assert '"statistics"' not in output
    assert "Warning" not in output


@pytest.mark.parametrize("change", [dict(n=2), dict(seed=321), dict(gpu="Another GPU")])
def test_compare_warns_about_uncontrolled_workloads(tmp_path, capsys, change):
    a, b = tmp_path / "a", tmp_path / "b"
    experiment(a)
    experiment(b, **change)
    assert cli.main(["compare", str(a), str(b)]) == 0
    assert "not a controlled comparison" in capsys.readouterr().out


def test_json_compare_saves_paths_without_using_rich(tmp_path, monkeypatch, capsys):
    a = tmp_path / "a"
    experiment(a)
    monkeypatch.setattr(cli, "_console", lambda: pytest.fail("Rich invoked in --json mode"))
    output = tmp_path / "compare.json"
    assert cli.main(["compare", str(a), "--json", "--output", str(output)]) == 0
    text = capsys.readouterr().out
    assert str(output)+".gz" in text
    assert '"experiments"' not in text and "\x1b" not in text
    assert read_json(output)["experiments"][0]["summary"]["record_count"] == 2


def test_json_process_does_not_import_rich(tmp_path):
    pose = write_json(tmp_path / "pose.json", dict(n=1, side=2, poses=[[0, 0, 0]], trial_id=1))
    code = "from asquerix.cli import main; import sys; status=main(sys.argv[1:]); assert 'rich' not in sys.modules; raise SystemExit(status)"
    result = subprocess.run([sys.executable, "-c", code, "validate", str(pose), "--json", "--output", str(tmp_path / "valid.json")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "Validation:" in result.stdout and '"status"' not in result.stdout


@pytest.mark.parametrize("compressed", [False, True])
def test_validate_and_render_saved_poses(tmp_path, capsys, compressed):
    directory = tmp_path / "run"
    (directory / "poses").mkdir(parents=True)
    document = dict(n=1, side=2, poses=[[0, 0, 0]], trial_id=1, validation_status="NUMERICALLY_VALIDATED")
    path = directory / "poses" / "trial-1.json"
    if compressed:
        write_json(path, document)
    else:
        path.write_text(json.dumps(document))
    assert cli.main(["validate", str(directory)]) == 0
    assert "NUMERICALLY_VALIDATED" in capsys.readouterr().out
    render = tmp_path / "render"
    assert cli.main(["render", str(directory), "--output", str(render), "--json"]) == 0
    assert (render / "trial-1.svg").is_file()
    assert read_json(render / "render.json")["files"] == [str(render / "trial-1.svg")]
    assert "SVG:" in capsys.readouterr().out


def test_cli_errors_remain_visible_on_stderr(tmp_path, capsys):
    assert cli.main(["validate", str(tmp_path / "missing.json")]) == 2
    capture = capsys.readouterr()
    assert "ERROR:" in capture.err
    assert capture.out == ""


def test_real_tty_progress_starts_and_counts_only_finished_batches(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    stream = StringIO()
    console = Console(file=stream, force_terminal=True, width=110)
    event = dict(event="init", experiment_name="tty-test", n=12, device="cuda:0 RTX 4070 Ti", completed=0,
                 requested=8, batch_size=4, elapsed_seconds=0, device_seconds=0,
                 validated_count=0, best_validated_L=None)
    with RunProgress(console) as progress:
        progress.update(event)
        progress.update({**event, "event": "batch-start"})
        assert progress.progress.tasks[0].completed == 0
        progress.update({**event, "event": "batch-completed", "completed": 4, "device_seconds": 2,
                         "validated_count": 1, "best_validated_L": 4.1})
        assert progress.progress.tasks[0].completed == 4
        assert "best validated L 4.10000000" in progress.progress.tasks[0].fields["metrics"]
    assert "tty-test" in stream.getvalue()


def test_single_gpu_batch_shows_activity_without_a_percentage_or_completion_bar(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    console = Console(file=StringIO(), force_terminal=True, width=110)
    event = dict(event="batch-start", experiment_name="single-batch", n=16, device="cuda:0",
                 completed=0, requested=1000, batch_size=32768, current_batch_trials=1000,
                 device_seconds=0, validated_count=0, best_validated_L=None)
    with RunProgress(console) as progress:
        progress.update(event)
        assert progress.progress.columns == progress.activity_columns
        assert progress.progress.tasks[0].completed == 0
        with console.capture() as captured:
            console.print(progress.progress.get_renderable())
        display = captured.get()
        assert "GPU batch 1/1" in display and "1000 trials running" in display
        assert "0/1000" not in display and "0%" not in display
        progress.update({**event, "event": "batch-completed", "completed": 1000,
                         "device_seconds": 2})
        assert progress.progress.tasks[0].completed == 1000
        assert progress.progress.columns == progress.activity_columns


def test_multiple_gpu_batches_show_progress_only_for_completed_results(monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    console = Console(file=StringIO(), force_terminal=True, width=110)
    event = dict(event="batch-start", experiment_name="multiple-batches", n=16, device="cuda:0",
                 completed=0, requested=1000, batch_size=400, current_batch_trials=400,
                 device_seconds=0, validated_count=0, best_validated_L=None)
    with RunProgress(console) as progress:
        progress.update(event)
        assert progress.progress.columns == progress.batch_columns
        progress.update({**event, "event": "batch-completed", "completed": 400, "device_seconds": 2})
        progress.update({**event, "completed": 400, "device_seconds": 2})
        assert progress.progress.tasks[0].completed == 400
        with console.capture() as captured:
            console.print(progress.progress.get_renderable())
        display = captured.get()
        assert "GPU batch 2/3" in display
        assert "40%" in display and "400/1000" in display


@pytest.fixture
def fake_run(monkeypatch):
    actual_run = runner.run
    monkeypatch.setattr(runner, "environment", lambda: dict(python="test", gpu_query=dict(exit_code=0), dependencies={}))
    def run(config, **options):
        return actual_run(config, **options, batch_factory=_factory())
    monkeypatch.setattr(runner, "run", run)


def test_cli_no_push_finalizes_artifacts_and_uses_offline_publisher(tmp_path, monkeypatch, capsys, fake_run):
    calls = []
    def publish(directory, *, push):
        calls.append(push)
        write_json(Path(directory) / "manifest.json", dict(test=True))
        return dict(status="LOCAL_ONLY", seconds=0, error=None, commit_sha=None, url=None)
    monkeypatch.setattr(publication, "publish", publish)
    output = tmp_path / "quiet-run"
    assert cli.main(["run", "--experiment", "quiet-run", "--n", "1", "--trials", "3", "--batch-size", "2", "--max-attempts", "0", "--output", str(output), "--json", "--no-push"]) == 0
    assert calls == [False]
    assert read_json(output / "summary.json")["record_count"] == 3
    assert (output / "manifest.json.gz").is_file()
    text = capsys.readouterr().out
    assert "Results:" in text and "Trials:" in text and "COMPLETED + LOCAL_ONLY" in text
    assert '"statistics"' not in text and "\x1b" not in text


def test_cli_default_publication_and_failure_are_separate_from_computation(tmp_path, monkeypatch, capsys, fake_run):
    calls = []
    def publish(directory, *, push):
        calls.append(push)
        return dict(status="PUSH_FAILED", seconds=0.1, error="Authentication unavailable", commit_sha=None, url=None)
    monkeypatch.setattr(publication, "publish", publish)
    output = tmp_path / "push-failure"
    assert cli.main(["run", "--experiment", "push-failure", "--n", "1", "--trials", "2", "--max-attempts", "0", "--output", str(output)]) == 3
    capture = capsys.readouterr()
    assert calls == [True]
    assert "Authentication unavailable" in capture.err
    assert "COMPLETED + PUSH_FAILED" in capture.out
    assert '"statistics"' not in capture.out and "\x1b" not in capture.out
    assert read_json(output / "summary.json")["record_count"] == 2
    assert read_json(output / "publication.json")["status"] == "PUSH_FAILED"


def test_tty_runtime_diagnostics_are_managed_above_progress_on_stderr(tmp_path, monkeypatch, fake_run):
    class TTYBuffer(StringIO):
        def isatty(self):
            return True
    stdout, stderr = TTYBuffer(), TTYBuffer()
    monkeypatch.setenv('TERM', 'xterm-256color')
    monkeypatch.setattr(sys, 'stdout', stdout)
    monkeypatch.setattr(sys, 'stderr', stderr)
    actual_run = runner.run
    def run(config, **options):
        from rich.file_proxy import FileProxy
        assert isinstance(sys.stdout, FileProxy)
        assert isinstance(sys.stderr, FileProxy)
        print('Warp initialization diagnostic')
        print('CUDA compilation diagnostic', file=sys.stderr)
        result = actual_run(config, **options)
        sys.stderr.write('Final diagnostic without newline')
        return result
    monkeypatch.setattr(runner, 'run', run)
    monkeypatch.setattr(publication, 'publish', lambda *args, **kwargs: dict(status='LOCAL_ONLY', seconds=0, error=None))
    assert cli.main(['run', '--experiment', 'tty-diagnostics', '--n', '1', '--trials', '2', '--max-attempts', '0', '--no-push', '--output', str(tmp_path/'run')]) == 0
    output, diagnostics = stdout.getvalue(), stderr.getvalue()
    assert 'COMPLETED + LOCAL_ONLY' in output
    for message in ('Warp initialization diagnostic', 'CUDA compilation diagnostic', 'Final diagnostic without newline'):
        assert diagnostics.count(message) == 1
        assert message not in output


def test_tty_runtime_failure_keeps_traceback_on_stderr(tmp_path, monkeypatch):
    class TTYBuffer(StringIO):
        def isatty(self):
            return True
    stdout, stderr = TTYBuffer(), TTYBuffer()
    monkeypatch.setenv('TERM', 'xterm-256color')
    monkeypatch.setattr(sys, 'stdout', stdout)
    monkeypatch.setattr(sys, 'stderr', stderr)
    def run(*args, **kwargs):
        print('CUDA compiler detail', file=sys.stderr)
        raise RuntimeError('CUDA compilation failed')
    monkeypatch.setattr(runner, 'run', run)
    assert cli.main(['run', '--no-push', '--output', str(tmp_path/'failure')]) == 2
    assert 'CUDA compiler detail' in stderr.getvalue()
    assert 'Traceback' in stderr.getvalue()
    assert 'RuntimeError: CUDA compilation failed' in stderr.getvalue()
    assert 'CUDA compilation failed' not in stdout.getvalue()
