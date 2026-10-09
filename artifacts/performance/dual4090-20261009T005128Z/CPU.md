# CPU/GPU critical path diagnosis

The user's observation was 100% for one CPU core. The supplied `nvtop` screenshot shows CPU 100% beside a `pytest -q -m gpu` process and GPU 93%; it does not show aggregate host CPU saturation. The host exposes sixteen logical CPUs. Direct per-thread sampling, native/Python profiling and a controlled blocking-event comparison distinguish waiting from useful host processing.

## Native waiting

The diagnostic ordinary-runner campaign used the frozen production kernel, N=12, B=131072, W=524288, gzip level 9, A alone and then both cards. Nsight Systems traced CUDA, OS runtime, native process-tree samples, context switches and Python samples. Diagnostic wrappers recorded monotonic wall, process CPU and thread CPU time. These are instrumented measurements, excluded from headline throughput.

For A alone, fourteen native `wp.synchronize_device` calls consumed 45.916 s wall and 45.902 s thread CPU. Four full production batches used 43.840 s CUDA-event time; the runner's separate one-world warm-up accounts for approximately 2.078 s. Native leaf samples inside the matching timeline are predominantly driver/vDSO code. The main thread's sampled median CPU utilization during native waits is 99.63% of one logical CPU, while other worker threads' medians are zero. Both concurrent workers show approximately 99.65% during their native waits; this is about two busy logical CPUs, not all sixteen. The same main threads also perform real host work after batches. Sampling boundaries can mix phases; `cpu-thread-attribution.json.gz` labels that limitation.

An isolated controlled probe replaced only the process-owned Python synchronization entry with an owned CUDA event created using `CU_EVENT_BLOCKING_SYNC | CU_EVENT_DISABLE_TIMING`, recorded on the same device and synchronized through Warp's event API. No CUDA context scheduling policy was changed. Full context flags remained **8**, whose scheduling-policy mask is 0 (AUTO), throughout every measurement. The probe is not a production change.

| Wait | Median wall s | Wall range s | Median main-thread CPU s | Repeats | Complete results/poses |
|---|---:|---|---:|---:|---|
| Production device synchronization | 10.969667 | 10.966148–10.974816 | 10.969318 | 3 | Bytewise identical |
| Owned blocking event | 10.959093 | 10.958689–10.974354 | 0.001785 | 3 | Bytewise identical |

Lower CPU activity did not establish a reliable throughput gain: latency ranges overlap and the median difference is approximately 0.10%. There was no aggregate CPU saturation or confirmed host contention on this quiet host. The production waiting policy is therefore retained. The probe establishes that the high CPU reading during long GPU execution primarily represents native waiting, rather than a CPU computation starving that running kernel. It does not establish performance under an unrelated heavily contended host.

## Real host gaps

The ordinary runner processes results before submitting its next batch. The Nsight timeline measured single-A inter-batch simulation-kernel gaps of **3.978, 3.536 and 3.527 s**; concurrent A/B gaps were **3.414/3.906 s**. These intervals include scalar/selected-pose transfer, Python result construction, selection, independent validation, serialization and compression. They are real host-induced submission gaps, even though CPU activity during the preceding GPU batch is mainly waiting. Instrumentation enlarges these gaps; unprofiled per-batch `Batch.run` intervals in the sustained campaign provide the separate performance measurement.

The profiled A runner attributed approximately 2.58 s to scalar-record construction, 0.56 s to selection, 0.55 s to selected-pose transfer, 1.04 s to independent validation of 128 geometries, 3.68 s to JSON serialization, 4.13 s to gzip writes, and 4.21 s to report generation. JSON/gzip/report wrappers nest, so these durations must **not** be added to derive wall time. Python native profiles separately show approximately 3.98 s in zlib compression. The initial diagnostic also had a 0.349 s gather JIT cost; subsequent unprofiled campaigns prewarm gathering before release. Persistence timing alone misses record construction and selection. Remaining intervals are retained as host/unattributed rather than invented into named phases.

The successful diagnostic's full common intervals were 65.999 s for A and 33.875 s for dual. They are **not** benchmark headline numbers. The dual trace contains **20.854 s of simultaneous production-kernel execution**, with physical-A/B kernel unions of 21.947/21.768 s. Local device ordinal zero was mapped through `(PID, ordinal)` to different physical UUIDs; grouping ordinal zero alone would incorrectly merge the cards.

## Lossless gzip experiment

Installed Python 3.14.7 `gzip.GzipFile` selects level 9 when omitted. The old helper omitted it. Levels 1, 3, 6 and 9 were measured separately on the same 131072 completed N=12 records (61,017,607 uncompressed bytes), with three alternating-order repetitions. Serialization and disk writes were outside compression timing. Every decompressed byte and parsed record matched, and a uint64 boundary/negative-zero round trip was checked separately.

| Level | Median compression s | Range s | Compressed bytes | Size relative to level 9 |
|---|---:|---|---:|---:|
| 1 | 0.089303 | 0.087999–0.094844 | 5,312,998 | 1.556x |
| 3 | 0.100342 | 0.099567–0.101173 | 4,852,308 | 1.421x |
| 6 | 0.285211 | 0.285084–0.285773 | 3,768,779 | 1.104x |
| 9 | 0.961497 | 0.957787–0.967774 | 3,415,049 | 1.000x |

Level 3 is about 9.58x faster for this isolated compression operation, with 42.1% larger output than level 9. This is not a solver or end-to-end speedup. Level 1 saves only about 0.011 s over level 3 for this batch while increasing its size another 9.5%. The sustained campaign independently evaluates level 9 versus 3 in the actual ordinary runner, saving every record and preserving a fixed global-ID validation policy, at fixed kernel and device count.

No producer/consumer pipeline, reduced validation, dropped records, best-only output or format conversion was introduced. The minimal host candidate is an explicit lossless gzip level with its setting persisted in run metadata. Atomic finalization, deterministic gzip headers, normal publication ordering, interruption behavior, schema and numerical values are preserved. Final retained policy and measured sustained gains are reported in `REPORT.md`.

Evidence: `profiling/cpu-pipeline-2.nsys-rep`, `timeline-analysis/`, `cpu-phases/`, `cpu-diagnosis-2/thread-activity.json.gz`, `cpu-thread-attribution.json.gz`, `blocking-wait.json.gz`, `gzip-levels.json.gz`, and the sustained campaign's complete per-worker intervals. The first diagnostic attempt failed before measurement because of a harness `NameError`; its log/native trace remain preserved, and the corrected fresh run is explicitly suffixed `-2`.
