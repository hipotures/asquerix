"""GPU telemetry sessions, power-limit validation and the monitor endpoint."""

from fastapi.testclient import TestClient
import pytest

from asquerix.lab import gpumon
from asquerix.lab.api import create_app


def gpu(index=0, utilization=50.0):
    return {"index": index, "uuid": f"GPU-{index}", "name": "NVIDIA GeForce Test", "temperature_c": 40.0,
            "fan_percent": 30.0, "power_w": 60.0, "power_limit_w": 285.0, "power_min_w": 100.0,
            "power_max_w": 285.0, "power_default_w": 285.0, "utilization_percent": utilization, "memory_percent": 20.0}


def test_sessions_sample_only_while_computing_freeze_and_restart():
    active = {"id": None}
    calls = []
    monitor = gpumon.GpuMonitor(lambda: active["id"], sampler=lambda: calls.append(1) or [gpu(0), gpu(1, 90.0)])
    monitor.tick()
    assert monitor.snapshot()["session"] == 0 and not calls
    active["id"] = "a" * 32
    monitor.tick()
    monitor.tick()
    first = monitor.snapshot()
    assert first["live"] and first["session"] == 1 and len(first["samples"]) == 2
    assert first["samples"][0]["gpus"][1][3] == 90.0
    active["id"] = None
    monitor.tick()
    monitor.tick()
    frozen = monitor.snapshot()
    assert not frozen["live"] and frozen["finished"] and len(frozen["samples"]) == 2 and len(calls) == 2
    active["id"] = "b" * 32
    monitor.tick()
    restarted = monitor.snapshot()
    assert restarted["session"] == 2 and restarted["campaign_id"] == "b" * 32 and len(restarted["samples"]) == 1


def test_history_is_bounded_and_sampler_errors_keep_previous_values():
    monitor = gpumon.GpuMonitor(lambda: "c" * 32, sampler=lambda: [gpu()])
    for _ in range(gpumon.HISTORY + 5):
        monitor.tick()
    assert len(monitor.snapshot()["samples"]) == gpumon.HISTORY

    def broken():
        raise OSError("nvidia-smi missing")
    monitor.sampler = broken
    monitor.tick()
    snapshot = monitor.snapshot()
    assert snapshot["error"] == "nvidia-smi missing" and snapshot["gpus"] == [gpu()]


def test_power_limit_is_validated_before_any_command(monkeypatch):
    monkeypatch.setattr(gpumon.subprocess, "run", lambda *a, **k: pytest.fail("no command for invalid input"))
    with pytest.raises(ValueError, match="between 100 and 285 W"):
        gpumon.set_power_limit(0, 300, [gpu()])
    with pytest.raises(KeyError):
        gpumon.set_power_limit(3, 200, [gpu()])


def test_monitor_endpoint_and_power_limit_requires_client_header(tmp_path):
    app = create_app(tmp_path, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        data = client.get("/api/v1/gpu-monitor").json()
        assert data["session"] == 0 and data["live"] is False and "available" in data["power_control"]
        assert client.post("/api/v1/gpus/0/power-limit", json={"watts": 200}).status_code == 403
    app.state.service.catalog.close()
