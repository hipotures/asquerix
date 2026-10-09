"""Shared fixture requiring a real CUDA device without a CPU fallback."""
import os
import pytest


@pytest.fixture(scope="session")
def cuda_device():
    wp = pytest.importorskip("warp", reason="Warp is required for CUDA correctness tests")
    try:
        wp.init()
        device = wp.get_device(os.environ.get("ASQUERIX_TEST_DEVICE", "cuda:0"))
    except Exception as exc:
        pytest.skip(f"CUDA device unavailable: {exc}")
    if not device.is_cuda:
        pytest.skip("CUDA correctness tests require an accessible CUDA device")
    expected_uuid = os.environ.get("ASQUERIX_TEST_UUID")
    if expected_uuid and device.uuid != expected_uuid:
        pytest.fail(f"CUDA test device mismatch: expected {expected_uuid}, got {device.uuid}")
    return device
