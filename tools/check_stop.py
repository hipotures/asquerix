"""Exercise graceful SIGINT stopping without writing into archived evidence."""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
from pathlib import Path
from time import perf_counter, sleep

from asquerix.persistence import read_json, write_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("runs/stop-sigint"))
    parser.add_argument("--log", type=Path)
    parser.add_argument("--controller", type=Path)
    parser.add_argument("--wait-seconds", type=float, default=2.0)
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    args = parser.parse_args(argv)
    if args.wait_seconds < 0.0 or args.timeout_seconds <= 0.0:
        parser.error("wait-seconds must be non-negative and timeout-seconds must be positive")

    log_path = args.log or args.output.parent / f"{args.output.name}.log"
    controller_path = args.controller or args.output.parent / "stop-controller.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "asquerix.cli",
        "run",
        "--n",
        "12",
        "--trials",
        "64",
        "--batch-size",
        "8",
        "--max-seconds",
        "60",
        "--keep-best",
        "3",
        "--max-images",
        "2",
        "--output",
        str(args.output),
        "--no-push",
    ]
    with log_path.open("w", encoding="utf-8") as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        sleep(args.wait_seconds)
        requested = perf_counter()
        child.send_signal(signal.SIGINT)
        returncode = child.wait(timeout=args.timeout_seconds)
    value = {
        "command": command,
        "returncode": returncode,
        "signal": "SIGINT",
        "signal_sent_to_process_exit_seconds": perf_counter() - requested,
        "log": str(log_path),
        "output": str(args.output),
        "note": "External request-to-exit includes in-flight drain, audit, persistence and reporting.",
    }
    write_json(controller_path, value)
    if returncode != 0:
        raise RuntimeError(f"experiment process exited with status {returncode}")
    metadata = read_json(args.output / "environment.json")
    if metadata["stop_reason"] != "SIGINT" or metadata["completed_trials"] >= 64:
        raise RuntimeError("SIGINT run did not preserve a partial completed result")
    print(f"Controller: {controller_path}.gz")
    print(f"Status: {metadata['stop_reason']} | completed={metadata['completed_trials']} | drain={metadata['stop_observed_to_batch_completion_seconds']:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
