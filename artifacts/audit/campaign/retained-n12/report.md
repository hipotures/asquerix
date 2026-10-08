# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 32
- GPU-feasible trials: 32
- Trials without an accepted pose: 0
- Budget-exhausted trials: 14
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 32 | 4.21993303299 | 4.49542164803 | 4.27530536652 | 5.71885380745 |
| Independently numerically validated | 32 | 4.21993303299 | 4.49542164803 | 4.27530536652 | 5.71885380745 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 32 | 37 | 108 | 128 | 128 |
| Sweeps | 32 | 2176 | 9728 | 12465.1 | 12573 |

## Independent validation coverage

- Audited trials: 32 / 32 (1.000)
- Numerically validated: 32
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 14
- `STEP_FLOOR_REACHED`: 18

## Timing

- `module_load_seconds`: 0.00101927199285
- `warmup_seconds`: 0.336345054966
- `simulation_seconds`: 2.18348599999
- `device_seconds`: 2.18313830566
- `transfer_seconds`: 0.00162988904049
- `validation_seconds`: 0.417367858026
- `render_seconds`: 0.00243927398697
- `persistence_seconds`: 0.00616832100786
- `max_stage_seconds`: 0.162073730469

## Amortized throughput

- `simulation_seconds`: attempted 14.6554637859 trials/s; GPU-feasible 14.6554637859 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 14.6577978669 trials/s; GPU-feasible 14.6577978669 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

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
        "min_pair_separation": 1.798374877091946e-05,
        "min_wall_clearance": 1.8719589438997986e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 12,
      "proposals": 17,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.219933032989502,
      "sweeps": 11911,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4097,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 107,
      "attempts": 118,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.798162953409177e-05,
        "min_wall_clearance": 1.867381210640673e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.262322425842285,
      "sweeps": 10342,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 4124,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.786751461718694e-05,
        "min_wall_clearance": 1.8022458624145088e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 12,
      "proposals": 26,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.285927772521973,
      "sweeps": 11340,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4107,
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

Final report and end-to-end timings are in `summary.json`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
