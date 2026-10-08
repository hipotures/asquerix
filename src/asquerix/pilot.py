"""Reproducible single-GPU pilot: identical n=12 inputs across batch sizes."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .gpu import Config
from .runner import run, write_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="Bounded single-GPU pilot campaign")
    parser.add_argument("--output", type=Path, default=Path("runs/pilot"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--max-seconds", type=float, default=300.0)
    args = parser.parse_args(argv)
    if not np.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("max-seconds must be positive and finite")
    args.output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    results = []
    def execute(label, n, batch_size, trials=512, retain_all=False):
        remaining = args.max_seconds - (perf_counter() - started)
        if remaining <= 0:
            return False
        result = run(Config(n=n), trials=trials, batch_size=batch_size, device=args.device,
                     output=args.output / label, sample_every=128, keep_best=10, max_images=3,
                     audit_size=32, retain_all=retain_all, max_seconds=remaining)
        results.append({"label": label, "n": n, "batch_size": batch_size, "summary": result["summary"]})
        write_json(args.output / "campaign.json", {"elapsed_seconds": perf_counter() - started,
                   "wall_budget_seconds": args.max_seconds, "runs": results})
        environment = json.loads((args.output / label / "environment.json").read_text())
        return environment["stop_reason"] == "TRIALS_COMPLETED"
    for n in (11, 16):
        if not execute(f"tiny-n{n}", n, 8, trials=8, retain_all=True):
            return 0
    for size in (8, 32, 128, 512):
        if not execute(f"sweep-b{size}", 12, size):
            return 0
    sweep = [r for r in results if r["label"].startswith("sweep")]
    chosen = max(sweep, key=lambda r: r["summary"]["throughput"]["simulation_seconds"]["attempted_trials_per_second"])["batch_size"]
    for repeat in range(3):
        if not execute(f"repeat-{repeat}", 12, chosen):
            return 0
    for n in (11, 16):
        if not execute(f"search-n{n}", n, chosen):
            return 0
    rates = [r["summary"]["throughput"]["simulation_seconds"]["attempted_trials_per_second"]
             for r in results if r["label"].startswith("repeat")]
    # Scalar search outcomes must be identical for every batch partition and
    # repeat. Timing and audit status are intentionally excluded from equality.
    reference = None
    partition_equal = True
    for result in results:
        if result["n"] != 12:
            continue
        records = [json.loads(line) for line in (args.output / result["label"] / "trials.jsonl").read_text().splitlines()]
        scalars = [{k: v for k, v in r.items() if k not in ("validation_status", "independent_validation")}
                   for r in records]
        if reference is None:
            reference = scalars
        else:
            partition_equal &= reference == scalars
    write_json(args.output / "campaign.json", {
        "elapsed_seconds": perf_counter() - started, "wall_budget_seconds": args.max_seconds,
        "chosen_batch_size": chosen, "repeat_throughput_mean": float(np.mean(rates)),
        "repeat_throughput_std": float(np.std(rates, ddof=1)),
        "n12_scalar_partition_equality": partition_equal, "runs": results,
    })
    if not partition_equal:
        raise RuntimeError("Batch partitioning changed scalar search outcomes; artifacts preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
