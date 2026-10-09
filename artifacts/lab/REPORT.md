# Experiment laboratory: implementation and pilot report

Date: 2026-10-09. Hardware: one display-attached NVIDIA GeForce RTX 4070 Ti (`GPU-64d50ac7-f623-65a8-8784-b9ec14d16527`), driver 615.71.09, Warp 1.18.0. Requirements: [`docs/lab-prd.md`](../../docs/lab-prd.md).

This is a functional pilot. A valid construction supports an upper bound only. Nothing here claims optimality, a lower bound, or that one search method is better than another.

## Implementation status

| Area | Status |
|---|---|
| Frozen pre-laboratory references | `artifacts/lab/baseline`: legacy solver bytes for `n = 1, 4, 11, 12, 16, 32`, two seeds, high and historical IDs (`tools/lab_freeze.py`). The legacy `gpu.py` is unchanged. |
| Strategy language, compiler, CUDA interpreter | All required opcodes, selectors, bounded `REPEAT`/`IF`, three geometry states, global work budgets, slices and cancellation. `legacy_compress` matches every frozen reference byte for byte. |
| Search | Random program search and `(1 + lambda)`, shared initial pool, fixed controls, training/holdout banks, resumable controller checkpoints. |
| Service | FastAPI + SQLite catalog, owned CUDA worker process, SSE progress, pause/resume/stop, crash recovery, Rich CLI clients. |
| Inspection | Browser UI, program and mutation views, paired replays, campaign history, strategy overlay in the existing trajectory viewer, self-contained offline report, zip export. |
| Publication | Finalized campaign directories publish to remote `main` through the existing isolated-index publisher. |

### Finished or fixed in this session

The implementation was written in an interrupted Codex session. This session found and fixed these defects:

1. **Replay traces were rejected by the viewer format.** The best snapshot and the finalization frame share one VM step, so `sequence` was not strictly increasing, and every automatic replay failed. The trace now stores the strictly increasing record order as `sequence` and keeps the VM counter as `vm_sequence`. The CUDA kernel is unchanged. A new test covers replay → NPZ → `load_trace`.
2. **Campaign publication was broken.** `publication.py` imported a `bounded_json` helper that did not exist, so every publishing campaign failed after its science had finished. The helper now exists. A publication exception is recorded as a failed publication, not a failed campaign. A CUDA end-to-end test now covers worker → report → publication to a temporary bare repository. Lab commits are titled `lab campaign: <name> (<state>, <episodes> episodes)`.
3. **Headless Chromium navigation hung.** On this host, Chromium waited on the desktop keyring for every network navigation, including `https://example.com`. The shared launcher in `tools/trajectory_browser_smoke.py` now passes `--password-store=basic`.
4. **Small UI fixes.** After finalization the phase line showed `REPLAYS`; it now shows the final state. Added a favicon, because the 404 appeared as a console error. Long ranking tuples now wrap instead of scrolling the page sideways.
5. **Controls-only campaigns were rejected.** The `n=12`/`n=16` control checks are now accepted.
6. **New tools and examples.** `tools/lab_overhead.py`, the extended `tools/lab_browser_smoke.py`, the pilot examples in `examples/lab`, and a README section.

## Tests

`uv run pytest -q`: **395 passed, 7 skipped, 0 failed** (all CUDA tests ran on the RTX 4070 Ti). The 7 skipped tests are dual-GPU benchmark tests that need two physical CUDA devices.

## Browser evidence (PRD section 17F)

`uv run python tools/lab_browser_smoke.py --url http://127.0.0.1:8766` → **PASS**. Interaction log: `artifacts/lab/browser/report.json.gz`. Screenshots: `artifacts/lab/browser/screens/`. Chromium 153.0.8010.52, headless. The check:

1. Fills and submits the campaign form: both methods, both controls, 4 candidates per method.
2. Leaves the page and reopens it. The same CUDA campaign completes in the background.
3. Opens a mutated `(1 + lambda)` program from the program table and checks the before/after diff.
4. Runs the existing full viewer check on a laboratory replay: play, pause, scrub, zoom, pan, square selection, trails and SVG geometry.
5. Checks every recorded frame of every replay (5 replays, 224 frames): the highlighted instruction equals the saved `pc`, and the rollback/restore/best/finalization markers are shown.
6. Finds rollback markers (`legacy_compress`, `pulse_rotate`), `RESTORE_BEST` restore markers (generated programs) and frames where current L ≠ protected best L (`pulse_rotate` after `EXPAND`).
7. Compares two different programs on the same initial world with synchronized frame seeking.
8. Scrubs the durable history and checks event labels and program state against the API.
9. Opens the exported `report.html` from `file://` with the network emulated offline. An embedded trajectory plays with zero network requests.
10. Checks a historical viewer saved before the laboratory, and the historical ID 4124 trajectory re-rendered with the current viewer. Both pass with no page exceptions or console errors.

Test-only browser flag: sandboxed replay iframes are kept in process (`--disable-features=IsolateSandboxedIframes`) so CDP can drive them. The product does not depend on this flag. The older `artifacts/trajectories/demo-historical-4124/.../trial-4124.html` predates later viewer controls and fails the current viewer check's newer UI assertions. Its NPZ re-renders and passes.

## Bounded scientific pilot (PRD section 17G)

All campaigns used `rigid-square-lab-v1`, FP32, initial side 10, initializer seed 20261008, operator seed 20261009, one operator replicate, and recording off for scientific episodes. Execution seconds are the worker's measured execution time and exclude finalization and publication.

| Campaign | Episodes | CPU-validated | Exec. s | Published commit |
|---|---|---|---|---|
| `n11-three-program-evaluation` (3 programs × 64 training + 64 holdout) | 384 | 384/384 | 15.5 | `b540777` |
| `n12-controls` (2 controls × 16 + 16) | 64 | 64/64 | 12.8 | `adec8e9` |
| `n16-controls` (2 controls × 16 + 16) | 64 | 64/64 | 17.6 | `90f19ab` |
| `n11-random-vs-mutation-pilot` (section 16, complete, not partial) | 4480 = 4224 + 256 | 4480/4480 | 109.9 | `8f682db` |

Artifacts: `experiments/<name>/<campaign-id>/` on `main` (campaign, datasets, NPZ evaluation chunks, programs, genealogy, events, comparisons, summaries, selected trajectories, `report.html`, `report.md`). All selected replays reported `REPLAY_MATCHED`.

### Section 16 comparison (n = 11, 64 training / 64 holdout starts)

| Program | Training mean L | Training median | Holdout mean L | Holdout median | Holdout sd | Mean charged work (training) |
|---|---|---|---|---|---|---|
| `legacy_compress` control | 4.241177 | 4.107867 | 4.308026 | 4.244100 | 0.3141 | 5.22 M |
| `pulse_rotate` control | 4.280872 | 4.151624 | 4.310613 | 4.267562 | 0.3305 | 2.68 M |
| Random search winner (candidate 20) | 4.212025 | 4.091101 | 4.317198 | 4.129514 | 0.3989 | 5.33 M |
| `(1 + lambda)` winner (candidate 30) | 4.144496 | 4.064871 | 4.227160 | 4.095698 | 0.3121 | 6.64 M |

Paired holdout mean difference (left best L − right best L, same 64 starts): legacy − `(1 + lambda)` winner = +0.0809, random winner − `(1 + lambda)` winner = +0.0900, legacy − random winner = −0.0092.

Interpretation: on this single campaign, the `(1 + lambda)` winner had the lowest holdout mean. It also used about 27% more charged work than the legacy control. This is one search seed and one initial bank, with no confidence intervals or repeated campaigns. It is not evidence that mutation search is superior. 891 of 4224 training episodes ended on the global work limit; their protected best states are still valid results. The smallest L in any campaign is ≈ 4.0001. That is a trivial 4 × 4 grid-type packing, not a new construction for n = 11.

### Other observations

- The generated program in the three-program evaluation contains only fixed-fraction compressions and expansions, with no legacy `COMPRESS`. Its best L is 9.024651 on every start, the product of its fractions applied to L = 10. This is intended operator semantics, not a defect.
- The first `n12-controls` run (`558395dec53c432ca96913b1f02d7683`) completed its science, then failed in publication because of defect 2. Its local results are preserved and were not published. The rerun after the fix reproduced the same summary statistics.
- The three LOCAL_ONLY pilot campaigns were published after finalization with `asquerix.publication.publish`. That rewrote `manifest.json.gz`, so their catalog artifact hashes and publication status were re-registered offline after a SQLite Online Backup (`PRAGMA integrity_check` = ok). Campaigns that publish from the service do not need this step.

## Interpreter overhead (recording disabled)

`uv run python tools/lab_overhead.py` → `artifacts/lab/overhead/n11-1024.json.gz`. Setup: n = 11, 1024 matched worlds, 3 measured repeats after one warm-up, `legacy_compress` (128 attempts × 480 sweeps). Every result field was byte-identical to the legacy solver in every repeat; otherwise the tool reports no numbers.

| Slice sweeps | Legacy compression device s | Interpreter device s | Interpreter loop s (incl. per-slice host sync) |
|---|---|---|---|
| 16 | 2.924 | 2.739 (×0.94) | 4.175 (×1.43) |
| 128 | 2.926 | 2.756 (×0.94) | 2.999 (×1.03) |

Legacy compression time is the full legacy device time minus an initialization-only submission of the same IDs. This is an approximation, because the legacy kernel fuses both phases. Most of the host overhead comes from slice synchronization; it falls as slices get longer.

## Remaining limitations

- Single GPU only. Dual-GPU tools are preserved, but their tests were skipped (one GPU present).
- Paired comparisons report mean differences without uncertainty intervals. Method comparison needs repeated campaigns with different search seeds and banks.
- `REPLAY_MATCHED` covers defined endpoints, VM/result fields, RNG and work. It does not prove that unrecorded intermediate states are equal.
- Numerical validation is float64 checking, not `CERTIFIED`.
