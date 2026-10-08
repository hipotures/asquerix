# n12-s480-b128-run-20261008T224231Z-e623d409c434 compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 3840
- GPU-feasible trials: 3840
- Trials without an accepted pose: 0
- Budget-exhausted trials: 1453
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 3840 | 4.00019073486 | 4.35880088806 | 4.00020074844 | 5.09786565304 |
| Independently numerically validated | 178 | 4.00019073486 | 4.00040030479 | 4.00019788742 | 5.00020051003 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 3840 | 35 | 83 | 128 | 128 |
| Sweeps | 3840 | 5858 | 24075.5 | 46623.1 | 49797 |

## Independent validation coverage

- Audited trials: 178 / 3840 (0.046)
- Numerically validated: 178
- Indeterminate: 0
- Invalid: 0
- Not checked: 3662

## Termination reasons

- `BUDGET_EXHAUSTED`: 1453
- `STEP_FLOOR_REACHED`: 2387

## Timing

- `module_load_seconds`: 0.136227298994
- `warmup_seconds`: 3.12025567298
- `simulation_seconds`: 133.323113079
- `device_seconds`: 133.318041504
- `transfer_seconds`: 0.031567746948
- `validation_seconds`: 1.86315669518
- `render_seconds`: 0.0160815450072
- `persistence_seconds`: 1.11346361392
- `max_stage_seconds`: 0.689203186035

## Amortized throughput

- `simulation_seconds`: attempted 28.8022077442 trials/s; GPU-feasible 28.8022077442 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 28.803303414 trials/s; GPU-feasible 28.803303414 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 3840,
  "experiment": "n12-s480-b128-run-20261008T224231Z-e623d409c434",
  "experiment_name": "n12-s480-b128-run-20261008T224231Z-e623d409c434",
  "experiment_slug": "n12-s480-b128-run-20261008T224231Z-e623d409c434",
  "leaderboard": [
    {
      "accepted": 96,
      "attempts": 107,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.802840018399335e-05,
        "min_wall_clearance": 1.8245078486245347e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 23,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000190734863281,
      "sweeps": 34873,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2484,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 86,
      "attempts": 97,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799136875459161e-05,
        "min_wall_clearance": 1.8916528353507545e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 26,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001912117004395,
      "sweeps": 28377,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 754,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 110,
      "attempts": 121,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.803548840939584e-05,
        "min_wall_clearance": 1.8034519681187078e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 12,
      "proposals": 20,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001912117004395,
      "sweeps": 41367,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1726,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 113,
      "attempts": 124,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.815036635832712e-05,
        "min_wall_clearance": 1.8038352131100055e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000191688537598,
      "sweeps": 41018,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 825,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 76,
      "attempts": 87,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7893341622103598e-05,
        "min_wall_clearance": 1.8303178647816054e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 27,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001935958862305,
      "sweeps": 26668,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 279,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 67,
      "attempts": 78,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8012096778430298e-05,
        "min_wall_clearance": 1.8203747299327944e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000196933746338,
      "sweeps": 19464,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2046,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 67,
      "attempts": 78,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.79556221492007e-05,
        "min_wall_clearance": 1.8252526670536895e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 15,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000196933746338,
      "sweeps": 13800,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3583,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 74,
      "attempts": 85,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7969097123149425e-05,
        "min_wall_clearance": 1.8084344714175415e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197410583496,
      "sweeps": 25683,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1403,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 62,
      "attempts": 73,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.785545158973712e-05,
        "min_wall_clearance": 1.8204773052588052e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197887420654,
      "sweeps": 20928,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 501,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 61,
      "attempts": 72,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7968735350366558e-05,
        "min_wall_clearance": 1.888676980810189e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 23,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197887420654,
      "sweeps": 19780,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1372,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 54,
      "attempts": 65,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.803025091626612e-05,
        "min_wall_clearance": 1.828588456787017e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197887420654,
      "sweeps": 16473,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1423,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 58,
      "attempts": 69,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7925292256272692e-05,
        "min_wall_clearance": 1.815756127321322e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 25,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197887420654,
      "sweeps": 19609,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2271,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 61,
      "attempts": 72,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.802703682635175e-05,
        "min_wall_clearance": 1.8201272616202857e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 24,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197887420654,
      "sweeps": 21314,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3308,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 84,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800440612061946e-05,
        "min_wall_clearance": 1.8263663652540174e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 15,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 25549,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1331,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 59,
      "attempts": 70,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7935631484666814e-05,
        "min_wall_clearance": 1.834174254788934e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 19833,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2632,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 74,
      "attempts": 85,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.795392654746486e-05,
        "min_wall_clearance": 1.821259619116944e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 18,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 26366,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2886,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 60,
      "attempts": 71,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8107476235407536e-05,
        "min_wall_clearance": 1.8650576143919295e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 12,
      "proposals": 16,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 20222,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3352,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8033015541707442e-05,
        "min_wall_clearance": 1.8499295782348213e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 12,
      "proposals": 20,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 13343,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3829,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 45,
      "attempts": 56,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8117506027515818e-05,
        "min_wall_clearance": 1.8260877325815272e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 24,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 11626,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 579,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 52,
      "attempts": 63,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797401672343213e-05,
        "min_wall_clearance": 1.821716585492794e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 12,
      "proposals": 20,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 16036,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 951,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 56,
      "attempts": 67,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8096719344496402e-05,
        "min_wall_clearance": 1.843969119530442e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 12,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 18451,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1126,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 51,
      "attempts": 62,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7942537871795672e-05,
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
      "proposals": 33,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 15666,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1145,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 61,
      "attempts": 72,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7967949430799455e-05,
        "min_wall_clearance": 1.838008649279743e-05,
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
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 19098,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1546,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 46,
      "attempts": 57,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.805755977235757e-05,
        "min_wall_clearance": 1.8868118023540603e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 25,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 12548,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2000,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 53,
      "attempts": 64,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8062738559826582e-05,
        "min_wall_clearance": 1.8830550236437205e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 12,
      "proposals": 14,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 13783,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3143,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 47,
      "attempts": 58,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7970799723254543e-05,
        "min_wall_clearance": 1.816941429932939e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 12,
      "proposals": 21,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 13390,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3399,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 53,
      "attempts": 64,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8013747764199212e-05,
        "min_wall_clearance": 1.8616412026162266e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 12,
      "proposals": 22,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 13030,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3479,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 114,
      "attempts": 125,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7941537898247262e-05,
        "min_wall_clearance": 1.8060379463946674e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 12,
      "proposals": 20,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 39843,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3795,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 51,
      "attempts": 62,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7932435369381433e-05,
        "min_wall_clearance": 1.886698485131788e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 12,
      "proposals": 33,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000199317932129,
      "sweeps": 15645,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 108,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 64,
      "attempts": 75,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7952567415841696e-05,
        "min_wall_clearance": 1.832048179739587e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 12,
      "proposals": 13,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000199317932129,
      "sweeps": 20289,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 774,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 10000,
  "retained_pose_count": 178,
  "run_id": "run-20261008T224231Z-e623d409c434",
  "run_status": "PARTIAL",
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
  "stop_reason": "SIGINT"
}
```

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
