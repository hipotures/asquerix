"""Isolated host-path instrumentation and lossless gzip-level experiments."""
from collections import defaultdict
from contextlib import contextmanager
import cProfile
import gzip
import hashlib
import io
import json
from pathlib import Path
import pstats
from time import perf_counter_ns, process_time_ns, thread_time_ns

from asquerix.persistence import read_jsonl, write_json


class Observer:
    """Diagnostic wrappers only; never used in headline throughput runs."""
    def __init__(self):
        self.totals = defaultdict(lambda: dict(calls=0, wall_seconds=0.0, process_cpu_seconds=0.0,
                                              thread_cpu_seconds=0.0))
        self.events = []
        self.originals = []

    def wrap(self, owner, name, phase, timeline=True):
        original = getattr(owner, name)
        self.originals.append((owner, name, original))

        def measured(*args, **kwargs):
            start, cpu, thread = perf_counter_ns(), process_time_ns(), thread_time_ns()
            try:
                return original(*args, **kwargs)
            finally:
                end = perf_counter_ns()
                row = dict(started_ns=start, finished_ns=end, wall_seconds=(end - start) / 1e9,
                           process_cpu_seconds=(process_time_ns() - cpu) / 1e9,
                           thread_cpu_seconds=(thread_time_ns() - thread) / 1e9)
                total = self.totals[phase]
                total["calls"] += 1
                for key in ("wall_seconds", "process_cpu_seconds", "thread_cpu_seconds"):
                    total[key] += row[key]
                if timeline:
                    self.events.append(dict(phase=phase, **row))
        setattr(owner, name, measured)

    def restore(self):
        for owner, name, original in reversed(self.originals):
            setattr(owner, name, original)


@contextmanager
def observe(runner, wp, batch, directory, enabled):
    observer = Observer()
    profiler = cProfile.Profile()
    if enabled:
        observer.wrap(wp, "synchronize_device", "native_device_wait")
        observer.wrap(batch, "run", "production_batch")
        observer.wrap(batch, "get_poses", "pose_transfer")
        observer.wrap(runner, "scalar_records", "scalar_records")
        observer.wrap(runner, "select_indices", "selection")
        observer.wrap(runner, "validate_pose", "cpu_validation")
        observer.wrap(runner, "write_json", "atomic_json_persistence")
        observer.wrap(runner, "render_selected", "rendering")
        observer.wrap(runner, "write_report", "report_generation")
        observer.wrap(json, "dumps", "json_serialization", timeline=False)
        observer.wrap(gzip.GzipFile, "write", "gzip_write", timeline=False)
        observer.wrap(gzip.GzipFile, "flush", "gzip_flush")
        observer.wrap(gzip.GzipFile, "close", "gzip_close")
        profiler.enable()
    try:
        yield observer
    finally:
        if enabled:
            profiler.disable()
            observer.restore()
            directory = Path(directory)
            profiler.dump_stats(str(directory / "python.pstats"))
            stream = io.StringIO()
            pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("tottime").print_stats(60)
            (directory / "python-profile.txt").write_text(stream.getvalue())
            write_json(directory / "phases.json", dict(totals=dict(observer.totals), events=observer.events,
                       warning="Instrumented diagnostic. Nested intervals overlap; do not sum them as end-to-end time."))


def gzip_sweep(records_path, directory, count=131072, repeats=3):
    """Recompress identical completed JSONL bytes; timings exclude serialization."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    rows = []
    records = []
    for record in read_jsonl(records_path):
        records.append(record)
        if len(records) == count:
            break
    payload = "".join(json.dumps(record, allow_nan=False) + "\n" for record in records).encode()
    # The simulator's uint64 boundary is exercised separately by CUDA tests;
    # verify gzip/JSON round trips at that boundary without changing the payload.
    boundary = json.dumps(dict(trial_id=2**64 - 1, seed=2**64 - 123, value=-0.0))
    assert json.loads(gzip.decompress(gzip.compress(boundary.encode(), compresslevel=1))) == json.loads(boundary)
    for repeat in range(repeats):
        levels = [1, 3, 6, 9] if repeat % 2 == 0 else [9, 6, 3, 1]
        for level in levels:
            begin, cpu = perf_counter_ns(), process_time_ns()
            compressed = gzip.compress(payload, compresslevel=level, mtime=0)
            seconds, cpu_seconds = (perf_counter_ns() - begin) / 1e9, (process_time_ns() - cpu) / 1e9
            assert gzip.decompress(compressed) == payload
            decoded = [json.loads(line) for line in gzip.decompress(compressed).splitlines()]
            assert decoded == records
            path = directory / f"level-{level}.jsonl.gz"
            persistence_begin = perf_counter_ns()
            if repeat == 0:
                path.write_bytes(compressed)
            rows.append(dict(repeat=repeat, level=level, wall_seconds=seconds, cpu_seconds=cpu_seconds,
                             compressed_bytes=len(compressed), uncompressed_bytes=len(payload),
                             persistence_seconds=(perf_counter_ns() - persistence_begin) / 1e9,
                             compressed_sha256=hashlib.sha256(compressed).hexdigest(), exact_decompressed=True))
    write_json(directory / "measurements.json", dict(records=len(records), source=str(records_path),
               uncompressed_sha256=hashlib.sha256(payload).hexdigest(), measurements=rows,
               scope="In-memory gzip of identical completed JSONL; serialization and disk writes measured separately."))
    print(f"Gzip comparisons saved: {directory / 'measurements.json.gz'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=131072)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    gzip_sweep(args.records, args.output, args.count, args.repeats)
