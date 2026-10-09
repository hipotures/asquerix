# n12-s480-b8-run-20261009T001019Z-d20a5541585b compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 8
- GPU-feasible trials: 8
- Trials without an accepted pose: 0
- Budget-exhausted trials: 2
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 8 | 4.00010061264 | 4.06523919106 | 4.00010061264 | 4.37989046574 |
| Independently numerically validated | 8 | 4.00010061264 | 4.06523919106 | 4.00010061264 | 4.37989046574 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 8 | 52 | 93.5 | 128 | 128 |
| Sweeps | 8 | 8709 | 29688 | 45447.6 | 45827 |

## Independent validation coverage

- Audited trials: 8 / 8 (1.000)
- Numerically validated: 8
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 2
- `STEP_FLOOR_REACHED`: 6

## Timing

- `module_load_seconds`: 0.150637448009
- `warmup_seconds`: 2.237490834
- `simulation_seconds`: 2.788253423
- `device_seconds`: 2.78813378906
- `transfer_seconds`: 0.00491904604132
- `validation_seconds`: 0.064574355958
- `render_seconds`: 0.00085771799786
- `persistence_seconds`: 0.0714813430105
- `max_stage_seconds`: 0.466056945801

## Amortized throughput

- `simulation_seconds`: attempted 2.86917965706 trials/s; GPU-feasible 2.86917965706 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 2.86930276853 trials/s; GPU-feasible 2.86930276853 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 8,
  "experiment": "n12-s480-b8-run-20261009T001019Z-d20a5541585b",
  "experiment_name": "n12-s480-b8-run-20261009T001019Z-d20a5541585b",
  "experiment_slug": "n12-s480-b8-run-20261009T001019Z-d20a5541585b",
  "leaderboard": [
    {
      "accepted": 40,
      "attempts": 52,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8002183517145238e-05,
        "min_wall_clearance": 1.8753607720967125e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000100612640381,
      "sweeps": 8709,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 40,
      "attempts": 52,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.792476335960025e-05,
        "min_wall_clearance": 1.811421351938236e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 23,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000100612640381,
      "sweeps": 8775,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 7,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 8,
  "retained_pose_count": 8,
  "run_id": "run-20261009T001019Z-d20a5541585b",
  "run_status": "COMPLETED",
  "solver": {
    "acceptance_tolerance": 2e-06,
    "guard": 2e-05,
    "initial_side": 10.0,
    "max_attempts": 128,
    "max_rotation": 0.08,
    "max_sweeps": 480,
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

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
