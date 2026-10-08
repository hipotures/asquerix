"""Small research CLI; no rendering or host search decisions in the hot path."""
import argparse
from dataclasses import fields
import json
from pathlib import Path
import sys

from .geometry import validate_document
from .output import render_selected, write_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Batched GPU compression of rotating unit squares")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="Run a bounded CUDA batch campaign")
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
    run_parser.add_argument("--output", default="runs/run")
    run_parser.add_argument("--retain-all", action="store_true", help="Transfer/audit all poses in a small correctness run")
    commands.add_parser("diagnose", help="Record actual software and CUDA environment")
    valid = commands.add_parser("validate", help="Independently check saved pose JSON or run directory")
    valid.add_argument("path", type=Path)
    valid.add_argument("--tolerance", type=float, default=1e-8)
    render = commands.add_parser("render", help="Render saved coordinates offline")
    render.add_argument("path", type=Path)
    render.add_argument("--output", type=Path, required=True)
    render.add_argument("--max-images", type=int, default=10)
    report = commands.add_parser("report", help="Regenerate a report from persisted scalar records")
    report.add_argument("directory", type=Path)
    compare = commands.add_parser("compare", help="Compare recorded run statistics, with budgets shown")
    compare.add_argument("directories", type=Path, nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            from .runner import run
            options = vars(args).copy()
            options.pop("command")
            config = Config(**{f.name: options.pop(f.name) for f in fields(Config)})
            result = run(config, **options)
            print(json.dumps({"directory": result["directory"], "throughput": result["summary"]["throughput"],
                              "statistics": result["summary"]["statistics"]}, indent=2))
        elif args.command == "diagnose":
            from .runner import environment
            import warp as wp
            wp.init()
            value = environment()
            value["cuda_devices"] = [str(device) for device in wp.get_cuda_devices()]
            value["cuda_available"] = bool(value["cuda_devices"])
            print(json.dumps(value, indent=2))
        elif args.command in ("validate", "render"):
            paths = sorted((args.path / "poses").glob("*.json")) if args.path.is_dir() else [args.path]
            documents = [json.loads(path.read_text()) for path in paths]
            if args.command == "validate":
                results = []
                for d in documents:
                    no_pose = (isinstance(d, dict) and d.get("termination_reason") == "INIT_FAILED"
                               and d.get("gpu_status") == "NO_ACCEPTED_POSE"
                               and d.get("side") is None and d.get("poses") == [])
                    validation = ({"status": "NOT_CHECKED", "diagnostic": "Initialization exhausted; no final pose exists."}
                                  if no_pose else validate_document(d, args.tolerance))
                    identifier = d.get("trial_id", d.get("fixture_id")) if isinstance(d, dict) else None
                    results.append({"trial_id": identifier, **validation})
                print(json.dumps(results, indent=2, allow_nan=False))
                return 1 if any(r["status"] == "INVALID" for r in results) else 0
            rendered = render_selected(documents, args.output, args.max_images)
            print(json.dumps([str(p) for p in rendered]))
        elif args.command == "report":
            directory = args.directory
            records = [json.loads(line) for line in (directory / "trials.jsonl").read_text().splitlines()]
            old = json.loads((directory / "summary.json").read_text())
            print(json.dumps(write_report(directory, records, old["timings"], old.get("metadata")), indent=2))
        elif args.command == "compare":
            for directory in args.directories:
                summary = json.loads((directory / "summary.json").read_text())
                config = json.loads((directory / "config.json").read_text())
                print(json.dumps({"directory": str(directory), "config": config,
                                  "throughput": summary["throughput"], "statistics": summary["statistics"],
                                  "audit": summary["audit_coverage"]}))
        return 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
