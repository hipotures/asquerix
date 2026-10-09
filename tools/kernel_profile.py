"""Run one complete production batch for separately instrumented stage profiling."""
import argparse
from dataclasses import asdict
from pathlib import Path

from kernel_benchmark import clear_scratch, digest, load_source, save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--count", type=int, default=8192)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = load_source(args.source, "asquerix_profile_reference")
    config = module.Config(n=args.n, max_sweeps=480)
    batch = module.Batch(config, args.count, device=args.device)
    clear_scratch(batch)
    results, timing = batch.run(args.count, 0)
    save_json(args.output, dict(config=asdict(config), source_sha256=digest(args.source),
              device=str(batch.device), uuid=batch.device.uuid, count=args.count,
              timing=timing, kernel_properties=batch.kernel_properties,
              feasible_count=int(results["feasible"].sum()),
              timing_warning="Instrumented run; excluded from performance claims."))


if __name__ == "__main__":
    main()
