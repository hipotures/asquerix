"""Reproduce the original scientific workload in a bounded single-GPU audit."""
import argparse
from collections import Counter
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np
import warp as wp

from asquerix.geometry import validate_document
from asquerix.gpu import Batch, Config
from asquerix.runner import environment, run, write_json


def records_at(directory):
    path = directory / "trials.jsonl"
    if path.exists():
        return [json.loads(line) for line in path.read_text().splitlines()]
    with gzip.open(directory / "trials.jsonl.gz", "rt") as source:
        return [json.loads(line) for line in source]


def search_results(records):
    return [{key: value for key, value in record.items()
             if key not in ("validation_status", "independent_validation")}
            for record in records]


def archive_run(source, target):
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("trials.jsonl"))
    raw = (source / "trials.jsonl").read_bytes()
    with (target / "trials.jsonl.gz").open("wb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as zipped:
            zipped.write(raw)
    return hashlib.sha256(raw).hexdigest()


def recheck(directory):
    outcomes = Counter()
    details = {}
    for path in sorted((directory / "poses").glob("*.json")):
        document = json.loads(path.read_text())
        if document["side"] is None:
            continue  # No final geometry exists after INIT_FAILED.
        result = validate_document(document)
        assert result == document["validation"], path
        outcomes[result["status"]] += 1
        details[path.name] = result
    write_json(directory / "revalidation.json", {"counts": dict(outcomes), "poses": details})
    return dict(outcomes)


def profile(output):
    batch = Batch(Config(), 32, "cuda:0")
    batch.run(1, 100000)
    host_calls = []
    original_launch = wp.launch
    original_numpy = wp.array.numpy
    original_sync = wp.synchronize_device
    def launch(*args, **kwargs):
        kernel = args[0] if args else kwargs["kernel"]
        host_calls.append({"operation": "launch", "kernel": kernel.key,
                           "dim": kwargs.get("dim", args[1] if len(args) > 1 else None),
                           "device": str(kwargs.get("device"))})
        return original_launch(*args, **kwargs)
    def numpy_read(array, *args, **kwargs):
        host_calls.append({"operation": "numpy", "shape": list(array.shape),
                           "device": str(array.device)})
        return original_numpy(array, *args, **kwargs)
    def synchronize(*args, **kwargs):
        host_calls.append({"operation": "synchronize_device"})
        return original_sync(*args, **kwargs)
    wp.launch, wp.array.numpy, wp.synchronize_device = launch, numpy_read, synchronize
    try:
        wp.timing_begin(wp.TIMING_ALL, synchronize=False)
        scalars, timing = batch.run(32, 100000)
        poses, transfer = batch.get_poses([0, 7, 16, 31])
        activities = wp.timing_end(synchronize=False)
    finally:
        wp.launch, wp.array.numpy, wp.synchronize_device = original_launch, original_numpy, original_sync
    first_read = next(i for i, call in enumerate(host_calls) if call["operation"] == "numpy")
    prior_launches = [call for call in host_calls[:first_read] if call["operation"] == "launch"]
    assert len(prior_launches) == batch.stage_count == 8
    assert all(call["kernel"] == "simulate" and call["dim"] == 32 for call in prior_launches)
    assert {str(activity.device) for activity in activities} == {"cuda:0"}
    write_json(output / "profile.json", {
        "method": "Warp TIMING_ALL CUDA-event activities plus host API trace; instrumented, excluded from throughput",
        "config": asdict(Config()), "count": 32, "trial_offset": 100000,
        "host_calls": host_calls,
        "activities": [{"name": a.name, "device": str(a.device), "filter": a.filter,
                        "elapsed_ms": a.elapsed} for a in activities],
        "batch_timing": timing, "gather_seconds": transfer,
        "selected_poses": poses.tolist(), "kernel_properties": batch.kernel_properties,
        "returned_scalar_count": len(scalars),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/audit/campaign"))
    parser.add_argument("--runs-output", type=Path, default=Path("runs/audit"))
    parser.add_argument("--max-seconds", type=float, default=300)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    baseline = Path("artifacts/pilot/extended/repeat-0")
    old_config = json.loads((baseline / "config.json").read_text())
    assert asdict(Config()) == old_config["solver"]
    original = search_results(records_at(baseline))
    initial_environment = environment()
    write_json(args.output / "environment-start.json", initial_environment)
    measurements = []
    def measured(name, config, trials, batch_size, **options):
        remaining = args.max_seconds - (perf_counter() - started)
        if remaining <= 0:
            raise RuntimeError("Audit campaign scheduling wall budget reached")
        directory = args.runs_output / name
        call_started = perf_counter()
        result = run(config, trials=trials, batch_size=batch_size, output=directory,
                     max_seconds=remaining, **options)
        call_seconds = perf_counter() - call_started
        assert result["summary"]["record_count"] == trials, "Incomplete matched workload"
        revalidation = recheck(directory)
        sha = archive_run(directory, args.output / name)
        entry = {"name": name, "run_call_seconds": call_seconds,
                 "scalar_uncompressed_sha256": sha, "revalidation": revalidation,
                 "summary": result["summary"]}
        measurements.append(entry)
        write_json(args.output / "measurements.json", {"elapsed_seconds": perf_counter() - started,
                   "wall_budget_seconds": args.max_seconds, "runs": measurements})
        return search_results(records_at(directory)), entry
    # All final states in these small multi-batch control runs are retained.
    for n in (11, 12, 16):
        records, entry = measured(f"retained-n{n}", Config(n=n), 32, 16,
                                  trial_offset=4096, retain_all=True, sample_every=8,
                                  keep_best=3, audit_size=8, max_images=3)
        assert entry["revalidation"] == {"NUMERICALLY_VALIDATED": 32}
    profile(args.output)
    for repeat in range(3):
        records, entry = measured(f"matched-b512-r{repeat}", Config(), 12288, 512,
                                  sample_every=1024, keep_best=10, audit_size=64, max_images=3)
        assert entry["summary"]["timings"]["device_seconds"] >= 20
        assert records == original, "Search results differ from the archived original workload"
        entry["original_search_equality"] = True
    records, entry = measured("matched-b128", Config(), 12288, 128,
                              sample_every=1024, keep_best=10, audit_size=64, max_images=3)
    assert entry["summary"]["timings"]["device_seconds"] >= 20
    assert records == original, "Batch partition changed the scientific results"
    entry["original_search_equality"] = True
    # Exercise deadline draining separately; it is not a throughput measurement.
    stop_directory = args.runs_output / "stop-wall-time"
    result = run(Config(), trials=64, batch_size=8, output=stop_directory,
                 retain_all=True, sample_every=0, audit_size=0, max_images=1,
                 max_seconds=0.001)
    stop_metadata = json.loads((stop_directory / "environment.json").read_text())
    assert result["summary"]["record_count"] == 8
    assert stop_metadata["stop_reason"] == "MAX_SECONDS"
    assert stop_metadata["stop_observed_to_batch_completion_seconds"] > 0
    recheck(stop_directory)
    archive_run(stop_directory, args.output / "stop-wall-time")
    failure_directory = args.runs_output / "init-failed"
    result = run(Config(n=2, initial_side=1.5, proposals_per_square=1, max_attempts=0),
                 trials=4, batch_size=4, output=failure_directory, retain_all=True,
                 sample_every=0, audit_size=0, max_images=1, max_seconds=5)
    assert result["summary"]["failure_counts"]["initialization_failed"] == 4
    archive_run(failure_directory, args.output / "init-failed")
    final_environment = environment()
    assert initial_environment["source_sha256"] == final_environment["source_sha256"]
    rates = [entry["summary"]["throughput"]["simulation_seconds"]["attempted_trials_per_second"]
             for entry in measurements if entry["name"].startswith("matched-b512")]
    write_json(args.output / "measurements.json", {
        "elapsed_seconds": perf_counter() - started, "wall_budget_seconds": args.max_seconds,
        "original_solver_config_equality": True, "original_search_equality": True,
        "batch_partition_search_equality": True, "source_unchanged_during_campaign": True,
        "batch512_mean_trials_per_second": float(np.mean(rates)),
        "batch512_sample_std_trials_per_second": float(np.std(rates, ddof=1)),
        "runs": measurements, "stop_metadata": stop_metadata,
    })
    write_json(args.output / "environment-end.json", final_environment)


if __name__ == "__main__":
    main()
