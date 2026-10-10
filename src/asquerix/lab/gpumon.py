"""Live GPU and CPU telemetry and GPU power limits for the browser, sampled only while computing.

Telemetry comes from one `nvidia-smi --query-gpu` call per interval (about
30 ms for all GPUs); it never creates a CUDA context. A monitoring session
starts when the service begins a campaign or replay and freezes when it ends,
so the browser can keep showing the last values.
"""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
from threading import Event, Lock, Thread
import time
from typing import Callable

FIELDS = ("index", "uuid", "name", "temperature.gpu", "fan.speed", "power.draw", "power.limit",
          "power.min_limit", "power.max_limit", "power.default_limit", "utilization.gpu",
          "memory.used", "memory.total")
HISTORY = 180


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:  # "[N/A]", "[Not Supported]"
        return None


def query() -> list[dict]:
    result = subprocess.run(["nvidia-smi", "--query-gpu=" + ",".join(FIELDS), "--format=csv,noheader,nounits"],
                            capture_output=True, text=True, timeout=3, check=True)
    gpus = []
    for values in csv.reader(result.stdout.splitlines()):
        if len(values) != len(FIELDS):
            continue
        row = dict(zip(FIELDS, (value.strip() for value in values)))
        used, total = _number(row["memory.used"]), _number(row["memory.total"])
        gpus.append({"index": int(row["index"]), "uuid": row["uuid"], "name": row["name"],
                     "temperature_c": _number(row["temperature.gpu"]), "fan_percent": _number(row["fan.speed"]),
                     "power_w": _number(row["power.draw"]), "power_limit_w": _number(row["power.limit"]),
                     "power_min_w": _number(row["power.min_limit"]), "power_max_w": _number(row["power.max_limit"]),
                     "power_default_w": _number(row["power.default_limit"]),
                     "utilization_percent": _number(row["utilization.gpu"]),
                     "memory_percent": round(100 * used / total, 1) if used is not None and total else None})
    return gpus


def _power_command(index: int, watts: int) -> list[str]:
    command = [shutil.which("nvidia-smi") or "/usr/bin/nvidia-smi", "-i", str(index), "-pl", str(watts)]
    return command if os.geteuid() == 0 else ["sudo", "-n", *command]


def power_control() -> dict:
    """Whether power limits can be changed without an interactive password."""
    if os.geteuid() == 0:
        return {"available": True, "reason": "Server runs as root"}
    command = _power_command(0, 100)
    try:
        allowed = subprocess.run(["sudo", "-n", "-l", *command[2:]], capture_output=True, timeout=3).returncode == 0
    except (OSError, subprocess.SubprocessError):
        allowed = False
    if allowed:
        return {"available": True, "reason": "Allowed by sudoers for nvidia-smi"}
    user = os.environ.get("USER", "user")
    return {"available": False,
            "reason": "Changing a GPU power limit requires root. Allow only this command without a password, "
                      "e.g. with `sudo visudo -f /etc/sudoers.d/asquerix-power`:",
            # An anchored regular expression (sudo >= 1.9.10): a `*` wildcard would also match extra arguments.
            "sudoers": f"{user} ALL=(root) NOPASSWD: {command[2]} ^-i [0-9] -pl [0-9]{{2,4}}$"}


def set_power_limit(index: int, watts: float, gpus: list[dict]) -> dict:
    gpu = next((item for item in gpus if item["index"] == index), None)
    if gpu is None:
        raise KeyError("Unknown GPU index")
    low, high = gpu["power_min_w"], gpu["power_max_w"]
    if low is None or high is None:
        raise ValueError("This GPU does not report adjustable power limits")
    watts = round(watts)
    if not low <= watts <= high:
        raise ValueError(f"Power limit must be between {low:g} and {high:g} W")
    result = subprocess.run(_power_command(index, watts), capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        raise PermissionError((result.stderr or result.stdout).strip().splitlines()[-1] if (result.stderr or result.stdout).strip()
                              else "nvidia-smi refused the power limit")
    return {"index": index, "uuid": gpu["uuid"], "previous_w": gpu["power_limit_w"], "requested_w": watts}


class CpuSampler:
    """CPU load of the host and of this server's process tree (worker and validation pool included), from /proc.

    `app_cores` is CPU time used per second (2.0 means two cores fully busy); `busy_threads` counts the tree's
    threads that ran more than half of the interval.
    """

    def __init__(self, root_pid: int | None = None):
        self.root = root_pid or os.getpid()
        self.tick = os.sysconf("SC_CLK_TCK")
        self.cores = os.cpu_count() or 1
        self.previous = None

    @staticmethod
    def _fields(path: str) -> list[str]:
        with open(path, encoding="ascii", errors="replace") as stream:
            text = stream.read()
        return text[text.rindex(")") + 2:].split()  # the command name may contain spaces

    def _tree(self) -> list[int]:
        # Walk down through each thread's `children` file instead of reading every process in /proc.
        tree, frontier = [], [self.root]
        while frontier:
            pid = frontier.pop()
            tree.append(pid)
            try:
                for task in os.scandir(f"/proc/{pid}/task"):
                    with open(f"/proc/{pid}/task/{task.name}/children", encoding="ascii") as stream:
                        frontier += [int(child) for child in stream.read().split()]
            except OSError:
                continue
        return tree

    def sample(self) -> dict | None:
        with open("/proc/stat", encoding="ascii") as stream:
            values = [int(value) for value in stream.readline().split()[1:]]
        idle, total = values[3] + values[4], sum(values[:8])
        threads = {}
        for pid in self._tree():
            try:
                for task in os.scandir(f"/proc/{pid}/task"):
                    fields = self._fields(f"/proc/{pid}/task/{task.name}/stat")
                    threads[(pid, task.name)] = int(fields[11]) + int(fields[12])
            except (OSError, ValueError, IndexError):
                continue
        now, previous = time.monotonic(), self.previous
        self.previous = (now, idle, total, threads)
        if previous is None:
            return None
        then, idle_before, total_before, threads_before = previous
        seconds = max(now - then, 1e-3)
        deltas = [(ticks - threads_before.get(key, ticks)) / self.tick for key, ticks in threads.items()]
        busy = total - total_before
        return {"load_percent": round(100 * (1 - (idle - idle_before) / busy), 1) if busy else None,
                "app_cores": round(sum(deltas) / seconds, 2), "busy_threads": sum(delta > 0.5 * seconds for delta in deltas),
                "app_processes": len({key[0] for key in threads}), "cores": self.cores}


class GpuMonitor:
    def __init__(self, computing: Callable[[], str | None], *, interval: float = 1.0, sampler=query):
        self.computing, self.interval, self.sampler = computing, interval, sampler
        self.lock = Lock()
        self.stopped = Event()
        self.thread = None
        self.session = 0
        self.live = False
        self.campaign_id = None
        self.started = self.finished = None
        self.gpus: list[dict] = []
        self.samples: list[dict] = []
        self.error = None
        self.cpu_sampler = CpuSampler()
        self.cpu = None

    def start(self):
        self.thread = Thread(target=self._run, name="asquerix-gpu-monitor", daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=5)

    def _run(self):
        while not self.stopped.is_set():
            self.tick()
            self.stopped.wait(self.interval)

    def tick(self):
        campaign = self.computing()
        if campaign and not self.live:
            with self.lock:  # a new computation starts a fresh session
                self.session += 1
                self.live, self.campaign_id = True, campaign
                self.started, self.finished = time.time(), None
                self.samples, self.error = [], None
        elif not campaign and self.live:
            with self.lock:  # freeze the last values; nothing is sampled until the next computation
                self.live, self.finished = False, time.time()
            return
        if not self.live:
            return
        try:
            cpu = self.cpu_sampler.sample()
        except (OSError, ValueError):
            cpu = None
        try:
            gpus = self.sampler()
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            with self.lock:
                self.error = str(error)
            return
        with self.lock:
            self.gpus = gpus
            self.cpu = cpu
            self.error = None
            self.samples.append({"t": time.time(), "cpu": [cpu["load_percent"], cpu["app_cores"]] if cpu else None, "gpus": [
                [gpu["temperature_c"], gpu["fan_percent"], gpu["power_w"], gpu["utilization_percent"], gpu["memory_percent"]]
                for gpu in gpus]})
            del self.samples[:-HISTORY]

    def snapshot(self) -> dict:
        with self.lock:
            return {"session": self.session, "live": self.live, "campaign_id": self.campaign_id,
                    "started": self.started, "finished": self.finished, "interval_seconds": self.interval,
                    "sample_fields": ["temperature_c", "fan_percent", "power_w", "utilization_percent", "memory_percent"],
                    "cpu_fields": ["load_percent", "app_cores"], "cpu": self.cpu,
                    "gpus": list(self.gpus), "samples": list(self.samples), "error": self.error}
