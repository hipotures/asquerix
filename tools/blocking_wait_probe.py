"""Compare production device waiting with an owned blocking CUDA event.

This isolated process leaves context scheduling flags unchanged. The alternative
uses cuEventCreate(CU_EVENT_BLOCKING_SYNC) and Warp's event synchronization API;
it does not change the production Batch implementation or solver submissions.
"""
import argparse
import ctypes
from dataclasses import asdict
from pathlib import Path
from time import perf_counter, process_time, thread_time

import numpy as np
import warp as wp

from kernel_benchmark import clear_scratch, digest, exact, load_source, save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=131072)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    module = load_source(args.source, "asquerix_blocking_wait_reference")
    config = module.Config(n=12, max_sweeps=480)
    batch = module.Batch(config, args.count, device=args.device)
    clear_scratch(batch)
    batch.run(min(32, args.count), 0)
    driver = ctypes.CDLL("libcuda.so.1")
    handle, flags = ctypes.c_void_p(), ctypes.c_uint()
    with wp.ScopedDevice(batch.device):
        assert driver.cuCtxGetFlags(ctypes.byref(flags)) == 0
        # Flags are from the installed CUDA event API, not context flags.
        assert driver.cuEventCreate(ctypes.byref(handle), ctypes.c_uint(1 | 2)) == 0
    event = wp.Event(batch.device, cuda_event=handle.value)
    original = wp.synchronize_device

    def blocking(device):
        selected = wp.get_device(device)
        if selected != batch.device:
            raise ValueError("blocking probe event belongs to a different device")
        with wp.ScopedDevice(selected):
            wp.record_event(event)
        wp.synchronize_event(event)

    expected = None
    entries = []
    try:
        for repeat in range(args.repeats):
            modes = ["production", "blocking_event"] if repeat % 2 == 0 else ["blocking_event", "production"]
            for mode in modes:
                clear_scratch(batch)
                original(batch.device)
                wp.synchronize_device = original if mode == "production" else blocking
                begin, cpu, thread = perf_counter(), process_time(), thread_time()
                results, timing = batch.run(args.count, 0)
                elapsed, cpu_seconds, thread_seconds = perf_counter() - begin, process_time() - cpu, thread_time() - thread
                poses, _ = batch.get_poses(np.arange(args.count, dtype=np.int32))
                if expected is None:
                    expected = (results, poses)
                else:
                    exact(results, expected[0], "wait-mode complete results")
                    exact(poses, expected[1], "wait-mode complete poses")
                with wp.ScopedDevice(batch.device):
                    current = ctypes.c_uint()
                    assert driver.cuCtxGetFlags(ctypes.byref(current)) == 0
                    assert current.value == flags.value
                entries.append(dict(mode=mode, repeat=repeat, timing=timing, wall_seconds=elapsed,
                                    process_cpu_seconds=cpu_seconds, thread_cpu_seconds=thread_seconds,
                                    exact=True, context_flags=current.value))
                print(f"{mode} repeat={repeat}: {elapsed:.6f}s wall, {thread_seconds:.6f}s thread CPU, exact")
    finally:
        wp.synchronize_device = original
        original(batch.device)
        with wp.ScopedDevice(batch.device):
            assert driver.cuEventDestroy_v2(handle) == 0
    save_json(args.output / "measurements.json", dict(config=asdict(config), count=args.count,
              device=str(batch.device), uuid=batch.device.uuid, context_flags=flags.value,
              source_sha256=digest(args.source), measurements=entries,
              scope="Complete production Batch.run including scalar transfer; full equality outside timed interval."))


if __name__ == "__main__":
    main()
