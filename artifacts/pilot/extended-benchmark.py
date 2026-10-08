"""Longer matched GPU measurements; archive large scalar logs with gzip."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
from time import perf_counter

import numpy as np

from asquerix.gpu import Config
from asquerix.runner import run, write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("artifacts/pilot/extended"))
parser.add_argument("--runs-output", type=Path, default=Path("runs/extended"))
args = parser.parse_args()
archive = args.output
archive.mkdir(parents=True, exist_ok=False)
started = perf_counter()
measurements = []
reference = None
for repeat in range(3):
    remaining = 160 - (perf_counter() - started)
    if remaining <= 0:
        raise RuntimeError("Extended campaign wall budget reached")
    directory = args.runs_output / f"repeat-{repeat}"
    result = run(Config(n=12), trials=12288, batch_size=512, output=directory,
                 sample_every=1024, keep_best=10, max_images=3, audit_size=64,
                 max_seconds=remaining)
    summary = result["summary"]
    if summary["record_count"] != 12288 or summary["timings"]["device_seconds"] < 20:
        raise RuntimeError("Measurement is incomplete or shorter than 20 seconds of GPU work")
    records = [json.loads(line) for line in (directory/"trials.jsonl").read_text().splitlines()]
    comparable = [{key: value for key,value in r.items() if key not in ("validation_status","independent_validation")} for r in records]
    if reference is None:
        reference = comparable
    else:
        assert reference == comparable, "Repeated inputs changed scalar search results"
    target = archive/f"repeat-{repeat}"
    shutil.copytree(directory, target, ignore=shutil.ignore_patterns("trials.jsonl"))
    data = (directory/"trials.jsonl").read_bytes()
    with (target/"trials.jsonl.gz").open("wb") as output:
        with gzip.GzipFile(filename="",mode="wb",fileobj=output,mtime=0) as compressed:
            compressed.write(data)
    measurements.append({
        "repeat":repeat, "raw_directory":str(directory), "archive_directory":str(target),
        "scalar_uncompressed_sha256":hashlib.sha256(data).hexdigest(),
        "scalar_compressed_sha256":hashlib.sha256((target/"trials.jsonl.gz").read_bytes()).hexdigest(),
        "summary":summary,
    })
    write_json(archive/"measurements.json",{"elapsed_seconds":perf_counter()-started,"runs":measurements})
rates = [m["summary"]["throughput"]["simulation_seconds"]["attempted_trials_per_second"] for m in measurements]
write_json(archive/"measurements.json",{
    "elapsed_seconds":perf_counter()-started, "wall_budget_seconds":160,
    "minimum_device_seconds_per_repeat":20,"scalar_repetition_equality":True,
    "throughput_mean":float(np.mean(rates)), "throughput_std":float(np.std(rates,ddof=1)),
    "runs":measurements,
})
