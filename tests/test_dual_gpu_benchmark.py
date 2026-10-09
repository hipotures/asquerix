"""Partition, archived-byte, and real physical-device benchmark regressions."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import pytest

from asquerix.persistence import read_json

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/dual_gpu_benchmark.py"
spec = importlib.util.spec_from_file_location("asquerix_dual_benchmark_test", TOOL)
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


@pytest.mark.parametrize("mode", ["A", "B", "dual"])
@pytest.mark.parametrize("count,offset,capacity", [(11, 413, 3), (2, 2**64 - 2, 1), (262144, 0, 131072)])
def test_partition_has_exact_complete_disjoint_ranges(mode, count, offset, capacity):
    assignments = bench.partition(mode, count, offset, capacity)
    ids = [i for assignment in assignments for chunk in assignment
           for i in range(chunk["offset"], chunk["offset"] + chunk["count"])]
    assert sorted(ids) == list(range(offset, offset + count))
    assert len(set(ids)) == count
    assert all(1 <= c["count"] <= capacity for a in assignments for c in a)
    if count == 262144 and mode == "dual":
        assert assignments == [[dict(count=131072, offset=0)], [dict(count=131072, offset=131072)]]


@pytest.mark.parametrize("count,offset,capacity", [(0, 0, 1), (3, 2**64 - 2, 1), (1, -1, 1),
                                                (True, 0, 1), (2, 0.0, 1), (2, 0, 0), (2, 0, 1048577)])
def test_invalid_workload_is_rejected(count, offset, capacity):
    with pytest.raises(ValueError):
        bench.chunks(count, offset, capacity)


@pytest.mark.parametrize("requested", [["a", "a"], ["a", "missing"], ["a"], ["cuda:0", "cuda:1"]])
def test_duplicate_or_unknown_physical_devices_are_rejected(requested):
    with pytest.raises(ValueError):
        bench.select_devices(requested, [dict(uuid="a"), dict(uuid="b")])


def test_exact_comparison_preserves_zero_and_nan_bits():
    a = np.array([0, 0x7fc00001], dtype=np.uint32).view(np.float32)
    bench.exact(a, a.copy(), "identical NaN representations")
    for bits in ([0x80000000, 0x7fc00001], [0, 0x7fc00002]):
        with pytest.raises(AssertionError, match="bytewise"):
            bench.exact(a, np.array(bits, dtype=np.uint32).view(np.float32), "changed bits")
    with pytest.raises(AssertionError, match="dtype or shape"):
        bench.exact(a, a.astype(np.float64), "changed type")


def _archive(path, ids):
    arrays = {key: np.asarray(ids, dtype=np.uint64)[:, None] for key in bench.ARRAYS}
    np.savez_compressed(path, ids=np.asarray(ids, dtype=np.uint64), **arrays)
    return dict(path=str(path), sha256=bench.sha256(path))


def test_merge_orders_global_ids_and_rejects_missing_duplicate_or_tampered(tmp_path):
    a = _archive(tmp_path / "a.npz", [43, 44])
    b = _archive(tmp_path / "b.npz", [41, 42])
    merged = bench.merge_archives([a, b], 4, 41)
    assert merged["ids"].tolist() == [41, 42, 43, 44]
    assert merged["poses"][:, 0].tolist() == [41, 42, 43, 44]
    from asquerix.persistence import write_json
    manifest = tmp_path / "manifest.json"
    write_json(manifest, dict(count=4, offset=41, measurements=[dict(status="COMPLETE", n=1,
               variant="baseline", measurement=1, archives=[a, b])]))
    bench.replay(manifest, tmp_path / "replay.json")
    assert read_json(tmp_path / "replay.json")["exact"]
    for parts in ([a], [a, a]):
        with pytest.raises(AssertionError):
            bench.merge_archives(parts, 4, 41)
    with (tmp_path / "a.npz").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(AssertionError, match="hash mismatch"):
        bench.merge_archives([a, b], 4, 41)


def test_cpu_validation_decodes_each_compressed_member_once(tmp_path, monkeypatch):
    results = np.zeros(128, dtype=[("side", "f4"), ("termination", "i4")])
    results["side"] = 2.0
    path = tmp_path / "poses.npz"
    np.savez_compressed(path, results=results, poses=np.zeros((128, 1, 3), dtype=np.float32),
                        ids=np.arange(128, dtype=np.uint64))
    original = np.load
    reads = {}

    class CountedArchive:
        def __enter__(self):
            self.archive = original(path, allow_pickle=False)
            return self

        def __getitem__(self, name):
            reads[name] = reads.get(name, 0) + 1
            return self.archive[name]

        def __exit__(self, *_):
            self.archive.close()

    monkeypatch.setattr(bench.np, "load", lambda *_args, **_kwargs: CountedArchive())
    entry = dict(archives=[dict(path=str(path), count=128, uuid="CPU_ARCHIVE_READ_TEST")])
    bench.validate_archives(entry)
    assert reads == {"results": 1, "poses": 1, "ids": 1}
    assert [row["trial_id"] for row in entry["cpu_validation"]] == np.linspace(0, 127, 32, dtype=int).tolist()
    assert all(row["status"] == "NUMERICALLY_VALIDATED" for row in entry["cpu_validation"])


@pytest.fixture
def physical_devices():
    try:
        devices = bench.inventory()
    except (OSError, RuntimeError):
        pytest.skip("nvidia-smi and two physical CUDA devices are required")
    if len(devices) < 2:
        pytest.skip("two physical CUDA devices are required; no mock substitute")
    return [d["uuid"] for d in devices[:2]]


def _run_command(tmp_path, devices, *extra):
    return [sys.executable, str(TOOL), "run", "--baseline-source", str(ROOT / "src/asquerix/gpu.py"),
            "--devices", *devices, "--n", "4", "--count", "11", "--offset", "413", "--batch-size", "3",
            "--repeats", "1", "--timeout", "90", "--max-seconds", "120", "--json",
            "--output", str(tmp_path / "evidence"), "--archives", str(tmp_path / "arrays"), *extra]


@pytest.mark.gpu
def test_real_dual_devices_multibatch_and_ordered_equality(tmp_path, physical_devices):
    result = subprocess.run(_run_command(tmp_path, physical_devices, "--debug"), cwd=ROOT,
                            text=True, capture_output=True, timeout=160)
    assert result.returncode == 0, result.stdout + result.stderr
    report = read_json(tmp_path / "evidence/measurements.json")
    assert report["status"] == "COMPLETE"
    assert {w["uuid"] for w in report["workers"]} == set(physical_devices)
    assert all(w["local_device"] == "cuda:0" for w in report["workers"])
    assert len(report["measurements"]) == 3
    assert all(m["completed_unique"] == 11 and not m["incomplete_ranges"] for m in report["measurements"])
    assert report["measurements"][-1]["comparison"] == "BASELINE_BYTEWISE_MATCH"
    assert len(report["measurements"][-1]["archives"]) == 4  # two rounds, uneven final batches
    bench.replay(tmp_path / "evidence/measurements.json.gz", tmp_path / "replay.json")
    assert read_json(tmp_path / "replay.json")["exact"]
    assert "{" not in result.stdout  # --json prints paths/status, no payload dumps


@pytest.mark.gpu
def test_ordinary_pipeline_keeps_ids_validation_and_decompressed_records(tmp_path, physical_devices):
    from asquerix.persistence import read_jsonl
    command = _run_command(tmp_path, physical_devices, "--offset", "4094", "--pipeline", "ordinary",
                           "--gzip-levels", "9", "3")
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=160)
    assert result.returncode == 0, result.stdout + result.stderr
    report = read_json(tmp_path / "evidence/measurements.json")
    assert len(report["measurements"]) == 6 and report["status"] == "COMPLETE"
    assert all(m["completed_unique"] == 11 and not m["incomplete_ranges"] for m in report["measurements"])
    digests = {m["pipeline_equality"]["decompressed_sorted_jsonl_sha256"] for m in report["measurements"]}
    assert len(digests) == 1
    for measurement in report["measurements"]:
        rows = [r for archive in measurement["archives"]
                for r in read_jsonl(Path(archive["path"]) / "trials.jsonl.gz")]
        assert sorted(r["trial_id"] for r in rows) == list(range(4094, 4105))
        assert next(r for r in rows if r["trial_id"] == 4096)["validation_status"] == "NUMERICALLY_VALIDATED"
        for archive in measurement["archives"]:
            cfg = read_json(Path(archive["path"]) / "config.json")
            assert cfg["runner"]["gzip_compression_level"] == archive["gzip_level"]
    bench.replay(tmp_path / "evidence/measurements.json.gz", tmp_path / "replay.json")
    assert read_json(tmp_path / "replay.json")["exact"]


@pytest.mark.gpu
def test_worker_failure_is_bounded_and_names_physical_device(tmp_path, physical_devices):
    bad = tmp_path / "bad.py"
    bad.write_text("raise RuntimeError('deliberate worker failure')\n")
    command = _run_command(tmp_path, physical_devices)
    command[command.index("--baseline-source") + 1] = str(bad)
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=110)
    assert result.returncode != 0
    report = read_json(tmp_path / "evidence/measurements.json")
    assert report["status"] == "FAILED"
    assert not report["measurements"]
    failures = list((tmp_path / "arrays").glob("failure-*.json.gz"))
    assert failures
    assert all(read_json(p)["uuid"] in physical_devices for p in failures)
    assert all("deliberate worker failure" in read_json(p)["error"] for p in failures)


@pytest.mark.gpu
@pytest.mark.parametrize("pipeline", ["compute", "ordinary"])
def test_interrupt_drains_current_batches_and_stops_new_assignments(tmp_path, physical_devices, pipeline):
    command = _run_command(tmp_path, physical_devices, "--n", "12", "--count", "20000",
                           "--batch-size", "1024", "--modes", "dual", "--pipeline", pipeline)
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        limit = time.monotonic() + 100
        # stdout is line-buffered by explicit flushes in the coordinator.
        import selectors
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        executing = False
        while time.monotonic() < limit and process.poll() is None:
            if selector.select(timeout=0.2):
                line = process.stdout.readline()
                if "executing" in line:
                    executing = True
                    break
        selector.close()
        assert executing, "worker start was not observed"
        time.sleep(0.2)
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=100)
        assert process.returncode == 2, stdout + stderr
        report = read_json(tmp_path / "evidence/measurements.json")
        assert report["status"] == "PARTIAL"
        assert report["stop_reason"] == f"SIGNAL_{signal.SIGINT}"
        assert len(report["measurements"]) == 1
        entry = report["measurements"][0]
        assert 0 < entry["completed_unique"] < 20000
        assert entry["incomplete_ranges"] and entry["archives"]
        assert not report.get("forced_shutdown_pids")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)


@pytest.mark.gpu
@pytest.mark.parametrize("pipeline", ["compute", "ordinary"])
def test_midrun_failure_preserves_completed_ranges_and_archives(tmp_path, physical_devices, pipeline):
    bad = tmp_path / "failing.py"
    # Real CUDA submissions complete before a deliberate later host failure.
    bad.write_text((ROOT / "src/asquerix/gpu.py").read_text() + """

_ProductionBatch = Batch
_failure_probe_calls = 0
class Batch(_ProductionBatch):
    def run(self, count, offset):
        global _failure_probe_calls
        _failure_probe_calls += 1
        if _failure_probe_calls == FAILURE_AT:
            raise RuntimeError('deliberate midrun failure')
        return super().run(count, offset)
""".replace("FAILURE_AT", str(4 if pipeline == "ordinary" else 3)))
    command = _run_command(tmp_path, physical_devices, "--modes", "dual", "--pipeline", pipeline)
    command[command.index("--baseline-source") + 1] = str(bad)
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=160)
    assert result.returncode != 0
    report = read_json(tmp_path / "evidence/measurements.json")
    assert report["status"] in ("PARTIAL", "FAILED")
    assert len(report["measurements"]) == 1
    entry = report["measurements"][0]
    assert 0 < entry["completed_unique"] < 11
    assert entry["incomplete_ranges"] and entry["archives"]
    assert sum(a["count"] for a in entry["archives"]) == entry["completed_unique"]
    assert not report.get("forced_shutdown_pids")
    assert all(a["uuid"] in physical_devices for a in entry["archives"])
