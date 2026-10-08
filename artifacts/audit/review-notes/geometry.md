# Geometry and validator audit

## Scope and evidence

This review covered `src/asquerix/geometry.py`, the GPU support/SAT contact
code in `src/asquerix/gpu.py`, the existing geometry and CUDA contact tests, and
the saved pose documents under `artifacts/pilot/`. The CPU path was checked
against the geometry contract in `AGENTS.md`, `PROMPT_01_IMPLEMENTATION.md`,
and `PROMPT_02_AUDIT.md`. No production search algorithm was added.

The CPU validator reconstructs four vertices for every saved pose, derives
edge-normal axes from those vertices, and projects both polygons on all eight
candidate axes. It checks every vertex against the centered container walls
separately. The GPU path uses the four square axes and support functions; its
pair correction includes both translation and angular derivatives, including
the derivative of a separating axis when the axis belongs to the other square.
The existing CUDA finite-difference tests cover both axis-owner branches,
off-center rotation, symmetric zero-torque contacts, and coincident centers.

## Findings

### F1 — finite extreme poses could emit non-JSON metrics (high, fixed)

Before the fix, finite centers around `1e16` caused float64 vertex offsets to
round away. The four reconstructed vertices then collapsed, and the edge-normal
path returned zero-normal divisions. For two such squares, `validate_pose`
returned `min_pair_separation=-inf` and `max_penetration=inf` while reporting
`INVALID`; `json.dumps(..., allow_nan=False)` raised. This violated the
validator's documented JSON-safe result contract and could corrupt a persisted
audit record if an out-of-domain pose reached the validator.

The fixed validator rejects non-representable unit edges before SAT and checks
edge normals, projections, wall clearances, and separation metrics for finite
values. It returns a JSON-safe `INVALID` result with no non-finite metric. The
validator identifier is now `cpu-f64-projection-v2` so the hardening is
distinguishable from the archived v1 records.

### F2 — schema-coercing scalar inputs could validate malformed documents
(medium, fixed)

Before the fix, NumPy scalar conversion accepted textual values such as
`"2.0"` and booleans for `side` and `tolerance`. Consequently a persisted
document with a string side could be accepted as a valid geometry document.
The scalar parser now accepts only integer and floating numeric dtypes and
rejects strings, bytes, booleans, and other non-numeric scalar schemas.

### F3 — normal-domain geometry and contact behavior (no defect found)

The CPU SAT implementation correctly handles edge/vertex contact, AABB false
positives, coincident centers, nearly parallel orientations, quarter-turn
periodicity, tiny wall violations, and deliberately overlapping squares. The
GPU contact equations have the expected signs: pair center gradients push the
two centers apart, wall gradients move a body inward, and the angular terms
allow asymmetric contacts to rotate. Symmetric aligned contacts have zero
angular correction. No defect was confirmed in these cases, so no speculative
rewrite was made.

## Regression tests

`tests/test_audit_geometry.py` adds deterministic checks for:

- vertex-only contact versus polygon separation;
- coincident-center overlap;
- wall violations inside and outside the numerical tolerance;
- quarter-turn and near-parallel angle handling;
- float64 center-offset degeneration and JSON-safe rejection;
- rejection of textual and boolean scalar schema values; and
- pose/document JSON round-trip behavior.

The focused command passed:

```
UV_CACHE_DIR=/tmp/asquerix-uv-cache uv run pytest -q \
  tests/test_audit_geometry.py tests/test_geometry.py tests/test_documents.py
```

Result: **39 passed**.

## Saved-artifact revalidation

The archived pilot contains 712 selected pose documents. Re-running the
validator after the fix produced 708 `NUMERICALLY_VALIDATED` documents and
four expected `INVALID` documents from the explicit `INIT_FAILED` experiment;
those four contain zero poses while declaring `n=2` and were intentionally
marked `NOT_CHECKED` by the runner. The 708 normal-domain statuses and reported
pair/wall metrics match their archived v1 validation values exactly. Archived
files were not rewritten; historical v1 provenance remains intact.

The validator remains a float64 numerical oracle, not an exact certificate.
The representability guard protects the unit-side invariant when reconstructing
saved data; it does not promote any result to `CERTIFIED`.

## Limitations

This sub-audit did not claim a new GPU benchmark or exact proof. CUDA execution
and the bounded benchmark reproduction are owned by the main audit workflow.
The conclusions above concern the independent CPU geometry path, its input and
serialization contract, and source-level review of the GPU contact equations.
