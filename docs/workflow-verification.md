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
