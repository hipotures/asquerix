# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 8
- GPU-feasible trials: 8
- Trials without an accepted pose: 0
- Budget-exhausted trials: 5
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 8 | 4.9419965744 | 5.52754306793 | 5.02149856091 | 5.83967308998 |
| Independently numerically validated | 8 | 4.9419965744 | 5.52754306793 | 5.02149856091 | 5.83967308998 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 8 | 37 | 128 | 128 | 128 |
| Sweeps | 8 | 1863 | 12064 | 12649.45 | 12654 |

## Independent validation coverage

- Audited trials: 8 / 8 (1.000)
- Numerically validated: 8
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 5
- `STEP_FLOOR_REACHED`: 3

## Timing

- `device_seconds`: 1.79581958008
- `end_to_end_seconds`: 3.416455762
- `max_stage_seconds`: 0.258112518311
- `module_load_seconds`: 0.00261465000222
- `persistence_seconds`: 0.00154461301281
- `render_seconds`: 0.00146195699926
- `report_seconds`: 0.00152685999637
- `simulation_seconds`: 1.79604419001
- `transfer_seconds`: 0.000624186970526
- `validation_seconds`: 0.0754376130062
- `warmup_seconds`: 1.50134975699

## Amortized throughput

- `simulation_seconds`: attempted 4.45423338942 trials/s; GPU-feasible 4.45423338942 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 4.45479049719 trials/s; GPU-feasible 4.45479049719 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 2.34160795787 trials/s; GPU-feasible 2.34160795787 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
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
        "validator_version": "cpu-f64-projection-v1"
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
      "accepted": 29,
      "attempts": 40,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8086201180489425e-05,
        "min_wall_clearance": 1.809795656537716e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 30,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.169145107269287,
      "sweeps": 2252,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.788409127612134e-05,
        "min_wall_clearance": 1.87558513538022e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 27,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.172454357147217,
      "sweeps": 12131,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 2,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 121,
      "attempts": 128,
      "final_step": 0.0015625000232830644,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8048304833317985e-05,
        "min_wall_clearance": 1.8317171401438515e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 7,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.432807445526123,
      "sweeps": 12654,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.801327667627639e-05,
        "min_wall_clearance": 1.905550202652151e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.9073486328125e-05,
      "n": 16,
      "proposals": 47,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.622278690338135,
      "sweeps": 11997,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 3,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8098382263576074e-05,
        "min_wall_clearance": 1.879731887566294e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 43,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.639449596405029,
      "sweeps": 12641,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 0,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 26,
      "attempts": 37,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800129714579768e-05,
        "min_wall_clearance": 1.8039015712290052e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 16,
      "proposals": 45,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.639847755432129,
      "sweeps": 1863,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 7,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.817827941996697e-05,
        "min_wall_clearance": 1.8965489367417376e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 66,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 5.947271347045898,
      "sweeps": 12471,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 6,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "requested_trials": 8,
  "retained_pose_count": 8,
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
