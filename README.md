# Asquerix

A standalone NVIDIA Warp proof of concept for wall-driven quasistatic compression of freely translating and rotating unit squares. Every integer `1 <= n <= 32` is supported. `n` counts squares in one world, `trials` counts independent worlds, and `batch_size` counts worlds submitted together.

This searches for feasible constructions and potential **upper bounds**. Stagnation and unsuccessful searches establish neither lower bounds nor optimality. Float64 validation is a numerical check, not a rigorous certificate.

## Setup and tested commands

Tested versions: Python 3.14.7, Warp 1.18.0, NumPy 2.5.3, Rich 14.3.4, pytest 9.1.1. Install the isolated environment from the checked-in lock:

```bash
uv sync --locked
uv run asquerix diagnose
uv run pytest -q
```

The default Warp wheel uses CUDA 13.4 and requires an R580 or newer driver and a Turing or newer GPU. Earlier measurements used a display-attached RTX 4070 Ti with 12,282 MiB memory. The latest campaign used two physical RTX 4090 cards with 24,564 MiB each and driver 615.71.09. No driver changes were made. Wheel URLs and hashes are in `uv.lock`. See [official compatibility documentation](https://nvidia.github.io/warp/stable/user_guide/compatibility.html).

CUDA tests explicitly skip when CUDA is unavailable; independent CPU tests still run. GPU runs fail with a diagnostic rather than substituting CPU execution. In the original Codex sandbox `/dev/nvidia*` was hidden; authorized execution outside that sandbox exposed the GPU.

A short run retains and independently checks every pose:

```bash
uv run asquerix run --n 12 --trials 8 --batch-size 8 --retain-all --sample-every 0 --max-images 3 --max-seconds 30 --output runs/short
uv run asquerix validate runs/short
uv run asquerix render runs/short --output runs/short-rerender --max-images 3
uv run asquerix report runs/short
```

Run directories must not already exist, to protect previous results. Offline commands use saved coordinates without running or repairing a simulation.

Integer CLI options accept case-insensitive binary suffixes: `k = 1024`, `m = 1048576`, and `g = 1073741824`. For example, `--trials 1m --batch-size 64k` requests 1,048,576 trials in batches of at most 65,536. `65k` means 66,560; plain `65000` remains 65,000. Fractional prefixes are accepted only when they expand to a whole number (`1.5k = 1536`). Saved configurations contain the expanded integers. The batch-size limit is 1,048,576, so both `--batch-size 1000000` and `--batch-size 1m` are accepted. Large batches allocate storage for every world and require sufficient GPU memory.

A longer, explicitly user-initiated search:

```bash
uv run asquerix run --n 12 --trials 12288 --batch-size 512 --seed 20261008 --trial-offset 0 --sample-every 1024 --audit-size 64 --keep-best 10 --max-images 3 --max-seconds 120 --output runs/long
```

This is the solver and runner configuration exercised by the extended measurements: three complete 12,288-trial runs, each with more than 28 seconds of timed GPU work. The runtime limit applies to scheduling after setup and warm-up. An already submitted batch drains before saving results. Elapsed time, deadline overrun, and stopping drain are recorded. Ctrl-C stops new batches and preserves completed output. Change `trial_offset` to use a new global trial range.

Reproduce the bounded pilot and compare runs:

```bash
uv run python -m asquerix.pilot --output runs/pilot --max-seconds 300
uv run asquerix compare runs/pilot/sweep-b8 runs/pilot/sweep-b32 runs/pilot/sweep-b128 runs/pilot/sweep-b512
```

The pilot uses identical seed, global trial IDs, initializer, tolerances, and full budgets for the `n=12` sweep. It checks scalar partition equality, chooses the measured fastest size, repeats it three times, and runs `n=11,16` controls. Tiny control runs audit every pose first. All loops are bounded; a wall limit stops scheduling rather than cancelling an in-flight kernel.

The short high-throughput measurements in that initial sweep are preliminary. The principal throughput result uses three longer matched runs. Reproduce those with fresh destinations:

```bash
uv run python tools/extended_benchmark.py --output runs/extended-archive-new --runs-output runs/extended-new
```

The extended script preserves every scalar record in gzip archives, with uncompressed SHA-256 hashes. New run directories under `runs/` use gzip JSON/JSONL. See [the measured report](artifacts/pilot/REPORT.md) for durations, variability, audit coverage, and limitations.

The completed first CUDA optimization campaign froze revision `d4ec238`, including the `eb8d2ac` minimum-step correction. See [its historical report](artifacts/performance/cuda-20261009/REPORT.md). The new reference already includes that accepted optimization: production `d5ea525`, archived with its source hash in [the dual-4090 report](artifacts/performance/dual4090-20261009T005128Z/REPORT.md). It measures actual concurrent execution, full bytewise output equality, CPU/native waiting, and the ordinary result-saving pipeline. No additional kernel candidate was retained. Explicit lossless gzip level 3 improved ordinary-pipeline throughput at fixed kernel/device count; new run metadata records this policy.

```bash
uv run --locked pytest -q
uv run --frozen python tools/kernel_benchmark.py compare \
  --reference artifacts/performance/dual4090-20261009T005128Z/corpus-A \
  --source src/asquerix/gpu.py --device cuda:0 --output runs/kernel-exact-check.json.gz
uv run --frozen python tools/kernel_benchmark.py benchmark \
  --baseline-source artifacts/performance/dual4090-20261009T005128Z/baseline/gpu.py \
  --device cuda:0 --count 131072 --repeats 3 --output runs/kernel-benchmark-new
```

The benchmark tool never publishes experiments. Its frozen source is an archival comparison reference; production retains one solver. `axes()` shares the existing standard sine/cosine evaluations and uses bit-preserving CUDA operand copies to retain the original SAT rounding behavior. No fast math, tolerance, contact ordering, or stopping criterion changes are enabled.

## Geometry and numerical method

The container is `[-L/2,L/2]^2`. A pose is `(x,y,theta)`, with radians and square side exactly one. With `u=(cos(theta),sin(theta))`, `v=(-sin(theta),cos(theta))`, vertices are `c +/- u/2 +/- v/2`. Projection support is `h(theta,a)=(abs(u.a)+abs(v.a))/2` for a unit axis `a`. The exact SAT signed separation is:

```text
g = max over u_i,v_i,u_j,v_j of abs((c_j-c_i).a) - h_i(a) - h_j(a)
```

Nonnegative `g` means disjoint interiors in exact arithmetic, with equality permitting contact. Wall clearance is separate. Every pair is checked.

Initialization uses bounded rejection sampling on the GPU. Centers are at least `sqrt(2)/2 + guard` from initial walls; squared center distances must be at least `2 + 4*guard`. Orientations are sampled from `[0,pi/2)`. This is conservative and does not sample all feasible packings uniformly. Dense requests can return `INIT_FAILED` despite the existence of a packing. This initializer requires `initial_side > sqrt(2)+2*guard`. No automatic resizing or grid substitution occurs.

Compression proposes `L-step` without rescaling centers. Sequential contact sweeps project constraints into translation and rotation coordinates. The gradient includes derivatives of the moving SAT axis and support functions. For axis owner `i`:

```text
d = c_j-c_i, a_perp = (-a_y,a_x), sigma = sign(d.a)
D_j = (sign(u_j.a)*(v_j.a) - sign(v_j.a)*(u_j.a))/2
gradient_c_i = -sigma*a, gradient_c_j = sigma*a
gradient_theta_i = sigma*(d.a_perp) + D_j
gradient_theta_j = -D_j
```

The projection scalar is `(guard-g)/(sum of mobility-weighted squared gradients)`, multiplied by relaxation `0.8`. Translation mobility is one, angular mobility `0.3`. Corrections are capped at `0.1` length units and `0.08` radians per body/contact. These are numerical mobilities, not inertial dynamics. Geometry is recomputed after updates and every sweep.

Axes tied within `1e-6` have averaged gradients; support cusps use zero derivative within `1e-6`. Symmetric aligned face contacts have zero torque; asymmetric contacts can translate and rotate. Coincident centers use deterministic axis/sign choices. Tests check derivatives for both axis owners against finite differences.

Search uses FP32 with fast math disabled. Default `guard=2e-5` is separate from `acceptance_tolerance=2e-6`. Acceptance requires raw pair and wall clearances at least `1.8e-5`. The unit-square geometry, clearance target, residual tolerance, and independent validation policy are distinct.

Budgets: 2000 proposals per square, 128 compression attempts, 120 sweeps per attempt. Failure restores all accepted pose components and the previous side, then halves the initial `0.2` step, clamped to a `1e-4` floor. The floor is attempted within the remaining budget; successful floor steps continue until a floor attempt fails or the budget is exhausted. Accepted sides are nonincreasing. Four consecutive sweeps with maximum individual correction at most `1e-7` mark relaxation stagnation. This conservative motion measure cannot cancel signed corrections; feasibility is checked separately.

Termination reasons include `STEP_FLOOR_REACHED`, `STAGNATED`, `BUDGET_EXHAUSTED`, `INIT_FAILED`, and `NUMERICAL_FAILURE`. A feasible pose may exhaust its budget. Transient overlaps are search residuals; continuous collision-free trajectories between corrections are not established.

## GPU mapping and reproducibility

One CUDA thread owns a world, with block size 32 and preallocated `(square,world)` pose/rollback storage. A fixed batch submission uses kernels of at most 16 compression attempts, retaining state on the device: eight kernels for the default budget. The host submits this predetermined sequence and reads nothing until the batch finishes. Initialization, relaxation, compression decisions, acceptance, and rollback are on the GPU. No per-trial GPU launches or per-contact/sweep host synchronization occurs. CUDA events measure total work and maximum stage duration.

All trials transfer compact scalar records. Selected poses use a batched GPU gather. Selection retains the independent numerical leaderboard, global-ID periodic samples, a bounded reproducible random audit sample, and bounded failure examples. Checked valid or indeterminate candidates remain saved after a later candidate supersedes them; `keep_best` caps the leaderboard rather than deleting the inputs to completed checks. Invalid debug examples retain their separate cap. Small correctness runs explicitly transfer every pose.

RNG identity is `(seed, global_trial_id)`, both uint64. SplitMix64 starts at `seed XOR mix64(global_trial_id)`, adds its 64-bit Weyl constant per draw, and converts the top 24 bits to FP32. Out-of-range identifiers are rejected rather than truncated. Tests cover IDs near `2**64-1`, distinct sampled worlds, repetition, and partition equivalence. Statistical independence is not proved. Bitwise reproducibility is tested on the same hardware/configuration/kernel/dependency versions; cross-hardware/compiler/version equivalence is not promised.

The focused benchmark `tools/dual_gpu_benchmark.py` assigns disjoint global-ID ranges to persistent spawned workers identified by physical UUID. It verifies each worker's local CUDA mapping, prewarms both cards, releases a common start and measures actual overlap. The production CLI remains single-GPU. Reproduction commands, timing boundaries and the durable full-array manifest are in [the dual-4090 report](artifacts/performance/dual4090-20261009T005128Z/REPORT.md).

## Validation and evidence

The CPU validator independently reconstructs float64 vertices, derives edge-normal axes, projects polygons, and checks every pair and wall. It never calls GPU support/gradient helpers. Saved-document validation also checks that pose count matches `n`. At default tolerance `1e-8`:

- `NUMERICALLY_VALIDATED`: every clearance is strictly greater than tolerance.
- `INDETERMINATE`: all clearances are at least negative tolerance, with at least one near contact.
- `INVALID`: larger violations, malformed/count-inconsistent records, or nonfinite data.
- `NOT_CHECKED`: no independent geometry check exists.

`GPU_FEASIBLE` remains a separate search status. Exact fixture tangencies remain numerically indeterminate; slightly separated derivatives exercise strict validation. The eleven-square Trump fixture includes coordinates, exact polynomial/isolating interval, immutable source hash/revision, attribution, and MIT notice. The [current case record](https://jlevy.github.io/squares/cases/11.html) reports optimality with its stated machine-check/review qualifications. This program tests the construction without reproducing the global proof. References never become random-solver inputs.

Each run stores configuration, hardware/dependency/source-hash provenance, `trials.jsonl.gz`, audit IDs, retained poses, validation diagnostics, sparse SVGs, `summary.json.gz`, `report.md`, and a histogram of observed data. JSON preserves round-trip values. SVG uses actual vertices and container at equal scale. `max_images` is independent of retained coordinates. Independent leaderboards exclude invalid/indeterminate results and break ties by global ID. Histograms distinguish GPU acceptance from the selected independently checked subset; the latter is not an unbiased whole-run distribution.

Principal throughput includes initialization and full compression, with synchronized boundaries and CUDA events. Module loading, warm-up, transfers/selection, validation, persistence, rendering/reporting, and end-to-end time are separate. Amortized microseconds/trial denote throughput rather than individual-world latency. The display GPU had other workloads; repeat variability is reported.

Evidence is retained under [artifacts/pilot](artifacts/pilot). Local runtime directories are ignored under `runs/`. Normal CLI runs automatically publish finalized artifacts on `main`, under `experiments/<name>/<run-id>/`, with a provenance and hash manifest. Historical evidence remains unchanged.

## Independent audit

The follow-up audit preserves the original pilot files and independently checks their hashes, scalar records, retained geometry, and SVG coordinates. The hardened numerical validator is `cpu-f64-projection-v2`; it rejects malformed numeric schemas and float64 vertex reconstructions that cannot represent unit edges. Historical v1 records retain their original provenance.

The runner writes the report and histogram once. Final `summary.json.gz` timings include their generation and persistence, with the summary's own final serialization explicitly excluded. The audit also records the external duration of each complete `run()` call, including that serialization.

See the [audit report](artifacts/audit/REPORT.md) for confirmed findings, regression results, independently reconstructed evidence and the matched benchmark. Selected SVGs: [n=12, trial 6233](artifacts/audit/campaign/matched-b512-r0/svg/trial-6233.svg), [n=11 control](artifacts/audit/campaign/retained-n11/svg/trial-4122.svg), and [n=16 control](artifacts/audit/campaign/retained-n16/svg/trial-4114.svg).

Reproduce the matched audit campaign into fresh destinations:

```bash
uv run --locked python tools/reproduce_audit.py --output runs/audit-archive-new --runs-output runs/audit-new --max-seconds 300
```

It retains all final states for bounded `n=11,12,16` controls, captures instrumented CUDA activities separately, repeats the original 12,288-trial `n=12` workload three times at batch size 512, compares batch size 128 on the same IDs and full solver budget, and exercises deadline draining and initialization exhaustion. Repeat and partition checks compare every search scalar with the first current-solver run. Equality with the archived pilot is reported separately: the corrected minimum-step behavior changes search outcomes despite identical configuration values. Historical evidence under `artifacts/audit` retains its original solver provenance.

## Rich workflow and automatic publication

Normal interactive runs show one updating progress display. Completed counts advance only when a GPU batch has finished and its records are saved. An active spinner and elapsed time remain visible while the next batch runs. Best L and validation counts refer to independent CPU checks; GPU acceptance is a separate status. Redirected output uses stable plain text without ANSI animation.

When all requested trials fit in one batch, the display shows a spinner, elapsed time and the number of trials running. It omits the completion bar and percentage because the solver does not expose progress within a batch. Multi-batch runs show a completion bar advancing at batch boundaries. `--batch-size` is a maximum; 1000 trials with batch size 32768 execute as one production batch. Changing batch size affects measured throughput, so the CLI never reduces it for presentation.

During `run`, Warp initialization and module-loading informational messages are hidden so they do not interrupt the display. Warnings, compilation errors and exception tracebacks remain visible on stderr. `diagnose` retains environment details. This display policy does not change kernel settings or measured GPU work.

```bash
uv run asquerix run \
  --experiment n12-s480-b8192 \
  --n 12 --max-sweeps 480 --trials 16384 --batch-size 8192 \
  --output runs/n12-s480-b8192
```

The inherited 30-second scheduling limit may produce a partial run. Set `--max-seconds` explicitly for longer benchmarks. Large batches on the display GPU are user-selected workloads, not the bounded development test campaign.

Quiet structured-output mode saves the same artifacts and prints their paths, never JSON payloads:

```bash
uv run asquerix run \
  --experiment n12-s480-b8192-json \
  --n 12 --max-sweeps 480 --trials 16384 --batch-size 8192 \
  --json --output runs/n12-s480-b8192-json

uv run asquerix compare \
  runs/perf-b128-n12 runs/perf-b512-n12 \
  runs/perf-b1024-n12 runs/perf-b2048-n12
```

Compare shows CUDA-event GPU time/rate, relative speedup, end-to-end timing, budgets, quality and validation coverage. It warns about different configurations, trial ranges, hardware, dependencies, source hashes or host audit workloads. The previously reported synchronized simulation rate remains in the saved summary as a separate timing interval.

`diagnose`, `validate`, `render`, `report` and `compare` also accept `--json`. For commands without an existing run destination, use `--output results-name.json.gz`; otherwise a unique file is created under `runs/`. Validation and comparison do not overwrite historical source files.

New runs save `summary.json.gz`, `config.json.gz`, `environment.json.gz`, `validation.json.gz`, `audit_ids.json.gz`, `trials.jsonl.gz`, and `poses/trial-<id>.json.gz`. Gzip level 3 is explicit and lossless. Gzip metadata and JSON serialization are deterministic; identical serialized bytes, compression level and streaming flush boundaries produce identical compressed bytes. JSONL is streamed and finalized on graceful interruption. Readers transparently accept both historical plain files and compressed archives. Markdown, CSV and SVG remain uncompressed.

Names use 1–80 ASCII letters, digits, dots, underscores or hyphens, starting with a letter or digit. Omitted names incorporate N, sweeps, batch size and a unique UTC run ID. Existing output directories are never overwritten.

Every normal `run` attempts publication after data, report and SVG finalization. `--no-push` creates a local manifest without contacting a remote. `manifest.json.gz` records the run-start code revision and source hashes, full solver/runner configuration, GPU/software provenance, completion status, timing intervals and artifact hashes. The code revision differs from the results commit. The local `publication.json.gz` receipt records the confirmed results commit, GitHub URL, publication timing and total CLI duration; it is excluded from the published tree to avoid circular dependencies.

Open the printed commit URL, then browse `experiments/<experiment-name>/<run-id>/`. All results are also discoverable under [experiments on main](https://github.com/hipotures/asquerix/tree/main/experiments). Download gzip files and read them with `gzip -dc`, Python's `gzip`, or these CLI readers.

Publication uses a private snapshot and temporary Git index, never the active index or checkout. It works from detached HEAD and serializes local publishers using a lock in the shared Git directory. Remote advances trigger up to three fast-forward attempts preserving existing source files and history. No helper branch is created. Publication advances remote `main` while leaving local HEAD unchanged; run `git pull --ff-only` before subsequent development pushes from a clean, otherwise unchanged local `main`. A duplicate run path is rejected. Failed pushes retain local files and an anchored local commit when one was created. Per-file publication is limited to 95 MiB and the total to 500 MiB; oversized or invalid artifacts are reported without data loss. Git identity and remote authentication must already be configured.

Statuses are `COMPLETED + PUBLISHED`, `PARTIAL + PUBLISHED`, or computation status plus `LOCAL_ONLY`/`PUSH_FAILED`. Exit codes: 0 for successful computation/publication or explicit local-only mode, 1 for invalid saved geometry, 2 for input/runtime errors, 3 for failed automatic publication. Ctrl-C or a deadline stops new batches and publishes completed partial results after the current batch drains.

CUDA-event `device_seconds` excludes transfers, CPU validation, gzip and Git. Persistence/compression, rendering/reporting and publication have separate intervals. Summary end-to-end time includes computation and reporting through the documented final-summary boundary; the publication receipt adds the full `run()` duration and total CLI duration. Maintained tools under `tools/` read old/new formats and default to fresh runtime output paths. Archived scripts under `artifacts/` remain immutable provenance; internal library/pilot runs stay local and do not automatically publish.
