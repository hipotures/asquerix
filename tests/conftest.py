"""Shared fixture requiring a real CUDA device without a CPU fallback."""
import pytest


@pytest.fixture(scope="session")
def cuda_device():
    wp = pytest.importorskip("warp", reason="Warp is required for CUDA correctness tests")
    try:
        wp.init()
        device = wp.get_device("cuda:0")
    except Exception as exc:
        pytest.skip(f"CUDA device unavailable: {exc}")
    if not device.is_cuda:
        pytest.skip("CUDA correctness tests require an accessible CUDA device")
    return device
