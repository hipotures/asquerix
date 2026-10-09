# trajectory-best-demo compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 32
- GPU-feasible trials: 32
- Trials without an accepted pose: 0
- Budget-exhausted trials: 10
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 32 | 4.00010061264 | 4.35040688515 | 4.00010061264 | 5.02108623981 |
| Independently numerically validated | 22 | 4.00010061264 | 4.11006689072 | 4.00010061264 | 5.00325932503 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 32 | 42 | 65.5 | 128 | 128 |
| Sweeps | 32 | 7032 | 17900.5 | 45942.2 | 48099 |

## Independent validation coverage

- Audited trials: 22 / 32 (0.688)
- Numerically validated: 22
- Indeterminate: 0
- Invalid: 0
- Not checked: 10

## Termination reasons

- `BUDGET_EXHAUSTED`: 10
- `STEP_FLOOR_REACHED`: 22

## Timing

- `module_load_seconds`: 0.151812277036
- `warmup_seconds`: 3.7706675831
- `simulation_seconds`: 6.348313728
- `device_seconds`: 6.34721289063
- `transfer_seconds`: 0.012636178988
- `validation_seconds`: 0.335068056069
- `render_seconds`: 0.00676279800246
- `persistence_seconds`: 0.313261509995
- `max_stage_seconds`: 1.01420849609

## Amortized throughput

- `simulation_seconds`: attempted 5.04070866234 trials/s; GPU-feasible 5.04070866234 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 5.04158290441 trials/s; GPU-feasible 5.04158290441 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 32,
  "experiment": "trajectory-best-demo",
  "experiment_name": "trajectory-best-demo",
  "experiment_slug": "trajectory-best-demo",
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
    },
    {
      "accepted": 40,
      "attempts": 52,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.81670124304114e-05,
        "min_wall_clearance": 1.8276770562764e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 19,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000100612640381,
      "sweeps": 8475,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 10,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 67,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8028015154451378e-05,
        "min_wall_clearance": 1.8872817010517906e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000101566314697,
      "sweeps": 18146,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 24,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 95,
      "attempts": 107,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8073912225857747e-05,
        "min_wall_clearance": 1.820127291862761e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000199794769287,
      "sweeps": 36757,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 5,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.807063488734606e-05,
        "min_wall_clearance": 1.8325947767294792e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.022468566894531,
      "sweeps": 44743,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 2,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 35,
      "attempts": 47,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7965049009832645e-05,
        "min_wall_clearance": 1.8856923651000557e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 12,
      "proposals": 15,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0334038734436035,
      "sweeps": 8441,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 28,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 70,
      "attempts": 82,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.793566548508041e-05,
        "min_wall_clearance": 1.8217165988154704e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.049123287200928,
      "sweeps": 25958,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 27,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8052909473462858e-05,
        "min_wall_clearance": 1.8901825167727537e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 17,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.06895112991333,
      "sweeps": 45435,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 12,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 117,
      "attempts": 128,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7913100465782872e-05,
        "min_wall_clearance": 1.8634398431416344e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.073663234710693,
      "sweeps": 45155,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 31,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 32,
  "retained_pose_count": 22,
  "run_id": "run-20261009T090828Z-674546d6c151",
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
