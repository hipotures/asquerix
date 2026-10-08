"""Human-readable CLI with optional quiet, disk-based structured output."""
import argparse
import csv
from contextlib import redirect_stdout
from dataclasses import fields
from pathlib import Path
import sys
from time import perf_counter
import traceback
from uuid import uuid4

from .geometry import validate_document
from .output import render_selected, write_report
from .persistence import pose_paths, read_json, read_jsonl, write_json


def _result_path(command, output=None):
    return Path(output) if output else Path("runs") / f"{command}-{uuid4().hex[:12]}.json.gz"


def _saved(paths):
    for label, path in paths:
        print(f"{label}: {path}")


def _console(*, file=None):
    from rich.console import Console
    stream = sys.stdout if file is None else file
    tty = bool(sys.stdout.isatty() and stream.isatty())
    return Console(file=stream, force_terminal=tty, color_system="auto" if tty else None,
                   markup=False, highlight=False)


def _validate(documents, tolerance):
    results = []
    for document in documents:
        no_pose = (isinstance(document, dict) and document.get("termination_reason") == "INIT_FAILED"
                   and document.get("gpu_status") == "NO_ACCEPTED_POSE"
                   and document.get("side") is None and document.get("poses") == [])
        validation = ({"status": "NOT_CHECKED", "diagnostic": "Initialization exhausted; no final pose exists."}
                      if no_pose else validate_document(document, tolerance))
        identifier = document.get("trial_id", document.get("fixture_id")) if isinstance(document, dict) else None
        results.append({"trial_id": identifier, **validation})
    return results


def _comparisons(directories):
    rows, warnings = [], []
    for directory in directories:
        try:
            environment = read_json(directory / "environment.json")
        except FileNotFoundError:
            environment = None
        rows.append({"directory": str(directory), "summary": read_json(directory / "summary.json"),
                     "config": read_json(directory / "config.json"), "environment": environment})
    first = rows[0]
    base_runner, base_solver = first["config"]["runner"], first["config"]["solver"]
    def provenance(row):
        environment = row["environment"]
        if environment is None:
            return None
        gpu_rows = list(csv.reader(environment.get("gpu_query", {}).get("stdout", "").splitlines()))
        hardware = tuple(tuple(item.strip() for item in record[:3]) for record in gpu_rows[1:])
        dependencies = environment.get("dependencies", {})
        return (hardware, dependencies.get("warp-lang"), dependencies.get("numpy"),
                environment.get("source_sha256"))
    baseline_provenance = provenance(first)
    if baseline_provenance is None:
        warnings.append(f"{first['directory']}: environment provenance unavailable; controlled comparability cannot be verified.")
    for row in rows[1:]:
        reasons = []
        if row["config"]["solver"] != base_solver:
            reasons.append("solver configuration (including N, seed, budgets or tolerances)")
        runner = row["config"]["runner"]
        if (runner.get("trial_offset", 0), runner.get("trials"), row["summary"]["record_count"]) != (
                base_runner.get("trial_offset", 0), base_runner.get("trials"), first["summary"]["record_count"]):
            reasons.append("requested or completed trial range")
        if runner.get("device") != base_runner.get("device"):
            reasons.append("GPU device selection")
        if any(runner.get(key) != base_runner.get(key) for key in (
                "retain_all", "sample_every", "audit_size", "keep_best", "max_images", "failure_examples")):
            reasons.append("host validation/persistence workload")
        current_provenance = provenance(row)
        if baseline_provenance is None or current_provenance is None:
            reasons.append("missing environment provenance")
        elif current_provenance != baseline_provenance:
            reasons.append("hardware, dependencies or source hashes")
        if reasons:
            warnings.append(f"{row['directory']}: different {', '.join(reasons)}; speedup is not a controlled comparison.")
    return rows, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Batched GPU compression of rotating unit squares")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="Run a bounded CUDA campaign and publish its artifacts")
    from .gpu import Config
    defaults = Config()
    for field in fields(Config):
        value = getattr(defaults, field.name)
        run_parser.add_argument("--" + field.name.replace("_", "-"), type=type(value), default=value)
    for key, default in (("trials", 64), ("batch_size", 32), ("trial_offset", 0), ("sample_every", 1000),
                         ("keep_best", 10), ("max_images", 10), ("audit_size", 16), ("failure_examples", 3)):
        run_parser.add_argument("--" + key.replace("_", "-"), type=int, default=default)
    run_parser.add_argument("--max-seconds", type=float, default=30.0)
    run_parser.add_argument("--device", default="cuda:0")
    run_parser.add_argument("--output", type=Path)
    run_parser.add_argument("--experiment", help="Safe human-readable experiment name")
    run_parser.add_argument("--no-push", action="store_true", help="Save artifacts locally without Git publication")
    run_parser.add_argument("--retain-all", action="store_true", help="Transfer/audit all poses in a small correctness run")
    diagnose = commands.add_parser("diagnose", help="Inspect actual software and CUDA environment")
    diagnose.add_argument("--output", type=Path)
    valid = commands.add_parser("validate", help="Independently check saved poses, including gzip archives")
    valid.add_argument("path", type=Path)
    valid.add_argument("--tolerance", type=float, default=1e-8)
    valid.add_argument("--output", type=Path)
    render = commands.add_parser("render", help="Render saved coordinates offline")
    render.add_argument("path", type=Path)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--max-images", type=int, default=10)
    report = commands.add_parser("report", help="Regenerate a report from persisted records")
    report.add_argument("directory", type=Path)
    compare = commands.add_parser("compare", help="Compare measured performance and validation coverage")
    compare.add_argument("directories", type=Path, nargs="+")
    compare.add_argument("--output", type=Path)
    for command in (run_parser, diagnose, valid, render, report, compare):
        command.add_argument("--json", action="store_true", help="Save compressed structured results; print paths, never JSON payloads")
    args = parser.parse_args(argv)
    console = None if args.json else _console()
    try:
        if args.command == "run":
            from .runner import run
            from .publication import publish
            from .presentation import PlainProgress, RunProgress
            import warp as wp
            display = PlainProgress() if args.json else RunProgress(_console(file=sys.stderr))
            options = vars(args).copy()
            for key in ("command", "json", "no_push"):
                options.pop(key)
            config = Config(**{f.name: options.pop(f.name) for f in fields(Config)})
            call_started = perf_counter()
            with wp.ScopedLogLevel(wp.LOG_WARNING), display:
                with redirect_stdout(sys.stderr):
                    result = run(config, **options, progress=display.update)
            computation_seconds = perf_counter() - call_started
            publication = publish(result["directory"], push=not args.no_push)
            publication["computation_end_to_end_seconds"] = computation_seconds
            publication["total_end_to_end_seconds"] = perf_counter() - call_started
            publication["timing_boundary"] = "Total CLI time includes run and publication; excludes final receipt serialization and completion display."
            receipt = write_json(Path(result["directory"]) / "publication.json", publication)
            if publication.get("error") and not args.no_push:
                print(f"Publication failed; saved results remain at {result['directory']}: {publication.get('error')}", file=sys.stderr)
            if args.json:
                metadata = result["summary"].get("metadata", {})
                print(f"Experiment: {metadata.get('experiment_name', args.experiment)}")
                print(f"Completed: {result['summary']['record_count']}/{args.trials}")
                directory = Path(result["directory"])
                _saved([(label, directory / filename) for label, filename in (
                    ("Results", "summary.json.gz"), ("Trials", "trials.jsonl.gz"), ("Report", "report.md"))])
                print(f"Status: {metadata.get('run_status', 'UNKNOWN')} + {publication['status']}")
                _saved([("Publication", receipt)])
                if publication.get("commit_sha"):
                    print(f"Commit: {publication['commit_sha']}")
                if publication.get("url"):
                    print(f"GitHub: {publication['url']}")
            else:
                from .presentation import run_summary
                run_summary(console, result, publication)
            return 3 if publication["status"] == "PUSH_FAILED" else 0
        if args.command == "diagnose":
            from .runner import environment
            import warp as wp
            with redirect_stdout(sys.stderr):
                wp.init()
                value = environment()
                value["cuda_devices"] = [str(device) for device in wp.get_cuda_devices()]
                value["cuda_available"] = bool(value["cuda_devices"])
            if args.json or args.output:
                path = write_json(_result_path("diagnose", args.output), value)
                if args.json:
                    _saved([("Environment", path)])
            if not args.json:
                from .presentation import diagnose_table
                diagnose_table(console, value)
        elif args.command in ("validate", "render"):
            paths = pose_paths(args.path / "poses") if args.path.is_dir() else [args.path]
            if not paths:
                raise ValueError(f"No saved pose documents found: {args.path}")
            documents = [read_json(path) for path in paths]
            if args.command == "validate":
                results = _validate(documents, args.tolerance)
                if args.json or args.output:
                    path = write_json(_result_path("validation", args.output), {"source": str(args.path), "tolerance": args.tolerance, "results": results})
                    if args.json:
                        _saved([("Validation", path)])
                if not args.json:
                    from .presentation import validation_table
                    validation_table(console, results)
                return 1 if any(r["status"] == "INVALID" for r in results) else 0
            rendered = render_selected(documents, args.output, args.max_images)
            if args.json:
                path = write_json(args.output / "render.json", {"source": str(args.path), "files": [str(p) for p in rendered]})
                _saved([("Rendering", path), *(("SVG", path) for path in rendered)])
            else:
                console.print(f"Rendered {len(rendered)} SVG files in {args.output}")
                for path in rendered:
                    console.print(str(path))
        elif args.command == "report":
            directory = args.directory
            records = list(read_jsonl(directory / "trials.jsonl"))
            old = read_json(directory / "summary.json")
            summary = write_report(directory, records, old["timings"], old.get("metadata"))
            if args.json:
                _saved([("Results", directory / "summary.json.gz"), ("Report", directory / "report.md"), ("Histogram", directory / "histogram.svg")])
            else:
                from .presentation import run_summary
                run_summary(console, {"directory": str(directory), "summary": summary}, {"status": "REPORT_ONLY"})
        elif args.command == "compare":
            rows, warnings = _comparisons(args.directories)
            if args.json:
                path = write_json(_result_path("comparison", args.output), {"experiments": rows, "warnings": warnings})
                _saved([("Comparison", path)])
                for warning in warnings:
                    print(f"Warning: {warning}", file=sys.stderr)
            else:
                from .presentation import compare_table
                compare_table(console, rows, warnings)
        return 0
    except RuntimeError:
        traceback.print_exc(file=sys.stderr)
        return 2
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
