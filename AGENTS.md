# Agent instructions

## Project purpose

This repository is a standalone GPU proof of concept for quasistatic compression of freely translating and rotating unit squares in a square container. The main research case is `n=12`, but `n` is a configurable input, not a constant. Cases such as `n=11` and `n=16` are important controls.

Implementation and audit evidence is preserved under `artifacts/pilot` and `artifacts/audit`. Current maintained reproduction tools live under `tools/`; archived scripts are provenance, not the entry points for new runs.

## Language and role

All authored repository content must be English, including code, comments, documentation, configuration descriptions, CLI messages, reports, chart labels, and commit messages. Conversation with the user may be Polish. Preserve external source data and verbatim logs accurately.

Execute the assigned goal: implement, test, run bounded experiments, preserve artifacts, and report evidence. Do not replace an executable assignment with another proposal. Choose reasonable implementation details independently, but surface genuine blockers and unresolved scientific uncertainty.

## Scope discipline

The legacy compression path remains maintained. The Experiment Laboratory assignment additionally authorizes a single-host FastAPI server and browser client, rigid-square strategy programs, transactional compression/expansion/move/rotation operators, independent random and `(1 + lambda)` mutation search, durable common datasets, and campaign/program/trajectory inspection. The requirements are preserved in `docs/lab-prd.md`. Keep ordinary campaigns uninstrumented and selected replays separate from scientific episode counts.

Do not add morphing, soft shape deformation, crossover, population evolution, modifier frameworks, reinforcement learning, arbitrary executable programs, or production multi-GPU orchestration. Only explicitly programmed rigid-square operations act within an episode; there is no autonomous compressor. Numerical rollback is allowed and does not refund RNG or work. A new initial world is dataset preparation, not an in-trial restart operator.

Use NVIDIA Warp for GPU kernels. Keep one implementation of the production simulation; the independent CPU validator is an oracle, not a second production simulator. Inspect actual installed APIs and wheel/driver compatibility. Do not silently fall back to CPU for a GPU run.

## Scientific invariants

- Every square has side exactly 1 in the mathematical model. Never resize squares to remove overlap or improve a result.
- Accepted geometry, search tolerances, numerical guards, and independent validation are distinct concepts.
- The contact solver must permit both translations and rotations. A translation-only solver does not satisfy the goal.
- A numerical no-motion state is neither a non-overlap certificate nor a proof of optimality.
- Failed search is not a lower bound, impossibility proof, or proof of rigidity.
- A valid construction supports an upper bound. Do not confuse it with the earlier Squares project's lower-bound certificates.
- Reserve `CERTIFIED` for rigorous exact/error-bounded verification. Float64 or extra decimal places alone are insufficient.
- Keep GPU acceptance, independent numerical validation, indeterminate results, and invalid results visibly separate.
- Known-packing fixtures test geometry; random rediscovery tests a heuristic. Do not leak fixtures or known target lengths into ordinary search runs.
- Keep source/date/proof-status metadata for external references. Do not infer current optimality status from an old catalogue.

## GPU and reproducibility

Run many independent worlds per launch or bounded device-resident work submission. Keep initialization, contact iteration, compression decisions, and rollback on the GPU. No per-contact/per-sweep host readback or per-experiment GPU launch loop.

Persist the seed and global trial identifiers. Batch partitioning must not reset random worlds. Record configuration, numerical precision, tolerances, budgets, dependency versions, hardware, and source revision. State the actual scope of deterministic reproducibility.

Report complete-experiment throughput with synchronized/device timing. Separate JIT, warm-up, simulation, transfers, validation, and rendering. Do not improve a benchmark by silently weakening correctness or shortening search budgets.

## Execution and persistence

Run correctness tests before large batches. Start tiny on a display-attached GPU, bound all loops, and keep the initial benchmark campaign short. Stop scheduling after a stop request; preserve completed output and disclose in-flight drain time.

Keep important reports, configurations, selected poses, provenance, and negative results in durable repository-managed locations, not only temporary files. Follow the existing Git workflow and user instructions. Avoid putting huge generated datasets into Git by accident; retain a documented durable location and a reproducible manifest when appropriate.

Do not overwrite unrelated user changes or alter system GPU drivers as a routine setup step. Inspect the environment before choosing installation actions.

Conclude with actual implementation/test/measurement status, artifact paths, tested reproduction commands, and unresolved limitations. Never invent benchmark numbers, successful tests, GPU execution, commits, or pushes.

## Working conventions

Use `uv` for dependency and environment management; never use `pip`.
Choose the simplest implementation that meets the assigned requirements. Do not add speculative abstractions. Historical experiment readers intentionally support both plain and gzip JSON; never rewrite old evidence to adopt a new format.

Inspect Git status, worktrees, HEAD and running experiments before development. Work on `main` in the existing project workspace. Do not create branches or worktrees without explicit user permission. Do not switch branches used by running experiments, touch their partial outputs, or modify their environment. Solver changes require a separate scientific assignment and matched correctness evidence.

Numerical correctness takes precedence over apparent performance. GPU measurements must come from actual synchronized device execution. Keep the GPU engine independent of Rich, gzip and Git. Presentation and persistence occur at existing batch boundaries; publication occurs only after artifact finalization.

Commit task changes using explicit paths, excluding unrelated user changes. Do not finish with uncommitted task changes without explaining why. Use concise English commit messages. Never use `git add -A`, force pushes, destructive resets or cleaning commands. Normal CLI experiments publish only their finalized artifacts on remote `main` using an isolated index and a shared repository lock; `--no-push` is the local-only escape hatch. Preserve results on publication failure. Publication must preserve the existing source tree and history without changing the active checkout or index.

For SQLite snapshots, use SQLite's Online Backup API or `.backup`, never plain `cp`. Test migrations only on a temporary snapshot and verify `PRAGMA integrity_check`.

Always load the `sqlite-optimization` skill before designing or changing SQLite usage: schema, indexes, queries, connection PRAGMAs, transactions or write paths.
