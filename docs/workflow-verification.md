# Experiment workflow verification

The workflow changes are developed in an isolated worktree on `feat/experiment-workflow`. The active `main` checkout and detached floor-check worktree are not switched or updated. Local runtime output is ignored; published artifacts belong to the separate `experiment-results` branch.

## Scientific scope

`src/asquerix/gpu.py` and `src/asquerix/geometry.py` are byte-for-byte unchanged from `d4884c9214da01c00a2e10b93f55542276de95c8`. No GPU algorithms, budgets, floating-point parameters, random streams, collision predicates or acceptance rules changed. The new real-CUDA regression executes four original full-budget trials at batch sizes 2 and 4, with and without progress callbacks, and compares every search scalar against the original archived benchmark. Independent validation checks every returned pose.

## Verification

Final result: **180 passed, 0 failed, 0 skipped**, including 18 CUDA cases (8.41 seconds). Two upstream Warp ctypes deprecation warnings were reported. The full test suite ran with real CUDA on the RTX 4070 Ti, Python 3.14.7, NumPy 2.5.3, Warp 1.18.0, Rich 14.3.4 and pytest 9.1.1. Tests cover Rich TTY/non-TTY presentation, quiet disk-based `--json`, compressed/plain readers, deterministic atomic documents and streamed JSONL, graceful stop, real GPU partition equality, and temporary local Git remotes. Publication tests exercise detached HEAD, unrelated staged files, concurrent publishers, remote advances, partial/empty runs, invalid gzip, artifact size limits, failed authentication/push, immutable snapshots and exact committed byte hashes. No test pushes to the production repository.

All 943 pilot and 723 audit manifest file hashes and sizes were checked: zero differences. Historical pilot and audit files are preserved. The maintained independent checker processed the actual pilot (19 runs, 41,524 records, 712 pose documents) and audit campaign (9 runs, 49,260 records, 586 pose documents), with zero geometry, SVG or summary mismatches. Archived scripts remain unchanged; maintained counterparts are under `tools/`.

Timing definitions remain separate: CUDA-event device time, synchronized simulation time, transfers, independent CPU validation, gzip persistence, rendering/report generation, Git publication and observed end-to-end wall time. Final summary/receipt timing boundaries explicitly exclude their own final serialization.

## Reproduction

```bash
uv run --locked pytest -q
uv run --locked asquerix compare artifacts/audit/campaign/matched-b512-r0 artifacts/audit/campaign/matched-b128
uv run --locked asquerix validate artifacts/audit/campaign/retained-n12
uv run --locked python tools/check_artifacts.py artifacts/pilot --output runs/check-pilot.json.gz
uv run --locked python tools/check_artifacts.py artifacts/audit/campaign --output runs/check-audit.json.gz
```

The initialization prompts were untracked one-time assignment files and have been removed from the original checkout at the user's request. Current project instructions are tracked as `AGENTS.md`. Manifest instruction hashes in historical archives are preserved as historical provenance.

Production publication verification is recorded below only after an actual bounded CLI run and remote confirmation. Such runs test orchestration, not solver throughput; their small sample is not a benchmark claim.


## Confirmed production publications

Code revision used by both clean-worktree runs: `cb2b5eb45002c68fd264714ff14e00cf3d8880b6`.

| CLI mode | Completion | Independent validation | Confirmed results commit | Published directory |
| --- | --- | --- | --- | --- |
| Rich TTY | COMPLETED, 8/8 | 8/8 numerically validated | [`119e2b9`](https://github.com/hipotures/asquerix/commit/119e2b9acb8d7b0fb88766aa93556d9cf01a24ab) | `experiments/workflow-rich-smoke/run-20261008T221818Z-cd07e203ab07` |
| Quiet `--json`, 0.001-second scheduling budget | PARTIAL, 4/8 | 4/4 numerically validated | [`5aa9290`](https://github.com/hipotures/asquerix/commit/5aa9290a670ac54389c0507d9ece6c240185b3eb) | `experiments/workflow-json-partial-smoke/run-20261008T221834Z-81cb5fb7803d` |

Both used the unchanged default N=12 scientific workload, seed 20261008, batch size 4, and global trial range starting at zero. The Rich run used 1.8356705322265623 seconds of CUDA-event work; the partial run used 0.9016453247070313 seconds. These are bounded workflow smoke tests, not performance estimates from a sufficiently large benchmark population. The partial run drained exactly one batch and scheduled no second batch.

Both successful pushes were confirmed against the remote. Every published blob was read from Git and checked against the local bytes and manifest SHA-256: 18 hashed data files for the full run and 14 for the partial run, plus each manifest. Gzip files decompressed successfully. The independent maintained checker reported zero geometry, SVG and summary mismatches for both. Compare displayed a warning because their completed trial sets differ. Quiet stdout contained no ANSI sequences or raw JSON payload; initialization/JIT diagnostics remained on stderr.

Full local publication receipts are retained in `workflow-publications.json.gz`, with computation/publication/total timings and confirmed commit URLs. The production result commits already contain compressed scientific files, reports, histograms and selected SVGs. The active main checkout remains at `d4884c9`; the detached benchmark worktree remains at `61f77c6`. Integration is delivered as a pull request to preserve concurrent development.

Tested smoke commands (use fresh output paths when repeating):

```bash
uv run --locked asquerix run --experiment workflow-rich-smoke --n 12 --trials 8 --batch-size 4 --retain-all --sample-every 0 --audit-size 8 --keep-best 3 --max-images 2 --max-seconds 30 --output runs/workflow-rich-smoke
uv run --locked asquerix run --experiment workflow-json-partial-smoke --n 12 --trials 8 --batch-size 4 --retain-all --sample-every 0 --audit-size 8 --keep-best 3 --max-images 2 --max-seconds 0.001 --json --output runs/workflow-json-partial-smoke
uv run --locked asquerix compare runs/workflow-rich-smoke runs/workflow-json-partial-smoke
```

Quiet `diagnose` saved the actual CUDA environment as gzip and printed only its path. `report --json` was exercised on a private copy of the completed compressed run; regenerated statistics retained all eight records. Published run directories were not modified by this offline verification.
