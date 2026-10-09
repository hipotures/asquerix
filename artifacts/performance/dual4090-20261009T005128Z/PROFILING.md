# Representative kernel profiles

The final profiles use the installed Nsight Compute 2026.3.1, the frozen current production solver, physical GPU B, B=131072 and block dimension 32. The early case is the first simulation submission (initialization and early compression); dense cases capture the fourth submission (launch-skip=3), after compression has brought squares into contact. N=12 is the research case and N=16 the heavier control. All profiler command lines explicitly use `--clock-control none`. These are instrumented runs and their times are excluded from every headline speedup. Metric names came from the installed supported-metric query preserved in this directory.

| Case | Achieved occupancy | Active warps/scheduler | Eligible warps/scheduler | Issue utilization | Uniform branch targets | Registers/thread | Local load/store sectors |
|---|---:|---:|---:|---:|---:|---:|---|
| early-n12 | 27.775% | 3.500 | 1.407 | 71.119% | 90.475% | 128 | 0/0 |
| dense-n12 | 30.975% | 3.727 | 1.474 | 72.961% | 87.431% | 128 | 0/0 |
| dense-n16 | 30.983% | 3.730 | 1.491 | 73.204% | 87.199% | 128 | 0/0 |

| Case | Wait | Long scoreboard | Math pipe throttle | Not selected | Global load/store sectors | DRAM Mbytes |
|---|---:|---:|---:|---:|---|---:|
| early-n12 | 1.247 | 0.065 | 0.218 | 0.978 | 10022123577/6500757948 | 14.766 |
| dense-n12 | 1.346 | 0.074 | 0.212 | 1.020 | 221180147262/143479029456 | 55.518 |
| dense-n16 | 1.314 | 0.103 | 0.217 | 1.037 | 396949843048/259242513328 | 105.807 |

Stall columns are the installed `smsp__average_warps_issue_stalled_*_per_issue_active.ratio` metrics. They are average stalled-warp counts per issue-active cycle, not percentages and not additive fractions. Full names and units are in `profiling/no-clock-control/metrics-summary.json.gz`. Global cache-sector activity is large despite modest DRAM bytes; repeated world-state accesses can hit cache. These counters do not establish a DRAM-bandwidth bottleneck.

Measured facts are occupancy around 28–31%, registers/thread 128, issue utilization 71–73%, modest eligible warps, branch nonuniformity and zero measured local load/store sectors in these launches. Dependency waiting is more prominent than long-scoreboard waiting. This supports investigating instruction dependencies and redundant state accesses; it does not establish that a particular source-level arithmetic expression survives compilation or can be removed without changing rounding. Register allocation and dependency/divergence limits remain inferred constraints. No forced register cap, block change or layout rewrite was justified in this bounded round.

The compiler reports local allocation/stack space. That is not a measured spill count. Zero local traffic here does not prove zero spills on all paths, N values or stages. The old report's theoretical occupancy is separate from the achieved-occupancy counters above.

Initial exploratory profiles used Nsight Compute's default temporary boost clock control, contrary to the requested clock restriction; the session exports and `profiling/clock-control-review.json.gz` disclose this mistake. No manual or persistent settings were changed, and all throughput measurements ran without profiling. The replacement profiles above explicitly disable profiler clock control. The initial 8192-world runs are unsaturated and are not generalized to B=131072. One old PC-sampling pass overflowed its buffer; that warning is retained, and its PC stall percentages are not used.

Counter access worked on both installed tools; there is no permission blocker or fabricated metric. Native reports retain profiling details. Nsight Systems independently shows 20.853905 s simultaneous production-kernel activity across two distinct UUIDs in the diagnostic ordinary-pipeline run; [CPU.md](CPU.md) explains native CPU waiting and host-induced idle gaps.
