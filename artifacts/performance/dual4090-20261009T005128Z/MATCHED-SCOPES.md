# Matched multi-batch compute and ordinary-pipeline scopes

Both campaigns use W=524288 IDs 0..524287, B=131072, N=12/16, the same seed and full solver budgets, and three repetitions per mode. Each isolated card executes four full batches; each concurrent card executes two. The compute harness and ordinary result-saving pipeline intentionally have different common intervals. Compute acknowledges complete GPU submissions/scalar readbacks before pose archival and validation; ordinary acknowledges only after all per-trial records, 128 fixed-ID CPU validations and final reports are durable. The ordinary interval also includes its separate one-world warm-up, which is excluded from trial counts.

| N | Mode | Compute trials/s (median) | Ordinary gzip 9 trials/s | Ordinary gzip 3 trials/s | Host gain 3 vs 9 | Compute rate range |
|---|---|---:|---:|---:|---|
| 12 | A | 11916.89 | 9321.61 | 9925.54 | 6.479% | 11916.39–11928.75 |
| 12 | B | 12022.98 | 9389.15 | 9967.36 | 6.158% | 11995.49–12036.81 |
| 12 | dual | 23882.42 | 17971.82 | 19096.67 | 6.259% | 23852.62–23914.70 |
| 16 | A | 6745.07 | 5732.17 | 5930.63 | 3.462% | 6734.15–6747.92 |
| 16 | B | 6798.28 | 5762.73 | 5977.23 | 3.722% | 6778.88–6804.45 |
| 16 | dual | 13531.62 | 11034.49 | 11440.82 | 3.682% | 13482.97–13536.49 |

The difference between compute and ordinary rates is the cost of a broader workload, not a kernel regression or a kernel optimization. Only the level-3/level-9 ratio at fixed device count and fixed kernel is the measured host-pipeline gain. All 36 ordinary runs retain every trial record and match the sorted decompressed schema/data hash; all 18 compute runs compare every defined byte of every initial/final result and pose, and validate 128 documented sampled geometries independently. The two checks complement one another: compressed files need not have identical container bytes across levels.

| Campaign | Startup/prewarm s | Full harness snapshot s | External full process s |
|---|---:|---:|---|
| Compute sustained | 9.929194 | 1197.220359 | 1197.370158 |
| Ordinary sustained | 18.624757 | 2276.155773 | 2276.298192 ±0.11 |

The snapshot spans `run()` entry through worker shutdown/telemetry closure and excludes final manifest serialization and terminal table; the external timing includes them. Compute external timing starts before the uv subprocess launch; ordinary timing uses process creation ticks through observed exit and excludes the uv launcher. These are entire campaign times including every repetition, reference initialization, archives, comparisons and CPU validation, not W divided by one experiment duration. Per-measurement preparation, collection, equality and CPU-validation times are all retained. Worker phases overlap, so sums of phases are not reported as end-to-end wall time. Publication was disabled for every campaign.

After these campaigns, the NPZ sample validator was corrected to decode each large member once instead of decoding it once per sampled ID. The same 32 selected IDs and validation outcomes remain unchanged. Controlled single archive measurements are in `archive-validation-improvement.json.gz` (N12 2.1611→0.2231 s; N16 2.7916→0.3276 s), with a regression test counting member reads. They are single-pair observations, not another headline throughput claim. This reader correction is outside CUDA/common execution scopes. The full campaign times above accurately retain the old repeated-decode cost; final-code archival replay is faster and does not rewrite those measurements.
