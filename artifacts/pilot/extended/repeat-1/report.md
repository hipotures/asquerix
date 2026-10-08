# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 12288
- GPU-feasible trials: 12288
- Trials without an accepted pose: 0
- Budget-exhausted trials: 6873
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 12288 | 4.00020027161 | 4.62030816078 | 4.26504437923 | 5.57121376991 |
| Independently numerically validated | 114 | 4.00020027161 | 4.3953166008 | 4.01911227703 | 5.44991912842 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 12288 | 33 | 128 | 128 | 128 |
| Sweeps | 12288 | 1666 | 11155.5 | 12480 | 13299 |

## Independent validation coverage

- Audited trials: 114 / 12288 (0.009)
- Numerically validated: 114
- Indeterminate: 0
- Invalid: 0
- Not checked: 12174

## Termination reasons

- `BUDGET_EXHAUSTED`: 6873
- `STEP_FLOOR_REACHED`: 5415

## Timing

- `module_load_seconds`: 0.00037645798875
- `warmup_seconds`: 0.786891652009
- `simulation_seconds`: 29.084272266
- `device_seconds`: 29.0810675049
- `transfer_seconds`: 0.0242068340594
- `validation_seconds`: 0.738416148932
- `render_seconds`: 0.00200907001272
- `report_seconds`: 0.0460880169994
- `persistence_seconds`: 0.118211108056
- `max_stage_seconds`: 0.175208450317
- `end_to_end_seconds`: 30.978148856

## Amortized throughput

- `simulation_seconds`: attempted 422.496388688 trials/s; GPU-feasible 422.496388688 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 422.542948189 trials/s; GPU-feasible 422.542948189 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 396.666697456 trials/s; GPU-feasible 396.666697456 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 52,
      "attempts": 63,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8017752592770147e-05,
        "min_wall_clearance": 1.856174380243658e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 12,
      "proposals": 22,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000200271606445,
      "sweeps": 4372,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 6233,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8059530536265796e-05,
        "min_wall_clearance": 1.8493733586755212e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 12,
      "proposals": 15,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 2952,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3801,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8359589340821714e-05,
        "min_wall_clearance": 1.8202943943279593e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8358230590820312e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 24,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 2881,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 11032,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 99,
      "attempts": 110,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.801294591243779e-05,
        "min_wall_clearance": 1.8140965597268632e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 22,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000202655792236,
      "sweeps": 9834,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 8314,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 84,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8018671474662185e-05,
        "min_wall_clearance": 1.7999812542690563e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000207901000977,
      "sweeps": 6312,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 476,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.806184493324814e-05,
        "min_wall_clearance": 1.814504479025203e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 25,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.012516975402832,
      "sweeps": 11166,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 1611,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 50,
      "attempts": 61,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800059886614136e-05,
        "min_wall_clearance": 1.814166803626449e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 19,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.022663593292236,
      "sweeps": 4221,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 420,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 84,
      "attempts": 95,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7957088060883974e-05,
        "min_wall_clearance": 1.8336375277705486e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 14,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.027942657470703,
      "sweeps": 7950,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4684,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8077306771557833e-05,
        "min_wall_clearance": 1.8416410895838453e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.028914928436279,
      "sweeps": 11518,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 10003,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 33,
      "attempts": 44,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.857662599724641e-05,
        "min_wall_clearance": 1.8097956384188763e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8596649169921875e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.031255722045898,
      "sweeps": 2150,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 9843,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 12288,
  "retained_pose_count": 86,
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
