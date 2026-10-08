# n12-s480-b66560-run-20261008T235305Z-3f11275eec60 compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 32768
- GPU-feasible trials: 32768
- Trials without an accepted pose: 0
- Budget-exhausted trials: 16302
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 32768 | 4.00009393692 | 4.35502743721 | 4.00010061264 | 5.0817029953 |
| Independently numerically validated | 26 | 4.00009393692 | 4.01528930664 | 4.00009441376 | 4.70646238327 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 32768 | 36 | 127 | 128 | 128 |
| Sweeps | 32768 | 6288 | 36065.5 | 46699 | 50979 |

## Independent validation coverage

- Audited trials: 26 / 32768 (0.001)
- Numerically validated: 26
- Indeterminate: 0
- Invalid: 0
- Not checked: 32742

## Termination reasons

- `BUDGET_EXHAUSTED`: 16302
- `STEP_FLOOR_REACHED`: 16466

## Timing

- `module_load_seconds`: 2.75329824595
- `warmup_seconds`: 2.93776617595
- `simulation_seconds`: 5.43602433498
- `device_seconds`: 5.43588867188
- `transfer_seconds`: 2.37181993504
- `validation_seconds`: 0.151053884067
- `render_seconds`: 9.54499701038e-05
- `persistence_seconds`: 0.540809548034
- `max_stage_seconds`: 0.793915405273

## Amortized throughput

- `simulation_seconds`: attempted 6027.93475172 trials/s; GPU-feasible 6027.93475172 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 6028.08519047 trials/s; GPU-feasible 6028.08519047 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 32768,
  "experiment": "n12-s480-b66560-run-20261008T235305Z-3f11275eec60",
  "experiment_name": "n12-s480-b66560-run-20261008T235305Z-3f11275eec60",
  "experiment_slug": "n12-s480-b66560-run-20261008T235305Z-3f11275eec60",
  "leaderboard": [
    {
      "accepted": 104,
      "attempts": 116,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8021606432938597e-05,
        "min_wall_clearance": 1.8267632642121612e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 19,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000093936920166,
      "sweeps": 38820,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 27451,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 97,
      "attempts": 109,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8054971964744364e-05,
        "min_wall_clearance": 1.8316341352964116e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 17,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094413757324,
      "sweeps": 37288,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 9300,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 76,
      "attempts": 88,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8041890594178156e-05,
        "min_wall_clearance": 1.836368402940991e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 28,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094413757324,
      "sweeps": 27215,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 9611,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 94,
      "attempts": 106,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7937571741646263e-05,
        "min_wall_clearance": 1.8474222445608035e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 12,
      "proposals": 26,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094890594482,
      "sweeps": 35337,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 19300,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 85,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797795778335498e-05,
        "min_wall_clearance": 1.814166803626449e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094890594482,
      "sweeps": 23200,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 25050,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 65,
      "attempts": 77,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.809074162650859e-05,
        "min_wall_clearance": 1.7975043387963296e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 12,
      "proposals": 22,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095367431641,
      "sweeps": 21112,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 12814,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 88,
      "attempts": 100,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7975066415321095e-05,
        "min_wall_clearance": 1.8378840062727164e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 17,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095367431641,
      "sweeps": 31830,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 32046,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 109,
      "attempts": 121,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7943737418368855e-05,
        "min_wall_clearance": 1.821716633942927e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 26,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 41687,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 6798,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 74,
      "attempts": 86,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8029079477122067e-05,
        "min_wall_clearance": 1.797874727582638e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 12,
      "proposals": 31,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 24245,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 8341,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 75,
      "attempts": 87,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7966548422341943e-05,
        "min_wall_clearance": 1.8499295622476097e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 15031,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 13457,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 32768,
  "retained_pose_count": 26,
  "run_id": "run-20261008T235305Z-3f11275eec60",
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
