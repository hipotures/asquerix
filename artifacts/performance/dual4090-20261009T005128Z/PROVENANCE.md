# Provenance and workload

The reference is current optimized production at `d5ea5255e37725d02f4cb3dfc21a12ef70e1be14`, including the accepted axis optimization `d5e98a4f07ae196a9af9b344fab903869c9a9869` and minimum-step correction `eb8d2ac42a089a19a172074f554d6bed2cb17bb0`. The production and frozen `gpu.py` SHA-256 is `a73adf65e92336a1c865f698497cdbba03b8efd2eb19670f8b17885b846e9d0d`. The kernel was retained unchanged after two rejected candidates. The earlier `d4ec238` reference and RTX 4070 Ti performance results are historical evidence only.

The checkout was clean on `main` with one worktree and no running experiment before the freeze. `baseline/freeze.json.gz` records `production_source_dirty=false`; its broader environment `source_dirty=true` reflects this newly created untracked evidence directory. The snapshot is archival, loaded with its own module identity, and is never a production fallback. Worker caches are separate by campaign and physical device; existing caches were not cleared. The accepted native `volatile mov.b32` operand barriers remain intact. Generated CUDA/PTX and their hashes are in `baseline/compiler/`.

## Physical devices

| Label | Name | Physical UUID | PCI bus | Memory |
|---|---|---|---|---|
| A | NVIDIA GeForce RTX 4090 | GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d | 00000000:01:00.0 | 24564 MiB |
| B | NVIDIA GeForce RTX 4090 | GPU-81ac6e96-0bfe-390d-beb1-241466569d6b | 00000000:02:00.0 | 24564 MiB |

Both are distinct physical sm_89 cards with 128 SMs. Driver: 615.71.09. CUDA driver compatibility, runtime and compiler details are recorded verbatim in `hardware.txt`; the installed CUDA toolkit and Warp wheel use 13.4.92. Python 3.14.7, Warp 1.18.0, NumPy 2.5.3, Rich 14.3.4, pytest 9.1.1, uv 0.12.16. Nsight Compute 2026.3.1.0 and Nsight Systems 2026.3.2.476 were available and counter access worked. The original `uv.lock` SHA-256 is `e14eff967e954d063ea3874aa7bb4dca0ef15c19ff966883046cf4950d5a300a`; dependencies and lockfile were preserved.

Initial `CUDA_VISIBLE_DEVICES` and `CUDA_DEVICE_ORDER` were unset. Each spawned worker sets `CUDA_VISIBLE_DEVICES` to exactly its assigned physical UUID, then initializes CUDA and verifies that its only visible `cuda:0` has that UUID. Both local ordinals therefore equal zero while referring to different cards. Nsight's `(PID, local ordinal)` mapping independently confirms this. The coordinator does not initialize CUDA.

The cards share a PCIe host bridge (PHB) and CPU affinity 0–15. No peer access, NVLink, NCCL or cross-device contacts are used. No driver, security, power, thermal or persistent clock settings were manually changed. Initial Nsight Compute profiles used the profiler's default temporary boost clock control; this was discovered in session exports and is explicitly disclosed. Replacement profiles use `--clock-control none`. All throughput campaigns are unprofiled. The initial power limit was 480 W per card, idle temperatures were 35/33 °C, and idle clocks were 210/405 MHz. `hardware.txt` records complete initial capabilities and telemetry; each campaign's `gpu-monitor.csv` records simultaneous utilization, temperatures, clocks, power and memory at one-second intervals. Each measurement records competing compute processes before and after execution. The user's `nvtop` monitor was left running.

## Numerical configuration

All principal and sustained measurements use the complete configuration below, varying only N between 12 and 16. Initialization and all production solver stages remain inside the workload.

```text
initial_side = 10.0
seed = 20261008
step = 0.2
step_floor = 0.0001
step_reduction = 0.5
guard = 0.00002
acceptance_tolerance = 0.000002
motion_tolerance = 0.0000001
rotation_mobility = 0.3
relaxation = 0.8
max_translation = 0.1
max_rotation = 0.08
max_attempts = 128
max_sweeps = 480
stagnation_sweeps = 4
proposals_per_square = 2000
```

Precision remains float32 in the solver and float64 in the independent CPU validator, with `fast_math=false`, backward generation disabled, block dimension 32, and eight bounded submissions of at most sixteen attempts. Budgets, stopping rules, tolerances, operation order and RNG were preserved. The ordinary CLI default sweep budget is not substituted for the explicit 480 here.

Principal batch size B is 131072 on each active GPU. Every principal mode executes W=262144 unique global IDs 0..262143: A alone and B alone each execute two full batches; concurrent A receives 0..131071 and B receives 131072..262143. Sustained campaigns use W=524288 IDs 0..524287: four full batches alone, two full batches per device concurrently. Seed identity stays `(global_seed, global_trial_id)` without adding a GPU ordinal.

The controlled ordinary-pipeline policy saves every scalar trial record and validates the fixed global IDs divisible by 4096. It uses `sample_every=4096`, `audit_size=0`, `keep_best=0`, `failure_examples=0`, `max_images=0`, and `retain_all=false`. There are 128 independently checked geometries for W=524288, irrespective of partition. This makes per-trial validation outcomes and schemas exactly comparable across devices and gzip levels. It is a documented benchmark policy, not a change to ordinary CLI selection defaults. Sparse rendering and ordinary selection are exercised separately by the CLI smoke test and regression suite. Benchmark publication is disabled; normal CLI publication remains after finalization.

## Timing boundaries

CUDA time uses existing start/end events on the same physical device around all production submissions, including initialization. Event times are summed only for consecutive batches on that same device. No cross-device event subtraction or sum-of-simultaneous-times throughput is used.

Compute common execution wall time starts at the coordinator's warmed-worker release and ends after all GPU completion acknowledgements. It includes `Batch.run` synchronization, scalar readback and required IPC. It excludes startup/JIT, scratch preparation, full pose readback, reference initialization checks, archives, comparison, CPU validation, rendering and publication.

Ordinary-pipeline common execution wall time starts at the same warmed-worker release and ends after all actual ordinary runner operations finalize their gzip streams, selected-pose evidence and reports. It includes the runner's one-world warm-up and all host processing. Warm-up IDs are excluded from completed counts. This scope deliberately differs from compute-only common time.

The full harness timing snapshot includes discovery, worker creation, isolated JIT/prewarm, every repetition, full archival, comparison, CPU validation, intermediate metadata and shutdown. It ends before final manifest serialization and terminal summary. Independent external process timing, where recorded, includes those final outputs and documents its exact boundary. It is reported per campaign, not disguised as a single experiment time. Profiling replay and diagnostic wrappers are confined to separate campaigns; their times are excluded from headline rates. Nested diagnostic phases and concurrent worker CPU durations overlap and must not be summed into wall time.

## Documentation consulted

Installed-version behavior was checked against [Warp concurrency](https://nvidia.github.io/warp/stable/user_guide/execution_and_performance/concurrency.html), [Nsight Compute profiling](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html), [Nsight Compute CLI](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html), [CUDA events](https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__EVENT.html), [CUDA context scheduling](https://docs.nvidia.com/cuda/cuda-driver-api/group__CUDA__CTX.html), [counter access permissions](https://developer.nvidia.com/nvidia-development-tools-solutions-err-nvgpuctrperm-nsightcompute), and [Python 3.14 gzip](https://docs.python.org/3.14/library/gzip.html). Installed API signatures, supported metric queries and actual device execution take precedence over theoretical assumptions.
