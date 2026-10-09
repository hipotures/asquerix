# CUDA kernel optimization, 2026-10-09

The accepted optimization increases completed-experiment GPU throughput by **52.8% for N=16** and **53.9% for N=12**, with bitwise-identical results in the recorded CUDA comparisons. It reuses standard sine/cosine evaluations inside `axes()` while preserving independent operands for the original SAT rounding. No solver budgets, tolerances, contact order, orientation equations, final residual calculations, RNG, memory layout, or batch submission behavior changed.

## Source and environment

- Frozen main baseline: `d4ec2384c4ad2c5fa303772214c0793633e95f3b`.
- Preserved minimum-step correction: `eb8d2ac42a089a19a172074f554d6bed2cb17bb0`.
- Optimized source commit: [`d5e98a4f07ae196a9af9b344fab903869c9a9869`](https://github.com/hipotures/asquerix/commit/d5e98a4f07ae196a9af9b344fab903869c9a9869).
- Baseline `gpu.py` SHA-256: `e21c939b07edab77b50f32d5b74e1f9b9ad4c510ed7ad323e417714dacbe9571`.
- Optimized `gpu.py` SHA-256: `a73adf65e92336a1c865f698497cdbba03b8efd2eb19670f8b17885b846e9d0d`.
- Actual CUDA device: NVIDIA GeForce RTX 4070 Ti, sm_89, 60 SMs, 12,282 MiB, display attached.
- Driver 615.71.09; CUDA toolkit 13.4.92; Warp 1.18.0; locked dependencies. Complete dependency/hardware metadata is in the corpus and measurement JSON.
- `fast_math=False`, `enable_backward=False`, 32 threads/block. These settings are unchanged.

HEAD was clean before capture tooling was added. The corpus environment subsequently reports a dirty tree because the new tools and evidence existed; its production-source hash still exactly matches baseline main. The frozen module was independently compared with the unedited production module before optimization. Three paired medium measurements of identical source differed by less than 0.5% in median throughput and matched every output byte. Already published remote experiment commits were merged on main after measurements; they changed only experiment artifacts and preserved the baseline production-source hash. No branches or worktrees were created or switched.

The inspected historical N=16, batch=131000 run completed 393000 trials at 1938.66 GPU trials/s. It recorded dirty source revision `578023b`, so that number is context, not the comparison baseline. Its configuration/provenance is preserved in [historical-workload.json](historical-workload.json). All accepted speedups below use fresh, paired measurements of the frozen baseline.

## Exact workload

The main workload uses N=16. The N=12 control changes only `n`:

```json
{
  "n": 16,
  "initial_side": 10.0,
  "seed": 20261008,
  "step": 0.2,
  "step_floor": 0.0001,
  "step_reduction": 0.5,
  "guard": 0.00002,
  "acceptance_tolerance": 0.000002,
  "motion_tolerance": 0.0000001,
  "rotation_mobility": 0.3,
  "relaxation": 0.8,
  "max_translation": 0.1,
  "max_rotation": 0.08,
  "max_attempts": 128,
  "max_sweeps": 480,
  "stagnation_sweeps": 4,
  "proposals_per_square": 2000
}
```

Each saturated measurement completes 131072 worlds, global trial IDs 0–131071. Both variants use identical inputs and full budgets. Initialization and all eight 16-attempt kernel submissions remain device resident, with one thread per world. No batch scheduling optimization was attempted.

## Saturated results

Median of three synchronized measurements per variant and N. Order alternated baseline/optimized, optimized/baseline, baseline/optimized. Every repeated baseline and optimized run was compared byte-for-byte with the first baseline's complete scalar and pose arrays. All 131072 results per run remained GPU-feasible. Independent CPU validation checked 32 deterministic samples per run; this is sampled numerical validation, not validation of every saturated geometry or a rigorous certificate.

| Variant | GPU trials/s | Speedup | Registers/thread | Exact equality | Validation |
|---|---:|---:|---:|---|---|
| Baseline N=16 | 1907.09 | 1.000× | 139 | Yes, repeated baseline | 32 CPU samples/run |
| Shared trig with independent operands N=16 | 2913.59 | 1.528× | 128 | Yes, all poses/results | 32 CPU samples/run |
| Baseline N=12 | 3278.56 | 1.000× | 139 | Yes, repeated baseline | 32 CPU samples/run |
| Shared trig with independent operands N=12 | 5044.13 | 1.539× | 128 | Yes, all poses/results | 32 CPU samples/run |

| N | Variant | GPU trials/s range | Range span / median | Median device seconds | Median batch/readback seconds | Median harness end-to-end seconds |
|---:|---|---:|---:|---:|---:|---:|
| 16 | Baseline | 1900.77–1925.96 | 1.32% | 68.728844 | 68.753628 | 69.900121 |
| 16 | Optimized | 2911.25–2941.16 | 1.03% | 44.986430 | 45.021067 | 45.654284 |
| 12 | Baseline | 3253.85–3279.17 | 0.77% | 39.978523 | 39.994645 | 40.567560 |
| 12 | Optimized | 5043.54–5046.34 | 0.06% | 25.985061 | 25.998050 | 26.304148 |

`device_seconds` comes from CUDA events around the production submission, followed by device synchronization. It excludes JIT, warm-up, pose/scalar transfer, CPU validation, compression, rendering and publication. Batch/readback time includes synchronized simulation and complete scalar/pose readback. Harness end-to-end additionally includes exact comparison, independent sample validation and reference archival on the first baseline. Metadata serialization, process snapshots, JIT and warm-up are outside that end-to-end scope. This is a benchmark-harness measurement, not total ordinary CLI campaign latency; its phases are recorded separately in [measurements.json](axes-opaque-saturated/measurements.json).

Background desktop applications and an NVENC video encoder were active during the campaign. No user process was stopped. GPU-process snapshots and one-second utilization, clocks, temperature and power logs are preserved with the measurements. Alternation and the observed small ranges reduce bias but do not eliminate interference. These are actual measurements under recorded shared-device conditions; a dedicated idle-device campaign remains useful.

## Isolated candidates

Broad phases were implemented first and tested independently, then reverted because they did not improve throughput. Their final exact SAT residual paths were unchanged. All medium results below use 4096 worlds and three alternating measurements. Each speedup uses that candidate's paired baseline, not a baseline from another series. Slow or numerically invalid candidates were not promoted to saturated runs.

| Variant | GPU trials/s | Speedup | Registers/thread | Exact equality | Validation |
|---|---:|---:|---:|---|---|
| Pair broad phase N=16 | 523.13 (baseline 525.23) | 0.996× | 148 | Yes | CPU samples passed |
| Pair broad phase N=12 | 879.40 (baseline 892.45) | 0.985× | 148 | Yes | CPU samples passed |
| Wall broad phase N=16 | 513.61 (baseline 535.95) | 0.958× | 156 | Yes | CPU samples passed |
| Wall broad phase N=12 | 882.01 (baseline 917.42) | 0.961× | 156 | Yes | CPU samples passed |
| Simple shared trig operands | Not measured | Not measured | Not recorded | **No** | Rejected: 15 tests failed |
| Independent trig operands N=16 | 690.76 (baseline 507.18) | 1.362× | 128 | Yes | CPU samples passed |
| Independent trig operands N=12 | 1197.82 (baseline 883.86) | 1.355× | 128 | Yes | CPU samples passed |

The conservative pair test used `distance_squared > 2*(1+guard)^2 + 0.001` within bounded squared distances and orientations, with the original SAT path otherwise. The wall test used circumradius plus guard and a numerical margin. Adversarial diagnostics, guard-boundary tests and complete corpus runs passed both candidates. Both added branches and increased register counts; measured throughput did not improve. The patches and negative measurement series are retained under `candidates/`, `pair-medium/` and `wall-medium/`; neither broad phase remains in production.

Simple trig reuse initially preserved all four axis components but changed downstream compiler algebra and FMA rounding. In a 65536-angle CUDA probe, `dot(u,v)` and `dot(v,u)` differed for 65514 angles, and `dot(v,v)` for 11919. Complete poses, counters and contact diagnostics also changed. That variant was rejected without a performance run. The accepted redesign uses native volatile `mov.b32` copies for the second axis, preserving the bit patterns while separating compiler operands. The redesigned probe matched all eight axis/dot columns exactly. [Compiler evidence](candidates/axes-compiler.json), [PTX excerpts](candidates/axes-compiler-extracts.txt), probe results and isolated patches are preserved.

## Correctness and normal behavior

The checked-in [corpus](corpus/corpus.json) contains complete final and initialization poses and every `Result` field for 106 trials across N=1,4,11,12,16,32. Each N has seeds 20261008 and 987654321, at offsets 0 and 4096. It also includes N=11/seed=20261008/trials 4124 and 4372, and an unsigned-64-bit seed/ID boundary range for N=4.

All comparisons use dtype, shape and every byte, including signed zeros and NaN payloads. They cover L, x/y/theta, termination, feasibility, attempts, accepted/rejected steps, sweeps, proposals, final step, minimum SAT separation, wall clearance and maximum penetration. Initialization arrays and proposal counts preserve RNG-derived identity; each global trial ID is the recorded offset plus row index.

Ten dense N=32 cases fail initialization identically. The harness zeroes both variants' pose/work buffers before launch, outside timing, to define otherwise unwritten slots. It does not repair initialization or change production behavior. Every initialized small final geometry (96 cases) passes the independent float64 CPU validator. Initialization failures are not mislabeled as validated geometry.

The corpus includes 8204 initial pair/wall diagnostics with near tangency, nearly parallel axes, corner and coincident contacts, tiny positive separations, rotated edge contacts, wall boundaries and randomized guard/circumcircle rings. Additional CUDA tests cover extreme/invalid wall inputs, dense simultaneous-contact resumes, numerical failure statuses, traces, and the axis/dot rounding regression.

For saturated N=12 and N=16, every scalar and every final pose matched across three optimized runs and repeated baselines: 262144 distinct trial inputs, 786432 optimized completions. A separate [full initialization check](initial-saturated-check.json) compared all 262144 initial result/pose records against the frozen archives. The independent saturated sample contains 64 distinct geometries, checked again on every repetition.

The full existing suite plus new regressions passed on actual CUDA: **248 passed, 0 skipped, 0 failed**, with two upstream Warp ctypes deprecation warnings, in 85.60 seconds. See [test evidence](tests.json) and [full log](tests-full.log). Earlier isolated candidate test outcomes are preserved separately.

A bounded ordinary CLI smoke run used `--json --no-push`, completed and independently validated all eight N=12 trials, saved gzip records/poses, rendered SVG, and returned `COMPLETED + LOCAL_ONLY`. Its complete artifacts are under [cli-smoke](cli-smoke/report.md). Existing CLI, Rich, batch partitioning, validation, persistence, rendering, naming, publication and interruption tests also passed. No production runner, CLI, publication or persistence code changed.

## Profiling findings and remaining work

Generated CUDA/PTX shows repeated standard trigonometric range-reduction/polynomial work in axes, wall support, pair constraints/gaps and residuals. Original p-axis calculations were already hoisted across the residual j-loop; source call counts alone would overstate duplicated work. The accepted `simulate` PTX is smaller (7601 versus 11274 lines; 403 versus 565 static FMA instructions). These are static text counts, not measured dynamic operation counts.

Warp/driver properties show registers falling from 139 to 128 per thread. The driver occupancy API increases theoretical residency from 12 to 16 blocks/SM, or 25% to 33.3% of the device's 1536 threads/SM with unchanged 32-thread blocks. Local-memory allocation remains 32 bytes/thread. This allocation is not a measured spill count: generated code also contains libdevice local-memory paths. The measurement demonstrates throughput improvement but cannot apportion it between reduced arithmetic and register pressure.

Nsight Compute/System tools were unavailable. Achieved occupancy, SM utilization, dynamic spill traffic and branch divergence were not measured. `nvidia-smi` GPU/memory utilization is logged and must not be presented as those metrics. [Profiling metadata](profiling.json) explicitly records the gaps.

[Work-count evidence](work-counts.json) shows substantial within-warp variation: mean/maximum sweep-count ratios average 0.661 for N=16 and 0.612 for N=12. This is a work-count proxy, not measured branch efficiency; sweep costs also vary. Stopping criteria and world ordering remain unchanged.

The `(square, world)` layout already coalesces accesses across world threads. No layout change was justified by the available evidence. Further work should profile on an idle device with Nsight, inspect remaining identical-orientation reuse without changing FMA grouping, and verify whether initial residual calls or rejection-buffer restoration survive compiler dead-code elimination before attempting their removal. Any such change needs a separate isolated exact-output comparison. The native operand barrier and bitwise acceptance are scoped to the tested GPU, driver, Warp and compiler; future toolchains require renewed CUDA regression evidence.

## Artifacts and reproduction

Small correctness arrays, source snapshots, timing JSON/CSV, test evidence, patches and this report are versioned here. Complete medium/saturated numerical archives remain in the durable local directory `runs/performance-cuda-20261009/`; approximately 100 MB is deliberately excluded from Git. [data-manifest.json](data-manifest.json) records paths, sizes, SHA-256 values and array semantics. Each series also has N-specific manifests with full configurations and offsets. Optimized arrays equal the archived baseline byte-for-byte, so the archives represent both variants without duplicating identical large datasets.

Commands actually exercised, using `UV_CACHE_DIR=/tmp/asquerix-uv-cache` in this environment:

```bash
uv run --locked pytest -q
uv run --locked python tools/kernel_benchmark.py benchmark --count 4096 --repeats 3 --output runs/performance-cuda-20261009/axes-opaque-medium
uv run --locked python tools/kernel_benchmark.py benchmark --count 131072 --repeats 3 --output runs/performance-cuda-20261009/axes-opaque-saturated
uv run --locked python tools/kernel_benchmark.py check-initial --benchmark-directory runs/performance-cuda-20261009/axes-opaque-saturated --output artifacts/performance/cuda-20261009/initial-saturated-check.json
uv run --locked python tools/kernel_axes_probe.py --output artifacts/performance/cuda-20261009/candidates/axes-opaque-probe.json
uv run --locked asquerix run --n 12 --max-sweeps 480 --trials 8 --batch-size 8 --retain-all --sample-every 0 --audit-size 8 --keep-best 2 --max-images 1 --max-seconds 30 --output runs/performance-cuda-20261009/cli-smoke --json --no-push
```

Use fresh output paths when repeating commands; existing benchmark/run directories are protected. The benchmark tool directly exercises production `Batch` on CUDA and never invokes publication. The CLI smoke explicitly used `--no-push`. Large arrays and failed candidates were not published as ordinary scientific experiments. The frozen solver is solely an archival reference, not an alternate production implementation or fallback.
