# Complete compute benchmark

This is an actual unprofiled two-RTX-4090 experiment. B=131072 per active GPU; W=262144 unique IDs 0..262143 in every mode. There are three repeats per N/mode. The current optimized kernel is retained unchanged: no incremental kernel speedup is claimed. Full configuration, physical mappings and timing boundaries are in [PROVENANCE.md](PROVENANCE.md).

| N | GPU UUID | Variant | CUDA trials/s | Speedup vs current baseline | Registers/thread | Exact comparison | CPU validation coverage |
|---|---|---|---:|---:|---:|---|---|
| 12 | GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d | Current baseline (retained) | 11943.18 | 1.000x | 128 | All defined arrays/bytes match | 64 fixed IDs, 32 per batch |
| 12 | GPU-81ac6e96-0bfe-390d-beb1-241466569d6b | Current baseline (retained) | 12033.17 | 1.000x | 128 | All defined arrays/bytes match | 64 fixed IDs, 32 per batch |
| 16 | GPU-6c849b47-7111-9265-9d42-ff8eddc05a2d | Current baseline (retained) | 6760.44 | 1.000x | 128 | All defined arrays/bytes match | 64 fixed IDs, 32 per batch |
| 16 | GPU-81ac6e96-0bfe-390d-beb1-241466569d6b | Current baseline (retained) | 6815.57 | 1.000x | 128 | All defined arrays/bytes match | 64 fixed IDs, 32 per batch |

CUDA rates above use isolated same-device events; no event times from different GPUs are combined. Initialization and full solver execution are included. All initial/final poses, results, RNG initialization and counters are compared. Large captures use debug=false (defined zero trace); actual debug traces and contact diagnostics are covered by the small CUDA corpus/tests.

| N | Variant | A-alone trials/s | B-alone trials/s | Actual dual trials/s | Dual/A speedup | Dual/B speedup | Capacity efficiency | IDs complete/exact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 12 | Current baseline (retained) | 11941.38 | 12029.83 | 23908.72 | 2.0022x | 1.9875x | 99.739% | 262144/262144; every repeat exact |
| 16 | Current baseline (retained) | 6759.83 | 6814.66 | 13553.85 | 2.0051x | 1.9889x | 99.848% | 262144/262144; every repeat exact |

These rates use the same common execution scope: coordinator release through all completion acknowledgements, including scalar readback and IPC. Efficiency is concurrent throughput divided by the sum of **measured isolated** capacities. It is not a utilization counter.

| N | Mode | Median common wall s | Rate range trials/s | Rate CV | Repeats |
|---|---|---:|---|---:|---:|
| 12 | A | 21.952564 | 11937.32–11959.07 | 0.079% | 3 |
| 12 | B | 21.791171 | 12022.81–12031.27 | 0.031% | 3 |
| 12 | dual | 10.964367 | 23856.01–23910.13 | 0.105% | 3 |
| 16 | A | 38.779688 | 6757.08–6765.86 | 0.054% | 3 |
| 16 | B | 38.467678 | 6791.72–6816.96 | 0.167% | 3 |
| 16 | dual | 19.340930 | 13529.88–13556.32 | 0.088% | 3 |

| N | Mode | GPU A CUDA s, median (range) | GPU B CUDA s, median (range) |
|---|---|---|---|
| 12 | A | 21.949271 (21.915846–21.950943) | idle |
| 12 | B | idle | 21.785117 (21.784286–21.795143) |
| 12 | dual | 10.962225 (10.962067–10.983188) | 10.894555 (10.889878–10.907862) |
| 16 | A | 38.776158 (38.741627–38.792014) | idle |
| 16 | B | idle | 38.462525 (38.451195–38.590031) |
| 16 | dual | 19.339188 (19.329715–19.373479) | 19.302086 (19.273791–19.335701) |

Full campaign wall time: **604.211904 s**, including 9.924341 s startup/prewarm, all 18 measurements, full poses and independently rerun initialization archives, byte comparisons, CPU validation, intermediate metadata and shutdown. Its snapshot ends before the final manifest/terminal summary; rendering and publication are excluded. All per-measurement preparation, archive/transfer/initialization, comparison and validation durations are retained in `compute-principal/measurements.json.gz`; these phases may overlap across workers and are not additive wall time.

Zero missing or duplicate IDs were verified by exact sorted uint64 ID arrays. Per-ID square order is preserved. Cross-card equality holds for all 262144 IDs at N=12 and N=16 on these cards/toolchain, and for the 106-world small corpus including failure cases and uint64 boundaries. This is a tested scope, not a guarantee for other hardware or compiler versions.

Raw full arrays remain in `runs/dual4090-compute-principal/` inside the repository workspace. Compact extracts of 64 documented IDs per N, all workload counters, the small per-card corpus and exact replay outcomes are versioned here. The large-array manifest records durable paths, sizes and hashes; archives are not pushed as oversized evidence.
