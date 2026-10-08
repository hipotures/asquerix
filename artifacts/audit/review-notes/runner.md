# Runner and output audit

Date: 2026-10-08

Scope: `src/asquerix/runner.py`, `src/asquerix/output.py`, `src/asquerix/cli.py`, their tests, and the persisted pilot records under `artifacts/pilot`. The audit did not change the solver workload or add a search algorithm. CUDA benchmark reproduction was handled outside this bounded runner/output audit.

## Findings

### F1 — Medium — runner controls accepted non-contract types (fixed)

Before the fix, `run()` checked numeric ranges but did not require exact integer types for `trials`, `batch_size`, `trial_offset`, `sample_every`, `keep_best`, `max_images`, `audit_size`, and `failure_examples`. It also accepted `bool` as `max_seconds` and accepted strings convertible to float. This allowed `trial_offset=True` to silently start the global stream at ID 1 and allowed `sample_every=2.0` or `failure_examples=True` to pass. Other values failed later with implementation-level `TypeError` from NumPy or slicing, after the output directory had already been created.

The fix adds bounded exact-integer validation, rejects booleans, requires a finite positive real wall-time budget, and normalizes NumPy scalar values to Python scalars before scheduling. Regression coverage is in `tests/test_runner.py`.

### F2 — Medium — unknown validation labels were counted as audited (fixed)

The output layer previously passed any string through as a validation status. `summarize()` then counted an unknown status as audited because only `NOT_CHECKED` was excluded, while it was absent from the explicit invalid count. `render_pose()` likewise rendered an unknown status without the required invalid-debug marker. This could make malformed saved data appear to have audit coverage.

The output layer now maps labels outside `NUMERICALLY_VALIDATED`, `INDETERMINATE`, `INVALID`, and `NOT_CHECKED` to `INVALID`. The renderer consequently emits `INVALID DEBUG`; summary coverage includes the record in `invalid_trials`. Regression coverage is in `tests/test_output.py`.

### F3 — Low — sanitized SVG names could overwrite distinct documents (fixed)

`render_selected()` sanitizes IDs for filenames. Distinct non-integer IDs such as `a/b` and `a?b` both became `trial-a_b.svg`; the second render overwrote the first while both paths were returned. Production runner IDs are uint64 integers, but the offline CLI accepts saved documents and this violated sparse-output preservation for malformed or external documents.

The renderer now adds a deterministic numeric suffix on filename collisions while retaining the original ID in SVG metadata and labels. Regression coverage is in `tests/test_output.py`.

### F4 — Medium — final report is written twice and its persisted timing omits the second write (open)

`runner.run()` calls `write_report()` once before measuring `report_seconds` and then calls it again after updating timing fields. The returned and persisted `end_to_end_seconds` and `report_seconds` therefore omit the second report write. A direct fake-batch probe counted two report writes for one trial. This is a measurement bookkeeping defect; it does not affect solver geometry or trial selection. It should be resolved by the owning integration change, with a clear definition of whether report timing includes file writes.

## Artifact checks

The committed `artifacts/pilot/campaign/repeat-0` scalar file contains 512 records. Its persisted summary reports 512 records, matching GPU-status and validation-status totals; the recomputed GPU-accepted population, histogram, validation coverage, and termination counts match the persisted summary exactly. The same consistency was spot-checked for the archived extended repeat and the stop/initialization-failure runs. No malformed validation labels occur in these saved artifacts.

The sparse selection tests cover global periodic IDs, fixed random audit IDs, deterministic side/ID ranking, multiple batches, retain-all correctness runs, bounded failure examples, and image caps. Existing persisted stop artifacts show completed records and no subsequent batch after SIGINT/wall-time stop; this audit did not reinterpret those measurements as solver evidence.

## Verification

Command:

```text
UV_CACHE_DIR=/tmp/asquerix-uv-cache uv run pytest -q tests/test_runner.py tests/test_output.py tests/test_config.py tests/test_audit_runner.py
```

Result: 55 passed, 0 failed, 2 upstream Warp ctypes deprecation warnings.

The full CUDA suite was not rerun by this subtask. No changes were made to GPU solver code or the scientific budgets.
