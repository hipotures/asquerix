"""Run the bounded matched GPU measurements used by the original pilot."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from time import perf_counter

import numpy as np

from asquerix.gpu import Config
from asquerix.persistence import open_binary, read_jsonl, resolve_path, write_json
from asquerix.runner import run


def archive_run(source: Path, target: Path) -> tuple[str, str]:
    """Copy a run and archive its scalar stream without loading it in memory."""

    scalar = resolve_path(source / "trials.jsonl")
    if not scalar.exists():
        raise FileNotFoundError(f"missing trials.jsonl or trials.jsonl.gz in {source}")
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("trials.jsonl", "trials.jsonl.gz"))
    target_scalar = target / "trials.jsonl.gz"
    raw_digest = hashlib.sha256()
    compressed_digest = hashlib.sha256()
    descriptor, temporary_name = tempfile.mkstemp(prefix=".trials.jsonl.", suffix=".tmp", dir=target)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with open_binary(scalar, "rb") as scalar_stream, temporary.open("w+b") as raw_target:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_target, mtime=0) as zipped:
                while block := scalar_stream.read(1024 * 1024):
                    raw_digest.update(block)
                    zipped.write(block)
            raw_target.flush()
            raw_target.seek(0)
            while block := raw_target.read(1024 * 1024):
                compressed_digest.update(block)
        temporary.replace(target_scalar)
    finally:
        temporary.unlink(missing_ok=True)
    return raw_digest.hexdigest(), compressed_digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("runs/extended-archive"))
    parser.add_argument("--runs-output", type=Path, default=Path("runs/extended-runs"))
    parser.add_argument("--max-seconds", type=float, default=160.0)
    args = parser.parse_args(argv)
    if not np.isfinite(args.max_seconds) or args.max_seconds <= 0.0:
        parser.error("max-seconds must be positive and finite")

    archive = args.output
    archive.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    measurements = []
    reference = None
    for repeat in range(3):
        remaining = args.max_seconds - (perf_counter() - started)
        if remaining <= 0:
            raise RuntimeError("Extended campaign wall budget reached")
        directory = args.runs_output / f"repeat-{repeat}"
        result = run(
            Config(n=12),
            trials=12288,
            batch_size=512,
            output=directory,
            sample_every=1024,
            keep_best=10,
            max_images=3,
            audit_size=64,
            max_seconds=remaining,
        )
        summary = result["summary"]
        if summary["record_count"] != 12288 or summary["timings"]["device_seconds"] < 20:
            raise RuntimeError("Measurement is incomplete or shorter than 20 seconds of GPU work")
        records = list(read_jsonl(directory / "trials.jsonl"))
        comparable = [
            {key: value for key, value in record.items() if key not in ("validation_status", "independent_validation")}
            for record in records
        ]
        if reference is None:
            reference = comparable
        else:
            assert reference == comparable, "Repeated inputs changed scalar search results"
        target = archive / f"repeat-{repeat}"
        raw_sha, compressed_sha = archive_run(directory, target)
        measurements.append(
            {
                "repeat": repeat,
                "raw_directory": str(directory),
                "archive_directory": str(target),
                "scalar_uncompressed_sha256": raw_sha,
                "scalar_compressed_sha256": compressed_sha,
                "summary": summary,
            }
        )
        write_json(archive / "measurements.json", {"elapsed_seconds": perf_counter() - started, "runs": measurements})

    rates = [
        measurement["summary"]["throughput"]["simulation_seconds"]["attempted_trials_per_second"]
        for measurement in measurements
    ]
    write_json(
        archive / "measurements.json",
        {
            "elapsed_seconds": perf_counter() - started,
            "wall_budget_seconds": args.max_seconds,
            "minimum_device_seconds_per_repeat": 20,
            "scalar_repetition_equality": True,
            "throughput_mean": float(np.mean(rates)),
            "throughput_std": float(np.std(rates, ddof=1)),
            "runs": measurements,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

