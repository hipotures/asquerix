# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 512
- GPU-feasible trials: 512
- Trials without an accepted pose: 0
- Budget-exhausted trials: 284
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 512 | 4.00020074844 | 4.46553635597 | 4.12516522408 | 5.39739179611 |
| Independently numerically validated | 45 | 4.00020074844 | 4.44257545471 | 4.00024671555 | 5.66071720123 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 512 | 34 | 128 | 128 | 128 |
| Sweeps | 512 | 1757 | 10987.5 | 12290.35 | 13039 |

## Independent validation coverage

- Audited trials: 45 / 512 (0.088)
- Numerically validated: 45
- Indeterminate: 0
- Invalid: 0
- Not checked: 467

## Termination reasons

- `BUDGET_EXHAUSTED`: 284
- `STEP_FLOOR_REACHED`: 228

## Timing

- `device_seconds`: 1.07738110352
- `end_to_end_seconds`: 1.58428776701
- `max_stage_seconds`: 0.157552642822
- `module_load_seconds`: 0.000290216994472
- `persistence_seconds`: 0.0124666179763
- `render_seconds`: 0.00197285000468
- `report_seconds`: 0.00429555997835
- `simulation_seconds`: 1.07750494702
- `transfer_seconds`: 0.00128434199723
- `validation_seconds`: 0.282177607907
- `warmup_seconds`: 0.158615714987

## Amortized throughput

- `simulation_seconds`: attempted 475.171832309 trials/s; GPU-feasible 475.171832309 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 475.226452672 trials/s; GPU-feasible 475.226452672 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 323.17361193 trials/s; GPU-feasible 323.17361193 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800060311762941e-05,
        "min_wall_clearance": 1.8097956698603923e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 11,
      "proposals": 19,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 2319,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 252,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 42,
      "attempts": 53,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8054543791390376e-05,
        "min_wall_clearance": 1.905860945328186e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.9073486328125e-05,
      "n": 11,
      "proposals": 19,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.00020170211792,
      "sweeps": 3217,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 183,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 84,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.818130156228115e-05,
        "min_wall_clearance": 1.8177385590067985e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 11,
      "proposals": 17,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000207901000977,
      "sweeps": 6305,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 476,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7986495269628477e-05,
        "min_wall_clearance": 1.803835186464653e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 11,
      "proposals": 14,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000401973724365,
      "sweeps": 11274,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 328,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7974608932442692e-05,
        "min_wall_clearance": 1.8753607720967125e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8030405044555664e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 11,
      "proposals": 15,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.004286766052246,
      "sweeps": 10534,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 337,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 43,
      "attempts": 54,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7952536012888487e-05,
        "min_wall_clearance": 1.8335754532028403e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 11,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.022663593292236,
      "sweeps": 3260,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 420,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 48,
      "attempts": 59,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8008512002509747e-05,
        "min_wall_clearance": 1.8567972347227624e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 11,
      "proposals": 12,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.03359842300415,
      "sweeps": 4223,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 20,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8022525753592922e-05,
        "min_wall_clearance": 1.815756127321322e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 11,
      "proposals": 19,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.033607482910156,
      "sweeps": 11250,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 156,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.803928913165012e-05,
        "min_wall_clearance": 1.893242159223263e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 11,
      "proposals": 21,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0406389236450195,
      "sweeps": 11917,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 485,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 33,
      "attempts": 44,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.848179026331387e-05,
        "min_wall_clearance": 1.808462231522867e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8537044525146484e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 11,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0421929359436035,
      "sweeps": 2179,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 123,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 512,
  "retained_pose_count": 45,
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
