# Strategy reference verification — 9 October 2026

The supplied CPU strategy-language reference runs successfully. All 31 supplied
unit tests and all three Python examples in the design document passed on
CPython 3.14.7 using uv 0.12.23. No strategy GPU engine, geometric solver,
evolutionary optimizer, or packing benchmark was executed.

## Inputs and provenance

Verified the files provided in `/home/user/Downloads`:

- `ASQUERIX_EVOLVING_STRATEGY_PROGRAMS_DESIGN.md`:
  SHA-256 `6f1fc9322f7759e7ee3fa2fc01463afc28bf9c0d49138ad526513fc0b4cf0a50`.
- `ASQUERIX_STRATEGY_DESIGN_AND_REFERENCE.zip`:
  SHA-256 `2949e09ae2662ac7b3820c68cb35e2dda08e547d579831398a1bb62c77a1096e`.

The ZIP passed its CRC integrity check, contained five expected files, and was
extracted into a temporary directory after checking its member paths and sizes.
The standalone Markdown document is byte-for-byte identical to the ZIP's copy.
The downloaded originals were not modified.

The design cites repository revision
`2f08bdb7520cb94bc472d5586d107956cf2905b5`; verification started on `main` at
`afa10b10802e46a4d16a1f56120295c685c908d0` with a clean checkout. This audit
adds evidence only. The production solver and environment were not changed.

The two files under `reference/` are exact copies of the supplied Python files,
preserved as audit provenance rather than production entry points. Their
hashes, the complete ZIP member manifest, executed commands, exit codes,
environment, and evidence hashes are in `manifest.json`.

## Executed results

| Check | Result |
|---|---|
| Standalone reference executable | Exit 0; 17 instructions; 556-byte payload; `HALTED` |
| Supplied unit tests | 31 passed |
| Generated control-flow cases inside the supplied suite | 500 passed |
| Generated/mutated strategies inside the supplied suite | 100 passed |
| Python examples from the Markdown | All 3 passed |
| Independent source-tree differential check | 859 accepted trees; 6,872 execution paths; zero mismatches |
| Oversized/deep generated source trees | 141 rejected by compiler limits |

The demo's canonical program digest is
`959669b0ae0bff912fcc82cb92e3b141e9d7520967c4291365ddf0482d5e1b9a`.
With all predicates true, it records four compression actions and three
expansion/rotation pairs. These are opcode records, not geometric operations.

The independent harness generated 1,000 source trees using seed `20261009`,
including nested sequences, repeats, both conditional arms, and early stops.
It traversed each accepted source tree directly and compared its action trace
and predicate consumption with the compiled bytecode on eight decision streams.
Every accepted tree also passed binary encode/decode round-trip comparison.
The 141 rejected trees were excluded from execution comparisons.

The supplied tests cover parameter validation, canonical float32 conversion,
binary encoding and decoding, malformed payloads, forward-only jumps, source
and dispatch limits, fuel reservations, deterministic template generation, and
one compression-parameter mutation. See `evidence/test-scope.txt` and the
execution logs for the exact coverage and results.

## Scope and limitations

The reference imports only the Python standard library. Its `dry_run_control`
records action opcodes; it contains no Warp kernels or geometric dispatcher.
The following parts remain design proposals in this package:

- Geometry, selectors, contact repair, and accepted/trial/best-state transactions.
- Geometry rollback without refunding work or rewinding random state.
- Device work accounting, sliced GPU execution, and protected finalization.
- Fitness evaluation, crossover, selection, and population evolution.
- Rounded-shape collision handling and restoration to exact square geometry.
- GPU compatibility, numerical packing validation, throughput, and scientific
  improvement over existing search.

`Fuel` tests demonstrate CPU reservation arithmetic. They do not verify charging
inside native operators or behavior across geometric rollback. The dry-run's
predicate callback is a trusted test helper; its own execution is outside the
bytecode termination argument.

No failures were observed in the executed cases. These finite tests are not a
complete safety proof or a numerical packing certificate. Only CPython 3.14.7
was exercised in this audit; the package's complete Python 3.11+ support range
was not tested. External literature citations were not independently audited.

## Reproduction

The following commands use the preserved input files and require uv plus the
existing system Python. They need no third-party dependencies or installations.
The verification reran these invocations from the corresponding working
directories before saving the final logs.

```bash
cd /home/user/DEV/asquerix/artifacts/audit/strategy-reference-20261009
export UV_CACHE_DIR=/tmp/asquerix-strategy-uv-cache
export PYTHONDONTWRITEBYTECODE=1

(
  cd reference
  uv run --no-project --python /usr/bin/python3 python strategy_reference.py
  uv run --no-project --python /usr/bin/python3 python -m unittest -v test_strategy_reference.py
)

PYTHONPATH=reference uv run --no-project --python /usr/bin/python3 python evidence/doc_example_1_authoring.py
PYTHONPATH=reference uv run --no-project --python /usr/bin/python3 python evidence/doc_example_2_fuel.py
PYTHONPATH=reference uv run --no-project --python /usr/bin/python3 python evidence/doc_example_3_generation.py
uv run --no-project --python /usr/bin/python3 python evidence/differential_check.py reference
```

Logs under `evidence/` and timings in the manifest describe CPU verification
commands only. They are not GPU or packing-performance measurements.
