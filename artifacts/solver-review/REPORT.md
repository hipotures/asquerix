# Compression stopping review: trial 4124

Reviewed revision: `d4884c9214da01c00a2e10b93f55542276de95c8`.
Input: `artifacts/audit/campaign/retained-n11/poses/trial-4124.json`.
This review addresses the visually loose packing at `L=4.152742862701416`,
not the global square-packing problem.

## Findings

### Rotations and sliding are not disabled

`correct_pair` updates both centers and both angles. `correct_wall` updates
position and angle using the derivative of the support function. There is no
tangential friction constraint, sticky contact, or permanent attachment to a
wall. The box is centered at the origin: all four walls move when L decreases.

However, the algorithm is bounded sequential constraint projection, not an
oracle for mechanical equilibrium or collective jamming. A collision-free
saved pose can still admit movement. `NUMERICALLY_VALIDATED` concerns geometry,
not convergence, rigidity, or optimality. The contact formulas were not changed
by this patch.

### An admissible compression step was skipped

The original failure branch multiplied the step by `0.5` and then terminated
when the result was below `step_floor`. With the defaults, the last tested
step was about `0.0001953125`; halving produced `0.00009765625`, below the
configured floor `0.0001`. The admissible step `0.0001` was never attempted.
The archived trial has exactly this final step and `STEP_FLOOR_REACHED`.

The fix clamps the next proposed step to the configured floor and terminates
for floor failure only after an unsuccessful attempt actually used that floor.
A successful floor step can be followed by another. Exhausting the attempt
budget before trying the floor remains `BUDGET_EXHAUSTED`.

A deterministic one-square regression isolates this defect from complicated
contacts. A centered unit square in a box of side `1.00018` cannot fit after a
reduction of `0.0001953125`, but fits with the unchanged guard after a reduction
of `0.0001`. The old policy stops without trying the feasible reduction; the
new policy accepts it. This does not require shaking, morphing, added torque,
or relaxed collision tolerances.

### The 120-sweep cap can interrupt convergence

I resumed the saved trial 4124 coordinates, rather than generating a new random
world. The observations below come from the actual source function bodies
executed with scalar NumPy FP32 primitives. They are diagnostic results, **not
compiled Warp or CUDA results**, and need confirmation on the target backend.
The scalar adapter does not reproduce compiler transformations, FMA, or device
math implementations.

| Source/policy | Sweep cap per attempt | Attempts executed | Sweeps executed | Accepted side |
| --- | ---: | ---: | ---: | ---: |
| Original, original last step | 120 | 1 | 120 | 4.152742862701416 (unchanged) |
| Fixed, same initial step, then exact floor | 120 | 2 | 220 | 4.152642726898193 |
| Original, original last step | 240 | 1 | 122 | 4.152547359466553 |

Thus, in this diagnostic execution the larger proposed reduction needed just
two more sweeps than the default cap. The floor retry converged in 100 sweeps.
The rotations changed; the solver did not need a new rotation operator.

Independent float64 vertex-projection checks found positive pair and wall
clearances in both smaller configurations. For the fixed-policy result:

- Minimum pair separation: `1.8100931794329256e-5`.
- Minimum wall clearance: `1.8217165988154704e-5`.

For the 240-sweep-cap result:

- Minimum pair separation: `1.8043456413430192e-5`.
- Minimum wall clearance: `1.815756127321322e-5`.

Coordinates, counters, source hashes, and validation diagnostics are saved in
`source-checks.json`. These checks are numerical, not exact certificates.
Transient projection iterates may overlap, as in the existing algorithm; this
review does not certify a continuous collision-free motion between iterates.

## What changed and what did not

Only the compression-floor scheduling/termination policy changed in production.
Default attempt/sweep budgets, contact equations, guard, acceptance tolerance,
FP32 geometry, rotation mobility, rollback, and GPU execution mapping are
unchanged. Existing pilot and audit evidence remains untouched.

This is not a general solution for all L-shaped or wall-aligned traps. A finite
sweep limit can still reject a feasible proposal, and monotone compression can
still produce poor packings. Historical benchmark results must not be presented
as measurements of the patched version.

The existing kernel's `debug` trace contains only the accepted side after each
attempt. It does not record poses, contact sweeps, attempted states, or rollback
trajectories. A trajectory viewer requires additional instrumentation; it is not
implemented by this stopping-policy fix.

## Verification actually performed

Local diagnostic environment: Python 3.13.5, NumPy 2.3.5, no Warp, no CUDA device.

The fetched original `gpu.py` was reconstructed byte for byte and its Git blob
hash checked as `1f8283435ee8356684d262f1da3b64a75529b9c0` before editing.
Python syntax compilation of the patched module and the new tests passed.
Four scalar source-body regression scenarios passed: a successful floor retry,
budget exhaustion before that retry, failed-floor termination with rollback,
and repeated successful floor steps before an eventual failed floor attempt.
The three saved-pose diagnostics above were executed and independently checked.

`tests/test_step_floor.py` adds four scenarios on each of Warp CPU and CUDA:
eight backend-parametrized cases. **These native Warp tests and the repository's
full pytest suite were not executed in this review environment**, which has
neither Warp nor a CUDA device. No GPU benchmark was performed. The change is
therefore submitted on a separate branch for target-machine verification.

## Reproduction

From the repository root, the diagnostic source-body adapter needs NumPy but
not Warp. It always labels its output as a non-CUDA diagnostic:

```bash
uv run python artifacts/solver-review/replay_source.py
```

To compare the original source against the same saved pose:

```bash
git show d4884c9:src/asquerix/gpu.py > /tmp/asquerix-gpu-d4884c9.py
uv run python artifacts/solver-review/replay_source.py \
  --source /tmp/asquerix-gpu-d4884c9.py --attempts 2 --sweeps 120
uv run python artifacts/solver-review/replay_source.py \
  --source /tmp/asquerix-gpu-d4884c9.py --attempts 1 --sweeps 240
```

Run the actual backend regression tests on the development machine before
merging, then run the full suite:

```bash
uv run pytest -q tests/test_step_floor.py
uv run pytest -q
```

A fresh GPU experiment on the same seed/ID, with a larger sweep budget:

```bash
uv run asquerix run --n 11 --seed 20261008 --trial-offset 4124 \
  --trials 1 --batch-size 1 --max-sweeps 240 --retain-all \
  --sample-every 0 --max-images 1 --max-seconds 30 \
  --output runs/trial-4124-sweeps-240
```

That last command reruns the whole random experiment, rather than resuming the
archived final pose; changing the sweep budget can change earlier accepted
states. It is a proposed target-machine check, not a command executed here.
