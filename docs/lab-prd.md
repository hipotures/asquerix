# Asquerix Experiment Laboratory
## Product requirements and end-to-end implementation assignment for Codex

**Version:** 1.0  
**Date:** 2026-10-09  
**Repository:** `hipotures/asquerix`  
**Delivery:** extend the existing application on `main`; do not create a replacement project  
**Primary product requirement:** an experiment is not complete without understandable results, inspectable programs, and usable trajectory replay

---

## 0. Assignment, authority, and interpretation

Read `AGENTS.md`, inspect the actual local repository, and implement this PRD end to end. Do not stop after generating scaffolding, a proposal, a static dashboard, or mock results.

Build a small, single-host web laboratory for generating, evaluating, comparing, and replaying square-packing strategy programs executed by the existing Warp/CUDA geometry engine. Preserve the working command-line tools and their Rich presentation.

This is a **new functional and scientific extension**, not a performance-only task. It explicitly authorizes a server, a browser interface, rigid-square strategy operators, and two program-search methods. Update outdated scope language in `AGENTS.md` accordingly. It does **not** authorize changing the mathematical validity rules, weakening collision checks, discarding old evidence, or rewriting the existing solver without regression evidence.

Work directly on the existing `main`. Do not create branches, pull requests, or worktrees. Inspect the index, local changes, running processes, and remote advances before editing or committing. Preserve concurrent user/agent work and active experiment outputs. Never use `git add -A`, force-push, destructive resets, or cleaning commands.

Communicate with the user in Polish. All authored code, comments, documentation, schemas, UI labels, chart labels, reports, and commit messages must be in English. Use `uv`; keep dependencies isolated and locked. Never install or alter system GPU drivers as an incidental development step.

**Do not treat “a better packing was not found” as implementation failure.** Correct execution, fair comparison, durable evidence, and actual working visualization are the delivery requirements. Improved search performance is an experimental outcome.

### Decisions already made

Do not reopen these choices unless an actual implementation blocker is demonstrated:

1. One strategy program controls one complete world, not one program per square.
2. There is no autonomous background compressor. Compression happens only when the program requests it.
3. The first laboratory uses rigid unit squares only.
4. Implement exactly two search methods: independent random program search and mutation-guided `(1 + lambda)` search.
5. Keep two fixed program controls: legacy-compatible compression and a handwritten compression/expansion/perturbation strategy.
6. Python performs generation, compilation, scheduling, aggregation, API handling, and presentation. Warp/CUDA executes geometric operators and per-world program decisions.
7. The browser is a control and inspection client. Closing it must not stop computation.
8. A usable trajectory viewer and campaign-history viewer are core functionality, not optional enhancements.
9. Ordinary numerical output stays compressed; raw JSON is not dumped into the console.
10. Existing legacy `run`, validation, SVG export, profiling tools, and trajectory viewers must continue to work.

### Relationship to earlier design material

The earlier `ASQUERIX_EVOLVING_STRATEGY_PROGRAMS_DESIGN.md` and reference compiler are useful design material if present locally, not a finished strategy executor. Reuse compatible ideas and tests rather than requiring the user to install an external reference package.

This PRD intentionally narrows or supersedes earlier proposals:

- A web server is now in scope.
- Full population evolution, crossover, and morphing are deferred.
- V1 uses an explicit deterministic ranking rule, not an unspecified Pareto or weighted objective.
- Finalization validates and returns a protected best state; it does **not** secretly compress, rearrange, or repair the program's result.
- There must be no independent per-square controllers and no algorithm mutation in the middle of an episode.

---

## 1. Existing project: integration anchors, not an obsolete frozen target

The repository was inspected at `afa10b10802e46a4d16a1f56120295c685c908d0` while drafting this document. Re-read the actual current local and remote `main` before implementation. Do not reset to that commit, assume it is still HEAD, or replace newer work with this snapshot.

At the inspected revision the following are documented or visible in the repository:

| Existing component | How the laboratory must use it |
|---|---|
| `src/asquerix/gpu.py` | Unit-square geometry, contact corrections, RNG initialization, bounded compression, step-floor correction, and numerical operand barriers. |
| `src/asquerix/geometry.py` | Independent CPU float64 validation; do not replace it with the GPU's own validity flags. |
| `src/asquerix/runner.py`, `output.py` | Established result collection, statistics, reporting, and persisted evidence conventions. |
| `presentation.py`, `cli.py` | Rich output, non-TTY behavior, and the project-specific `--json` contract. |
| `persistence.py`, `publication.py` | Lossless gzip level 3, old/new readers, atomic output, manifests, and safe publication to remote `main`. |
| Existing trajectory modules, including `trace_gpu.py` | Selected CUDA replay, bounded frame storage, reference comparison, and explicit provisional states. Inspect exact current module names. |
| Existing HTML trajectory viewer | Initial/current panels, stable IDs, orientation marks, pan/zoom, center trails, selected-square focus, range playback, and current-frame SVG export. Preserve these controls. |
| `tools/kernel_benchmark.py`, profiling and dual-GPU tools | Numerical regression references and device identity practices. Do not confuse a benchmark-only two-GPU harness with a production multi-GPU scheduler. |

The inspected README describes trajectory schema `asquerix-trajectory-v1`, `.npz` geometry, `.meta.json.gz`, self-contained HTML, and source/reference mismatch handling. It also documents publication using an isolated Git index and a lock, without changing the active checkout. Use these existing capabilities. [P1–P4]

Freeze the actual pre-change production source hashes and a small numerical regression corpus before adding strategy execution. Preserve the minimum-step correction and the accepted sine/cosine operand-separation mechanism. Adding control state or recording can alter compiler behavior: numerical equivalence must be tested, not inferred from similar-looking equations.

---

## 2. Product outcome and release boundaries

### 2.1 The user must be able to

1. Start the laboratory server from the terminal and open its browser interface.
2. Configure a campaign without editing Python or pasting large JSON documents.
3. Select a detected GPU, square count, common starting dataset, operators, parameter ranges, search method, and finite evaluation budget.
4. Launch one method or a controlled comparison of both methods.
5. Close the browser and return later without stopping the experiment.
6. Inspect generated programs and see why a mutation was retained or rejected.
7. Compare quality, reliability, and cost against the fixed controls.
8. Open an actual geometric replay, with traces and the currently executing instruction highlighted.
9. Compare two programs acting on the same initial world.
10. Browse the entire recorded search history after the campaign has finished.
11. Export a compact offline report with selected playable trajectories.
12. Obtain the confirmed publication commit and inspect results through GitHub, without copying console JSON.

### 2.2 Required V1 scope

- Rigid unit squares, configurable `n` in the existing supported range, at least 1–32.
- Typed strategy representation, compiler, validator, and bounded GPU executor.
- `COMPRESS`, `EXPAND`, `MOVE`, `ROTATE`, `RELAX`, `RESTORE_BEST`, and `STOP`.
- Object selectors, bounded conditions, and bounded repetition.
- Shared initial states, protected best results, independent validation, reproducible scoring.
- Random program search and `(1 + lambda)` mutation search, plus fixed controls.
- FastAPI server, durable local catalog/queue, browser UI, SSE progress, and Rich terminal views.
- Selected trajectory replays and campaign/mutation-history replay.
- Gzip/NPZ evidence, safe publication, interruption, recovery, and real CUDA tests.

### 2.3 Explicitly deferred

Morphing, circles or rounded squares, deformable bodies, friction/inertia simulation, crossover, large population evolution, reinforcement learning, LLM-generated executable code, distributed servers, multi-user accounts, arbitrary code execution, a general visual programming IDE, 3D packing, live video streaming of every world, and per-square programs.

Production V1 must run on one explicitly selected GPU. Design task identities and worker ownership so the existing independent-device approach can be extended later. Simultaneous dual-GPU execution is not a new release gate for this assignment; do not delay a working single-GPU laboratory for a distributed scheduler. Preserve all existing dual-GPU tools.

---

## 3. Terminology and exact execution model

| Term | Meaning |
|---|---|
| Square | One rigid object with fixed side 1 and state `(x, y, theta)`. |
| World / board | One square container and all its squares. |
| Strategy / program | An immutable sequence/tree of allowed instructions controlling one world. |
| Episode | Execution of one program on one initial world, with one declared operator-RNG replicate and evaluation profile. |
| Candidate | A program being evaluated by a search method. |
| Search method | A CPU algorithm proposing programs and consuming their evaluation results. |
| Search arm | One instance of a search method within a campaign. |
| Campaign | Immutable specification, common datasets, controls, one or two search arms, evaluations, reports, and replays. |
| Training bank | Initial worlds used to guide candidate selection. |
| Holdout bank | Separate worlds evaluated only after the winning programs are frozen. |
| Slice | A bounded device execution segment; not a program operation or a scientific restart. |

A strategy contains operations such as “compress toward a 5% reduction”, “expand by 4%”, and “rotate three near-wall objects”. Different selected squares may receive different proposals. Unselected squares remain movable when the contact solver propagates corrections.

Operators execute sequentially per world. Many worlds execute concurrently on the GPU. A method never edits the program of an already-running episode. Mutation produces a new immutable candidate for later episodes.

No compressor runs independently of the strategy. An expansion-only strategy is legal, terminates under the same limits, and normally returns its original starting size as its best result. A compression target is an attempted geometric goal, not permission to declare an infeasible size successful.

For fractions measured from the current side, a successful 5% compression followed by 4% expansion multiplies `L` by `0.95 * 1.04 = 0.988`. Display percentage semantics explicitly; do not confuse additive percentages with absolute length increments.

---

## 4. Scientific contracts

### 4.1 Immutable evaluation profile

A campaign fixes the geometry and evaluator profile before execution. Programs cannot mutate:

- Square dimensions, collision predicates, contact ordering, numerical precision, guards, or acceptance/validation tolerances.
- Compiler fast-math settings or operand barriers.
- Global budgets, resource limits, scoring rules, dataset identity, reference targets, or validation policy.
- The protected best-state validity flag or score.

Expose safe campaign settings separately from evolved operator parameters. A study using different numerical tolerances is a different profile, not an evolved strategy.

### 4.2 Three geometry states

Maintain separate per-world geometry and container side for:

- `current`: the latest accepted feasible state; may be worse than an earlier state.
- `trial`: the proposal under repair; may temporarily overlap or violate walls.
- `best`: the smallest accepted square-feasible state found in this episode, owned by the evaluator.

Initialize `current` and `best` from the valid starting world. Update `best` only after a full required GPU feasibility check and a strict improvement in `L`; preserve the earlier snapshot on an exact tie. Independent CPU validation is still required before a result is promoted as validated.

A failed transaction restores all geometric state, including `L`, and invalidates caches. It does not rewind operator RNG, program dispatch counts, consumed work, or event counters.

Return `best`, not necessarily `current` at `STOP`. Record both so the viewer can explain an exploration that ends after expansion. Numerical failure remains a failure even when a previously valid `best` can be salvaged for inspection.

### 4.3 Correctness is separate from search quality

| Comparison | Required property |
|---|---|
| Existing legacy `run`, before/after this extension | Same defined numerical bytes in the tested environment. No hidden new search. |
| Legacy-compatible compression program versus legacy solver | Same final geometry, numerical diagnostics, compression counters, and corresponding termination meaning. Additional VM bookkeeping is separate. |
| Same strategy and inputs under different slices, partitions, or replay | Same defined endpoint/result bytes within the tested device/toolchain scope. |
| Different strategies | Different outcomes are expected; compare validity, quality, and cost. |

Do not normalize angles, reorder square IDs, round saved poses, or loosen tolerances to make tests pass. A bitwise test must actually compare bytes of defined fields, not only approximate equality or matching histograms. Exclude uninitialized struct padding; define and report scratch initialization in the test harness.

---

## 5. Operator catalogue and transaction semantics

The names below are the V1 contract. Defaults are proposed initial profile values, not claims of optimal parameters.

### 5.1 `COMPRESS`

Parameters:

- `target_reduction`: either `null` for legacy-compatible “compress within the operator budget” behavior, or a finite fraction `0 < f < 1` within the campaign's allowlisted range.
- `attempt_limit`: bounded by the profile.
- `sweep_limit`: per compression attempt, bounded by the profile.
- Adaptive step settings come from the immutable solver profile, not from hidden defaults.

At invocation, capture `L_entry`. A fractional request sets a fixed `L_target = L_entry * (1 - f)`; do not repeatedly recompute the target from a shrinking current state.

Reuse the tested compression procedure. Every substep must repair and validate before acceptance. A failed substep restores the immediately preceding accepted state, not necessarily the operator-entry state. Earlier accepted improvements survive.

Stop on target reached, no progress under the step policy, operator limit, global budget, numeric failure, or user-requested draining. Preserve the step-floor fix: an admissible floor is tried before floor failure is declared.

For a target-clipped final increment, define the effective floor as the smaller of the profile floor and the positive remaining target distance. Test it explicitly. If FP32 subtraction cannot change the side, return a bounded no-progress result. Never iterate forever on a zero-size numerical step.

`target_reduction=null` must preserve the legacy step/counter behavior in the compression reference test. A new invocation starts with the profile's initial step unless a future, separately versioned operator explicitly says otherwise. Technical slices do not restart that step.

### 5.2 `EXPAND`

`fraction`: finite `0 < f <= campaign.expand_max`, proposed default range 0.005–0.10, initial hard operator cap 0.25.

Propose `L_new = L_current * (1 + f)` and change the container only. Centers, angles, and square dimensions do not scale. All four walls remain symmetric under the existing centered-container convention.

Reject requests exceeding the profile's maximum container side, proposed as `min(100, 2 * initial_side)`. Do not silently clamp a strategy's requested action and pretend it executed unchanged. `best` never becomes worse.

### 5.3 `MOVE`

Parameters: selector, `max_distance`, `repair_sweeps`. Proposed normal range: 0.005–0.20 unit lengths; hard profile cap: 0.5.

Select objects once from `current`. For each selected object, propose an independent displacement uniformly in a disk of radius `max_distance` in world coordinates. Specify and version the exact RNG draw order. Preserve selected-square order by ID.

Build all selected displacements from the same pre-proposal state, then perform one bounded joint repair with all squares mobile. Accept the full transaction only if the complete world passes feasibility; otherwise restore `current`. There is no invisible container expansion during repair.

### 5.4 `ROTATE`

Parameters: selector, `max_angle_rad`, `repair_sweeps`. Proposed normal range: 0.01–0.30 radians; hard profile cap: `pi/4`.

Select objects once. Give each selected object an independent signed increment in `[-max_angle_rad, +max_angle_rad]`, preserving ID order and the declared RNG mapping. Propose rotation about its current center, then jointly repair at the same `L`, allowing translations and rotations of all squares.

Commit all selected proposals together or roll back together. This is not equivalent to committing one object at a time. Do not silently substitute the sequential interpretation.

### 5.5 `RELAX`

Bounded fixed-container contact relaxation. It cannot change `L` or invent an attraction toward the center.

In V1 every public instruction boundary is already feasible. Therefore `RELAX` returns `ALREADY_FEASIBLE` without geometric changes when the current state meets the acceptance criterion. It is not an implicit mutation or a hidden compressor. Transactional `MOVE` and `ROTATE` own their internal repair; they cannot leave an unresolved proposal for a later opcode.

Retain the explicit operation and its outcome for authoring, diagnostics, and future versioned semantics. Its default weight in random generation may be zero because a standalone feasible-state relaxation is normally redundant. The UI must explain this rather than suggest that it always improves packing.

### 5.6 `RESTORE_BEST`

Copy protected `best` into `current`. Preserve all RNG and budget progress. If already identical, return `UNCHANGED`. Invalidate relevant caches. Mark the transition as a discontinuous restore in visualization, not a physical trajectory.

### 5.7 `STOP`

Ends the program body and invokes fixed bounded finalization. It does not compress, perturb, or repair the answer.

### 5.8 Selectors

Support at least:

| Selector | Exact meaning |
|---|---|
| `ALL` | All square IDs in stable order. |
| `RANDOM_K(k)` | Up to `min(k,n)` distinct IDs sampled without replacement using a bounded method, then sorted by ID for proposal application. |
| `WALL_K(k)` | Up to `min(k,n)` squares with the smallest current minimum wall clearance; ties by ID. |

**`WALL_K` means nearest to the wall, not only objects in exact contact.** Otherwise `EXPAND` would often make the subsequent wall selector empty. This distinction is intentional and must appear in the UI/help.

The mask is chosen once when an operator begins and saved across slices. An empty valid selection returns `NO_TARGET`, consumes dispatch/sensing work, and never creates an uninitialized mask. Do not add fixed numerical square IDs to the evolving grammar; IDs are for stable identity and inspection.

### 5.9 Outcomes and observations

Keep these distinct:

- Operation outcome: `TARGET_REACHED`, `PARTIAL_PROGRESS`, `NO_PROGRESS`, `REJECTED`, `NO_TARGET`, `ALREADY_FEASIBLE`, `LIMIT_REACHED`.
- Episode termination: normal stop, instruction limit, global work limit, numerical failure, invalid program, cancellation.
- Execution state: `RUNNING` / `YIELDED`; yielding is never a scientific operation failure.
- Geometry status: GPU feasible, CPU validated, indeterminate, invalid, not checked.

Allow a small fixed predicate set, such as `LAST_NO_PROGRESS`, `LAST_REJECTED`, `LAST_IMPROVED_BEST`. Specify exactly which completed operation outcomes each predicate matches. Do not infer mathematical jamming from an iteration limit. No arbitrary Python predicates, callbacks, or string evaluation.

---

## 6. Program language, compiler, and bounded execution

### 6.1 Representation

Use typed CPU objects or validated JSON for authoring, and compact versioned numeric instructions for the GPU. Programs are **data**, not `eval`, `exec`, generated Python modules, or one newly JIT-compiled CUDA kernel per candidate.

The user sees a readable instruction listing and parameters, not opcode integers. Preserve a source-map from every emitted instruction to the authoring node so replay and mutation diffs remain intelligible after repeat expansion.

Initial bounds:

- At most 64 authoring nodes.
- Nesting depth at most 3.
- Repeat count 1–8.
- At most 128 emitted instructions including `STOP`.
- Only forward conditional jumps in bytecode. Expand bounded repeats during compilation.
- At most 256 dispatches per episode as defense in depth.
- Fixed-size, allowlisted opcode/selector/parameter layouts; reject reserved or unknown values.

Validate finite numbers, FP32 conversion, integer ranges, uint64 identity fields, target addresses, total expanded size, and executable fall-through before upload. Validate on GPU as needed to prevent bad memory access despite a host bug. Reject malformed programs before simulation, with useful node-level errors in the browser.

Hash the canonical compiled semantics, schema version, and operator version. Retain authored parameters plus exact compiled FP32 bit patterns; do not silently erase signed zero or change precision during a round trip. Keep candidate identity separate from a program hash so duplicate proposals and genealogy can be reported.

### 6.2 Example authored strategy

The following is a target schema example. Implement this representation or an equivalently explicit one, and document the actual schema.

```json
{
  "schema": "asquerix-strategy-v1",
  "name": "Pulse and rotate near-wall objects",
  "body": [
    {
      "op": "REPEAT",
      "count": 4,
      "body": [
        {"op": "COMPRESS", "target_reduction": 0.05, "attempt_limit": 8, "sweep_limit": 120},
        {"op": "EXPAND", "fraction": 0.04},
        {
          "op": "ROTATE",
          "selector": {"kind": "WALL_K", "k": 3},
          "max_angle_rad": 0.10,
          "repair_sweeps": 120
        }
      ]
    },
    {"op": "COMPRESS", "target_reduction": null, "attempt_limit": 64, "sweep_limit": 480},
    {"op": "STOP"}
  ]
}
```

Each fraction is measured at that operator's entry. This example may or may not be an effective packing method. It must never be presented as a measured successful strategy without running it.

### 6.3 Work budgets

Bound actual internal work, not only the number of opcodes. Use a fixed, versioned budget vector with at least:

- Instruction dispatches.
- Total compression attempts.
- Total contact sweeps across all operators.
- Constraint visits/geometry checks and sensing work.
- Per-operation repair/proposal limits.
- Maximum container size and finite state values.

A reasonable starting profile has 128 total compression attempts and 61,440 total contact sweeps (128 * 480), plus a documented constraint-visit limit derived from `n`. This is a ceiling, not a requirement to burn unused work. All strategies in a comparison use the same profile.

Charge deterministic nonzero work for selectors, validation scans, restore/copy operations, and dispatches as appropriate. A prepaid conservative charge per bounded microstep is acceptable if declared as such; it is not a measurement of CUDA instructions or elapsed time. Record actual sweeps/checks separately. Prevent overflow and counter wraparound.

A lower-cost but ineffective program must not beat an effective one solely because it stops immediately. Cost is secondary to valid packing quality under the fixed budget.

### 6.4 Slice and cancellation contract

Execute many complete worlds device-side, but permit resumable slices. A slice limit is a technical scheduling boundary, not an operator budget.

At a yield point persist PC, active opcode, target, mask, proposal, RNG state/counter, attempt number, sweep number, adaptive step, stagnation state, budgets, and all three geometry buffers. Resume without reselecting objects, redrawing proposals, refunding work, or repeating a committed substep.

Prefer safe boundaries between complete sweeps or other explicitly bounded microsteps. Use both a sweep allowance and a dispatch allowance per slice so no-op programs are also bounded. Tune a conservative slice size by a short pilot; do not claim a hard wall-time preemption guarantee for an in-flight CUDA launch.

The host may submit another slice and collect compact completion/progress data at slice boundaries. It must not decide per-contact movement or fetch every world's geometry after every sweep.

For global budget exhaustion or cancellation in a proposal, discard uncommitted geometry, preserve the last accepted state and best snapshot, and finalize honestly. Cancellation stops new work and drains the current bounded slice. Record observed latency. Hard process death can lose uncommitted slice work; recovery semantics below address that separately.

### 6.5 Finalization

Reserve enough bounded work outside the mutable body to validate/check and serialize a protected best snapshot. There is no hidden final compressor. Do not override numerical failure with a success label simply because an earlier state exists.

Record best-state location in logical operation/step coordinates, final current state, and termination. CPU validation then establishes the independent numerical status. Replays and finalization do not add scientific episode counts.

---

## 7. Datasets, randomness, and evaluation

### 7.1 Common initial-state banks

Generate the initial banks with the existing non-overlapping initializer, independently of every candidate program. Store actual FP32 positions/angles, `L0`, IDs, initializer provenance, and hashes in bounded NPZ chunks.

For the pilot use 64 valid training starts and 64 distinct holdout starts per `n`. If initialization fails, count and record the rejected initial ID, then use a bounded, deterministic replacement policy common to both arms. Do not let each strategy redraw its own easier starts. If the bank cannot be completed, fail preparation explicitly.

Use separate identities/streams for initial-world generation, operator proposal randomness, and outer program generation/mutation. Candidate order, GPU batching, or a new mutation must not change the shared starting geometry.

For V1 an operator stream may be derived from `(campaign operator seed, initial ID, replicate ID)` and advanced according to the immutable program. Different programs may consume different numbers of draws; do not claim identical stochastic actions across different programs. Rollback and yielding never rewind this stream. Save RNG scheme versions and exact identifiers.

Use decimal strings for uint64 identifiers in browser/API JSON. Do not round IDs through JavaScript `Number`. Backend hashing and numerical arrays retain exact integer representations.

### 7.2 Episode identity

Define a stable key including program hash, initial-bank hash and initial ID, operator replicate, and evaluation-profile hash. A worker retry is a new execution attempt for the same episode key, not a new independent scientific episode.

Keep retries, cache hits, logical evaluations, and actual executed episodes separately counted. Never inflate throughput by counting replay, initialization probes, warm-up, or cached records as fresh GPU episodes.

### 7.3 Result and ranking

For an initialized episode, return the minimum feasible accepted `L` encountered, including the initial state. Expansion-only, no-target, early-STOP, and normally budget-limited episodes remain in the score with their actual best result.

V1 must independently validate **all returned best poses used in candidate ranking** on CPU. Transfer them in batches. This is intentionally stricter than the sampled legacy throughput campaigns; do not apply old trials/s to this workload. Keep the validator implementation separate from GPU contact helpers.

A program with a numerical error, a malformed VM state, or an independently invalid result is ineligible for promotion. Preserve its outcomes and any earlier useful candidate geometry, but do not improve its ranking by dropping failed rows. CPU indeterminate results remain explicitly unvalidated; do not promote them as independently valid. Incomplete evaluations cannot compete with complete ones.

Among complete eligible candidates, minimize this deterministic tuple:

```text
(mean best_L over the common training episodes,
 median best_L,
 mean charged work,
 emitted instruction count,
 program_hash)
```

Use deterministic aggregation order by episode identity and documented host precision. No arbitrary weighted penalty combining invalid geometry with quality. Equal-quality ties use the stated rule; do not introduce hidden novelty rewards.

Report best, mean, median, quantiles, standard deviation, validity counts, normal budget exhaustion, errors, work, and threshold-hit counts separately. Thresholds are user/profile-declared descriptors, not mutable genome constants. A reference fixture value is not automatically a globally proved optimum; preserve its provenance and margins.

Keep a construction archive separate from strategy ranking: a genuinely good independently valid individual packing should remain inspectable even when its program has mediocre average quality.

### 7.4 Holdout and fair comparisons

Freeze each arm's training winner before evaluating holdout. Do not feed holdout results into parent selection or use them to choose a different winner. If a user subsequently tunes based on holdout, label it as reused and require a new untouched bank for a fresh assessment.

Compare arms using identical initial banks, operator-RNG policy, numerical profile, parameter ranges, per-episode work caps, validation, and maximum newly evaluated program count. Report actual work and actual time too: equal candidate counts alone do not prove equal computational expense.

Show quality versus completed candidate evaluations, charged work, and elapsed execution time. Per-program GPU timing inferred from mixed-strategy batches is not an isolated cost measurement. Use homogeneous matched batches for detailed timing of controls and final winners.

A single small campaign is a functional pilot. Do not claim statistically established superiority of mutation search from one lucky minimum. Support repeated campaign seeds and paired episode comparisons in the reporting data.

---

## 8. Two implemented search methods

Implement a small shared `ask -> evaluate -> tell` interface and serializable controller state. This is a concrete design choice; do not add a general optimization framework dependency unless it materially simplifies the implementation. Ask–tell and parent-plus-offspring selection are established interfaces, but our operator grammar and scoring remain project-specific. [R5]

### 8.1 Shared initialization and generation

Use a valid bounded grammar, not random raw bytes. Save the generation distribution in the campaign config. Proposed initial defaults:

- 4–16 authored operation nodes, respecting all expanded-size limits.
- Operation sampling weights: COMPRESS 40, EXPAND 20, ROTATE 20, MOVE 15, RESTORE_BEST 5, RELAX 0.
- `STOP` is inserted as a structural terminator; no autonomous compression is appended.
- Permit expansion-only or non-compressing bodies; they receive poor actual scores rather than being falsely rejected as invalid.
- Bounded repeat/condition insertion probabilities are explicit, low initially, and configurable.
- Finite parameter intervals are declared per opcode; integer limits are not confused with floats or bools.

The generation law is a research parameter and may be biased toward plausible programs; describe that bias rather than claim uniform sampling of all algorithms.

Deduplicate compiled programs within an arm. Bound all generation/mutation retries. Record rejected/duplicate proposals and retry cost. Exhaustion returns an explicit search-space/generator outcome, not an infinite retry loop.

### 8.2 `random_program_search`

Generate and evaluate independent valid programs until the candidate or campaign budget is reached. Retain the incumbent by the fixed training ranking. Previous evaluation quality does not change this generator's distribution.

For controlled comparisons, both arms start from the same pre-generated initial candidate pool. The random arm's subsequent candidates remain independently generated. Controls are not secretly injected into one arm but not the other.

### 8.3 `one_plus_lambda`

Evaluate the common initial pool, choose its best eligible program as parent, then repeat:

```python
# Algorithm contract; evaluation is performed by the GPU worker service.
parent = best_eligible(initial_pool_results)
while remaining_candidate_budget > 0:
    offspring = bounded_unique_mutations(parent, min(lambda_, remaining_candidate_budget))
    results = evaluate_on_the_fixed_training_bank(offspring)
    parent = best_eligible([cached_parent_result, *results])
    checkpoint_controller_and_record_selection()
```

Suggested default: initial pool 16, lambda 16, total new-candidate budget 64. This means 16 initial candidates plus three rounds of 16 offspring. If the budget is not a multiple, evaluate a bounded final partial offspring group. Finish all scheduled offspring evaluations before selection; GPU completion order must not change the parent.

Mutation types: change a numeric parameter, change a selector or `k`, insert/delete/replace an operation, change a repeat count, and edit a permitted conditional block. Store the selected mutation type, node path, before/after values, parent hash, child hash, and outcome. Mutation probabilities are declared and versioned. This is mutation-guided stochastic search, not deterministic search and not full population evolution.

The parent is not reevaluated each round when its immutable inputs/profile are unchanged. Cache reuse is recorded. For the controlled pilot do not share evaluation results across search arms: re-execute shared initial programs so both arms have directly measured workloads. Later cache-sharing experiments require separate accounting.

If all initial candidates are ineligible, stop that arm explicitly and preserve diagnostics; do not silently replace it with a handwritten winner. Neutral moves follow the ranking tuple. Stagnation is reported; do not add hidden restarts or crossover.

### 8.4 Fixed controls

- `legacy_compress`: one legacy-compatible `COMPRESS` with 128 attempts and 480 sweeps per attempt, then STOP, under sufficient matching global caps.
- `pulse_rotate`: bounded compress/expand/near-wall-rotate cycles followed by an explicit bounded COMPRESS, similar to section 6's example.

Evaluate controls on the same banks and profile. Report their costs separately from candidate-generation budgets. The old legacy `run` and `legacy_compress` comparison is a correctness test; control versus other programs is a search-quality experiment.

---

## 9. GPU executor integration

Add a strategy execution path beside the legacy runner, reusing the tested square-contact functions. Do not implement a second independent production collision model. An archival solver snapshot is a test reference only.

Compile a small bounded interpreter/profile family once, then upload validated program data. Do not compile thousands of distinct kernels for evolving candidates. Group tasks by program where practical so adjacent threads tend to follow the same instruction stream, while preserving task identity.

The device owns PC, operation branching, selection, proposal generation, contact loops, local acceptance, rollback, best-state updates, and budget decisions. CPU selects candidates and schedules tasks, not individual square corrections.

Batch capacity remains configurable. A small pilot may have fewer episodes than maximum capacity; launch only actual tasks, not duplicate worlds to fabricate utilization. Do not silently change the statistical sample size to fill the GPU.

Retain enough per-task state to resume slices. Memory estimates and preflight checks must account for three geometry buffers, interpreter continuation, program tables, output, and optional replay buffers. Use bounded queues and reusable arrays, not one Python object or one kernel launch per contact.

Use explicit GPU device resolution and physical UUID provenance. A persistent spawned worker initializes CUDA only after device selection; the API process must not initialize CUDA merely to serve a page. Do not fork a CUDA-initialized process.

No measured improvement claim is required for the new interpreter. Report its overhead relative to legacy compression on a bounded matched workload; the generated strategy path may intentionally do more work.

---

## 10. Application architecture and implementation stack

Use a small monolithic application with clean internal boundaries, not microservices:

```text
Browser / Rich CLI client
         |
   FastAPI HTTP + SSE
         |
   Campaign service + durable catalog + coordinator
         |
   Bounded IPC / task queue
         |
   Spawned Warp/CUDA worker for the selected GPU
         |
   Result chunks -> independent validation -> scoring -> durable events
         |
   Report/replay generation -> existing safe Git publication
```

### Stack

- Existing Python/uv/Warp/NumPy/Rich environment; do not casually upgrade Warp or CUDA.
- FastAPI with validated request/response models and an ASGI server.
- SQLite for the local durable catalog, task/controller checkpoints, and semantic events.
- Existing gzip/NPZ files for scientific arrays and export artifacts.
- Modular HTML/CSS/JavaScript ES modules, served from the application, reusing the current viewer.
- Prefer no Node build pipeline for V1. Do not introduce React/Vite, a general UI framework, or a server-side renderer merely to display forms, tables, charts, and the existing 2D viewer.

Heavy GPU jobs do not run inside HTTP request handlers or a nominal FastAPI `BackgroundTasks` callback. Keep an owned worker/coordinator lifecycle separate from HTTP response lifetime. The framework's documented background-task caveat is relevant, but this local application does not require Celery or Redis. [R1]

SQLite WAL can allow readers while the coordinator writes, but is single-writer and should live on local storage rather than an NFS share. Use short transactions, one coordinator writer, bounded busy timeouts, and the SQLite backup API for snapshots. Do not copy a live database with `cp`. [R3, R4]

Required single-host behavior: one active campaign owns one selected GPU, other requested jobs queue. Persist ownership/lease state. Do not terminate unrelated GPU processes. Report competing workloads and decline an automatic development pilot when resource conflict makes execution unsafe.

---

## 11. Lifecycle, checkpointing, and failure recovery

### 11.1 Campaign state

Expose at least:

```text
DRAFT -> QUEUED -> PREPARING -> RUNNING
                         -> FINALIZING -> COMPLETED
RUNNING -> PAUSE_REQUESTED -> PAUSED -> QUEUED/RUNNING
RUNNING -> STOP_REQUESTED -> FINALIZING -> PARTIAL
any execution state -> INTERRUPTED or FAILED, with retained evidence
```

Scientific status, artifact/report status, replay status, and publication status are separate fields. A failed push is not a failed geometry computation. A numerical failure cannot be hidden by a successful upload.

### 11.2 User controls

- Start submits an immutable manifest and returns a job identity promptly.
- Pause stops new task admission and reaches a documented safe checkpoint. Show PAUSE_REQUESTED while draining.
- Resume uses the same frozen program search state, input bank, and profile.
- Stop finalizes completed evidence and prevents further search work; it is not destructive deletion.
- Clone creates a new draft campaign with editable parameters. Running configurations cannot be edited in place.

V1 may checkpoint at task-group/batch boundaries rather than persisting every in-flight GPU world to disk. On cooperative pause, finish the current bounded evaluation group and record the drain. GPU slices still bound responsive stop observation; an unfinished episode can be separately finalized as cancelled. Document which actions finish versus cancel in-flight work.

On process/server crash, detect stale owned workers using a worker token/lease and process-start identity, not PID alone. Do not reassign a GPU while an orphaned owned worker is still running unchecked. Mark interrupted tasks, reconcile finalized result chunks, and retry only missing work when the user resumes. Do not count retries twice.

Persist search RNG state, candidate pool, current parent, generation/index, pending candidate IDs, evaluated hashes, common bank/profile hashes, and deterministic tie decisions. Never serialize a Python object graph with pickle for resumable untrusted state.

### 11.3 Reproducibility across deployments

Record executable source hashes at worker launch. Running workers must not hot-reload solver files. Before admitting new work, detect incompatible local source/dependency changes; pause/mark the campaign rather than mixing solver versions inside it.

Distinguish cosmetic/report-code changes from numerical executable identity where practical. Do not block a replay solely because a result-only commit advanced HEAD; use relevant source/profile hashes and explicit provenance checks. Never automatically check out or execute code from an uploaded artifact.

---

## 12. Browser UX: first-class acceptance requirements

Do not build a raw JSON editor as the main interface. Use readable forms, consistent units, explicit states, and charts tied to real data. The application must work with the network disabled once its local server is running; no CDN assets, remote fonts, analytics, or external JavaScript dependencies.

### 12.1 Campaign list and overview

Show name, `n`, methods, state, device, candidate/episode counts, training winner, holdout status, age, and publication state. Support simple filtering and pagination. An empty installation explains how to start the first experiment; do not populate fake successes.

### 12.2 New campaign form

Expose ordinary settings first, advanced settings separately:

- Name and optional description.
- Square count and initial side.
- Random, mutation-guided, or compare-both mode.
- Candidate budget, initial pool, lambda where applicable, and search seed.
- Training/holdout bank sizes and initializer/operator seeds.
- Available opcodes, selector choices, generation/mutation ranges and probabilities.
- Fixed evaluator profile and work caps, visually distinguished from evolved parameters.
- Explicit detected GPU, batch capacity, execution wall budget, and resource warnings.
- Replay policy and storage budget.
- Publication enabled by default; a visible local-only option.

Validate before queueing and show a plan summary: logical candidate evaluations, episode count, configured upper bounds, approximate storage, and what will be replayed. Do not invent an execution-time forecast before obtaining a relevant pilot.

### 12.3 Running campaign

Show real completed counts, active phase, current arm/generation, device, elapsed time, measured rates, best independently validated packing, current best training score, validation/error counts, and remaining configured budget.

Progress only advances when the represented work is complete. During a long slice/group, show activity and elapsed time, not fabricated intra-kernel percentages. Clearly distinguish a program's best individual packing from its mean score across starts.

### 12.4 Program explorer

For every candidate show a readable instruction listing, operator parameters/units, selectors, conditions, compiled/source mapping, hash, parent, mutation description, eligibility, evaluation completeness, and results.

Provide parent/child diffs highlighting changed operations and values. For random search, label a program as independently generated rather than inventing a parent. Users can clone an inspected program into a fixed-program evaluation draft. A complex drag-and-drop editor is not required.

### 12.5 Comparison view

Display fixed controls and both search arms with matched-scope warnings. Include quality distributions and paired per-start differences, training/holdout separation, success thresholds with counts, and quality-versus-evaluation/work/time curves.

A comparison must show `n`, dataset, profile, compiler/source identity, candidate/episode counts, device and timing scope. Do not place unlike workloads in one speedup table without warnings.

Charts must expose actual values on selection/hover and allow opening the corresponding program or episode. Use real timestamps/work coordinates, not evenly spaced points falsely labeled as time. Do not use an unlabeled 3D chart or decorative animation instead of readable diagnostics.

### 12.6 Campaign-history replay

Implement a time/index slider over durable semantic events. Selecting an event reconstructs the known state at that point: generated candidate, mutation, result, parent replacement/rejection, and incumbent curve.

For `(1 + lambda)`, show the parent and offspring group, not a fictitious large population. Record discarded children too. Show why the ranking chose a winner, with its compared score tuple. Random search shows candidate order and incumbent changes.

This is a replay of search decisions, separate from the replay of square motion. The history must remain usable after server restart and in an exported report.

---

## 13. Geometric replay and trace requirements

### 13.1 Reuse and extend the existing viewer

Preserve initial/current panels, square IDs/colors, orientation ticks, pan/zoom, fit-current/fit-full-trajectory, selection, dimming, center trails, last-K trace length, range playback, and on-demand SVG export.

Add:

- The strategy program beside the board, with active instruction and source node highlighted.
- Selected-object mask and operator parameters at invocation.
- Operator phase, attempt/sweep indices, and outcome.
- Current `L`, protected best `L`, and consumed work.
- A synchronized graph of current and best `L` against recorded logical progress.
- Explicit markers for proposal, repair, commit, rejection, rollback, best update, restore-best, yield, and finalization where relevant.
- A “go to best state” action separate from “go to final current state”.

Differentiate accepted and provisional geometry. Rejected trials may visibly overlap; that is not an accepted packing. A jump caused by rollback/restore is drawn as a discontinuity, not a continuous physical path. No interpolation is enabled by default. Dots represent stored states, not physical velocity.

Two-program comparison must use the same initial-world identity. Support synchronization by recorded frame, normalized consumed work, or independent stepping with the mode labeled. Do not imply that equal frame indices mean equal algorithmic work.

### 13.2 Replay identity and numerical verification

A trace requires more than the old `(seed, trial_id)` pair. Include program hash/bytecode, operator version, evaluation profile, initial-bank identity/actual state, operator seed/replicate, source hashes, precision, and environment.

Replay selected episodes on the same declared inputs, then compare original best/current endpoints, status, budgets/counters, RNG identity, and defined numerical fields. Adding instrumentation must not silently change the algorithm. Existing endpoint match statuses should be reused/extended.

`REPLAY_MATCHED` means the declared comparison passed; it is not proof of every unrecorded intermediate state. Mismatch or incomplete reference remains clearly visible and cannot replace the scientific result. Store the actual diagnostic replay separately. Never forge the original terminal frame by appending the old pose to a mismatching replay.

### 13.3 Bounded capture policy

Ordinary search runs without dense trajectory recording. After evaluation, schedule bounded selected replays; on-demand replays are queued separately and do not interrupt a GPU task arbitrarily.

Every successful campaign automatically produces at least these replay categories when available:

- Both fixed controls on one shared representative training start.
- Each arm's frozen winner on that same start.
- One informative winner-versus-parent mutation comparison, when a parent replacement occurred.

Deduplicate identical requested episode keys. Default maximum: 8 geometric traces per campaign, 256 frames per trace, and 10 MiB for the complete trace export collection including embedded HTML and metadata. User-requested later collections have separate explicit limits. A small valid budget may limit output; show what was omitted rather than silently raising it.

Accepted mode captures the real initial state, accepted compression substeps, accepted operator boundaries, restore transitions, selected best state, and final endpoint. Full-resolution operation summaries are bounded by the program/work limits; geometric frames may be compacted.

Sweeps mode records a sample, default every 16 completed sweeps, plus key transaction roles. Use deterministic bounded compaction preserving start, final, and best snapshots. Event-only metadata must still represent omitted operator boundaries. Reserve frame capacity for these endpoints or retain separately referenced endpoint arrays. Do not drop the actual best state simply because the recording buffer filled.

No one-JSON-per-frame output, no SVG-per-sweep export, and no streaming of every GPU world to the browser.

### 13.4 Compact and compatible schema

Extend trajectory v1 with a versioned strategy-trace schema or a documented optional extension while preserving old readers. Reuse `.npz` for primitive arrays and `.meta.json.gz` for compact metadata. A compressed NumPy archive already compresses numeric arrays; do not gzip it again. [R6]

Include bounded arrays for poses, current/best side, instruction index/source node, operator phase, selector mask, logical sequence, work indices, and role flags. Keep exact FP32 geometry and exact integer identities. No lossy decimals or angle normalization.

Load with `allow_pickle=False`; validate ZIP/NPY headers, decompressed sizes, shapes, dtypes, checksums, and index bounds before allocation. Use decimal string identifiers in browser JSON. Native files remain the source of truth; bounded view data may be supplied as JSON for convenience.

---

## 14. Rich CLI and HTTP interface

### 14.1 Target commands

Provide a coherent subcommand family; exact spelling below is the desired interface, not a claim that it exists today:

```bash
uv run asquerix lab serve --host 127.0.0.1 --port 8765
uv run asquerix lab submit --config examples/lab/n11-compare.json
uv run asquerix lab watch CAMPAIGN_ID
uv run asquerix lab status CAMPAIGN_ID
uv run asquerix lab pause CAMPAIGN_ID
uv run asquerix lab resume CAMPAIGN_ID
uv run asquerix lab stop CAMPAIGN_ID
uv run asquerix lab report CAMPAIGN_ID
uv run asquerix lab export CAMPAIGN_ID --output runs/lab-export
```

CLI clients and the browser use the same campaign service and validation rules. Do not duplicate a second algorithm implementation inside command handlers. `serve` starts the owned service lifecycle and prints a useful address; it does not launch a browser automatically.

Rich views show method/iteration, candidate and episode progress, incumbent quality, best validated `L`, work/time, worker state, replay/export, and publication. Reuse existing TTY/plain behavior. The project-specific `--json` mode disables Rich, saves structured reports to disk, and prints concise statuses/paths, not payloads. HTTP API JSON responses are expected and do not conflict with this console rule. [R7]

### 14.2 API contract

Use versioned endpoints and stable schema names. At minimum:

| Method / endpoint | Purpose |
|---|---|
| `GET /api/v1/capabilities` | Operators, selectors, parameter limits, profiles, supported methods, schema versions. |
| `GET /api/v1/devices` | Detected GPUs and owned-job state, with physical identity. |
| `POST /api/v1/programs/validate` | Typed validation, compilation, hash, source map, bounded diagnostics. |
| `POST /api/v1/campaigns` | Validate/freeze/queue a campaign; return 202 and its identity. |
| `GET /api/v1/campaigns` | Paginated campaign catalog. |
| `GET /api/v1/campaigns/{id}` | Current state and aggregate statistics. |
| `POST /api/v1/campaigns/{id}/pause|resume|stop|clone` | Explicit lifecycle changes. |
| `GET /api/v1/campaigns/{id}/events` | Resumable SSE notifications. |
| `GET /api/v1/campaigns/{id}/history` | Paginated durable semantic history for replay. |
| `GET /api/v1/campaigns/{id}/programs` | Candidate scores and genealogy, paginated. |
| `GET /api/v1/programs/{hash}` | Program, source map, and semantics. |
| `GET /api/v1/campaigns/{id}/episodes` | Filtered results and reference availability. |
| `POST /api/v1/campaigns/{id}/replays` | Queue selected replay with size/frame limits. |
| `GET /api/v1/replays/{id}` | Status, validation/provenance, and bounded viewer data links. |
| `GET /api/v1/artifacts/{id}` | Allowlisted artifact download by identity, not arbitrary filesystem path. |

Mutating requests need an idempotency key or equivalent deduplication token. Browser reconnect/retry must not launch duplicate campaigns. Return clear 4xx errors for invalid programs and conflicts. No API endpoint may execute uploaded Python, shell commands, Git refs, or arbitrary file paths.

### 14.3 SSE and backpressure

Use Server-Sent Events for one-way progress and ordinary HTTP for commands. Persist monotonic event IDs and support `Last-Event-ID`; the browser must deduplicate at-least-once deliveries and recover from reconnects. If a cursor is too old, return a documented reset/snapshot flow rather than silently losing history. [R2]

Coalesce frequent progress updates; durable semantic events such as candidate result and parent replacement are not discarded. SSE heartbeat timing is independent of scientific progress. A slow or closed browser must never block a worker or require an unbounded memory queue.

---

## 15. Storage, evidence, publication, and security

### 15.1 Durable catalog and artifacts

Catalog entities should cover campaigns, arms, datasets, programs, candidates/lineage, evaluation tasks, aggregate results, replay jobs, artifacts, semantic events, worker leases, and publication receipts. Choose a compact schema; do not put every trajectory coordinate into relational rows.

Proposed campaign export contents:

```text
campaign/
  campaign.json.gz
  environment.json.gz
  initial-bank.npz
  programs.jsonl.gz
  genealogy.jsonl.gz
  events.jsonl.gz
  evaluations/
    part-0000.jsonl.gz
    best-poses-0000.npz
  summaries.json.gz
  report.md
  report.html
  charts/*.svg
  trajectories/
    episode-<key>.npz
    episode-<key>.meta.json.gz
    episode-<key>.html
  manifest.json.gz
```

Every completed V1 evaluation used for ranking must retain its actual best pose and terminal current pose in bounded chunked arrays, so arbitrary selected episodes have references for replay. Retain the corresponding defined result fields, counters, and RNG identity as well. Do not save only a minimum `L` then claim a replay is fully verified. Initial-bank and final-pose storage are much smaller than full trajectories, but still preflight their size.

Use existing atomic persistence, gzip level 3, and historical-reader support. JSON/JSONL is compressed; NPZ is already compressed. Markdown, CSV, SVG, HTML, and source code remain directly usable. Publish neither a live SQLite database nor its WAL files; export finalized data and an optional proper backup snapshot for local recovery.

### 15.2 Bounded storage

Estimate output before admission. Default campaign artifact ceiling: 256 MiB, with the trace collection capped separately at 10 MiB. The application must respect current publication limits as an additional constraint. Allow explicit user overrides within supported safety limits; never silently raise a quota.

Stream evaluation records into bounded chunks, close each independently, and checkpoint manifests. Do not accumulate an unbounded Python list or one incompressible giant browser payload. Disk-full errors stop admission, preserve finalized chunks, and produce an honest partial/failed state.

Keep all program definitions and per-candidate summaries for the bounded campaign. This is the history needed for later inspection. Do not silently discard losing candidates or mutation failures merely because they are not on a leaderboard. Compact repetitive progress, not scientific decisions.

Offline `report.html` must include campaign charts/history and embedded selected replays, or an explicitly packaged relative-asset directory that works under `file://` without browser fetch restrictions. Prefer a self-contained report for the bounded default data size. Test with networking disabled; merely linking to the API is not an offline report.

### 15.3 Publication

Normally completed campaigns attempt the existing safe publication after evaluation, bounded automatic replays, and report finalization. A user stop or elapsed execution deadline must not start new compute-heavy replay or holdout jobs: preserve completed traces, mark remaining replays as available on demand, and finalize the partial report and publication. Do not hide a second GPU workload inside graceful stopping. Use one publication per campaign, not a Git commit per frame or candidate. Respect `--no-push`/local-only configuration.

Extend artifact manifests and allowlists narrowly for the laboratory output. Preserve source revision versus result-commit identity, publication locks, explicit artifact paths, retry bounds, and remote fast-forward safety. Large/private native profiling files and scratch data remain local with manifest hashes when needed.

Runtime results may advance remote `main` without changing the active checkout. Do not attempt to overwrite that history when committing implementation changes. Inspect and safely reconcile actual remote advances according to existing project conventions.

### 15.4 Single-user security baseline

Bind to loopback by default. Remote/LAN mode must be explicit and require configured authentication; document TLS/reverse-proxy or an existing secure access path rather than exposing an unauthenticated compute API.

Use validated Host/Origin handling, same-origin credentials, and CSRF protection for cookie-authenticated mutations. CORS is not authentication. Do not put long-lived secrets in URLs, published logs, manifests, or source files. Use parameterized database queries, escaped text rendering, allowlisted artifact paths, upload limits, bounded decompression, and schema validation.

Do not execute historical source code embedded in artifacts or open untrusted HTML in the privileged application origin. Generated viewer content must be controlled and escaped; imported HTML should be served as a download or sandboxed appropriately. No automatic deletion/reset endpoints are required in V1.

---

## 16. Reference campaign specification

The following is a proposed accepted configuration shape. Implement this shape or a documented equivalent and provide a working checked-in example; do not leave examples inconsistent with the actual parser.

```json
{
  "schema": "asquerix-lab-campaign-v1",
  "name": "n11-random-vs-mutation-pilot",
  "n": 11,
  "initial_side": 10.0,
  "device": "cuda:0",
  "batch_capacity": 4096,
  "datasets": {
    "initializer_seed": "20261008",
    "training": {"first_id": "100000", "valid_count": 64},
    "holdout": {"first_id": "200000", "valid_count": 64}
  },
  "operator_seed": "20261009",
  "operator_replicates": 1,
  "evaluation_profile": "rigid-square-lab-v1",
  "controls": ["legacy_compress", "pulse_rotate"],
  "search": {
    "methods": ["random_program_search", "one_plus_lambda"],
    "seed": "8001",
    "candidate_budget_per_method": 32,
    "initial_pool": 8,
    "lambda": 8,
    "shared_initial_pool": true
  },
  "recording": {
    "automatic": true,
    "mode": "accepted",
    "max_traces": 8,
    "max_frames_per_trace": 256,
    "max_trace_mib": 10
  },
  "limits": {"max_seconds": 600, "max_artifact_mib": 256},
  "publication": {"enabled": false}
}
```

`cuda:0` is an example local selector. Resolve and persist the physical UUID before execution. Development evidence is local-only until final compact artifacts are committed. User-facing normal campaigns default to publication enabled.

The example has 8 initial candidates and three offspring rounds of 8 for mutation search: 32 total. Random search receives the same candidate count and common initial candidate pool. Both still perform their own pilot evaluations. Two controls evaluated once plus 32 + 32 candidates on 64 starts gives 4,224 logical training episodes. Final frozen winners plus controls on 64 holdout starts adds up to 256 episodes before deduplication; report any deliberate deduplication separately.

A deadline can produce a partial campaign. It must not silently lower sweeps, omit difficult starts, or shrink the bank to claim completion. Use smaller explicitly named smoke profiles before this pilot.

---

## 17. Required testing and evidence

### A. Program/schema/compiler tests

Unknown opcodes/selectors, nonfinite parameters, 100% compression, negative/bool budgets, integer overflow, invalid jumps, backwards control flow, excessive repetition/depth, malformed bytecode, source-map round trips, deterministic hashing, and duplicate generation.

Property-style generation/mutation tests must show that accepted programs fit their bounds and terminate in a control-flow oracle. These tests do not substitute for geometric CUDA execution.

### B. Real operator tests

Use known feasible fixtures and adversarial contacts. Verify expansion changes only `L`; per-object random proposals are reproducible; joint proposals repair or fully roll back; unselected squares remain mobile; empty selections terminate; `WALL_K` works after expansion; best never worsens; restore does not refund RNG/work; and compression retains successful substeps.

Test the effective final target step and the legacy step-floor correction. Check no implicit compression in STOP/finalization or expansion-only programs. Confirm RELAX's declared feasible-state behavior.

### C. GPU/VM regression

Legacy-compatible compression matches the frozen current solver on `n=1,4,11,12,16,32`, multiple seeds, and diagnostic `n=11` IDs 4124 and 4372 where references are compatible. Check defined bytes, counters, status mapping, and independent float64 validation.

Test resumable execution with different slice limits, batches, program grouping, and nonzero/high uint64 identifiers. Pause/yield does not change output or RNG. Check global budgets exhausted within every opcode, in-progress proposals, cancellation, malformed input, and initialization failure.

A mock worker is allowed for server unit tests but may not be presented as a successful GPU laboratory.

### D. Scoring/search tests

Same common initial arrays for both methods; deterministic candidate generation; bounded duplicate retries; correct parent-plus-offspring selection; no selection from incomplete/invalid results; stable generation barriers; exact resume of search RNG/controller state; no holdout feedback; and correct logical/executed/cache/replay accounting.

An expansion-only strategy must score its actual unchanged best initial `L`. One lucky excellent episode must not be substituted for the program's declared mean score. Failed episodes must not disappear from denominators.

### E. API/catalog/recovery tests

Request validation, idempotent submission, pagination, event reconnection, stale cursor recovery, slow-client backpressure, browser disconnect while computation continues, catalog restart, stale leases, interrupted task retry without duplicate results, safe paths, escaped inputs, quota/disk failures, authentication/Origin checks, and SQLite backup/migration integrity.

Use temporary repositories/remotes to test publication. Do not push simulated test campaigns into production GitHub history.

### F. Browser and visualization tests — release blockers

Use available headless Chromium/browser tooling and retain compact evidence. Exercise actual UI actions, not just check HTML strings:

1. Create and submit a small campaign through forms.
2. Close/reopen the page and see the same campaign continue.
3. Inspect a program and its mutation diff.
4. Open real recorded geometry; play, pause, scrub, zoom, pan, select a square, and inspect its trail.
5. Verify the highlighted instruction and phase correspond to actual frame metadata.
6. Exercise rollback/restore markers and different current/best sides.
7. Compare two programs on the same start.
8. Replay campaign history and see the corresponding incumbent/program state.
9. Open the exported report with network disabled and play its selected trajectories.
10. Verify old trajectory files still render with existing controls and no console errors.

Screenshots and a concise interaction log are required. Do not fabricate visual test success when no browser executed.

### G. Bounded scientific pilot

Proceed in this order:

1. Tiny CPU/API/compiler tests and CUDA operator smoke tests.
2. A three-program `n=11` evaluation: legacy control, handwritten control, one generated program on 64 shared starts; validate all 192 returned best results.
3. The two-method comparison in section 16 with 64 training and 64 holdout starts, or an explicitly smaller pilot if the scheduling limit interrupts it. Preserve the partial outcome rather than pretending the large pilot finished.
4. Small `n=12` and `n=16` controls, e.g. 16 starts each, to verify configurability and no special-casing of the research case.
5. At least one ordinary browser-started campaign with actual search, recorded mutation decisions, real replays, and offline export.

Use the accessible selected GPU, beginning on RTX 4070 Ti when that is the development machine. Do not require access to both RTX 4090 cards to finish V1. Do not stop competing user workloads or rerun an hours-long saturation benchmark without need.

Measure legacy-path overhead with recording disabled and report it separately from strategy cost. Preserve actual timing scopes: JIT, warm-up, GPU execution, transfers, validation, scoring, persistence, replay, report, publication, and total wall time. Profiled/test runs are not peak-throughput benchmarks.

---

## 18. Failure modes and engineering priorities

| Risk | Required mitigation |
|---|---|
| A fast executor returns invalid or altered geometry | Independent validator, protected best, fixed numerical profile, bytewise references. |
| VM/instrumentation changes compiler rounding | Preserve operand barriers; compare actual CUDA outputs after each meaningful refactor. |
| An operation budget is reset at every invocation | Global cumulative counters; charge before work; no refunds on rollback/restore. |
| Slice boundaries change program behavior | Persist complete continuation and test multiple slice sizes. |
| Search selects programs adapted to a few starts | Fixed training bank, untouched holdout, separate campaign seeds, honest uncertainty. |
| Mutations never change semantics | Compiled-program deduplication, declared mutation distribution, rejected-proposal records. |
| Large central holes are mistaken for a collision bug | Display contacts/motion as evidence; validity and local search capability remain different. |
| One arm gets more computation or a cheaper audit policy | Identical profile/banks, explicit cost accounting, matched pilot policy. |
| Rich or browser disconnect blocks computation | Independent worker/service and bounded event queues. |
| Database/UI overhead starves the worker | Batch result ingestion, short transactions, paginated queries; measure before rewriting. |
| Artifact size grows with every sweep | Selected replay, chunked final poses, bounded frames and quotas. |
| Endpoint-only recording hides operator behavior | Operator source-map/phase/mask overlay, provisional-event mode, bounded detailed replay. |
| A mismatching replay looks like the original | Explicit mismatch badge and separate diagnostic output; never replace science. |
| A server restart replays completed experiments as new results | Stable episode keys, durable task attempts, atomic result admission, deterministic resume. |
| Concurrent commits/results collide | Existing main-only publication lock/index policy; explicit paths and remote checks. |
| A new framework overwhelms the core task | Simple FastAPI/SQLite/ES-module application; reuse existing viewer and geometry. |

Optimization comes after correct visible behavior. Candidate future targets are program grouping, bounded result ingestion, cached immutable program/dataset uploads, repeated geometry work verified at the compiler level, and independent-device scheduling. Do not optimize by dropping failed trials, weakening checks, simplifying strategies behind the user's back, or hiding publication/validation time.

---

## 19. Implementation milestones and acceptance gates

### M0 — Inspect and freeze

Record local/remote state, relevant source hashes, installed environment, existing viewer modules, and a small current-solver reference. Reconcile this PRD with the latest code without losing concurrent edits. Update project scope documentation for the authorized extension.

### M1 — One real vertical slice

A browser submits a fixed compression program to the durable service; a CUDA worker runs it; the UI shows real results and a playable trajectory using the existing viewer. No fake progress and no placeholder data. This is deliberately early so visualization cannot be postponed until the end.

### M2 — Complete rigid-square executor

Implement all required opcodes/selectors/conditions, three-state semantics, bounded compiler, work accounting, slices, and actual CUDA regressions. Legacy compression compatibility passes.

### M3 — Evaluation and two search methods

Common input banks, independent CPU ranking checks, random search, `(1 + lambda)` search, fixed controls, holdout separation, reproducible controller checkpoints, and fair comparison.

### M4 — Full inspection workflow

Program/parent-child views, campaign-history replay, geometric replay with active-instruction overlay and best/current charts, paired-program viewer, bounded automatic selections, offline export, and Rich watch/status.

### M5 — Robustness, evidence, and publication

Exercise reconnect, pause/stop/resume, crash recovery, quotas, security, historical compatibility, actual browser tests, and the bounded pilot. Produce README commands, implementation report, compact evidence, and tested commits on `main`. Verify the remote SHA and report any remaining limits precisely.

The application is not complete if only the HTTP API works, if search uses a dummy evaluator, if trajectories show only start/end, or if generated programs cannot be inspected and replayed.

---

## 20. Final delivery checklist for Codex

- [ ] Existing Asquerix commands and historical artifacts remain usable.
- [ ] One global strategy controls each world; no hidden compression or per-square program.
- [ ] Actual Warp/CUDA execution of the allowed operations, not CPU simulation disguised as a GPU task.
- [ ] Three geometry states and correct rollback/RNG/budget behavior.
- [ ] Finite control flow and resumable bounded work.
- [ ] Random and mutation-guided search both execute and produce inspectable candidates.
- [ ] Initial banks, budgets, validation, and ranking are controlled and recorded.
- [ ] Browser forms, campaign list, progress, program diffs, comparison, and event-history replay work.
- [ ] Selected actual trajectories have traces, zoom, instruction overlay, and explicit accepted/provisional states.
- [ ] Offline report playback works without an API server or network.
- [ ] Rich CLI is readable; `--json` writes artifacts without payload floods.
- [ ] Restart/reconnect/stop handling preserves data and does not duplicate scientific counts.
- [ ] Artifacts are bounded, compressed appropriately, and published safely according to user settings.
- [ ] Real CUDA and browser tests were executed; unavailable tests are not claimed as passed.
- [ ] A bounded end-to-end pilot and its honest results are saved.
- [ ] Only tested task changes and compact evidence are committed/pushed to `main`.

The final user response must include actual commit SHA, tested startup command and local URL, example campaign command/config, test pass/fail/skip counts, measured pilot completion, report/replay paths, publication status, and remaining limitations. Do not claim discovery of a better packing or superiority of mutation search unless the saved experiment supports it.

**Begin implementation. Deliver the working laboratory, not another design-only document.**

---

## 21. Source notes and design provenance

The requirements above are the agreed product design, not a claim that these features already exist. Existing-project statements are grounded in the inspected snapshot; proposed defaults and interfaces are explicitly new requirements. This PRD makes no new mathematical optimality claims.

### Project sources inspected on 2026-10-09

- **[P1] Current project instructions:** [AGENTS.md at afa10b1](https://github.com/hipotures/asquerix/blob/afa10b10802e46a4d16a1f56120295c685c908d0/AGENTS.md).
- **[P2] Existing CLI, persistence, publication, and trajectory contracts:** [README.md at afa10b1](https://github.com/hipotures/asquerix/blob/afa10b10802e46a4d16a1f56120295c685c908d0/README.md).
- **[P3] Existing numerical kernel:** [gpu.py at afa10b1](https://github.com/hipotures/asquerix/blob/afa10b10802e46a4d16a1f56120295c685c908d0/src/asquerix/gpu.py).
- **[P4] Existing project modules:** [src/asquerix at afa10b1](https://github.com/hipotures/asquerix/tree/afa10b10802e46a4d16a1f56120295c685c908d0/src/asquerix).
- Earlier user-approved design: `ASQUERIX_EVOLVING_STRATEGY_PROGRAMS_DESIGN.md`, version 0.1, and the selective trajectory-replay specification. Their broader future scope is not a requirement to implement morphing or full population evolution in V1.

### Primary technical references

- **[R1] FastAPI:** [Background tasks and the heavy-computation caveat](https://fastapi.tiangolo.com/tutorial/background-tasks/). Used only to justify separating heavy execution from HTTP request handling; the owned local worker design is a project decision.
- **[R2] WHATWG HTML:** [Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html). EventSource delivery, UTF-8 event framing, reconnects, and Last-Event-ID. Durable storage and application-level deduplication are additional project requirements.
- **[R3] SQLite:** [Write-ahead logging](https://www.sqlite.org/wal.html). Local shared-memory constraints and the single-writer model.
- **[R4] SQLite:** [Online Backup API](https://www.sqlite.org/backup.html). Safe live-database snapshots.
- **[R5] DEAP documentation:** [Algorithms](https://deap.readthedocs.io/en/master/api/algo.html). Parent-plus-offspring selection and ask–tell terminology; this PRD does not prescribe DEAP or its CMA-ES implementation.
- **[R6] NumPy:** [savez_compressed](https://numpy.org/doc/stable/reference/generated/numpy.savez_compressed.html). Compact multi-array archives; all safety/size limits remain application requirements.
- **[R7] Rich:** [Progress display](https://rich.readthedocs.io/en/latest/progress.html). Multiple tasks and configurable progress presentation.

Inspect installed APIs and current compatible releases before adding dependencies. Do not infer compatibility solely from a moving documentation URL, and do not change the locked numerical environment without a separate regression decision.
