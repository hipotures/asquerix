# workflow-json-partial-smoke compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 4
- GPU-feasible trials: 4
- Trials without an accepted pose: 0
- Budget-exhausted trials: 3
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 4 | 4.22853422165 | 4.3630964756 | 4.24071867466 | 4.53130366802 |
| Independently numerically validated | 4 | 4.22853422165 | 4.3630964756 | 4.24071867466 | 4.53130366802 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 4 | 120 | 128 | 128 | 128 |
| Sweeps | 4 | 8917 | 11610.5 | 11904.15 | 11934 |

## Independent validation coverage

- Audited trials: 4 / 4 (1.000)
- Numerically validated: 4
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 3
- `STEP_FLOOR_REACHED`: 1

## Timing

- `module_load_seconds`: 0.123406462983
- `warmup_seconds`: 0.760253280983
- `simulation_seconds`: 0.901767588017
- `device_seconds`: 0.901645324707
- `transfer_seconds`: 0.00941087497631
- `validation_seconds`: 0.0613520229526
- `render_seconds`: 0.00186637899606
- `persistence_seconds`: 0.0128721119956
- `max_stage_seconds`: 0.13492326355

## Amortized throughput

- `simulation_seconds`: attempted 4.43573272443 trials/s; GPU-feasible 4.43573272443 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 4.43633421079 trials/s; GPU-feasible 4.43633421079 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 4,
  "experiment": "workflow-json-partial-smoke",
  "experiment_name": "workflow-json-partial-smoke",
  "experiment_slug": "workflow-json-partial-smoke",
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
        "validator_version": "cpu-f64-projection-v2"
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
        "validator_version": "cpu-f64-projection-v2"
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
        "validator_version": "cpu-f64-projection-v2"
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
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 8,
  "retained_pose_count": 4,
  "run_id": "run-20261008T221834Z-81cb5fb7803d",
  "run_status": "PARTIAL",
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

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
