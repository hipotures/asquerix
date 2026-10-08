# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 512
- GPU-feasible trials: 512
- Trials without an accepted pose: 0
- Budget-exhausted trials: 313
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 512 | 4.58729362488 | 5.43633770943 | 5.0347012043 | 6.01318771839 |
| Independently numerically validated | 46 | 4.58729362488 | 5.41435146332 | 4.70952606201 | 6.08867311478 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 512 | 34 | 128 | 128 | 128 |
| Sweeps | 512 | 1863 | 11890.5 | 12833.25 | 13282 |

## Independent validation coverage

- Audited trials: 46 / 512 (0.090)
- Numerically validated: 46
- Indeterminate: 0
- Invalid: 0
- Not checked: 466

## Termination reasons

- `BUDGET_EXHAUSTED`: 313
- `STEP_FLOOR_REACHED`: 199

## Timing

- `device_seconds`: 2.11608276367
- `end_to_end_seconds`: 4.39421565001
- `max_stage_seconds`: 0.291655029297
- `module_load_seconds`: 0.000386068015359
- `persistence_seconds`: 0.0118453160103
- `render_seconds`: 0.00196197998594
- `report_seconds`: 0.00378773201373
- `simulation_seconds`: 2.11620605201
- `transfer_seconds`: 0.00123060095939
- `validation_seconds`: 0.655822087923
- `warmup_seconds`: 1.54989768899

## Amortized throughput

- `simulation_seconds`: attempted 241.942413648 trials/s; GPU-feasible 241.942413648 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 241.956509826 trials/s; GPU-feasible 241.956509826 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 116.516812278 trials/s; GPU-feasible 116.516812278 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
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
        "validator_version": "cpu-f64-projection-v1"
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
        "validator_version": "cpu-f64-projection-v1"
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
        "validator_version": "cpu-f64-projection-v1"
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
        "validator_version": "cpu-f64-projection-v1"
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
        "validator_version": "cpu-f64-projection-v1"
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
        "validator_version": "cpu-f64-projection-v1"
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
      "accepted": 31,
      "attempts": 42,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.793019942120111e-05,
        "min_wall_clearance": 1.85793447551319e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.858598232269287,
      "sweeps": 2468,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 395,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8039778296147224e-05,
        "min_wall_clearance": 1.878981244374245e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8030405044555664e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.873459339141846,
      "sweeps": 11841,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 106,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8095122544137254e-05,
        "min_wall_clearance": 1.8005989369740405e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 49,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.882819652557373,
      "sweeps": 5630,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 266,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8003232856944607e-05,
        "min_wall_clearance": 1.8141667819548957e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 76,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.932834148406982,
      "sweeps": 9902,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 261,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 512,
  "retained_pose_count": 46,
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
