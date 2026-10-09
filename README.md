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

## Selected trajectories and offline playback

Recording is off by default. The production kernel and its allocations are unchanged. Search first; only selected global trial IDs are replayed on one explicit CUDA device afterward. Replays never increase scientific trial counts, modify the histogram or replace the original best result.

These commands were exercised on a display-attached RTX 4070 Ti. Use fresh output paths:

```bash
# Ordinary campaign, no recording
uv run asquerix run --n 12 --trials 8 --batch-size 8 --max-images 0 \
  --no-push --json --output runs/ordinary

# Select once after search: up to three retained independently validated trials
uv run asquerix run --experiment trajectory-best-demo \
  --n 12 --max-sweeps 480 --trials 32 --batch-size 32 \
  --trace-best 3 --trace-max-frames 256 \
  --no-push --json --output runs/trajectory-best

# Explicit historical global ID, using exactly its saved solver configuration
uv run asquerix trace artifacts/audit/campaign/retained-n11 \
  --trial-id 4124 --mode accepted --max-frames 256 --device cuda:0 \
  --no-push --json --output runs/historical-4124

# Dense diagnostic replay, including provisional steps and rollback
uv run asquerix trace runs/trajectory-best \
  --trial-id 1 --mode sweeps --every 1 --max-frames 256 --max-mib 10 \
  --device cuda:0 --no-push --json --output runs/trajectory-sweeps

# Regenerate a viewer without a CUDA context; it embeds all numeric data
uv run asquerix trace-render runs/trajectory-sweeps/trajectories/trial-1.npz \
  --output runs/trajectory-sweeps-view.html --json
# Open runs/trajectory-sweeps-view.html in your browser using File > Open.
```

`trace --best K` is an alternative to repeated `--trial-id` arguments. IDs and `--best` are mutually exclusive. Selection uses the existing validated leaderboard, ordered by `(side, global_trial_id)`, with duplicates removed. It neither increases pose retention nor promotes unchecked results. Fewer retained eligible candidates produce fewer recordings. An explicit ID without a retained complete pose fails with `REFERENCE_INCOMPLETE` before replay. Plain historical JSON and current gzip JSON remain readable. Standalone tracing writes a new companion collection outside the source experiment.

Run options are `--trace-best` (default 0), `--trace-mode accepted|sweeps` (accepted), `--trace-max-frames` (256), `--trace-every` (16) and `--trace-max-mib` (10). Standalone spellings omit the `trace-` prefix. The maximum is 16 selected trials, 2–4096 frames per trial, and a positive sweep interval fitting signed 32 bits. The export limit covers all new trajectory files, viewers, operation metadata, manifest and receipt. A conservative 64 KiB publication reserve must fit inside it. Actual file sizes are checked before making a pending trial visible; a size limit stops further exports and preserves finalized earlier traces and the original search. No automatic SVG frames, GIFs or videos are generated. `--no-push` keeps the collection local; omitting it uses the existing isolated-index publisher on remote `main`. `--json` uses no Rich and prints statuses/paths, never raw payloads. Browsers are never launched by the CLI.

Each successful replay produces `trajectories/trial-ID.npz`, `trial-ID.meta.json.gz` and `trial-ID.html`. Schema `asquerix-trajectory-v1` stores C-contiguous little-endian `poses float32[F,N,3]`, `side float32[F]`, `sequence int64[F]`, `attempt/sweep/sweep_total int32[F]`, `phase/roles uint8[F]` and `square_ids int32[N]`. No pose quantization, rotation normalization, square reordering or lossy deltas are used. JSON uses deterministic gzip level 3. Loading checks bounded ZIP/NPY headers, primitive dtypes, shapes, endpoint roles, unique IDs and the NPZ checksum; pickle loading is disabled. Browser seed/trial identifiers are decimal strings, preserving all unsigned 64 bits.

`INITIAL=0` is the real successfully placed random arrangement before any compression. `TRIAL=1`, `RELAXING=2` and `REJECTED=4` use the proposed side and are provisional; they may overlap or violate walls. `ACCEPTED=3` and `ROLLBACK=5` use accepted-pose storage and accepted side. `FINAL=6` identifies a separately stored final accepted endpoint when needed. Role bits `INITIAL=1` and `FINAL=2` preserve endpoints without duplicating their geometry; a zero-attempt run has one frame with both roles. Attempts are zero-based, `sweep` counts completed sweeps within that attempt, and `sweep_total` is cumulative completed sweeps. Initial indices are `-1` and cumulative sweeps zero. Rejected accepted-mode attempts use bounded final scalar counters rather than repeated unchanged poses.

Online deterministic compaction and stride doubling bound GPU/host buffers during recording and retain coverage from start to final endpoint. Metadata/viewers disclose observed, retained and suppressed event counts and effective stride; omitted states cannot be recovered. The independent CPU validator checks every retained frame. Provisional checks are residual measurements, never accepted-geometry badges. Initialization failure emits only failure metadata, without unwritten pose slots or invented starting geometry. Ctrl-C stops scheduling new replays and drains the already executing bounded replay; drain time is recorded.

`REPLAY_MATCHED` means available defined FP32 endpoint/result fields—including signed-zero bits, counters, termination and identities—matched the saved reference exactly. It does not prove equality of every unrecorded intermediate state. Unknown reference precision or missing fields produce `REFERENCE_INCOMPLETE`; differences produce `REPLAY_MISMATCH` with bounded field diagnostics and the actual replay saved separately. Source/environment provenance has an independent status, hashes, revisions, GPU identity and dependency/driver versions. The historical ID 4124 demonstration intentionally reports a mismatch with its older solver evidence. No historical source is checked out or executed. Numerical validation is not mathematical certification or proof of optimality.

The viewer opens locally with no server or network. It starts paused at `[Initial arrangement | Current recorded frame]`, with a shared default units-per-pixel scale based on the initial container. Playback visits saved frames without interpolation; speed means frames per second, not physical time. Square IDs/colors stay stable and labels stay upright, with a clear gap before orientation marks. Container side captions sit outside the drawings, and validation appears as readable measurements rather than raw JSON.

Zoom the current panel with the wheel, buttons or `Zoom ×` (0.25–65536), and drag to pan. Container, squares and trails share one scene transform. The initial panel stays fixed; frame changes never move the camera automatically. `Fit container` uses the current frame's L, while `Fit full trajectory` fits all recorded positions. Select an ID and use `Focus selected ID` plus a high zoom to inspect micromovements. Labels and line widths keep readable screen sizes.

Center trails are enabled by default. `Trail frames` limits them to the last K saved frames; 0 means full history. Dots mark recorded centers, not physical speed, and connecting lines do not reconstruct skipped motion. Non-finite centers break the trail. Click a square, its color/ID legend entry or the selector to highlight its trail and dim the others; `only selected trail` hides the rest. Independent square, container boundary, ID and orientation toggles allow clean trails alone.

Drag A/B markers, enter their zero-based frame indices or use `Set A here` / `Set B here`. `Play range once` stops on B; `Loop range` returns to A. The default is the full recording. Manual slider/first/last/previous/next navigation pauses playback. On-demand SVG export preserves the camera, history window and visibility settings. Regenerate older HTML with `trace-render` to get these controls without replaying CUDA or changing recorded data. [Refreshed examples and browser evidence](artifacts/trajectories/viewer-center-trails/README.md) cover these controls.

Compact genuine examples and device/test evidence are in [the trajectory report](artifacts/trajectories/REPORT.md). A reproducible headless Chromium check uses the standard-library tool:

```bash
uv run python tools/trajectory_browser_smoke.py \
  --html artifacts/trajectories/viewer-center-trails/trial-1.html \
  --output runs/browser-smoke.json.gz --screenshot-dir runs/browser-smoke
```

Original search CUDA-event time and trials/s stay unchanged. `trace.json.gz` separates replay GPU, transfer, validation, export, module loading and total postprocessing; the publication receipt reports total CLI time including tracing/publication. Offline viewer regeneration alone does not publish or create a scientific experiment.

## Experiment laboratory

The laboratory (`asquerix lab`) runs rigid-square strategy programs on the same Warp/CUDA geometry. One immutable program controls one whole world with `COMPRESS`, `EXPAND`, `MOVE`, `ROTATE`, `RELAX`, `RESTORE_BEST` and `STOP`, bounded repetition and conditions. Nothing compresses unless the program asks for it. The evaluator keeps `current`, `trial` and a protected `best` state. It returns `best`, validates every ranked pose on the CPU and freezes training winners before an untouched holdout bank. Two search methods are implemented: independent random programs and mutation-guided `(1 + lambda)`. Fixed controls are `legacy_compress`, which reproduces the legacy solver's defined result bytes, and the handwritten `pulse_rotate`. Requirements: [`docs/lab-prd.md`](docs/lab-prd.md).

These commands were exercised on a display-attached RTX 4070 Ti. Port 8765 was in use on that machine, so the tested runs used `--port 8766` with a matching `--url`:

```bash
# Server, coordinator and owned CUDA worker; the browser UI is http://127.0.0.1:8765
uv run asquerix lab serve --port 8765 --root runs/lab

# Rich clients; closing them (or the browser) does not stop the campaign
uv run asquerix lab submit --config examples/lab/n12-controls.json
uv run asquerix lab watch <campaign-id>
uv run asquerix lab status <campaign-id>
uv run asquerix lab report <campaign-id>
uv run asquerix lab export <campaign-id> --output runs/lab-export/<campaign-id>
uv run asquerix lab pause|resume|stop <campaign-id>
uv run asquerix lab continue <campaign-id> --additional 32 [--batch-capacity N] [--max-seconds S] [--no-publish]
```

Ctrl+C stops the server within about a second. A running campaign is then finalized as PARTIAL with its completed results; use Pause first if you want to Resume it after a restart.

**Continuing a finished search.** `Continue search` in the browser (or `lab continue`) creates a new campaign that takes over a completed or partial search: the same starting worlds, results, programs, incumbents and random-generator state, plus more candidates per method. The original campaign is not changed. Only the name, description, GPU, batch capacity, slice sizes, time and storage budgets, replays and publication may differ; n, banks, seeds, the evaluation profile, the generation law, λ, methods and controls are kept. The numerical sources (kernel, geometry, program language, scoring, generation) and NumPy/Warp/Python must be unchanged since the parent ran; differing orchestration files are recorded. A continuation reproduces the programs, scores and RNG state of a single campaign with the larger budget (tested on CUDA). Holdout is evaluated only for new winners. Catalogs from earlier versions are migrated to schema version 2 when the server starts.

**GPU telemetry.** While the laboratory computes, the header shows one tile per GPU (temperature, fan, power draw/limit, utilization, memory and a utilization history), sampled once a second with `nvidia-smi --query-gpu`. The tiles freeze when the computation ends and can be dismissed; the next computation starts a new session. Click the power value to change a GPU power limit. This needs root; the server uses non-interactive `sudo`, so it works only after allowing exactly that command, e.g. with `sudo visudo -f /etc/sudoers.d/asquerix-power`:

```text
<user> ALL=(root) NOPASSWD: /usr/bin/nvidia-smi ^-i [0-9] -pl [0-9]{2,4}$
```

The anchored regular expression (sudo 1.9.10 or newer) permits only `-i <gpu> -pl <watts>`; a `*` wildcard would also match further arguments. Power-limit changes during a campaign are recorded in its history, because they affect measured speed but not numerical results.

Example campaigns are in `examples/lab`: `n11-compare.json` (the reference two-method comparison: 32 candidates per method, 4,224 training and up to 256 holdout episodes), `n11-three-program-evaluation.json`, `n12-controls.json`, `n16-controls.json` and `n11-fixed-smoke.json`. `--json` saves structured client output under `runs/lab-cli` and prints only paths. Campaigns publish their finalized directory to remote `main` by default (`"publication": {"enabled": false}` keeps them local). A publication failure is recorded on the campaign and never discards its results.

The browser shows the campaign list, the creation form with a plan summary, live progress, program inspection with mutation diffs, paired replays on the same initial world, durable history and selected geometric replays. Replays reuse the offline trajectory viewer with the executing instruction, selection mask, rollback/restore markers and current/best L overlaid. `report.html` in each campaign directory is self-contained and plays its selected trajectories with the network disabled.

Verification tools:

```bash
uv run pytest -q                                              # includes CUDA interpreter, replay and publication tests
uv run python tools/lab_browser_smoke.py --url http://127.0.0.1:8765   # real UI checks with headless Chromium
uv run python tools/lab_overhead.py                           # legacy_compress interpreter vs legacy solver
```

Evidence and the pilot report are in [`artifacts/lab/REPORT.md`](artifacts/lab/REPORT.md).
