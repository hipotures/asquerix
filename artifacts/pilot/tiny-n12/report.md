# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 8
- GPU-feasible trials: 8
- Trials without an accepted pose: 0
- Budget-exhausted trials: 5
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 8 | 4.22853422165 | 4.46583223343 | 4.25696461201 | 4.55817034245 |
| Independently numerically validated | 8 | 4.22853422165 | 4.46583223343 | 4.25696461201 | 4.55817034245 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 8 | 59 | 128 | 128 | 128 |
| Sweeps | 8 | 4113 | 11558.5 | 11968.45 | 11987 |

## Independent validation coverage

- Audited trials: 8 / 8 (1.000)
- Numerically validated: 8
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 5
- `STEP_FLOOR_REACHED`: 3

## Timing

- `device_seconds`: 6.06755419922
- `end_to_end_seconds`: 11.95622003
- `module_load_seconds`: 0.159925694985
- `persistence_seconds`: 0.00167483900441
- `render_seconds`: 0.00296571399667
- `report_seconds`: 0.0101575980079
- `simulation_seconds`: 6.06771890898
- `transfer_seconds`: 0.00135241201497
- `validation_seconds`: 0.0727314799442
- `warmup_seconds`: 5.17068233201

## Amortized throughput

- `simulation_seconds`: attempted 1.31845263764 trials/s; GPU-feasible 1.31845263764 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 1.31848842834 trials/s; GPU-feasible 1.31848842834 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 0.66910779326 trials/s; GPU-feasible 0.66910779326 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.22853422164917,
      "sweeps": 11486,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 0,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 109,
      "attempts": 120,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.9073486328125e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.3097639083862305,
      "sweeps": 8917,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8030405044555664e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.416429042816162,
      "sweeps": 11735,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 2,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 23,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.434383869171143,
      "sweeps": 11631,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 7,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 17,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.497280597686768,
      "sweeps": 11987,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 48,
      "attempts": 59,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 28,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.54863977432251,
      "sweeps": 4113,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 6,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 23,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.551575660705566,
      "sweeps": 11934,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 3,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 94,
      "attempts": 105,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.561721324920654,
      "sweeps": 9699,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 5,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 8,
  "retained_pose_count": 8,
  "solver": {
    "acceptance_tolerance": 2e-06,
    "guard": 2e-05,
    "initial_side": 10.0,
    "max_attempts": 128,
    "max_rotation": 0.08,
    "max_sweeps": 120,
    "max_translation": 0.1,
    "motion_tolerance": 1e-07,
    "n": 12,
    "proposals_per_square": 2000,
    "relaxation": 0.8,
    "rotation_mobility": 0.3,
    "seed": 20261008,
    "stagnation_sweeps": 4,
    "step": 0.2,
    "step_floor": 0.0001,
    "step_reduction": 0.5
  },
  "stop_reason": "TRIALS_COMPLETED"
}
```
