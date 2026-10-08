# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 32
- GPU-feasible trials: 32
- Trials without an accepted pose: 0
- Budget-exhausted trials: 22
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 32 | 4.75644111633 | 5.41172409058 | 4.90765328407 | 5.82809391022 |
| Independently numerically validated | 32 | 4.75644111633 | 5.41172409058 | 4.90765328407 | 5.82809391022 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 32 | 40 | 128 | 128 | 128 |
| Sweeps | 32 | 2425 | 12081 | 12874.25 | 12957 |

## Independent validation coverage

- Audited trials: 32 / 32 (1.000)
- Numerically validated: 32
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 22
- `STEP_FLOOR_REACHED`: 10

## Timing

- `module_load_seconds`: 0.00033768999856
- `warmup_seconds`: 1.40246169301
- `simulation_seconds`: 3.76522573299
- `device_seconds`: 3.76490905762
- `transfer_seconds`: 0.00174235200393
- `validation_seconds`: 0.764495925105
- `render_seconds`: 0.00212352399831
- `persistence_seconds`: 0.00537240403355
- `max_stage_seconds`: 0.267370483398

## Amortized throughput

- `simulation_seconds`: attempted 8.49882643679 trials/s; GPU-feasible 8.49882643679 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 8.4995412931 trials/s; GPU-feasible 8.4995412931 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 80,
      "attempts": 91,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799169196436967e-05,
        "min_wall_clearance": 1.8320256240045296e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.756441116333008,
      "sweeps": 8218,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4097,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.808359183308461e-05,
        "min_wall_clearance": 1.8344211078158423e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.794540882110596,
      "sweeps": 12158,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4114,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 34,
      "attempts": 45,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.824538081196536e-05,
        "min_wall_clearance": 1.8016771014206512e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8358230590820312e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 40,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.000199794769287,
      "sweeps": 2425,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4103,
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
    "n": 16,
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
