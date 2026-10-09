"""Freeze, compare, and time production CUDA kernels without CLI publication.

The archived module is an immutable comparison reference, never a production
fallback. Every timed launch uses Batch.run(), full budgets, and CUDA events.
"""
from __future__ import annotations

import argparse
import ctypes
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import numpy as np
import warp as wp

from asquerix import gpu
from asquerix.geometry import validate_pose
from asquerix.runner import environment

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/performance/cuda-20261009"
CURRENT_SOURCE_HASH = hashlib.sha256(Path(gpu.__file__).read_bytes()).hexdigest()


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_source(path, name="asquerix_perf_reference"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def exact(actual, expected, label):
    """Compare complete representations, including signed zeros and all fields."""
    if actual.dtype != expected.dtype or actual.shape != expected.shape:
        raise AssertionError(f"{label}: dtype/shape mismatch")
    if not np.array_equal(actual.view(np.uint8), expected.view(np.uint8)):
        raise AssertionError(f"{label}: bitwise mismatch")


def clear_scratch(batch):
    # INIT_FAILED leaves some pose slots unwritten. Define those input bytes
    # in the harness so exact comparisons include deterministic partial poses.
    batch.poses.zero_()
    batch.work.zero_()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def occupancy(module, device):
    """Query theoretical residency for the unchanged 32-thread launch size."""
    from warp._src.context import _resolve_cuda_kernel_forward_entry_point
    selected, owner, handle, block = _resolve_cuda_kernel_forward_entry_point(
        module.simulate, device, 32, "kernel_benchmark")
    driver = ctypes.CDLL("libcuda.so.1")
    blocks = ctypes.c_int()
    maximum_threads = ctypes.c_int()
    with wp.ScopedDevice(selected):
        status = driver.cuOccupancyMaxActiveBlocksPerMultiprocessor(
            ctypes.byref(blocks), ctypes.c_void_p(handle), ctypes.c_int(block), ctypes.c_size_t(0))
        attribute_status = driver.cuDeviceGetAttribute(
            ctypes.byref(maximum_threads), ctypes.c_int(39), ctypes.c_int(selected.ordinal))
    if status != 0 or attribute_status != 0:
        return {"cuda_status": status, "attribute_status": attribute_status}
    return {"active_blocks_per_sm": blocks.value, "threads_per_block": block,
            "maximum_threads_per_sm": maximum_threads.value,
            "theoretical_occupancy": blocks.value * block / maximum_threads.value,
            "sm_count": selected.sm_count, "method": "CUDA driver occupancy API; not achieved occupancy"}


def diagnostic(module, p_host, q_host, wall_mode, device="cuda:0"):
    p = wp.array(p_host, dtype=wp.vec3, device=device)
    q = wp.array(q_host, dtype=wp.vec3, device=device)
    values = wp.zeros((len(p_host), 7), dtype=float, device=device)
    wp.launch(module.contact_diagnostic, dim=len(p_host),
              inputs=[p, q, module.parameters(module.Config()), 2.0, wall_mode, values], device=device)
    wp.synchronize_device(device)
    return p.numpy().copy(), q.numpy().copy(), values.numpy().copy()


def contact_inputs():
    cases = [
        ((0, 0, 0), (1, 0, 0)),
        ((0, 0, 0), (1, 1, 0)),
        ((0, 0, 0), (1 + 1e-7, 0, 0)),
        ((0, 0, 0), (1 - 1e-7, 0, 0)),
        ((0, 0, 1e-7), (1, 0, -1e-7)),
        ((0, 0, 0.31), (0, 0, -0.27)),
        ((0, 0, 0.31), (1e-8, -1e-8, -0.27)),
        ((0, 0, np.pi / 4), (np.sqrt(2), 0, np.pi / 4)),
        ((0, 0, 0.31), (0.7, 0.2, -0.27)),
        ((0.5 - 1e-7, 0.2, 0), (2, 0, 0)),
        ((0.5 + 1e-7, 0.2, 0), (2, 0, 0)),
        ((1 - np.sqrt(0.5), 0.2, np.pi / 4), (2, 0, 0)),
    ]
    # Dense guard and broad-phase boundary rings, including offset centers.
    rng = np.random.default_rng(20261009)
    p = np.zeros((8192, 3), dtype=np.float32)
    q = np.zeros_like(p)
    p[:, :2] = rng.uniform(-50, 50, (len(p), 2))
    p[:, 2] = rng.uniform(-10, 10, len(p))
    q[:, 2] = rng.uniform(-10, 10, len(p))
    angle = rng.uniform(-np.pi, np.pi, len(p))
    radius = rng.choice([0.0, 1.0, np.sqrt(2), np.sqrt(2 * (1 + 2e-5)**2 + 0.001), 2.0], len(p))
    radius += rng.uniform(-1e-5, 1e-5, len(p))
    q[:, 0] = p[:, 0] + radius * np.cos(angle)
    q[:, 1] = p[:, 1] + radius * np.sin(angle)
    return (np.concatenate([np.asarray([a for a, _ in cases], np.float32), p]),
            np.concatenate([np.asarray([b for _, b in cases], np.float32), q]))


def capture(output):
    output.mkdir(parents=True, exist_ok=False)
    experiments = []
    specifications = [(n, seed, offset, 8) for n in (1, 4, 11, 12, 16, 32)
                      for seed, offset in ((20261008, 0), (987654321, 4096))]
    specifications += [(11, 20261008, 4124, 1), (11, 20261008, 4372, 1),
                       (4, 2**64 - 123, 2**64 - 8, 8)]
    for n, seed, offset, count in specifications:
        config = gpu.Config(n=n, seed=seed, max_sweeps=480)
        name = f"n{n}-seed{seed}-id{offset}"
        batch = gpu.Batch(config, count)
        clear_scratch(batch)
        results, timing = batch.run(count, offset)
        poses, _ = batch.get_poses(list(range(count)))
        initial = gpu.Batch(replace(config, max_attempts=0), count)
        clear_scratch(initial)
        initial_results, _ = initial.run(count, offset)
        initial_poses, _ = initial.get_poses(list(range(count)))
        np.savez_compressed(output / f"{name}.npz", results=results, poses=poses,
                            initial_results=initial_results, initial_poses=initial_poses)
        entry = dict(name=name, config=asdict(config), count=count, offset=offset, file=f"{name}.npz",
                     sha256=digest(output / f"{name}.npz"), timing=timing,
                     kernel_properties=batch.kernel_properties)
        experiments.append(entry)
        print(f"captured {name}: {count} trials", flush=True)
    p, q = contact_inputs()
    pair_p, pair_q, pair_values = diagnostic(gpu, p, q, 0)
    wall_p, wall_q, wall_values = diagnostic(gpu, p, q, 1)
    np.savez_compressed(output / "contacts.npz", input_p=p, input_q=q, pair_p=pair_p, pair_q=pair_q,
                        pair_values=pair_values, wall_p=wall_p, wall_q=wall_q, wall_values=wall_values)
    save_json(output / "corpus.json", {"environment": environment(), "experiments": experiments,
              "contact_count": len(p), "contacts_sha256": digest(output / "contacts.npz")})


def compare(module, reference):
    manifest = json.loads((reference / "corpus.json").read_text())
    validation = {}
    for entry in manifest["experiments"]:
        config = module.Config(**entry["config"])
        batch = module.Batch(config, entry["count"])
        clear_scratch(batch)
        results, _ = batch.run(entry["count"], entry["offset"])
        poses, _ = batch.get_poses(list(range(entry["count"])))
        initial = module.Batch(replace(config, max_attempts=0), entry["count"])
        clear_scratch(initial)
        initial_results, _ = initial.run(entry["count"], entry["offset"])
        initial_poses, _ = initial.get_poses(list(range(entry["count"])))
        with np.load(reference / entry["file"]) as frozen:
            for name, actual in (("results", results), ("poses", poses),
                                 ("initial_results", initial_results), ("initial_poses", initial_poses)):
                exact(actual, frozen[name], f"{entry['name']} {name}")
        statuses = [validate_pose(pose, float(result["side"]))["status"] if int(result["termination"]) != 3
                    else "INIT_FAILED_NO_COMPLETE_GEOMETRY"
                    for pose, result in zip(poses, results)]
        assert all(status in ("NUMERICALLY_VALIDATED", "INIT_FAILED_NO_COMPLETE_GEOMETRY")
                   for status in statuses), statuses
        validation[entry["name"]] = statuses
        print(f"exact {entry['name']}", flush=True)
    with np.load(reference / "contacts.npz") as contacts:
        for mode, prefix in ((0, "pair"), (1, "wall")):
            outputs = diagnostic(module, contacts["input_p"], contacts["input_q"], mode)
            for suffix, actual in zip(("p", "q", "values"), outputs):
                exact(actual, contacts[f"{prefix}_{suffix}"], f"contacts {prefix}_{suffix}")
    return {"exact": True, "validation": validation, "contact_count": manifest["contact_count"]}


def benchmark(args):
    current_hash = CURRENT_SOURCE_HASH
    baseline_hash = digest(args.baseline_source)
    assert digest(ROOT / "src/asquerix/gpu.py") == current_hash, "Current source changed after import"
    reference = load_source(args.baseline_source)
    modules = {"baseline": reference, "optimized": gpu}
    variants = args.variants.split(",")
    if variants not in (["baseline"], ["baseline", "optimized"]):
        raise ValueError("variants must be baseline or baseline,optimized; baseline is always the reference")
    entries = []
    for n in args.n:
        config = gpu.Config(n=n, max_sweeps=480)
        batches = {variant: modules[variant].Batch(modules[variant].Config(**asdict(config)), args.count)
                   for variant in variants}
        for variant, batch in batches.items():
            batch.run(min(args.count, 32), args.offset)
        profiles = {variant: occupancy(modules[variant], batch.device) for variant, batch in batches.items()}
        initial = reference.Batch(reference.Config(**asdict(replace(config, max_attempts=0))), args.count)
        clear_scratch(initial)
        initial_results, _ = initial.run(args.count, args.offset)
        initial_poses, _ = initial.get_poses(np.arange(args.count, dtype=np.int32))
        if "optimized" in variants:
            current_initial = gpu.Batch(replace(config, max_attempts=0), args.count)
            clear_scratch(current_initial)
            current_initial_results, _ = current_initial.run(args.count, args.offset)
            current_initial_poses, _ = current_initial.get_poses(np.arange(args.count, dtype=np.int32))
            exact(current_initial_results, initial_results, f"n{n} initial results")
            exact(current_initial_poses, initial_poses, f"n{n} initial poses")
        expected = None
        for repeat in range(args.repeats):
            order = variants if repeat % 2 == 0 else list(reversed(variants))
            for variant in order:
                batch = batches[variant]
                assert digest(args.baseline_source) == baseline_hash, "Baseline source changed"
                assert digest(ROOT / "src/asquerix/gpu.py") == current_hash, "Current source changed"
                clear_scratch(batch)
                wp.synchronize_device(batch.device)
                gpu_processes_before = subprocess.check_output([
                    "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                    "--format=csv"], text=True)
                started_utc = datetime.now(timezone.utc).isoformat()
                before = perf_counter()
                results, timing = batch.run(args.count, args.offset)
                poses, gather = batch.get_poses(np.arange(args.count, dtype=np.int32))
                complete_seconds = perf_counter() - before
                comparison_started = perf_counter()
                reference_persistence = 0.0
                first_reference = expected is None
                if first_reference:
                    expected = (results.copy(), poses.copy())
                    persistence_started = perf_counter()
                    np.savez_compressed(args.output / f"n{n}-reference.npz", results=results, poses=poses,
                                        initial_results=initial_results, initial_poses=initial_poses)
                    reference_persistence = perf_counter() - persistence_started
                else:
                    exact(results, expected[0], f"n{n} {variant} results")
                    exact(poses, expected[1], f"n{n} {variant} poses")
                comparison_seconds = perf_counter() - comparison_started - reference_persistence
                # A deterministic independent sample; all full states remain saved.
                indices = np.unique(np.linspace(0, args.count - 1, min(32, args.count), dtype=int))
                validation_started = perf_counter()
                statuses = [validate_pose(poses[i], float(results[i]["side"]))["status"]
                            if int(results[i]["termination"]) != 3 else "INIT_FAILED_NO_COMPLETE_GEOMETRY"
                            for i in indices]
                assert all(s in ("NUMERICALLY_VALIDATED", "INIT_FAILED_NO_COMPLETE_GEOMETRY")
                           for s in statuses), statuses
                entry = {"n": n, "variant": variant, "repeat": repeat, "count": args.count,
                         "started_utc": started_utc,
                         "gpu_processes_before": gpu_processes_before,
                         "offset": args.offset, "config": asdict(config), "timing": timing,
                         "module_load_seconds": batch.module_load_seconds,
                         "gather_seconds": gather, "complete_batch_seconds": complete_seconds,
                         "comparison_seconds": comparison_seconds,
                         "reference_persistence_seconds": reference_persistence,
                         "end_to_end_seconds": perf_counter() - before,
                         "end_to_end_scope": "Synchronized simulation, scalar/pose readback, exact comparison, "
                                              "reference archival when first, and independent sample validation; "
                                              "excludes JIT, warm-up and this measurement's metadata serialization.",
                         "validation_seconds": perf_counter() - validation_started,
                         "validation_count": sum(s == "NUMERICALLY_VALIDATED" for s in statuses),
                         "validation_statuses": statuses,
                         "validation": "NUMERICALLY_VALIDATED" if all(s == "NUMERICALLY_VALIDATED" for s in statuses)
                                       else "INITIALIZED_GEOMETRY_CHECKED",
                         "gpu_feasible_count": int(np.sum(results["feasible"])),
                         "kernel_properties": batch.kernel_properties, "exact": True,
                         "occupancy": profiles[variant],
                         "comparison": "BASELINE_CAPTURE" if first_reference else "BASELINE_BITWISE_MATCH",
                         "trials_per_second": args.count / timing["device_seconds"]}
                entry["gpu_processes_after"] = subprocess.check_output([
                    "nvidia-smi", "--query-compute-apps=pid,process_name,used_memory",
                    "--format=csv"], text=True)
                entries.append(entry)
                assert digest(args.baseline_source) == baseline_hash, "Baseline source changed during measurement"
                assert digest(ROOT / "src/asquerix/gpu.py") == current_hash, "Current source changed during measurement"
                save_json(args.output / "measurements.json", {"environment": environment(), "measurements": entries,
                          "baseline_source_sha256": baseline_hash, "current_source_sha256": current_hash})
                print(f"n={n} {variant} repeat={repeat}: {entry['trials_per_second']:.3f} trials/s, "
                      f"{timing['device_seconds']:.6f}s, exact, {batch.kernel_properties}", flush=True)
        save_json(args.output / f"n{n}-manifest.json", {"file": f"n{n}-reference.npz",
                  "sha256": digest(args.output / f"n{n}-reference.npz"), "config": asdict(config),
                  "count": args.count, "offset": args.offset,
                  "arrays": ["results", "poses", "initial_results", "initial_poses"]})


def check_initial(benchmark_directory, output):
    """Check current RNG initialization against complete benchmark archives."""
    entries = []
    for path in sorted(benchmark_directory.glob("n*-manifest.json")):
        manifest = json.loads(path.read_text())
        archive = benchmark_directory / manifest["file"]
        assert digest(archive) == manifest["sha256"], f"Archive changed: {archive}"
        config = replace(gpu.Config(**manifest["config"]), max_attempts=0)
        batch = gpu.Batch(config, manifest["count"])
        clear_scratch(batch)
        results, _ = batch.run(manifest["count"], manifest["offset"])
        poses, _ = batch.get_poses(np.arange(manifest["count"], dtype=np.int32))
        with np.load(archive) as frozen:
            exact(results, frozen["initial_results"], f"n{config.n} initial results")
            exact(poses, frozen["initial_poses"], f"n{config.n} initial poses")
        entries.append({"n": config.n, "count": manifest["count"], "offset": manifest["offset"],
                        "archive_sha256": manifest["sha256"], "exact": True})
    assert entries, "No benchmark manifests found"
    assert digest(ROOT / "src/asquerix/gpu.py") == CURRENT_SOURCE_HASH, "Source changed"
    save_json(output, {"source_sha256": CURRENT_SOURCE_HASH, "experiments": entries})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze = sub.add_parser("capture")
    freeze.add_argument("--output", type=Path, default=ARTIFACT / "corpus")
    check = sub.add_parser("compare")
    check.add_argument("--reference", type=Path, default=ARTIFACT / "corpus")
    check.add_argument("--source", type=Path)
    check.add_argument("--output", type=Path, required=True)
    initial = sub.add_parser("check-initial")
    initial.add_argument("--benchmark-directory", type=Path, required=True)
    initial.add_argument("--output", type=Path, required=True)
    bench = sub.add_parser("benchmark")
    bench.add_argument("--baseline-source", type=Path, default=ARTIFACT / "baseline/gpu.py")
    bench.add_argument("--variants", default="baseline,optimized")
    bench.add_argument("--count", type=int, default=131072)
    bench.add_argument("--offset", type=int, default=0)
    bench.add_argument("--n", type=int, nargs="+", default=[16, 12])
    bench.add_argument("--repeats", type=int, default=3)
    bench.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    wp.init()
    assert wp.get_device("cuda:0").is_cuda, "Real CUDA is required"
    if args.command == "capture":
        capture(args.output)
    elif args.command == "compare":
        source_hash = digest(args.source) if args.source else CURRENT_SOURCE_HASH
        module = load_source(args.source) if args.source else gpu
        report = compare(module, args.reference)
        assert digest(args.source or ROOT / "src/asquerix/gpu.py") == source_hash, "Source changed during comparison"
        report["source_sha256"] = source_hash
        save_json(args.output, report)
    elif args.command == "check-initial":
        check_initial(args.benchmark_directory, args.output)
    else:
        if args.count < 1 or args.repeats < 1:
            parser.error("count and repeats must be positive")
        args.output.mkdir(parents=True, exist_ok=False)
        # Monitor clocks, temperature and utilization outside the CUDA interval.
        with (args.output / "gpu-monitor.csv").open("w") as stream:
            monitor = subprocess.Popen([
                "nvidia-smi", "--query-gpu=timestamp,utilization.gpu,utilization.memory,temperature.gpu,"
                "clocks.sm,clocks.mem,power.draw,memory.used", "--format=csv", "-l", "1"],
                stdout=stream, stderr=subprocess.STDOUT)
            try:
                # The directory was created to start monitoring before JIT.
                benchmark(args)
            finally:
                monitor.terminate()
                monitor.wait()


if __name__ == "__main__":
    main()
