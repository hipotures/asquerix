"""Terminal presentation only; never imported by numerical kernels."""
from collections import Counter
from pathlib import Path
import sys
from time import monotonic


def number(value, digits=3):
    return "—" if value is None else f"{value:,.{digits}f}"


def _rate(summary, key):
    return summary.get("throughput", {}).get(key, {}).get("attempted_trials_per_second")


class PlainProgress:
    """Bounded plain-text logging for redirected output and --json."""
    def __init__(self):
        self.stream = sys.stdout
        self.last = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, event):
        now = monotonic()
        if event["event"] == "init":
            print(f"Experiment: {event['experiment_name']} | N={event['n']} | GPU={event['device']}", file=self.stream, flush=True)
        elif event["event"] in ("batch-completed", "finalizing") and (
                now - self.last >= 10 or event["event"] == "finalizing"):
            print(f"Completed: {event['completed']}/{event['requested']} | validated={event['validated_count']} | best validated L={number(event['best_validated_L'], 8)}", file=self.stream, flush=True)
            self.last = now


class TraceProgress:
    """Separate replay progress, never counted as scientific search trials."""
    def __init__(self, console):
        self.console = console
        self.progress = None
        self.task = None

    def __enter__(self):
        if self.console is not None:
            from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
            self.progress = Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(),
                                     console=self.console, transient=True)
            self.progress.start()
        return self

    def __exit__(self, *exc):
        if self.progress:
            self.progress.stop()
        return False

    def update(self, event):
        description = f"Recording replay {event['trial_id']} · {event['completed']}/{event['total']} finalized"
        if self.progress:
            if self.task is None:
                self.task = self.progress.add_task(description, total=event["total"])
            self.progress.update(self.task, description=description, completed=event["completed"])
        elif event["event"] == "replay-completed":
            print(f"Replay {event['trial_id']}: {event['status']}", file=sys.stderr, flush=True)


class RunProgress:
    """Show batch progress; a single GPU batch uses only a spinner and elapsed time."""
    def __init__(self, console):
        self.console = console
        self.plain = PlainProgress() if not console.is_terminal else None
        self.progress = None
        self.task = None

    def __enter__(self):
        if self.plain:
            return self
        # Imports stay lazy so --json does not load Rich.
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
        from rich.text import Text

        class DisplayProgress(Progress):
            def get_renderables(self):
                tasks = self.tasks
                if not tasks:
                    return
                task = tasks[0]
                if task.fields.get("header"):
                    yield Text(task.fields["header"])
                yield self.make_tasks_table(tasks)
                if task.fields.get("metrics"):
                    yield Text(task.fields["metrics"])

        self.activity_columns = (SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn())
        self.batch_columns = (
            SpinnerColumn(), TextColumn("{task.description}"), BarColumn(bar_width=None),
            TaskProgressColumn(), TextColumn("{task.completed:.0f}/{task.total:.0f}"),
            TimeElapsedColumn(), TimeRemainingColumn(),
        )
        self.progress = DisplayProgress(
            *self.activity_columns,
            console=self.console, refresh_per_second=2, transient=True,
            redirect_stdout=True, redirect_stderr=True,
        )
        self.task = self.progress.add_task("Preparing", total=1)
        self.progress.start()
        return self

    def __exit__(self, *exc):
        if self.progress:
            sys.stdout.flush()
            sys.stderr.flush()
            self.progress.stop()
        return False

    def update(self, event):
        if self.plain:
            self.plain.update(event)
            return
        gpu_seconds = event["device_seconds"]
        rate = event["completed"] / gpu_seconds if gpu_seconds > 0 else None
        requested, completed, size = event["requested"], event["completed"], event["batch_size"]
        batches = (requested + size - 1) // size
        self.progress.columns = self.batch_columns if batches > 1 else self.activity_columns
        phase = event["event"]
        if phase == "batch-start":
            count = event.get("current_batch_trials", min(size, requested - completed))
            description = f"GPU batch {completed // size + 1}/{batches} · {count} trials running"
        elif phase == "batch-completed":
            description = f"Saved batch {(completed + size - 1) // size}/{batches}"
        elif phase == "finalizing":
            description = "Finalizing artifacts"
        else:
            description = "Preparing GPU"
        header = f"{event['experiment_name']}\nN={event['n']} · {event['device']} · batch size={size}"
        metrics = (f"GPU {number(rate, 2)} trials/s · validated {event['validated_count']} · "
                   f"best validated L {number(event['best_validated_L'], 8)}")
        self.progress.update(self.task, description=description, total=requested, completed=completed,
                             header=header, metrics=metrics, refresh=True)


def run_summary(console, result, publication):
    from rich.table import Table
    summary = result["summary"]
    metadata = summary.get("metadata", {})
    times = summary.get("timings", {})
    stats = summary["statistics"]
    coverage = summary["audit_coverage"]
    table = Table(title=metadata.get("experiment_name", Path(result["directory"]).name), show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", overflow="fold")
    values = [
        ("N", metadata.get("solver", {}).get("n", "—")),
        ("Trials", f"{summary['record_count']:,} / {metadata.get('requested_trials', summary['record_count']):,}"),
        ("GPU time / throughput", f"{number(times.get('device_seconds'))} s / {number(_rate(summary, 'device_seconds'), 2)} trials/s"),
        ("Simulation end-to-end", f"{number(publication.get('computation_end_to_end_seconds', times.get('end_to_end_seconds')))} s"),
        ("End-to-end throughput", f"{number(summary['record_count'] / publication['computation_end_to_end_seconds'] if publication.get('computation_end_to_end_seconds') else _rate(summary, 'end_to_end_seconds'), 2)} trials/s"),
        ("Best validated L", number(stats["numerically_validated"]["best"], 8)),
        ("GPU-feasible mean / median L", f"{number(stats['gpu_accepted']['mean'], 8)} / {number(stats['gpu_accepted']['median'], 8)}"),
        ("Independent validation", f"{coverage['audited_trials']:,}/{coverage['total_trials']:,} checked; {coverage['numerically_validated_trials']:,} validated, {coverage['invalid_trials']:,} invalid, {coverage['indeterminate_trials']:,} indeterminate"),
        ("Termination", metadata.get("stop_reason", "UNKNOWN")),
        ("Status", f"{metadata.get('run_status', 'UNKNOWN')} + {publication['status']}"),
        ("Output", result["directory"]),
        ("Git publication time", f"{number(publication.get('seconds'))} s"),
        ("Total end-to-end", f"{number(publication.get('total_end_to_end_seconds', times.get('end_to_end_seconds')))} s"),
    ]
    if publication.get("commit_sha"):
        values.extend((("Commit", publication["commit_sha"]), ("GitHub", publication.get("url", "—"))))
    if publication.get("error"):
        values.append(("Publication diagnostic", publication["error"]))
    for label, value in values:
        table.add_row(label, str(value))
    console.print(table)


def compare_table(console, rows, warnings):
    from rich.table import Table
    table = Table(title="Experiment comparison", box=None, padding=(0, 1), collapse_padding=True)
    for label in ("Experiment", "N", "Trials", "Batch", "Sweeps", "GPU s", "GPU trials/s", "Speedup", "E2E s", "E2E trials/s", "Best validated L", "Mean L", "Median L", "Validated/total"):
        table.add_column(label, justify="left" if label == "Experiment" else "right", no_wrap=True)
    base = _rate(rows[0]["summary"], "device_seconds")
    for row in rows:
        summary, config = row["summary"], row["config"]
        stats = summary["statistics"]
        rate = _rate(summary, "device_seconds")
        metadata = summary.get("metadata", {})
        name = metadata.get("experiment_name", Path(row["directory"]).name)
        values = (name, config["solver"]["n"], summary["record_count"], config["runner"]["batch_size"],
                  config["solver"]["max_sweeps"], number(summary["timings"].get("device_seconds")), number(rate, 2),
                  f"{rate/base:.2f}x" if rate is not None and base and base > 0 else "—",
                  number(summary["timings"].get("end_to_end_seconds")), number(_rate(summary, "end_to_end_seconds"), 2),
                  number(stats["numerically_validated"]["best"], 8), number(stats["gpu_accepted"]["mean"], 7),
                  number(stats["gpu_accepted"]["median"], 7), f"{summary['audit_coverage']['numerically_validated_trials']}/{summary['record_count']}")
        table.add_row(*(str(value) for value in values))
    # Preserve every column in redirected logs; a wide comparison is scrollable.
    old_width = console.width
    console.width = max(old_width, 210)
    try:
        console.print(table, crop=False, soft_wrap=True)
    finally:
        console.width = old_width
    console.print("GPU time uses synchronized CUDA events; mean/median L use GPU-feasible trials. Best L uses independent validation.")
    for warning in warnings:
        console.print(f"Warning: {warning}", style="yellow", soft_wrap=True)


def validation_table(console, results):
    from rich.table import Table
    counts = Counter(result["status"] for result in results)
    table = Table(title="Independent numerical validation")
    table.add_column("Status")
    table.add_column("Candidates", justify="right")
    for status in ("NUMERICALLY_VALIDATED", "INDETERMINATE", "INVALID", "NOT_CHECKED"):
        table.add_row(status, str(counts[status]))
    console.print(table)
    for result in results:
        if result["status"] == "INVALID":
            console.print(f"Trial {result['trial_id']}: {result.get('error', 'Invalid geometry')}")
    console.print("Numerical validation is not a rigorous certificate.")


def diagnose_table(console, value):
    from rich.table import Table
    table = Table(title="Actual execution environment", show_header=False)
    for label, data in (("Python", value["python"]), ("Platform", value["platform"]),
                        ("CUDA devices", ", ".join(value["cuda_devices"]) or "Unavailable"),
                        ("GPU query", value["gpu_query"]["stdout"].strip() or value["gpu_query"].get("stderr", "")),
                        ("Source commit", value["git_revision"]["stdout"].strip())):
        table.add_row(label, str(data))
    for dependency, version in value["dependencies"].items():
        table.add_row(dependency, version)
    console.print(table)
