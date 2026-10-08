# demo-rich compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 100
- GPU-feasible trials: 100
- Trials without an accepted pose: 0
- Budget-exhausted trials: 62
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 100 | 4.60236597061 | 5.39999675751 | 4.95387229919 | 6.06553277969 |
| Independently numerically validated | 100 | 4.60236597061 | 5.39999675751 | 4.95387229919 | 6.06553277969 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 100 | 35 | 128 | 128 | 128 |
| Sweeps | 100 | 1863 | 11944.5 | 12848.35 | 12911 |

## Independent validation coverage

- Audited trials: 100 / 100 (1.000)
- Numerically validated: 100
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 62
- `STEP_FLOOR_REACHED`: 38

## Timing

- `module_load_seconds`: 0.109014410002
- `warmup_seconds`: 1.436003415
- `simulation_seconds`: 1.99746092001
- `device_seconds`: 1.99736010742
- `transfer_seconds`: 0.0125720170035
- `validation_seconds`: 3.08356773382
- `render_seconds`: 0.0100776080217
- `persistence_seconds`: 0.679996771012
- `max_stage_seconds`: 0.280124420166

## Amortized throughput

- `simulation_seconds`: attempted 50.0635576887 trials/s; GPU-feasible 50.0635576887 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 50.0660845425 trials/s; GPU-feasible 50.0660845425 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 100,
  "experiment": "demo-rich",
  "experiment_name": "demo-rich",
  "experiment_slug": "demo-rich",
  "leaderboard": [
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7960198523070403e-05,
        "min_wall_clearance": 1.8214287446305377e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 44,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.602365970611572,
      "sweeps": 12868,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 11,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 31,
      "attempts": 42,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8047109053231924e-05,
        "min_wall_clearance": 1.8439690931959518e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.709184169769287,
      "sweeps": 2760,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 20,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8401785155441885e-05,
        "min_wall_clearance": 1.8158118702427117e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8298625946044922e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 36,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.8089776039123535,
      "sweeps": 12060,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 23,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 34,
      "attempts": 45,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8207353273735905e-05,
        "min_wall_clearance": 1.8976132940551338e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.812699794769287,
      "sweeps": 2943,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 48,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 29,
      "attempts": 40,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.794859329301568e-05,
        "min_wall_clearance": 1.856395871335792e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.9419965744018555,
      "sweeps": 2470,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 5,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 34,
      "attempts": 45,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.811155976727541e-05,
        "min_wall_clearance": 1.8177522184359418e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.954497337341309,
      "sweeps": 3077,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 95,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7976352876036827e-05,
        "min_wall_clearance": 1.8825963147506286e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.007605075836182,
      "sweeps": 12103,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 69,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 47,
      "attempts": 58,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.80011140276104e-05,
        "min_wall_clearance": 1.897555846497312e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.0652360916137695,
      "sweeps": 4616,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 73,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8143226997224815e-05,
        "min_wall_clearance": 1.8845080545837334e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.066394329071045,
      "sweeps": 11888,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 56,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 52,
      "attempts": 63,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8000025620412696e-05,
        "min_wall_clearance": 1.8753607720967125e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.104883670806885,
      "sweeps": 5279,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 28,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 100,
  "retained_pose_count": 100,
  "run_id": "run-20261008T223741Z-619df56a13a7",
  "run_status": "COMPLETED",
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

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
