# GPU implementation and pilot evidence

Date: 2026-10-08. Scope: PROMPT_01_IMPLEMENTATION.md. PROMPT_02_AUDIT.md was not executed.

## Outcome

The principal n=12 measurement is **422.998 ± 2.876 complete experiments/second**, mean and sample standard deviation of three matched repeats. Each completes 12,288 trials at batch size 512, with 28.8–29.2 seconds of timed GPU work. Earlier short measurements are preliminary.

All 41,488 primary-campaign run occurrences returned GPU-feasible final poses, covering 13,312 distinct (n, global trial ID) configurations. Repeats deliberately reuse inputs to measure variability. Independent numerical validation passed 873 audited occurrences, representing 309 distinct configurations, with zero invalid or indeterminate search audits. Other records remain NOT_CHECKED; the whole histogram is not independently validated.

The heuristic did not rediscover the eleven-square Trump optimum or the sixteen-square grid. The n=12 construction approaches side 4 with a positive guard. These observations are not impossibility, rigidity, optimality, or rigorous certification results.

## Environment and implementation

- NVIDIA GeForce RTX 4070 Ti, UUID GPU-64d50ac7-f623-65a8-8784-b9ec14d16527, sm_89, 12,282 MiB, display active.
- Driver 615.71.09; default PyPI Warp CUDA 13.4 wheel, warp-lang 1.18.0; Python 3.14.7, NumPy 2.5.3, pytest 9.1.1, uv 0.12.23.
- Linux CachyOS kernel 7.2.9-1-cachyos, x86_64. First authorized query showed 2,946 MiB used and 9,336 MiB available. Other display/application workloads remained active. No driver changes.
- The sandbox hid NVIDIA device nodes despite visible PCI hardware. Authorized execution outside it enabled real CUDA; no CPU simulation fallback.
- One thread per world, block size 32; all-pair SAT generalized positional projections with moving-axis angular gradients, tied-axis averaging, bounded translations and rotations.
- Eight fixed device-resident stages of up to 16 compression attempts. No contact/sweep host readbacks or decisions. Reported kernel properties: 139 registers/thread, local_memory_size=32 bytes.
- Independent CPU float64 vertex-projection validator, separate containment checks, and saved-document square-count validation.

Implementation commit: ceaebce85d1dd046f97a9850cfb32b42850b8229. Extended-run hashes match every Python source file in that commit. Runtime metadata accurately retains the pre-commit base revision plus dirty state and exact source hashes. Earlier SVGs were rerendered after visual review, preserving original timing metadata and separately recording postprocessing. Simulation kernels were unchanged.

## Budgets and tolerances

All trials use initial_side=10, seed=20261008, IDs starting at 0, FP32 with fast math disabled, 2000 proposals/square, 128 compression attempts, 120 sweeps/attempt, step 0.2, halving factor 0.5, floor 1e-4. Translation mobility=1, rotation mobility=0.3, relaxation=0.8, correction caps=0.1 length and 0.08 radians. Guard=2e-5; acceptance tolerance=2e-6; required raw clearance >=1.8e-5; independent tolerance=1e-8. No square resizing, center rescaling, reference/grid seeds, shaking, or restart operators.

## Correctness evidence

Final uv run pytest -q: **85 passed, 0 failed, 0 skipped**, including **14 real CUDA tests**. Two upstream Warp ctypes deprecation warnings remain in tests-final.txt. Coverage includes oriented geometry, contact/containment, malformed/nonfinite data, exact and irrational fixtures, GPU initialization through n=32, uint64 RNG/partitioning, both gradient owners, actual rotation/translation, symmetric zero torque, complete rollback, monotonic accepted sides, budgets/failures, output selection/limits, and graceful stopping.

The offline Trump11 fixture includes exact algebraic definitions and a pinned MIT source, reconstructed without executing external proof code. Rounded tangencies are INDETERMINATE; a separate positive-clearance derivative validates. The [current case record](https://jlevy.github.io/squares/cases/11.html) reports optimality with V3/C3/S5 and review qualifications. This PoC does not reproduce the global proof.

## Principal extended timing

| repeat | trials | synchronized simulation (s) | CUDA events (s) | trials/s | end-to-end (s) | audited |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 12288 | 28.838872 | 28.835727 | 426.092 | 31.216533 | 114 |
| 1 | 12288 | 29.084272 | 29.081068 | 422.496 | 30.978149 | 114 |
| 2 | 12288 | 29.228975 | 29.225696 | 420.405 | 31.236990 | 114 |

Mean 422.998 trials/s; sample standard deviation 2.876, or 0.680% of mean. GPU-feasible rate equals attempted rate. About 2364.1 microseconds/trial is amortized throughput, not individual-world latency.

Each repeat has 114 numerical passes, zero invalid/indeterminate audits, and 12,174 NOT_CHECKED (0.9277% coverage), including all 64 reproducible random-audit IDs. All 86 retained poses per repeat were rechecked from archived coordinates. Scalar streams are identical; each has 6873 BUDGET_EXHAUSTED and 5415 STEP_FLOOR_REACHED outcomes, no initialization/numerical failures. Budget exhaustion is distinct from final feasibility. These are substantial compression experiments, without shortened budgets.

| repeat | cached load (s) | warm-up (s) | transfer/selection (s) | validation (s) | persistence (s) | render (s) | report (s) | maximum stage (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.146957 | 0.784149 | 0.030411 | 0.772632 | 0.108000 | 0.002119 | 0.040911 | 0.175958 |
| 1 | 0.000376 | 0.786892 | 0.024207 | 0.738416 | 0.118211 | 0.002009 | 0.046088 | 0.175208 |
| 2 | 0.000555 | 0.785854 | 0.024856 | 0.835918 | 0.128330 | 0.002032 | 0.044806 | 0.200653 |

Separate fresh-Warp-cache JIT/module loading: 0.991067 s; runtime setup plus loading: 1.287471 s. CUDA driver cache was not cleared. No simulation trials were executed in that check. Cached loading and full-budget warm-up are outside principal throughput.

Initial campaign elapsed 116.652 s; extended campaign 94.205 s; total 210.856 s (about 3.5 minutes), excluding setup, tests/debugging, separate cold compilation, and offline postprocessing.

## Preliminary identical-input batch sweep

| batch | trials | simulation (s) | trials/s | audited |
| --- | ---: | ---: | ---: | ---: |
| 8 | 512 | 66.225375 | 7.731 | 95 |
| 32 | 512 | 19.510097 | 26.243 | 81 |
| 128 | 512 | 5.141463 | 99.583 | 68 |
| 512 | 512 | 1.274209 | 401.818 | 45 |

All sizes use the same 512 IDs and identical budgets/tolerances. Scalar outcomes are partition-identical. Initial single-batch repeats averaged 403.559 ± 6.198 trials/s and are superseded by the principal timing. Larger batches expose more parallelism; occupancy remains limited and work divergent. This is not a maximum-throughput claim.

## Construction quality

| n | distinct sampled trials | best numerical side | median GPU side | reference construction | gap | GPU sides within reference + 0.001 | audited among those |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 11 | 512 | 4.0002007484436 | 4.465536356 | 3.87708359002281 | 0.123117158 | 0/512 (0.0000%) | 0 |
| 12 | 12288 | 4.00020027160645 | 4.620308161 | 4 | 0.000200272 | 5/12288 (0.0407%) | 5 |
| 16 | 512 | 4.58729362487793 | 5.436337709 | 4 | 0.587293625 | 0/512 (0.0000%) | 0 |

Reference + 0.001 is a report-only proximity statistic, distinct from all geometric/search tolerances. For n=12, side 4 is a known feasible construction, not an optimality assertion. For n=16 the grid is the exact control. References never enter random search. The n=11/16 pilot rates (475.17/241.94 trials/s) are short single-batch preliminary measurements.

| n | selected trial | minimum pair separation (float64) | minimum wall clearance (float64) | status |
| --- | ---: | ---: | ---: | --- |
| 11 | 252 | 1.80006031176e-05 | 1.80979566986e-05 | NUMERICALLY_VALIDATED |
| 12 | 6233 | 1.80177525928e-05 | 1.85617438024e-05 | NUMERICALLY_VALIDATED |
| 16 | 306 | 1.80139421729e-05 | 1.82163532272e-05 | NUMERICALLY_VALIDATED |

All selected best poses report zero penetration. SVGs for n=11,12,16 and observed histograms were visually inspected. Clipped headings and transparent backgrounds were corrected without changing coordinates.

## Stopping and negative evidence

- Actual SIGINT preserved 8/64 completed trials, returned success, and launched no next batch. External signal-to-exit was 1.368541 s, including drain, validation, and saving. The Python handler observed the signal near CUDA-call completion; internal observed-drain is not external request latency.
- Actual max_seconds=0.001 preserved 8/64 trials, recorded MAX_SECONDS, deadline drain 0.940053 s and total deadline overrun 1.001554 s.
- Dense n=2, initial_side=1.5, one-proposal initialization returned four INIT_FAILED records with null sides and an explicit invalid debug SVG. Initializer failure does not prove geometric impossibility.

## Artifacts and reproduction

- campaign/: eleven initial runs, all scalar records, provenance/configuration, selected JSON poses, validation and SVGs; campaign.json and campaign.log retain preliminary timing.
- extended/measurements.json: principal timing, equality and archive hashes; extended/repeat-{0,1,2}/trials.jsonl.gz: every scalar record, beside all selected poses/SVGs/configuration/provenance/reports.
- runs/extended/repeat-{0,1,2}: durable uncompressed local originals, ignored by Git. Compressed scalars and important artifacts are committed; no large raw scalar datasets enter Git.
- tests-final.txt, cold-compile.json/log, revalidation.json, extended/revalidation.json, stop-* and init-failed/ preserve tests, actual stopping, failures, and independent checks.
- manifest.json records file SHA-256 and implementation provenance. Archive hashes were checked after decompression.

Short CLI commands are in [README.md](../../README.md). Reproduce long matched measurements with fresh destinations:

    uv run python artifacts/pilot/extended-benchmark.py --output runs/new-extended-archive --runs-output runs/new-extended

Original default-path execution produced the results; fresh-path flags were added afterward without changing the measured workload. Restore a compressed archive before ordinary CLI reporting:

    cp -r artifacts/pilot/extended/repeat-0 runs/restored-new
    gzip -d runs/restored-new/trials.jsonl.gz
    uv run asquerix report runs/restored-new
    uv run asquerix validate runs/restored-new

Archive restoration, reporting, and validation were tested at runs/restored-extended. Source-control writes exclude the user's pre-existing untracked AGENTS.md and prompt files.

## Limits

FP32 heuristic search and numerical audits do not provide exact/error-bounded certification or continuous collision-free trajectories. Most large-run poses are NOT_CHECKED. Quality is weak for n=11/16, many worlds exhaust budgets, and only five of 12,288 n=12 trials approach the report reference within 0.001. Determinism is tested on this hardware/configuration/version; statistical independence and cross-device reproducibility are not proved. Display load and clocks were not isolated. Multi-GPU work and the later audit remain outside scope.
