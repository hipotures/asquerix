"""Measure strategy-interpreter overhead against the legacy solver on matched starts.

Both paths run the same initialized worlds with recording disabled. The legacy
time is the full legacy submission minus an initialization-only submission of
the same IDs; the interpreter time is its synchronized slice loop from those
initialized poses. Results must be byte-identical or the measurement fails.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from pathlib import Path
import statistics
from time import perf_counter

import numpy as np
import warp as wp

from asquerix.gpu import Batch, Config
from asquerix.lab.config import Campaign
from asquerix.lab.gpu import StrategyBatch
from asquerix.lab.storage import environment
from asquerix.lab.strategy import compile_program, control_program
from asquerix.persistence import write_json


def legacy(config, count, offset, device):
    full = Batch(config, count, device)
    init = Batch(Config(**{**asdict(config), "max_attempts": 0}), count, device)
    init.poses.zero_()
    init.work.zero_()
    initial, init_timing = init.run(count, offset)
    poses, _ = init.get_poses(np.arange(count, dtype=np.int32))
    final, full_timing = full.run(count, offset)
    return initial, poses, final, init_timing, full_timing


def interpreter(campaign, initial, poses, ids):
    program = compile_program(control_program("legacy_compress"))
    batch = StrategyBatch(campaign, [program], poses, initial, ids,
                          np.zeros(len(ids), dtype=np.uint64), np.zeros(len(ids), dtype=np.int32))
    begin = perf_counter()
    while not batch.advance():
        pass
    loop = perf_counter() - begin
    states, _, _ = batch.collect()
    return states, loop, batch.timings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=11)
    parser.add_argument("--count", type=int, default=1024)
    parser.add_argument("--offset", type=int, default=100000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--output", type=Path, default=Path("artifacts/lab/overhead/n11-1024.json.gz"))
    args = parser.parse_args()
    wp.init()
    device = wp.get_device(args.device)
    if not device.is_cuda:
        raise SystemExit("A CUDA device is required; no CPU fallback")
    config = Config(n=args.n, max_sweeps=480)  # the legacy_compress control uses 128 attempts x 480 sweeps
    ids = np.arange(args.count, dtype=np.uint64) + np.uint64(args.offset)
    rows = []
    for slice_sweeps in (16, 128):
        campaign = Campaign(name="Overhead", n=args.n, batch_capacity=args.count, slice_sweeps=slice_sweeps,
                            publication={"enabled": False})
        for repeat in range(args.repeats + 1):  # repeat 0 is the JIT/warm-up pass and is reported separately
            initial, poses, final, init_timing, full_timing = legacy(config, args.count, args.offset, args.device)
            keep = initial["termination"] != 3
            states, loop, timings = interpreter(campaign, initial[keep], poses[keep], ids[keep])
            for name in final.dtype.names:
                if states["result"][name].tobytes() != final[keep][name].tobytes():
                    raise SystemExit(f"Legacy program differs from legacy solver in result.{name}; no overhead reported")
            rows.append({"slice_sweeps": slice_sweeps, "repeat": repeat, "warmup": repeat == 0,
                         "worlds": int(keep.sum()),
                         "legacy_compression_device_seconds": full_timing["device_seconds"] - init_timing["device_seconds"],
                         "legacy_full_device_seconds": full_timing["device_seconds"],
                         "legacy_init_device_seconds": init_timing["device_seconds"],
                         "interpreter_device_seconds": timings["device_seconds"],
                         "interpreter_loop_seconds": loop, "interpreter_slices": timings["slice_count"],
                         "interpreter_transfer_seconds": timings["transfer_seconds"],
                         "interpreter_upload_initialize_seconds": timings["upload_initialize_seconds"]})
    summary = {}
    for slice_sweeps in (16, 128):
        measured = [row for row in rows if row["slice_sweeps"] == slice_sweeps and not row["warmup"]]
        legacy_s = statistics.median(row["legacy_compression_device_seconds"] for row in measured)
        device_s = statistics.median(row["interpreter_device_seconds"] for row in measured)
        loop_s = statistics.median(row["interpreter_loop_seconds"] for row in measured)
        summary[str(slice_sweeps)] = {"median_legacy_compression_device_seconds": legacy_s,
                                      "median_interpreter_device_seconds": device_s,
                                      "median_interpreter_loop_seconds": loop_s,
                                      "device_ratio": device_s / legacy_s, "loop_ratio": loop_s / legacy_s}
    document = {"schema": "asquerix-lab-overhead-v1", "n": args.n, "count": args.count, "offset": args.offset,
                "recording": False, "byte_identical_results": True,
                "scope": "Legacy compression = full legacy device time minus initialization-only device time on the same IDs. "
                         "Interpreter = legacy_compress program from those initialized poses; loop includes per-slice host synchronization.",
                "summary": summary, "rows": rows, "environment": environment(device)}
    write_json(args.output, document)
    for key, value in summary.items():
        print(f"slice_sweeps={key}: legacy {value['median_legacy_compression_device_seconds']:.4f}s, "
              f"interpreter device {value['median_interpreter_device_seconds']:.4f}s (x{value['device_ratio']:.2f}), "
              f"loop {value['median_interpreter_loop_seconds']:.4f}s (x{value['loop_ratio']:.2f})")
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
