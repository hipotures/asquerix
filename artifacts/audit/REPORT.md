# Independent implementation and experiment audit

Date: 2026-10-08. Audited implementation: `6e3f0d9` (fixes), against original implementation `ceaebce85d1dd046f97a9850cfb32b42850b8229` and evidence commit `23aa095`. The original `artifacts/pilot` files were preserved unchanged. This audit executed `PROMPT_02_AUDIT.md` and read the actual instructions, source, tests, JSON/JSONL/gzip records, fixture equations, and SVGs. The earlier conversational summary was not used as evidence.

## Verdict

The baseline satisfies the intended geometry and device execution contracts in the tested domain. Real contact response permits translations and rotations, unsuccessful proposals preserve the accepted pose, and batch partitioning preserves the tested search results. Selected constructions passed two independent float64 polygon checks. These are numerical checks, not certificates or continuous collision-free trajectory proofs.

The measurement is credible as a bounded same-device throughput experiment: initialization and the full compression workload were timed with CUDA events and synchronized boundaries, each main measurement lasted 28–113 seconds, and all four 12,288-trial search streams match the original saved search fields exactly. This is not a claim of isolated hardware performance or cross-architecture determinism. The display remained active.

Packing quality is modest: the n=12 median is 4.6203081608, with only 5 of 12,288 trials at or below 4.001. There was no apparent n=12 result below 4 and no new packing record. Neither budget exhaustion nor initializer failure establishes geometric infeasibility or optimality.

The audit fixed concrete defects in evidence retention, residual reporting, input validation, failure classification, SVG handling, and timing. The historical archive has 193 numerical-validation scalar rows whose pose files were discarded. Their original checks cannot be replayed from that archive; the new campaign has zero such missing positive audit inputs. This qualification remains attached to the old data.

## Confirmed findings and fixes

| Finding | Severity and evidence | Resolution and regression |
| --- | --- | --- |
| Earlier checked candidates lost their coordinates when superseded | Medium. Actual old JSONL/gzip has 193 `NUMERICALLY_VALIDATED` rows without pose JSON: sweep b8=50, b32=36, b128=23, extended repeats=28 each. | Fixed. Valid/indeterminate checked candidates remain durable after leaderboard replacement. `keep_best` still caps the leaderboard; invalid debug examples and images retain their explicit caps. `test_audited_scalar_records_have_durable_pose_evidence` reproduces the defect. New campaign: 0 missing audited poses. |
| GPU maximum penetration ignored the walls | Medium. Production finalization of an injected one-square state at x=5, L=10 reported wall clearance -0.5 but penetration 0. | Fixed to `max(0,-min(pair_gap,wall_clearance))`. `test_production_finalizer_reports_wall_penetration` runs the actual production kernel and demands 0.5 and infeasible status. Old accepted artifacts had positive wall clearance and did not exercise this defect. |
| Validated host parameters could become zero/infinite or lose inequalities in FP32 | Medium. The original accepted step 1e40, motion tolerance 1e-50, a reduction rounded to 1, and guard/tolerance values rounded equal. | Fixed by validating the converted FP32 numerical contract before parameter upload. Four deterministic regression cases. Ordinary defaults and measured budgets are unchanged. |
| Noninteger controls and invalid pose gathers reached lower-level GPU/runtime operations | Medium. Original count/offset/control checks accepted booleans or fractional values; an offset 1.5 reached Warp packing instead of being rejected as an invalid global ID. A gather could read stale worlds from a preceding larger batch. | Fixed exact integer/range checks, last-completed-batch bounds, and gather capacity bounds. CUDA regression also tests reading before any completed batch, negative and huge indices, and a smaller batch after a larger one. Runner controls have CPU regression cases. |
| Malformed/extreme finite pose data could crash or produce infinite diagnostics | Medium. Centers near 1e16 erased unit edges and generated infinite metrics; `10**400` raised `OverflowError`. Strings and booleans were silently coerced as coordinates, side or tolerance. | Fixed JSON-safe rejection, numeric schema checks, derived finite checks and unit-edge representability checks. Validator version is `cpu-f64-projection-v2`; historical v1 files remain unchanged. Regression tests include strict JSON serialization. |
| Offline validation confused initializer exhaustion with invalid geometry | Low. `validate` classified the actual empty `INIT_FAILED` examples as `INVALID` despite no final pose existing. | Fixed CLI classification to `NOT_CHECKED` for explicit `INIT_FAILED` / `NO_ACCEPTED_POSE` records with null side and empty poses. Malformed actual pose documents still fail validation. |
| Unknown validation labels and filename collisions could mislead SVG output | Low. Unknown labels were not classified as invalid; distinct IDs sanitizing to the same filename overwrote an SVG. | Fixed unknown labels to `INVALID DEBUG` and disambiguated filenames. Deterministic output regressions pass. Numeric global IDs retain their exact integer representation. |
| Reporting happened twice while timing omitted the second pass | Low. Source inspection confirmed duplicated report/histogram generation and understated final wall/report timing. | Fixed to one report/histogram pass, timed through their persistence. Final summary explicitly excludes its own serialization. The audit records an external complete `run()` duration including that serialization. A deterministic test checks the timing boundary after both files exist. |

No defect was confirmed in the ordinary-domain SAT signs, moving-axis angular derivative, wall forcing, full rollback, or world ownership. Those paths were not rewritten. No new search algorithm, fixture seed, center scaling, angle snapping, tolerance relaxation, or shortened solver budget was introduced.

## Reconstructed mathematical and numerical contract

The container is centered, `[-L/2,L/2]^2`. Every mathematical square has side 1, center `(x,y)` and angle theta in radians. Vertices are `c +/- u/2 +/- v/2`, with u and v orthonormal square axes. The GPU tests all n(n-1)/2 pairs with the four oriented-square SAT axes and checks wall support separately. The CPU oracle reconstructs vertices, derives polygon edge normals and projects every pair without using GPU helpers or contact lists.

Initialization is GPU rejection sampling: centers stay inside a circumscribed-radius wall margin, center-distance squared is at least `2+4*guard`, and independent sampled angles lie in `[0,pi/2)`. It is conservative, bounded, and not uniform over feasible packings. No automatic grid or larger container replaces an exhausted initializer.

Compression proposes `L-step` while initially leaving centers and angles unchanged. Sequential wall and pair projections change both translation and angle, with translation mobility 1, angular mobility 0.3, relaxation 0.8, and correction caps 0.1 length / 0.08 radians per body and contact. The generalized SAT gradient differentiates the moving axis as well as support. Ties and support cusps use the documented symmetric treatment within 1e-6. Symmetric face contacts correctly have zero torque; asymmetric contacts rotate in actual CUDA tests.

Every sweep recomputes all pair and wall residuals. Acceptance requires finite coordinates and FP32 clearance at least `guard-acceptance_tolerance`. Success replaces the accepted pose; failure restores all its components and halves the step. Accepted side is monotonically nonincreasing. Maximum individual correction, rather than a signed sum, controls four-sweep stagnation. A final accepted pose can independently be feasible while its termination reason is `BUDGET_EXHAUSTED`.

The matched workload is exactly the original solver configuration: n=12, initial side=10, seed=20261008, initial step=0.2, floor=1e-4, reduction=0.5, guard=2e-5, acceptance tolerance=2e-6, motion tolerance=1e-7, 128 attempts, 120 sweeps per attempt and 2000 proposals per square. Search is FP32 with fast math disabled. Each world has finite proposal, sweep, attempt and stage budgets; supported n is 1–32.

Float64 validation tolerance is 1e-8: all clearances above it yield `NUMERICALLY_VALIDATED`; near contact within +/- tolerance yields `INDETERMINATE`; larger violations or malformed/unrepresentable data yield `INVALID`. This tolerance is a numerical classification policy, not a proven floating-point error enclosure. `GPU_FEASIBLE`, termination reason and independent status remain separate. No output was promoted to `CERTIFIED`.

## Test and adversarial evidence

The original full suite ran on real CUDA before edits: **85 passed**, 0 failed, 0 skipped. The final full suite ran before the measured campaign: **126 passed**, 0 failed, 0 skipped, including **17 CUDA cases** and 109 CPU cases. There were two upstream Warp ctypes deprecation warnings on Python 3.14; neither affected execution.

The audit added 41 collected cases. Besides the defect regressions above, deterministic cases cover vertex and edge contact, intentional overlap, coincident centers, AABB false positives, nearly parallel angles, quarter-turn boundaries, wall violations smaller/larger than tolerance, JSON numeric round trips and reconstructed unit edge lengths. A batched CUDA diagnostic compares the production SAT with independent vertex projection on saved FP32 inputs. Existing actual CUDA tests cover angular response, correct zero torque, finite-difference gradients for both axis owners, rejection rollback, accepted-side monotonicity and uint64 RNG partitioning.

New regressions were also executed against an isolated source extraction from original commit `23aa095`: **30 failed, 32 passed**, as expected for the confirmed issues and extended input checks. The original working tree and archive were not rewritten for that experiment. Logs: `tests-baseline.txt`, `regressions-on-original.txt`, `tests-gpu-regressions.txt`, `tests-fixed.txt` and `gpu-test-collection.txt`.

## GPU residency and reproducibility

Source tracing confirms one CUDA thread owns one world and writes only its world column. Accepted/work pose arrays and scalar/gather buffers are preallocated and reused. The default submission is eight kernels, each allowing at most 16 attempts. The host submits this fixed stage sequence with no state read, per-sweep decision or synchronization between stages. GPU initialization, contacts, acceptance, step changes and rollback remain on device. Printing and file writes occur after a completed batch.

`campaign/profile.json` contains a short actual Warp `TIMING_ALL` CUDA-event activity capture and a host API trace. It shows eight simulation kernels of 32 worlds, then one scalar device-to-host transfer; selected indices move host-to-device, a gather collects four poses, and one pose transfer follows. Both `.numpy()` calls occur after all simulation stages. All activities used only `cuda:0`. Kernel properties: 139 registers/thread and 32 bytes local memory. Profiling instrumentation is excluded from throughput. Nsight Systems and Compute Sanitizer were unavailable locally; this is a Warp activity capture plus code/test evidence, not a sanitizer or full-system scheduling trace. Profiling API semantics were checked against the [official Warp 1.18 documentation](https://nvidia.github.io/warp/stable/user_guide/execution_and_performance/profiling.html) and installed source.

RNG state is keyed by seed and global uint64 trial ID; batch-local indices do not replace the ID. Tests cover repeated/distinct IDs, nonzero offsets, partitioning near `2**64-1`, and rejection of out-of-range or noninteger inputs. The matched measurements cover IDs 0–12287 identically at batch sizes 512 and 128. The retained-all controls use offset 4096. Exact search-field equality was demonstrated on this GPU/compiler/dependency combination; cross-device, cross-version equality and statistical independence are not claimed.

## Reproduced benchmark

Detected environment: NVIDIA GeForce RTX 4070 Ti, UUID `GPU-64d50ac7-f623-65a8-8784-b9ec14d16527`, sm_89, 12,282 MiB, driver 615.71.09, display active. Initial observed memory use was 2,938 MiB. Linux CachyOS kernel 7.2.9-1-cachyos, Python 3.14.7, uv 0.12.23, Warp 1.18.0 default CUDA 13.4 wheel, NumPy 2.5.3, pytest 9.1.1. `uv.lock` was used unchanged; no drivers or dependencies were upgraded. The sandbox hides NVIDIA devices, so authorized GPU execution occurred outside it. This was not a CPU fallback. The wheel/runtime match the installed APIs and [official compatibility requirements](https://nvidia.github.io/warp/stable/user_guide/compatibility.html).

Each main row contains **12,288 complete trials**, identical solver inputs and IDs. Simulation time includes random initialization and compression and excludes warm-up, transfer, validation and output. All 12,288 trials per row return a GPU-feasible pose; attempted and GPU-feasible rates therefore coincide.

| Run | Batch | Synchronized simulation s | CUDA-event s | Trials/s | External complete run s | Audits / trials |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| matched-b512-r0 | 512 | 28.325444 | 28.321439 | 433.814908 | 30.903410 | 114 / 12288 |
| matched-b512-r1 | 512 | 28.047661 | 28.043590 | 438.111405 | 30.528302 | 114 / 12288 |
| matched-b512-r2 | 512 | 28.294090 | 28.289968 | 434.295642 | 31.102098 | 114 / 12288 |
| matched-b128 | 128 | 112.766949 | 112.751582 | 108.968099 | 116.003201 | 136 / 12288 |

Batch 512 mean: **435.407319 +/- 2.354111 trials/s**, sample standard deviation across three repeats (0.54%). The throughput ratio to batch 128 is 3.9957 on identical results. Approximately 2297 microseconds/trial is amortized throughput, not an individual-world latency. Only batch 512 was repeated; the batch-128 row does not establish its run-to-run variance or a globally optimal batch size.

The original archived three extended rates, read from the saved records/timing metadata, were 426.091561, 422.496389 and 420.404752 trials/s: **422.997567 +/- 2.876340**. The new mean is 2.93% higher. There was no solver optimization in this audit, and other display/system activity was not controlled, so this difference is not attributed to a speedup. The short old batch sweep is preliminary, not substituted for the long comparison.

| Run | Cached module load s | Full-budget warm-up s | Transfer/gather s | CPU validation s | Persistence s | Pose rendering s | Report/histogram s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| b512-r0 | 0.000618 | 0.797733 | 0.021871 | 1.419817 | 0.119459 | 0.002134 | 0.033152 |
| b512-r1 | 0.000358 | 0.748911 | 0.023014 | 1.335741 | 0.129141 | 0.002144 | 0.046260 |
| b512-r2 | 0.000626 | 0.765519 | 0.024924 | 1.593882 | 0.142795 | 0.002658 | 0.056158 |
| b128 | 0.000578 | 0.782212 | 0.077329 | 1.884974 | 0.152391 | 0.002642 | 0.065124 |

A separately measured fresh Warp cache compiled/loaded the module in 1.262533 s; total runtime setup and loading was 1.573979 s. NVIDIA's driver cache was left intact. No trials ran in that measurement. `cold-compile.log/json` preserve it. Warm-up uses the full production budget and is excluded from recorded trial counts. Phase timers do not exactly partition wall time: metadata collection, Python selection/scalar processing and final summary serialization also cost time. `run_call_seconds` includes the final output serialization; the summary's own end-to-end boundary is explicitly narrower.

The entire measured campaign, including retained-all controls, profiler diagnostic, output archiving/revalidation, deadline test and initialization-failure example, lasted **233.208383 s**, below the 300 s bound. Tests, setup and the separate cold compilation were outside that campaign. Largest recorded stage: 0.267371 s in the n=16 tiny control; main benchmark stages stayed below 0.195 s. Desktop responsiveness was protected through the existing bounded stages, without changing scientific budgets.

## Distributions, residuals, and independent geometry totals

All four matched n=12 runs have exactly the same search fields as the old extended run, not merely equal best sides. Independent status/version fields were excluded from that comparison because validation changed to v2 and selection coverage depends on partitioning. Counters, proposals, attempted/accepted/rejected steps, termination, raw residuals, side and identity fields were included.

Shared retained pose JSON was also compared directly against the original extended repeat-0 coordinates and side, with exact equality of the saved values. `shared-pose-equality.json` records the intersecting trial IDs; this strengthens the source-level conclusion that contact evolution did not change, without pretending that the original retained every world.

| n=12 property, each matched run | Result |
| --- | ---: |
| Best L, trial 6233 | 4.000200271606445 |
| Median L | 4.620308160781860 |
| q05 / q95 | 4.265044379234314 / 5.571213769912720 |
| Worst L | 6.956242084503174 |
| BUDGET_EXHAUSTED | 6873 (55.9326%) |
| STEP_FLOOR_REACHED | 5415 (44.0674%) |
| INIT_FAILED / NUMERICAL_FAILURE / STAGNATED | 0 / 0 / 0 |
| Minimum GPU pair and wall residuals over every scalar row | 1.800060272216797e-5 / 1.800060272216797e-5 |
| Maximum reported GPU penetration | 0 |
| Trials at or below 4.001 / below 4 | 5 / 0 |
| Mean attempts / sweeps | 96.988607 / 8366.836507 |

The controls independently audit every final state: 32 trials each for n=11,12,16, at batch 16 and global IDs 4096–4127. All **96/96** passed; best sides were 4.018752574920654, 4.219933032989502 and 4.756441116333008 respectively. These small controls demonstrate geometry and varying n, not strong search success or stable throughput. The original n=11 and n=16 best selected candidates also passed the independent archive audit; their 512-trial best sides were 4.0002007484436035 and 4.58729362487793.

New campaign totals including the negative and stop diagnostics: **49,260 scalar records**, 49,256 GPU-feasible results, **582 numerical passes**, 48,678 `NOT_CHECKED`, zero checked search poses invalid or indeterminate, and four empty `INIT_FAILED` records. Every one of the **582 nonempty retained poses** was rechecked by the production-independent CPU oracle and by the standalone artifact checker, with zero status/residual mismatches. All 64 reproducible random audits in each main run passed. Coverage is 114/12288=0.9277% at batch 512 and 136/12288=1.1068% at batch 128. Selection is biased toward promising candidates; this is not whole-population independent validation. Repeated IDs are repeated observations, not new statistically independent samples.

The standalone checker imports no production geometry code. It reconstructs vertices and polygon edge normals using its own math, checks all pairs/walls, rebuilds distributions/counts from actual JSONL/gzip, and parses SVG XML. It independently checked **708 historical nonempty poses**, **53 historical SVGs**, **582 new nonempty poses**, and **23 new SVGs**, with zero geometric, metadata or rendered-polygon mismatches. Original manifest integrity: **943/943 files** matched sizes and SHA-256; the three original gzip streams matched compressed/uncompressed hashes and contained 12,288 rows each. Original source hashes were checked against the actual recorded Git revision separately. Source hashes differ in the new revision because of the declared fixes.

Rasterized views of the best n=12 candidate, n=11/n=16 controls and the empty initialization-failure debug SVG were opened. Numeric polygon and container equality, rather than visual plausibility, supplies the rendering check. `visual-inspection.json` lists the views. Histograms remain split between the GPU population and independently checked selected subset; no unchecked histogram was relabeled as independently validated.

## Fixture provenance and limitations

The Trump11 source is pinned to commit `176e8ad14d5b93f3a1f3d5a9e04ab1dfdb8c704b`; the 3,876-byte source copy has SHA-256 `3b4eae938c37c13af6252ac5d83fa99aa95f6b1627b99920c5df8be94c56bea9`. Attribution and the MIT notice are retained locally. The copy was inspected as text, never executed. Independent Decimal bisection of the polynomial for u, followed by `L=(6u+4)/(1+2u-u^2)`, recovers 3.87708359002281417730789706010096… and reproduces the rounded centers/angles within 4.44e-16. The rounded contact fixture is `INDETERMINATE`, while its explicitly separated unit-square derivative passes numerical validation.

The [current eleven-square case record](https://jlevy.github.io/squares/cases/11.html) and [proof review](https://jlevy.github.io/squares/papers/n11-optimality-review.html) were opened on 2026-10-08. They report the algebraic equality with V3/C3/S5 machine-check/review qualifications; this PoC does not replay or prove global optimality. Decimal reconstruction alone is not a certificate. The twelve-square 3-by-4 grid in L=4 remains a feasible reference, with no optimality assertion. Fixtures and target sides never enter ordinary GPU search.

No suspicious below-reference result appeared. Genuine remaining limitations are heuristic packing quality, selected rather than universal large-run audits, missing 193 historical pose inputs, lack of a rigorous numerical certificate, uncontrolled display activity and no cross-architecture reproducibility proof. These are disclosed limits, not blockers to the executed bounded audit. No required CUDA or independent validation path was unavailable.

## Stopping, artifacts and tested commands

The actual 1 ms scheduling-limit test requested 64 trials in batches of 8 and completed only IDs 0–7. No subsequent batch was submitted. `MAX_SECONDS` was saved, all 8 completed geometries passed, and drain beyond the deadline to batch completion was **1.046980 s**; total search overrun including collection/persistence was **1.149978 s**. The limit begins after setup/warm-up and cannot cancel an in-flight batch. Deterministic SIGINT tests also pass; a fresh real Ctrl-C run was not needed because the assignment allows the wall-limit alternative.

The negative n=2, initial-side=1.5, one-proposal initializer run produced four `INIT_FAILED` rows with null sides and no fabricated final packing. CLI validation reports them as `NOT_CHECKED`; their empty SVG is clearly a debug view. Failure is not an impossibility claim. Multi-batch sparse selection retains coordinates independently of its SVG cap: controls and benchmarks each have at most three images, diagnostics at most one, and the checker found no overwritten or mismatched polygons.

Durable evidence is under `artifacts/audit`: this report, regression logs, original-evidence audit, a standalone checker, actual profiler capture, all scalar streams compressed without loss, selected pose JSON, SVGs, environment/configuration, numerical revalidation and raw timing metadata. Uncompressed runs remain locally under ignored `runs/audit`; the compressed repository archive is sufficient to recover their records. The manifest records every file hash and the measured source revision. `review-notes` contains intermediate findings; this report states the final integrated resolution.

Commands actually exercised:

```bash
uv run --locked pytest -q
uv run --locked python artifacts/audit/reproduce.py
python artifacts/audit/prior-evidence/check.py artifacts/pilot --fixture-source artifacts/audit/prior-evidence/trump11-source.txt --output artifacts/audit/prior-evidence/replayed-check.json
python artifacts/audit/prior-evidence/check.py artifacts/audit/campaign --output artifacts/audit/independent-current.json
uv run --locked asquerix validate artifacts/audit/campaign/retained-n12
uv run --locked asquerix validate artifacts/audit/campaign/init-failed
uv run --locked asquerix compare runs/audit/matched-b512-r0 runs/audit/matched-b128
ASQUERIX_WARP_CACHE=/tmp/asquerix-audit-cold-20261008 uv run --locked python artifacts/audit/cold-compile.py
```

GPU commands require an environment exposing the NVIDIA device. The chosen reproduction destinations must not already exist; use the README's fresh `--output` and `--runs-output` paths for another campaign. For offline report generation from an archive, copy the non-database run directory into a fresh location, decompress its `trials.jsonl.gz` into `trials.jsonl`, then run `asquerix report`; never overwrite the historical evidence.
