# Compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 4
- GPU-feasible trials: 0
- Trials without an accepted pose: 4
- Budget-exhausted trials: 0
- Other initialization failures: 4
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 0 | — | — | — | — |
| Independently numerically validated | 0 | — | — | — | — |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 4 | 0 | 0 | 0 | 0 |
| Sweeps | 4 | 0 | 0 | 0 | 0 |

## Independent validation coverage

- Audited trials: 0 / 4 (0.000)
- Numerically validated: 0
- Indeterminate: 0
- Invalid: 0
- Not checked: 4

## Termination reasons

- `INIT_FAILED`: 4

## Timing

- `device_seconds`: 7.16800009832e-06
- `end_to_end_seconds`: 0.613530675007
- `max_stage_seconds`: 4.09599998966e-06
- `module_load_seconds`: 0.221853440016
- `persistence_seconds`: 0.000909694994334
- `render_seconds`: 0.00096943799872
- `report_seconds`: 0.0130175349768
- `simulation_seconds`: 0.000198634021217
- `transfer_seconds`: 0.000170932995388
- `validation_seconds`: 0
- `warmup_seconds`: 0.00181803698069

## Amortized throughput

- `simulation_seconds`: attempted 20137.5372431 trials/s; GPU-feasible 0 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 558035.706632 trials/s; GPU-feasible 0 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.
- `end_to_end_seconds`: attempted 6.51964141801 trials/s; GPU-feasible 0 trials/s. Amortized throughput over the end-to-end wall-clock interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "leaderboard": [],
  "requested_trials": 4,
  "retained_pose_count": 4,
  "solver": {
    "acceptance_tolerance": 2e-06,
    "guard": 2e-05,
    "initial_side": 1.5,
    "max_attempts": 0,
    "max_rotation": 0.08,
    "max_sweeps": 120,
    "max_translation": 0.1,
    "motion_tolerance": 1e-07,
    "n": 2,
    "proposals_per_square": 1,
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
