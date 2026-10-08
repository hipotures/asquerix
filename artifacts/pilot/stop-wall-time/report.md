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
| Independently numerically validated | 6 | 4.22853422165 | 4.42540645599 | 4.24884164333 | 4.55084168911 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 8 | 59 | 128 | 128 | 128 |
| Sweeps | 8 | 4113 | 11558.5 | 11968.45 | 11987 |

## Independent validation coverage

- Audited trials: 6 / 8 (0.750)
- Numerically validated: 6
- Indeterminate: 0
- Invalid: 0
- Not checked: 2

## Termination reasons

- `BUDGET_EXHAUSTED`: 5
- `STEP_FLOOR_REACHED`: 3

## Timing

- `device_seconds`: 0.939911193848
- `end_to_end_seconds`: 2.843518493
- `max_stage_seconds`: 0.142675964355
- `module_load_seconds`: 0.283674323
- `persistence_seconds`: 0.00149770398275
- `render_seconds`: 0.00130463999812
- `report_seconds`: 0.0316022080078
- `simulation_seconds`: 0.939985234989
- `transfer_seconds`: 0.0103022159892
- `validation_seconds`: 0.0511907329783
- `warmup_seconds`: 0.802167516988

## Amortized throughput

- `simulation_seconds`: attempted 8.51077198047 trials/s; GPU-feasible 8.51077198047 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 8.51144241325 trials/s; GPU-feasible 8.51144241325 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 2.81341585071 trials/s; GPU-feasible 2.81341585071 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

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
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7983070233928977e-05,
        "min_wall_clearance": 1.8825104854514052e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
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
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8154897875821696e-05,
        "min_wall_clearance": 1.9066736178796617e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
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
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8014450720915676e-05,
        "min_wall_clearance": 1.8318203143685707e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
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
    }
  ],
  "requested_trials": 64,
  "retained_pose_count": 6,
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
  "stop_reason": "MAX_SECONDS"
}
```
