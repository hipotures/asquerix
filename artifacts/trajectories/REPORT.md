# Selected trajectory recording evidence

Tested on 2026-10-09 using Python 3.14.7, Warp 1.18.0, NumPy 2.5.3 and driver 615.71.09 on the display-attached RTX 4070 Ti, UUID `GPU-64d50ac7-f623-65a8-8784-b9ec14d16527`. Only this physical CUDA device was available. No drivers or project dependencies were changed. The source checkout began at `cbdf6e66310f579efb87926675f5812a97b052d0` on `main`; each recording preserves the actual source hashes and dirty-state provenance rather than claiming that this pre-feature revision alone describes the implementation.

## Correctness and workflow verification

- Before implementation: full CUDA-enabled suite **272 passed, 7 skipped**, 99.57 s.
- Final full CUDA-enabled suite: `uv run --no-sync pytest -q` — **332 passed, 7 skipped**, 82.65 s. The seven skips require two physical CUDA cards; no RTX 4090 pair was accessible. Two warnings are Warp ctypes deprecations on Python 3.14.
- Focused recorder verification: **30 passed**, including supported N=1,4,11,12,16,32, two seeds, full unsigned-64 identifiers, independent initial RNG checks, exact defined Result fields and pose bytes, historical diagnostics 4124/4372, zero attempts, initialization exhaustion, rejection/rollback, repeated bounded compaction, cap-independent outcomes and the two-frame final-phase regression. A resumed diagnostic seam injects NaNs and checks production/trace numerical-failure behavior without sanitizing the recorded arrays.
- Storage/workflow tests cover signed zero, primitive dtype/shape checks, bounded ZIP central-directory/NPY/metadata loading, truncated/object archives, endpoint roles and IDs, deterministic gzip, plain/gzip reference readers, missing references, deliberate mismatches, global validated-only selection, actual export limits, injected partial-file failures, stop/drain behavior, default recording disabled, offline rendering without `wp.init`, Rich/quiet behavior and bounded receipts.
- Publication tests use temporary local Git remotes, including successful and failed publication of genuine NPZ/HTML/metadata, filename identity, path/symlink protections and preservation of the active index/source tree. No publication test targets GitHub.
- The production `src/asquerix/gpu.py` remains byte-for-byte unchanged: SHA256 `a73adf65e92336a1c865f698497cdbba03b8efd2eb19670f8b17885b846e9d0d`. [Baseline capture](baseline-capture.json.gz) records all 15 pre-edit CUDA endpoint/initial archives; their complete NPZ bytes equal the existing durable correctness corpus. No duplicate dataset is needed.

## Disabled-trace regression

The existing kernel comparison tool used the frozen current source and current production source, N=12, 512 worlds, seed 20261008, global offset 0, 128 attempts and 480 sweeps, three alternating repetitions per variant. Budgets and batch size were fixed. All complete results/poses matched exactly; both variants used 128 registers and 32 bytes of local memory. Measurements use synchronized CUDA events and exclude gathering/validation/persistence.

| Repetition | Frozen source GPU s | Current source GPU s |
|---|---:|---:|
| 0 | 3.399682 | 3.399634 |
| 1 | 3.394594 | 3.397716 |
| 2 | 3.379359 | 3.389033 |

Median GPU time changed by +0.092%; there is no observed meaningful slowdown in this short comparison. This is evidence for the disabled path, not a claim of zero overhead or a new optimization. Module loading was separate (0.230950 s frozen, 0.009224 s current; cached modules). Existing desktop/background GPU workloads remained running. Full data, configuration, hardware and timing boundaries are in [disabled-trace-benchmark.json.gz](disabled-trace-benchmark.json.gz).

Tested benchmark command (the frozen source was captured before editing):

```bash
uv run --no-sync python tools/kernel_benchmark.py benchmark \
  --baseline-source /tmp/asquerix-trajectory-baseline/gpu.py \
  --device cuda:0 --count 512 --n 12 --repeats 3 \
  --output /tmp/asquerix-trajectory-disabled-benchmark
```

The maintained `gpu.py` is the same frozen source; future reproductions should save it to a fresh temporary path before changing code.

## Genuine examples

All five viewers below are self-contained. Files contain real CUDA states, with side exactly one for every square; no interpolation or geometry repair is used. Each NPZ has associated `trial-ID.meta.json.gz`. Byte counts are measured emitted sizes.

| Collection / global ID | Frames | NPZ bytes | HTML bytes | Metadata bytes | Comparison / provenance |
|---|---:|---:|---:|---:|---|
| Best accepted / 1 | 41 | [5797](demo-best/trajectories/trial-1.npz) | [61931](demo-best/trajectories/trial-1.html) | 6101 | MATCHED / MATCHED |
| Best accepted / 7 | 41 | [6029](demo-best/trajectories/trial-7.npz) | [61901](demo-best/trajectories/trial-7.html) | 6160 | MATCHED / MATCHED |
| Best accepted / 10 | 41 | [6361](demo-best/trajectories/trial-10.npz) | [61968](demo-best/trajectories/trial-10.html) | 6179 | MATCHED / MATCHED |
| Dense sweeps / 1 | 139 | [15939](demo-sweeps/trajectories/trial-1.npz) | [113903](demo-sweeps/trajectories/trial-1.html) | 10614 | MATCHED / MATCHED |
| Historical accepted / 4124 | 118 | [14135](demo-historical-4124/trajectories/trial-4124.npz) | [94277](demo-historical-4124/trajectories/trial-4124.html) | 7760 | MISMATCH / DIFFERENT |

The best-K campaign completed **32 scientific trials**, with 22 independently validated trials and global winners 1,7,10. The three replays did not alter the original 32-record summary or histogram. All 123 retained accepted-mode states passed independent numerical validation. The dense replay observed 8827 recordable events, retained 139 and suppressed 8688, with six compactions and effective stride 64 despite the requested sweep interval 1. Its three retained accepted/initial/final states passed independent validation; 136 provisional states have measured residuals and no accepted badge. The final accepted state matches the original exactly.

Historical 4124 reads the archived N=11, seed 20261008, 120-sweep configuration unchanged. It reports differences in side, termination, final step, attempts, sweeps, accepted count, wall residual and final pose. All 118 retained accepted states of the actual new replay pass numerical validation. The original archive remains unchanged. The separate current-source 480-sweep diagnostic tests for IDs 4124 and 4372 match the frozen corpus exactly; those tests do not imply equality with the older 120-sweep experiment.

Comparison scope is all available defined FP32 endpoint/result fields, including signed-zero bits, square order, seed/global identity, feasibility, termination and counters. Original initial poses were not retained by these run collections, so their initial arrangements were not independently compared to original run evidence. Recorder-on/off initial RNG equality is covered separately by CUDA tests. Endpoint/counter equality does not prove identity of every unrecorded intermediate state. These are newly recorded replays, not certified constructions or directly recorded original histories.

## Size and postprocessing timing

| Operation | Replay GPU s | Transfer s | CPU validation s | Export s | Module loading s | Total postprocessing s | Actual collection bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Best three | 2.388355 | 0.004589 | 1.743796 | 0.042796 | 1.325526 | 5.589402 | 329436 including the ordinary campaign |
| Dense sweeps | 0.843186 | 0.001343 | 1.881574 | 0.028833 | 0.310217 | 3.315601 | 146109 |
| Historical 4124 | 0.849811 | 0.001133 | 1.257550 | 0.025277 | 0.304987 | 2.678399 | 121875 |

The best-three trajectory export before publication is 225449 bytes, independent of ordinary campaign artifacts. All operations remain well below their 10 MiB total limits, including manifests and receipts. `trace.json.gz` and each publication manifest retain exact artifact byte counts/checksums. The standalone collections have zero scientific-trial counts; they are classified as trajectory replays.

The demonstration ran alongside bounded correctness work on a display GPU. These timings are observed correctness-demo latency, not controlled throughput measurements. The original best-K search retains its own 6.347213 s CUDA-event time; tracing is separate. Final CLI durations including local publication are stored in each `publication.json.gz`. The examples used `--no-push`; this implementation/evidence commit publishes them together on `main` without changing those historical local-only receipts.

## Tested reproduction commands

Use fresh destinations rather than overwriting these artifacts:

```bash
uv run asquerix run --experiment trajectory-best-demo \
  --n 12 --max-sweeps 480 --trials 32 --batch-size 32 \
  --trace-best 3 --trace-max-frames 256 \
  --output runs/trajectory-best-new --no-push --json
uv run asquerix trace runs/trajectory-best-new --trial-id 1 \
  --mode sweeps --every 1 --max-frames 256 --max-mib 10 --device cuda:0 \
  --output runs/trajectory-sweeps-new --no-push --json
uv run asquerix trace artifacts/audit/campaign/retained-n11 --trial-id 4124 \
  --mode accepted --max-frames 256 --device cuda:0 \
  --output runs/historical-4124-new --no-push --json
uv run asquerix trace-render artifacts/trajectories/demo-sweeps/trajectories/trial-1.npz \
  --output runs/offline-view-new.html --json
```

Open the HTML using the browser's File > Open action. No server, CUDA, network, CDN or runtime installation is needed. Regeneration was exercised inside the sandbox where CUDA is unavailable, and a test replaces `wp.init` with a failure to ensure no CUDA context is created.

Real Chromium 153 playback/slider/SVG verification passed using `tools/trajectory_browser_smoke.py` on the finalized dense example. The exported polygon coordinates match the selected frame; the page made only a local `file://` request and produced no JavaScript errors. [Browser report](browser/demo-sweeps-trial-1-browser.json.gz) and [1500×1000 screenshot](browser/demo-sweeps-trial-1/trajectory-viewer.png) preserve evidence. The screenshot/report are separate test evidence, outside trajectory-operation size accounting.

Limits remain deliberate: at most 16 selected worlds per operation, bounded frames/events, no automatic complete event history, no cross-device/version determinism guarantee, no original initial-pose comparison when absent, and no mathematical certification or optimality claim. GPU initialization failures have no fabricated complete pose, numerical failures preserve diagnostic values, and failed export/publication cannot rewrite or remove original scientific evidence.
