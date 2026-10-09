# CPU critical path and measured dual RTX 4090 scaling

The ordinary result-saving pipeline is faster with explicit lossless gzip level 3: **6.26% at N=12 and 3.68% at N=16 with both GPUs**, with the GPU kernel fixed. Actual compute scaling is approximately 2x; actual ordinary-pipeline scaling is approximately 1.92x. No new GPU kernel optimization passed the measured acceptance gates. The current optimized kernel and its operand barriers are retained unchanged.

The nvtop screenshot shows CPU 100% for `pytest -q -m gpu`, alongside GPU 93%. On this host, native CUDA synchronization consumes approximately one logical CPU per active worker by busy waiting. It does not establish aggregate host CPU saturation or starvation of an already running kernel. Separate, real host processing between batches does delay the next submission. Profiling and the controlled gzip experiment distinguish these effects.

## Source and hardware provenance

- Frozen current optimized baseline: `d5ea5255e37725d02f4cb3dfc21a12ef70e1be14`.
- Previously accepted kernel optimization: `d5e98a4f07ae196a9af9b344fab903869c9a9869`; minimum-step correction: `eb8d2ac42a089a19a172074f554d6bed2cb17bb0`.
- Retained host/tool implementation: `d0140d7952f8f200ff6f2e0d1be9af2369c4583e`.
- Production and archival `gpu.py` SHA-256: `a73adf65e92336a1c865f698497cdbba03b8efd2eb19670f8b17885b846e9d0d`.
- Evidence commit: the main-branch commit adding this report; obtain its exact SHA with `git log -1 --format=%H -- artifacts/performance/dual4090-20261009T005128Z/REPORT.md`. The final delivery records that SHA and verifies remote main. A commit cannot embed its own SHA without changing it.

Both physical devices are NVIDIA GeForce RTX 4090, 24564 MiB, sm_89 with 128 SMs. GPU A is `GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d`, PCI `00000000:01:00.0`; GPU B is `GPU-81ac6e96-0bfe-390d-beb1-241466569d6b`, PCI `00000000:02:00.0`. Driver 615.71.09, CUDA toolkit/runtime 13.4.92, Warp 1.18.0, Python 3.14.7, NumPy 2.5.3, Rich 14.3.4. Lockfile and tested dependencies are unchanged. Each spawned worker exposes exactly one physical UUID as its local `cuda:0` and verifies the mapping. The parent never initializes CUDA. Full configuration, topology, scheduling, tool versions and timing boundaries are in [PROVENANCE.md](PROVENANCE.md), `baseline/freeze.json.gz`, `hardware.txt` and `hardware-final.txt`.

No drivers, security, power limits or thermal settings were changed. Initial exploratory Nsight Compute runs inadvertently used the tool's default temporary boost clock control. This mistake is disclosed in the session exports and clock-control review; replacement profiles explicitly use `--clock-control none`. All headline measurements are unprofiled. Existing power limits were 480 W per card. Principal telemetry reached 74/68 °C on A/B; the longer ordinary campaign reached 79/72 °C. One-second reported power peaks were 502.25/501.49 W despite the unchanged 480 W configured limits; these are telemetry samples, not a requested power change. Full clocks, power, temperature and competing-process records are preserved in `telemetry-summary.json.gz` and per-campaign CSVs. No results were excluded and no user process was terminated.

## Fixed-work compute results

B=131072 **per GPU**, W=262144 unique global IDs 0..262143, full initialization and solver budgets, seed 20261008. Each isolated card runs two full batches; concurrent A/B each run one. Three repetitions per N/mode, rotated mode order. The following are medians from actual device execution, not the earlier RTX 4070 Ti results or a projection.

| N | GPU UUID | Variant | CUDA trials/s | Speedup vs current baseline | Registers/thread | Exact comparison | CPU validation coverage |
|---|---|---|---:|---:|---:|---|---|
| 12 | GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d | Current baseline retained | 11943.18 | 1.000x | 128 | All defined bytes | 64 fixed IDs; 32/batch |
| 12 | GPU-81ac6e96-0bfe-390d-beb1-241466569d6b | Current baseline retained | 12033.17 | 1.000x | 128 | All defined bytes | 64 fixed IDs; 32/batch |
| 16 | GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d | Current baseline retained | 6760.44 | 1.000x | 128 | All defined bytes | 64 fixed IDs; 32/batch |
| 16 | GPU-81ac6e96-0bfe-390d-beb1-241466569d6b | Current baseline retained | 6815.57 | 1.000x | 128 | All defined bytes | 64 fixed IDs; 32/batch |

| N | Variant | A-alone trials/s | B-alone trials/s | Actual dual trials/s | Dual/A speedup | Dual/B speedup | Capacity efficiency | IDs complete/exact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 12 | Current baseline retained | 11941.38 | 12029.83 | 23908.72 | 2.0022x | 1.9875x | 99.739% | 262144/262144, every repeat |
| 16 | Current baseline retained | 6759.83 | 6814.66 | 13553.85 | 2.0051x | 1.9889x | 99.848% | 262144/262144, every repeat |

CUDA rates use events on the same device around complete production submissions. Common execution rates use coordinator release through all completion acknowledgements, including synchronization, scalar readback and control overhead. Concurrent throughput divides total completed unique IDs by this common wall interval. Capacity efficiency divides actual concurrent rate by the sum of measured isolated rates; it is not a hardware utilization counter. [COMPUTE.md](COMPUTE.md) contains all ranges, CVs, separate card times and the full campaign scope. No incremental GPU speedup is claimed.

## Sustained ordinary result-saving pipeline

W=524288 unique IDs 0..524287, B=131072, four batches alone or two batches on each concurrent card. Both levels execute the same kernel, validation policy and intended records. Variant order alternates and modes rotate; three repetitions per configuration. Common pipeline time includes all ordinary runner work through finalized compressed files and reports, including its separate warm-up; initial worker/JIT setup and Git publication are outside this interval.

| N | Pipeline | A-alone trials/s | B-alone trials/s | Actual dual trials/s | Dual/A | Dual/B | Capacity efficiency | IDs complete/exact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 12 | gzip 9 reference | 9321.61 | 9389.15 | 17971.82 | 1.9280x | 1.9141x | 96.051% | 524288, all records |
| 12 | gzip 3 retained | 9925.54 | 9967.36 | 19096.67 | 1.9240x | 1.9159x | 95.997% | 524288, all records |
| 16 | gzip 9 reference | 5732.17 | 5762.73 | 11034.49 | 1.9250x | 1.9148x | 95.995% | 524288, all records |
| 16 | gzip 3 retained | 5930.63 | 5977.23 | 11440.82 | 1.9291x | 1.9141x | 96.078% | 524288, all records |

Host gains at fixed kernel/device count are N12 A/B/dual **6.479%/6.158%/6.259%**, and N16 **3.462%/3.722%/3.682%**. No producer/consumer rewrite or processing overlap was introduced. Level 3 is persisted in ordinary run configuration/environment metadata. Every sorted decompressed JSONL record, including schema, result counters, IDs and validation status, matches across levels, cards and partitions. All 128 fixed global-ID audit geometries per operation are independently numerically validated; other records remain NOT_CHECKED. Gzip container bytes and hashes appropriately differ.

The benchmark policy is explicitly `sample_every=4096, audit_size=0, keep_best=0, failure_examples=0, max_images=0, retain_all=false`. It saves every scalar record and uses partition-independent audit IDs. This policy is fixed in both compared variants and does not change CLI defaults. A separate ordinary CLI smoke run retains/validates all eight poses, exercises leaderboard selection and produces a pose SVG. The regression suite covers normal validation, Rich, publication and interruption.

[PIPELINE.md](PIPELINE.md) records ranges, CVs, individual GPU event times and host gaps; [MATCHED-SCOPES.md](MATCHED-SCOPES.md) compares compute and ordinary paths on the same W=524288. The broader pipeline scope explains their rate difference. It must not be called a kernel slowdown or speedup.

## CPU diagnosis and profiling

Nsight Systems plus per-thread sampling show A's native synchronization consuming 45.916 s wall and 45.902 s main-thread CPU during the diagnostic run. The median main-thread activity during native waits is 99.63% of one logical CPU; other worker threads are mostly idle. Two workers consume about two of this host's sixteen logical CPUs. An isolated officially supported owned blocking-event wait reduced main-thread CPU from approximately 10.969 s to 0.0018 s for a full batch, with exact outputs and unchanged context flags. Completion-time ranges overlap; the approximately 0.10% median latency difference is not a reliable throughput gain. Production context/wait policy remains unchanged.

The runner's real host work creates idle gaps before the next GPU batch. Unprofiled N12 dual gaps fell from 2.176 to 1.294 s with gzip 3; N16 from 2.271 to 1.410 s. Python record construction, selection, validation, JSON serialization, zlib compression, disk writes and reports are accounted for separately in the diagnostic phases. Some wrappers nest; durations must not be summed. Existing `persistence_seconds` omits preceding Python work and is not a complete host attribution. [CPU.md](CPU.md) provides native/Python details, residual attribution and all gzip-level measurements. On the same 61,017,607-byte representative payload, levels 1/3/6/9 took median 0.0893/0.1003/0.2852/0.9615 s and produced 5,312,998/4,852,308/3,768,779/3,415,049 bytes. Every option was lossless. Level 3's approximately 9.58x isolated compression gain and 42.1% larger file are distinct from the measured full-pipeline gains above.

[PROFILING.md](PROFILING.md) records saturated early N12 and dense N12/N16 counters with clock control disabled. Achieved occupancy is 27.78–30.98%, issue utilization 71.12–73.20%, eligible warps/scheduler 1.41–1.49, registers/thread 128. Measured local load/store sectors are zero in these representative launches; compiler local allocation is not a measured spill count. Dependency waiting exceeds long-scoreboard waiting. Instruction dependencies and register/divergence constraints are plausible targets, not a proved single bottleneck. No block change, forced register cap or layout rewrite was justified.

## Retained and rejected changes

1. **Retained host policy:** explicit gzip level 3, measured independently with fixed GPU executable code. Generated PTX executable entries match bytewise across host variants (`baseline/compiler/host-kernel-equivalence.json.gz`). No numerical format, record, tolerance or validation shortcut was taken.
2. **Rejected unused residual call:** source and generated-code inspection suggested an unused first residual evaluation survived through volatile operands. Its removal changed 28 pose components and several residual/sweep fields on N4. The bytewise gate rejected it before performance promotion; the accepted operand barrier was never removed.
3. **Rejected rejection work-buffer copy:** removing restoration of a work buffer overwritten at the next attempt passed the fresh small corpus on both cards. Three matched 4096-world runs gave N12 0.9993x and N16 1.0029x baseline rates, within variability and without a reliable improvement on the research case. Accepted-state rollback remained intact. Candidate patches, hashes and negative evidence are preserved under `candidates/`; neither candidate entered production.
4. **Retained harness reader correction:** decode NPZ members once before checking 32 geometries, rather than decoding a full batch for every sample. Member-read regression and identical checks establish correctness. Single-pair archival observations improve N12 2.1611→0.2231 s and N16 2.7916→0.3276 s, outside GPU/common execution. These are not an additional headline gain. Recorded campaign end-to-end times honestly include the earlier repeated-decode cost.

Earlier failed broad phases were not repeated. No approximate trigonometry, changed precision, fast math, reassociation, altered contact order, RNG, stopping rule, search budget or packing strategy was used.

## Equality, concurrency and tests

Fresh independently loaded production/snapshot comparisons run on **each physical 4090**. The small corpus has 106 trials across N=1,4,11,12,16,32, multiple seeds/ranges, N11 IDs 4124/4372 and uint64 boundaries, plus contact diagnostics. All bytes match cross-card; 96 initialized final geometries pass independent float64 checks and ten INIT_FAILED cases are explicitly not treated as valid poses. Separate 65536-angle probes compare all axes and rounded dot-product bit patterns on both cards. Explicit-source initialization rechecks compare 8192 worlds per card.

All 18 principal and 18 sustained compute measurements compare complete dtype, shape and defined bytes of initial/final poses, every Result field, RNG initialization and sorted IDs. Zero missing/duplicate IDs and unchanged per-ID square ordering are verified. Scratch slots are canonicalized in the harness before timing; large runs use debug=false with defined zero trace. Actual accepted-step traces, numerical failures, difficult contacts, rollback, step-floor and axis rounding are exercised in the small corpus/tests. Fixed CPU checks cover 32 geometries per full batch, independent of full array comparison. These are tested reproducibility scopes on these devices/toolchain, not a guarantee for other hardware/compiler versions.

Recorded device intervals and the native Nsight Systems trace prove **20.853905 s of simultaneous production-kernel execution** in the diagnostic dual ordinary run. `(PID, local CUDA ordinal)` maps to two distinct physical UUIDs. This is measured overlap, not a sum of isolated capacities. Worker preparation barriers, reuse of allocations, bounded failure waits, deterministic uneven/partial batches, nonzero offsets, different completion orders, Ctrl-C drain and finalized partial evidence are exercised by real-device integration tests.

| Fresh final execution | Executed | Passed | Failed | Skipped | Deselected | Duration |
|---|---:|---:|---:|---:|---:|---:|
| Full suite with UUID-checked A | 279 | 279 | 0 | 0 | 0 | 104.30 s |
| CUDA subset with UUID-checked B | 49 | 49 | 0 | 0 | 230 | 99.84 s |

Both include actual two-device integration tests. These are separate executions, not 328 distinct tests. Two upstream Warp ctypes-layout deprecation warnings remain. Historical artifact, gzip, Rich, publication, minimum-step and stop behavior tests passed. Earlier fresh executions and failed candidate/diagnostic attempts remain in `test-outcomes.json.gz` and logs. Archived replay separately verified 18/18/36 complete compute-principal/compute-sustained/ordinary-sustained outcomes; it is clearly labeled as reading evidence rather than new CUDA execution.

## Timing and durable publication

[COMPUTE.md](COMPUTE.md), [PIPELINE.md](PIPELINE.md) and [MATCHED-SCOPES.md](MATCHED-SCOPES.md) separate same-device CUDA events, common execution intervals and whole-campaign wall time. The principal compute campaign snapshot is 604.211904 s; the ordinary campaign is 2276.155773 s, with external full Python process lifetime 2276.298192±0.11 s. The sustained compute campaign also has external subprocess timing through final outputs. These full campaign durations include startup, all repetitions, archives/comparison/CPU validation and shutdown; phase durations can overlap.

The separate normal CLI smoke took 7.080702 s externally, 4.281784 s CUDA for eight completed trials, 2.084241 s warm-up, 0.003849 s transfer, 0.032729 s validation, 0.042654 s recorded persistence, 0.000458 s pose rendering and 0.003977 s report generation. Module loading was 0.111653 s. The runner summary's 6.729796 s excludes its own final summary serialization; the external boundary includes the uv launcher, imports and final receipt/display. These phases do not sum to wall time, and unclassified scalar/selection work is resolved by the separate detailed profile. `--no-push` local manifest handling took 0.007622 s; this is **not a remote Git push measurement**.

Full numerical arrays and every ordinary trial record remain durably inside the repository workspace under `runs/dual4090-*`, excluded from Git. [MANIFEST.json.gz](MANIFEST.json.gz) records repository-relative paths, sizes, SHA-256 and regeneration commands. Compact small per-card references, selected 64 poses per N, source snapshots, compiler excerpts, complete timing/equality/telemetry metadata, logs and native profiling evidence are published here. No large data was discarded, no LFS/external storage was introduced, and historical evidence is untouched. Publication uses explicit paths, the shared repository lock, normal main commits and a non-force push. Its separate local receipt is `runs/dual4090-final-publication.json.gz`, outside all measured computation. Final remote SHA verification is part of delivery.

No hardware-access blocker remains. Remaining limits are the tested device/toolchain scope, no accepted incremental kernel gain, fixed documented benchmark validation policy, larger gzip files, and retained synchronous host gaps. The ordinary CLI remains single-GPU; the focused benchmark orchestrates independent experiments only.

## Reproduction

All output/archive directories must be fresh. Set physical UUIDs from this machine's inventory, not assumed CUDA ordinals:

```bash
TASK_EVIDENCE=artifacts/performance/dual4090-20261009T005128Z
TASK_GPU_A=GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d
TASK_GPU_B=GPU-81ac6e96-0bfe-390d-beb1-241466569d6b

# Separate A, separate B, or concurrent: use --modes A / B / dual.
uv run --frozen python tools/dual_gpu_benchmark.py run \
  --baseline-source "$TASK_EVIDENCE/baseline/gpu.py" \
  --devices "$TASK_GPU_A" "$TASK_GPU_B" --modes A \
  --n 12 16 --count 262144 --batch-size 131072 --repeats 3 \
  --timeout 300 --max-seconds 1800 \
  --output runs/replay-A-evidence --archives runs/replay-A-arrays --json

# Complete matched compute matrix; rotate modes across repeats.
uv run --frozen python tools/dual_gpu_benchmark.py run \
  --baseline-source "$TASK_EVIDENCE/baseline/gpu.py" \
  --devices "$TASK_GPU_A" "$TASK_GPU_B" --modes A B dual \
  --n 12 16 --count 262144 --batch-size 131072 --repeats 3 \
  --timeout 300 --max-seconds 1800 \
  --output runs/replay-matrix-evidence --archives runs/replay-matrix-arrays --json

# Actual sustained ordinary pipeline, fixed kernel, both lossless levels.
uv run --frozen python tools/dual_gpu_benchmark.py run \
  --baseline-source "$TASK_EVIDENCE/baseline/gpu.py" \
  --devices "$TASK_GPU_A" "$TASK_GPU_B" --modes A B dual \
  --n 12 16 --count 524288 --batch-size 131072 --repeats 3 \
  --pipeline ordinary --gzip-levels 9 3 --timeout 300 --max-seconds 3600 \
  --output runs/replay-pipeline-evidence --archives runs/replay-pipeline-data --json

# Full numerical equality replay against durable complete arrays.
uv run --frozen python tools/dual_gpu_benchmark.py replay \
  --manifest "$TASK_EVIDENCE/compute-principal/measurements.json.gz" \
  --output runs/replay-exact.json.gz

# Fresh CUDA production/snapshot equality and device-sensitive tests.
CUDA_VISIBLE_DEVICES="$TASK_GPU_A" uv run --frozen python tools/kernel_benchmark.py compare \
  --reference "$TASK_EVIDENCE/corpus-A" --source src/asquerix/gpu.py \
  --device cuda:0 --output runs/replay-corpus-A.json.gz
CUDA_VISIBLE_DEVICES="$TASK_GPU_B" uv run --frozen python tools/kernel_benchmark.py compare \
  --reference "$TASK_EVIDENCE/corpus-B" --source src/asquerix/gpu.py \
  --device cuda:0 --output runs/replay-corpus-B.json.gz
CUDA_VISIBLE_DEVICES="$TASK_GPU_A" ASQUERIX_TEST_UUID="$TASK_GPU_A" uv run --frozen pytest -q
CUDA_VISIBLE_DEVICES="$TASK_GPU_B" ASQUERIX_TEST_UUID="$TASK_GPU_B" uv run --frozen pytest -q -m gpu
```

For the separate B command, replace `--modes A` with `--modes B`, and use fresh `runs/replay-B-evidence` / `runs/replay-B-arrays` destinations. For concurrent execution, use `--modes dual` and fresh `runs/replay-dual-evidence` / `runs/replay-dual-arrays`. The A/B/dual commands were exercised separately as tiny multi-batch Rich smoke tests (N4, count11, offset413, batch3, one repeat); the saturated matrix above exercised all modes with the full workload. Omit `--json` for per-device/combined Rich progress and the final comparison table. `--json` saves gzip structured evidence and prints concise status/paths only. All benchmark paths disable automatic experiment publication; normal CLI publication remains after complete artifact finalization.
