# Audit of the Earlier Pilot Evidence

This note audits the evidence produced by the implementation revision recorded in `artifacts/pilot/manifest.json`. It is deliberately separate from the later audit run. No benchmark or external proof program was executed for this audit.

The complete independently reconstructed run table is in `reconstructed-stats.json` beside this file.

## Findings

### F-01 — scalar validation statuses outlive their pose documents (medium, confirmed)

The runner validates a candidate while building a temporary leaderboard, writes `validation_status=NUMERICALLY_VALIDATED` into the scalar record, and may later delete that candidate's pose document when a better global leaderboard replaces it. The scalar status is not reset when the document is deleted.

The saved evidence contains 193 such records:

| run | scalar numerical validations | saved pose documents | audited scalar rows without a saved pose |
| --- | ---: | ---: | ---: |
| `campaign/sweep-b8` | 95 | 45 | 50 |
| `campaign/sweep-b32` | 81 | 45 | 36 |
| `campaign/sweep-b128` | 68 | 45 | 23 |
| `extended/repeat-0` | 114 | 86 | 28 |
| `extended/repeat-1` | 114 | 86 | 28 |
| `extended/repeat-2` | 114 | 86 | 28 |

The other runs have one saved pose for every scalar row marked as audited. The 193 statuses are numerically plausible, but their poses and validator diagnostics cannot be independently replayed from the durable archive. This affects audit coverage and evidence retention, not the GPU search result itself. The regression test `tests/test_audit_artifacts.py` reproduces the failure with a deterministic non-CUDA batch double. A complete fix must either retain every audited pose or restore the scalar status to `NOT_CHECKED` when the pose is discarded. The replacement campaign should be audited after the runner fix.

### F-02 — the directory validator conflates `INIT_FAILED` with invalid geometry (low, confirmed)

The retained failure examples intentionally contain `n=2`, `side=null`, and an empty pose list with `validation.status=NOT_CHECKED`. Running the documented command

```text
uv run asquerix validate artifacts/pilot/init-failed
```

returns exit code 1 and four `INVALID` results because `validate_document` requires exactly `n` poses. That is a reasonable result for a malformed pose document, but it is misleading for a deliberate `INIT_FAILED` record and conflicts with the runner's explicit `NOT_CHECKED` status and `INIT_FAILED` termination reason. The CLI should preserve the failure status as not checked, or skip geometry validation for records with no accepted pose while reporting them separately.

### F-03 — the old GPU residual field omitted wall penetration (medium, confirmed in the audited revision; fixed in the current uncommitted audit edit)

In the implementation hash recorded by the earlier manifest, the production finalizer assigned `max_penetration=max(0,-pair_gap)` and omitted `-min_wall`. A state that crossed a wall could therefore report zero GPU penetration even though `min_wall` was negative. The current working-tree audit edit includes a CUDA regression test and combines the pair and wall terms. None of the archived primary results exercised this defect: every archived GPU-feasible result had positive wall clearance under the independent checker.

The fix must remain in the final committed source and be covered by the real CUDA test before the replacement campaign is treated as final evidence.

## Independent evidence checks

The manifest names and hashes are internally consistent: all 943 listed files exist with the recorded byte sizes and SHA-256 values, and there are exactly 943 files below `artifacts/pilot` excluding `manifest.json`. Each of the three gzip scalar archives expands to 12,288 JSONL records; compressed and uncompressed hashes match `extended/measurements.json`.

The saved scalar records have contiguous, unique global IDs within every run. The three extended repeats have identical complete scalar streams, not merely equal summary statistics. Recomputing counts, side distributions, histograms, quantiles, terminations, and counters directly from the records reproduces the persisted summaries.

I used a standalone float64 implementation that reconstructs the four vertices from each saved `(x, y, theta)`, derives edge normals from those vertices, projects every pair on all eight normals, and checks every vertex against the saved container. It rechecked all 708 nonempty retained pose documents. All 708 were numerically validated, with zero status or metric mismatches against their saved diagnostics. The four empty `INIT_FAILED` documents remain `NOT_CHECKED` and were not treated as geometry.

All 53 retained pose SVGs were parsed as XML. Their metadata matched the corresponding JSON documents, each used the expected 748-by-748 equal-scale container, and every rendered square polygon matched independently reconstructed coordinates within `2e-12` SVG units. Histogram bar counts also matched the recomputed persisted histograms.

The aggregate saved-data counts are 41,488 primary campaign records, 41,488 GPU-feasible results, 873 scalar numerical validation statuses, and 193 statuses without durable pose evidence. Including the stop/failure/control checks gives 41,524 records, 41,520 GPU-feasible results, 901 scalar numerical validation statuses, and 712 pose documents.

## Trump eleven-square fixture

The fixture metadata pins source commit `176e8ad14d5b93f3a1f3d5a9e04ab1dfdb8c704b`, source SHA-256 `3b4eae938c37c13af6252ac5d83fa99aa95f6b1627b99920c5df8be94c56bea9`, MIT attribution, and the 2026-10-08 retrieval date. The locally retained source copy has 3,876 bytes and the same SHA-256. It was read for comparison and not executed.

Independent 120-digit Decimal bisection of the stated polynomial gave

```text
u = 0.365769307604677293388545018143311315239104830794924193607064299673602905181459123920611947992432609473869965569744265508...
s = 3.87708359002281417730789706010096270637645566846316256076396834195899045867098871858757804599279121515078738895640441747...
```

The published degree-eight polynomial evaluated at this recovered side was below `1e-114` in the Decimal calculation. Reconstructing all stored centers and angles from the closed-form equations agreed with the fixture poses to at most `4.44e-16` in float64. The rounded pose has contact-level clearance and is correctly `INDETERMINATE`; the fixture does not claim a certificate. The current case record is <https://jlevy.github.io/squares/cases/11.html>, which reports the stated proof-status qualifications. The fixture remains a geometry reconstruction and does not feed random search.

## Verdict for the archived evidence

The archived selected geometry and SVGs are internally sound under an independent numerical check, and the old campaign statistics are reproducible from the bytes. The evidence-retention gap in F-01 prevents the archived scalar audit count from being fully replayable. The archived data therefore supports the reported GPU-feasible search observations and selected-pose checks after that qualification; it should not be treated as a complete durable audit of all scalar rows until the runner fix and replacement campaign are checked.
