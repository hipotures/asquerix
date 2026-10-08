"""Input and device selection checks that do not need CUDA."""
import pytest
from asquerix.gpu import Config, Batch


@pytest.mark.parametrize("arguments", [
    {"n": 0}, {"n": 33}, {"n": 1.5}, {"n": True}, {"seed": 2**64}, {"seed": -1},
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
