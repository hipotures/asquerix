# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 8
- GPU-feasible trials: 8
- Trials without an accepted pose: 0
- Budget-exhausted trials: 6
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 8 | 4.28905916214 | 4.40899825096 | 4.30382201672 | 4.73559508324 |
| Independently numerically validated | 8 | 4.28905916214 | 4.40899825096 | 4.30382201672 | 4.73559508324 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 8 | 45 | 128 | 128 | 128 |
| Sweeps | 8 | 2573 | 11683 | 11907.5 | 11967 |

## Independent validation coverage

- Audited trials: 8 / 8 (1.000)
- Numerically validated: 8
- Indeterminate: 0
- Invalid: 0
- Not checked: 0

## Termination reasons

- `BUDGET_EXHAUSTED`: 6
- `STEP_FLOOR_REACHED`: 2

## Timing

- `device_seconds`: 0.884410339355
- `end_to_end_seconds`: 1.51955085999
- `max_stage_seconds`: 0.131996963501
- `module_load_seconds`: 0.151084450015
- `persistence_seconds`: 0.00112836799235
- `render_seconds`: 0.00169295200612
- `report_seconds`: 0.0139890190039
- `simulation_seconds`: 0.884505558002
- `transfer_seconds`: 0.00763887498761
- `validation_seconds`: 0.0330655699945
- `warmup_seconds`: 0.151857446996

## Amortized throughput

- `simulation_seconds`: attempted 9.0446011646 trials/s; GPU-feasible 9.0446011646 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 9.04557493734 trials/s; GPU-feasible 9.04557493734 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 5.26471354837 trials/s; GPU-feasible 5.26471354837 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [
    {
      "accepted": 121,
      "attempts": 128,
      "final_step": 0.0015625000232830644,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799246724143444e-05,
        "min_wall_clearance": 1.909534223010212e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.9073486328125e-05,
      "n": 11,
      "proposals": 20,
      "rejected": 7,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.289059162139893,
      "sweeps": 9292,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 1,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 122,
      "attempts": 128,
      "final_step": 0.0031250000465661287,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.813018153051793e-05,
        "min_wall_clearance": 1.814166791369587e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 11,
      "proposals": 13,
      "rejected": 6,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.331238746643066,
      "sweeps": 11743,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 5,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 121,
      "attempts": 128,
      "final_step": 0.0015625000232830644,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7870322768454017e-05,
        "min_wall_clearance": 1.8810191946272425e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 11,
      "proposals": 23,
      "rejected": 7,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.393745422363281,
      "sweeps": 11967,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 6,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 34,
      "attempts": 45,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.86033743477948e-05,
        "min_wall_clearance": 1.819371200229014e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8537044525146484e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 11,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.401567459106445,
      "sweeps": 2573,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 0,
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
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8030405044555664e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 11,
      "proposals": 16,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.416429042816162,
      "sweeps": 11735,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 2,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 120,
      "attempts": 128,
      "final_step": 0.0007812500116415322,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8082380847439516e-05,
        "min_wall_clearance": 1.8382007423323188e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 11,
      "proposals": 18,
      "rejected": 8,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.434383869171143,
      "sweeps": 11631,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 7,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 79,
      "attempts": 90,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.810490097106654e-05,
        "min_wall_clearance": 1.8251894266185786e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8030405044555664e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 11,
      "proposals": 22,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.656262397766113,
      "sweeps": 7564,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8110307445640128e-05,
        "min_wall_clearance": 1.8872817010517906e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v1"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 11,
      "proposals": 16,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.778312683105469,
      "sweeps": 11797,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 4,
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
