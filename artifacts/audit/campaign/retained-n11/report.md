# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 32
- GPU-feasible trials: 32
- Trials without an accepted pose: 0
- Budget-exhausted trials: 16
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 32 | 4.01875257492 | 4.40000677109 | 4.15177469254 | 4.87782659531 |
| Independently numerically validated | 32 | 4.01875257492 | 4.40000677109 | 4.15177469254 | 4.87782659531 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 32 | 41 | 117 | 128 | 128 |
| Sweeps | 32 | 2077 | 10240 | 12240.35 | 12573 |

## Independent validation coverage

- Audited trials: 32 / 32 (1.000)
- Numerically validated: 32
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 16
- `STEP_FLOOR_REACHED`: 16

## Timing

- `module_load_seconds`: 0.152129994007
- `warmup_seconds`: 0.164280814031
- `simulation_seconds`: 1.86808012601
- `device_seconds`: 1.8677902832
- `transfer_seconds`: 0.0092497630103
- `validation_seconds`: 0.351529856009
- `render_seconds`: 0.00214873300865
- `persistence_seconds`: 0.00586105999537
- `max_stage_seconds`: 0.144126968384

## Amortized throughput

- `simulation_seconds`: attempted 17.1298862156 trials/s; GPU-feasible 17.1298862156 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 17.1325444231 trials/s; GPU-feasible 17.1325444231 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7976970451891866e-05,
        "min_wall_clearance": 1.8343859238711957e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 11,
      "proposals": 16,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.018752574920654,
      "sweeps": 11102,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4122,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 36,
      "attempts": 47,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.82175516210345e-05,
        "min_wall_clearance": 1.8622890654018676e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 11,
      "proposals": 20,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.1505913734436035,
      "sweeps": 2279,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4107,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 49,
      "attempts": 60,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.791609068813038e-05,
        "min_wall_clearance": 1.7978747409053142e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 11,
      "proposals": 13,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.152742862701416,
      "sweeps": 3929,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4124,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 32,
  "retained_pose_count": 32,
  "solver": {
    "acceptance_tolerance": 2e-06,
    "guard": 2e-05,
    "initial_side": 10.0,
    "max_attempts": 128,
    "max_rotation": 0.08,
    "max_sweeps": 120,
    "max_translation": 0.1,
    "motion_tolerance": 1e-07,
    "n": 11,
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

Final report and end-to-end timings are in `summary.json`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
