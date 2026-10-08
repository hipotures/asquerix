# demo-rich compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 1000
- GPU-feasible trials: 1000
- Trials without an accepted pose: 0
- Budget-exhausted trials: 597
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 1000 | 4.58729362488 | 5.43164873123 | 5.00019979477 | 5.98742620945 |
| Independently numerically validated | 1000 | 4.58729362488 | 5.43164873123 | 5.00019979477 | 5.98742620945 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 1000 | 32 | 128 | 128 | 128 |
| Sweeps | 1000 | 1809 | 11830 | 12861.05 | 13433 |

## Independent validation coverage

- Audited trials: 1000 / 1000 (1.000)
- Numerically validated: 1000
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 597
- `STEP_FLOOR_REACHED`: 403

## Timing

- `module_load_seconds`: 0.160539947014
- `warmup_seconds`: 1.42491160202
- `simulation_seconds`: 2.05390506799
- `device_seconds`: 2.05379174805
- `transfer_seconds`: 0.0102818830055
- `validation_seconds`: 17.1808289903
- `render_seconds`: 0.00674442801392
- `persistence_seconds`: 6.04747123898
- `max_stage_seconds`: 0.285947113037

## Amortized throughput

- `simulation_seconds`: attempted 486.877419791 trials/s; GPU-feasible 486.877419791 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 486.904283724 trials/s; GPU-feasible 486.904283724 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 1000,
  "experiment": "demo-rich",
  "experiment_name": "demo-rich",
  "experiment_slug": "demo-rich",
  "leaderboard": [
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8013942172934172e-05,
        "min_wall_clearance": 1.8216353227185067e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.58729362487793,
      "sweeps": 12215,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 306,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
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
      "accepted": 31,
      "attempts": 42,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8033618980506372e-05,
        "min_wall_clearance": 1.840794091378939e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.710551738739014,
      "sweeps": 2406,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 274,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 99,
      "attempts": 110,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8052674596202856e-05,
        "min_wall_clearance": 1.827677044374809e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 28,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.798253059387207,
      "sweeps": 10229,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 571,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 27,
      "attempts": 38,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8138379939580673e-05,
        "min_wall_clearance": 1.833863804767688e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 51,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.800004959106445,
      "sweeps": 1998,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 558,
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
      "accepted": 71,
      "attempts": 82,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7968791595546207e-05,
        "min_wall_clearance": 1.8149984015725096e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 57,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.843169212341309,
      "sweeps": 7180,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 926,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 28,
      "attempts": 39,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7865883656431603e-05,
        "min_wall_clearance": 1.8283724125822687e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 40,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.843754768371582,
      "sweeps": 2238,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 594,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 1000,
  "retained_pose_count": 1000,
  "run_id": "run-20261008T223813Z-c9d5b728c8f7",
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
