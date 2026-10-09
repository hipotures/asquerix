# Complete sustained ordinary-pipeline benchmark

This campaign executes the actual ordinary runner with all scalar records saved, fixed global-ID validation, finalized gzip files, reports and histograms. N=12/16; B=131072; W=524288 IDs 0..524287; three repeats per N/mode/level. Alone: four full batches. Dual: two full batches per physical GPU. Kernel source and every executable PTX entry are unchanged; this is a host comparison, not a new kernel speedup.

| N | Variant | A-alone trials/s | B-alone trials/s | Actual dual trials/s | Dual/A | Dual/B | Capacity efficiency | IDs complete/exact |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 12 | gzip 9 reference | 9321.61 | 9389.15 | 17971.82 | 1.9280x | 1.9141x | 96.051% | 524288/524288; every decompressed record identical |
| 12 | gzip 3 retained | 9925.54 | 9967.36 | 19096.67 | 1.9240x | 1.9159x | 95.997% | 524288/524288; every decompressed record identical |
| 16 | gzip 9 reference | 5732.17 | 5762.73 | 11034.49 | 1.9250x | 1.9148x | 95.995% | 524288/524288; every decompressed record identical |
| 16 | gzip 3 retained | 5930.63 | 5977.23 | 11440.82 | 1.9291x | 1.9141x | 96.078% | 524288/524288; every decompressed record identical |

Common wall time runs from warmed-worker release through all ordinary-runner finalization acknowledgements. It includes the separate one-world warm-up, host processing, JSON/JSONL/gzip, selected poses, durable files, report/histogram and final summary serialization. It excludes initial worker/JIT setup and Git publication. CUDA event times below exclude the one-world warm-up, which is recorded separately.

| N | Mode | Level | Median common s | Rate range trials/s | Rate CV | Host throughput gain vs 9 |
|---|---|---:|---:|---|---:|---:|
| 12 | A | 9 | 56.244377 | 9315.49–9349.39 | 0.158% | 0.000% |
| 12 | B | 9 | 55.839766 | 9335.34–9390.03 | 0.273% | 0.000% |
| 12 | dual | 9 | 29.172776 | 17965.31–17972.04 | 0.017% | 0.000% |
| 12 | A | 3 | 52.822137 | 9891.81–9966.04 | 0.306% | 6.479% |
| 12 | B | 3 | 52.600470 | 9957.87–10038.39 | 0.360% | 6.158% |
| 12 | dual | 3 | 27.454416 | 19089.97–19145.36 | 0.129% | 6.259% |
| 16 | A | 9 | 91.464113 | 5713.04–5732.36 | 0.158% | 0.000% |
| 16 | B | 9 | 90.979066 | 5757.79–5775.99 | 0.133% | 0.000% |
| 16 | dual | 9 | 47.513550 | 10999.47–11050.62 | 0.194% | 0.000% |
| 16 | A | 3 | 88.403356 | 5921.03–5942.37 | 0.147% | 3.462% |
| 16 | B | 3 | 87.714146 | 5967.40–5985.44 | 0.123% | 3.722% |
| 16 | dual | 3 | 45.826078 | 11438.54–11459.66 | 0.083% | 3.682% |

| N | Mode | Level | A CUDA s median | B CUDA s median | Median host gap between batches s |
|---|---|---:|---:|---:|---:|
| 12 | A | 9 | 43.975250 | idle | 2.185844 |
| 12 | A | 3 | 43.945537 | idle | 1.329821 |
| 12 | B | 9 | idle | 43.590730 | 2.198952 |
| 12 | B | 3 | idle | 43.675230 | 1.319175 |
| 12 | dual | 9 | 21.956984 | 21.791945 | 2.176272 |
| 12 | dual | 3 | 21.925474 | 21.840808 | 1.294386 |
| 16 | A | 9 | 77.755768 | idle | 2.267631 |
| 16 | A | 3 | 77.805920 | idle | 1.453905 |
| 16 | B | 9 | idle | 77.084400 | 2.261383 |
| 16 | B | 3 | idle | 77.355412 | 1.416728 |
| 16 | dual | 9 | 38.843545 | 38.628445 | 2.271161 |
| 16 | dual | 3 | 38.836209 | 38.690777 | 1.410023 |

Host gaps are the measured end of complete `Batch.run` (including scalar readback) through the next call, with the same buffers and operation order. This is host processing between submissions, not native waiting while kernels run. No processing/compute overlap pipeline was introduced. The explicit gzip level is the smallest measured intervention; remaining construction, selection and JSON costs are retained rather than removing intended records or audits.

Full harness snapshot time is 2276.155773 s, including 18.624757 s startup/prewarm, all 36 operations, comparisons and shutdown. The snapshot ends before its final manifest/terminal serialization; independently measured full Python CLI process lifetime (including those outputs) is in `pipeline-sustained/process-lifetime.json.gz`, with its stated clock/polling uncertainty. Publication is outside these measurements.

Each operation independently validates exactly 128 fixed geometries, with zero invalid or indeterminate outcomes. Its other 524160 records retain NOT_CHECKED; GPU acceptance is not promoted to a certificate. Every decompressed per-trial JSONL byte matches after sorting by uint64-compatible integer global IDs, including schema, counters and validation outcomes. Gzip container hashes and sizes differ and are recorded accurately.

Raw complete ordinary artifacts, including all trials, summaries, audit poses, reports and histograms, remain in `runs/dual4090-pipeline-sustained/`. The repository publishes compact telemetry, exact outcomes and the large-file manifest. All 36 measurements are included; none were excluded. Rendering of sparse pose SVGs and ordinary CLI defaults are exercised separately.
