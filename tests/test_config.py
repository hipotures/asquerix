"""Input and device selection checks that do not need CUDA."""
import pytest
from asquerix.gpu import Config, Batch


@pytest.mark.parametrize("arguments", [
    {"n": 0}, {"n": -1}, {"n": 1.5}, {"n": True}, {"seed": 2**64}, {"seed": -1},
    {"seed": 1.5}, {"initial_side": float("nan")}, {"initial_side": 1.0},
    {"step": 0}, {"step_floor": 1}, {"max_sweeps": 0}, {"max_attempts": -1},
    {"max_attempts": 3000}, {"step_reduction": 1.0}, {"guard": 1e-7},
    {"proposals_per_square": 0}, {"rotation_mobility": 0},
])
def test_invalid_config(arguments):
    with pytest.raises(ValueError):
        Config(**arguments).validate()


def test_cpu_device_is_never_a_gpu_fallback():
    with pytest.raises(ValueError, match="CPU fallback"):
        Batch(Config(n=1), 1, "cpu")


@pytest.mark.parametrize("capacity", [1000000, 1048576])
def test_million_world_batch_passes_validation_before_gpu_allocation(monkeypatch, capacity):
    from asquerix import gpu

    def reached_initialization():
        raise RuntimeError("GPU initialization reached")
    monkeypatch.setattr(gpu.wp, "init", reached_initialization)
    with pytest.raises(RuntimeError, match="GPU initialization reached"):
        Batch(Config(n=1), capacity)


def test_capacity_above_one_binary_million_is_rejected_before_gpu_initialization(monkeypatch):
    from asquerix import gpu

    monkeypatch.setattr(gpu.wp, "init", lambda: pytest.fail("GPU must not be initialized"))
    with pytest.raises(ValueError, match=r"batch_size must be in \[1,1048576\]"):
        Batch(Config(n=1), 1048577)
