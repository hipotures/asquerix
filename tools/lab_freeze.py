"""Freeze the actual pre-laboratory source and defined CUDA reference bytes."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
from pathlib import Path
import platform
import subprocess
from time import perf_counter

import numpy as np

from asquerix.geometry import validate_pose
from asquerix.gpu import Batch, Config
from asquerix.persistence import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/lab/baseline"))
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    destination = args.output.resolve()
    if destination.exists():
        raise ValueError("Refusing to overwrite a frozen baseline")
    destination.mkdir(parents=True)
    sources = {}
    for path in sorted((root / "src/asquerix").glob("*.py")):
        sources[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (destination / "gpu.py").write_bytes((root / "src/asquerix/gpu.py").read_bytes())
    experiments = []
    started = perf_counter()
    cases = [(n, seed, offset, 2) for n in (1, 4, 11, 12, 16, 32)
             for seed, offset in ((20261008, 0), (987654321, 4096))]
    cases += [(11, 20261008, offset, 1) for offset in (4124, 4372)]
    cases += [(4, 2**64 - 123, 2**64 - 4, 2)]
    for n, seed, offset, count in cases:
        config = Config(n=n, seed=seed, max_attempts=128, max_sweeps=480)
        initial = Batch(Config(**{**asdict(config), "max_attempts": 0}), count, args.device)
        initial.poses.zero_()
        initial.work.zero_()
        initial_results, initial_timing = initial.run(count, offset)
        initial_poses, _ = initial.get_poses(np.arange(count, dtype=np.int32))
        batch = Batch(config, count, args.device)
        batch.poses.zero_()
        batch.work.zero_()
        results, timing = batch.run(count, offset)
        poses, _ = batch.get_poses(np.arange(count, dtype=np.int32))
        arrays = {"initial_poses": initial_poses, "poses": poses}
        # Store each named field independently; never compare struct padding.
        arrays.update({"result_" + name: results[name].copy() for name in results.dtype.names})
        arrays.update({"initial_" + name: initial_results[name].copy() for name in results.dtype.names})
        filename = f"n{n}-seed{seed}-id{offset}.npz"
        np.savez_compressed(destination / filename, **arrays)
        validation = [validate_pose(pose, float(row["side"]), 1e-9)
                      for pose, row in zip(poses, results, strict=True)]
        entry = {"config": asdict(config), "offset": str(offset), "count": count,
                 "file": filename, "sha256": hashlib.sha256((destination / filename).read_bytes()).hexdigest(),
                 "validation": validation, "timing": timing, "initial_timing": initial_timing}
        experiments.append(entry)
        print(f"Frozen n={n}, seed={seed}, first ID={offset}, {count} worlds")
    import warp as wp
    device = wp.get_device(args.device)
    manifest = {"schema": "asquerix-lab-baseline-v1", "source_sha256": sources,
                "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                "remote_main": subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], cwd=root, text=True).strip(),
                "device": {"selector": str(device), "uuid": device.uuid, "name": device.name},
                "python": platform.python_version(),
                "dependencies": {key: importlib.metadata.version(key) for key in ("numpy", "warp-lang", "rich", "pytest")},
                "scratch_initialization": "All pose and proposal buffers zeroed; named result fields only, no struct padding.",
                "experiments": experiments, "wall_seconds": perf_counter() - started}
    write_json(destination / "manifest.json.gz", manifest)
    print(f"Baseline saved: {destination}")


if __name__ == "__main__":
    main()
