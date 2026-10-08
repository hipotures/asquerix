"""Measure module loading in a fresh Warp cache without running any trials."""
import json
import os
from time import perf_counter

from asquerix.gpu import Batch, Config

started = perf_counter()
batch = Batch(Config(), 1, "cuda:0")
print(json.dumps({
    "cache_directory": os.environ.get("ASQUERIX_WARP_CACHE"),
    "method": "Fresh Warp kernel cache; NVIDIA driver cache left intact; no simulation trials",
    "module_load_seconds": batch.module_load_seconds,
    "setup_and_load_seconds": perf_counter() - started,
    "kernel_properties": batch.kernel_properties,
    "device": str(batch.device),
}, indent=2))
