# n16-s480-b131000-run-20261008T225441Z-b5c9ec306a8f compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 393000
- GPU-feasible trials: 393000
- Trials without an accepted pose: 0
- Budget-exhausted trials: 168955
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 393000 | 4.00019025803 | 5.05272722244 | 4.79414291382 | 5.47324802876 |
| Independently numerically validated | 511 | 4.00019025803 | 5.03905153275 | 4.00019574165 | 5.50742912292 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 393000 | 29 | 99 | 128 | 128 |
| Sweeps | 393000 | 5638 | 31830 | 48051 | 52502 |

## Independent validation coverage

- Audited trials: 511 / 393000 (0.001)
- Numerically validated: 511
- Indeterminate: 0
- Invalid: 0
- Not checked: 392489

## Termination reasons

- `BUDGET_EXHAUSTED`: 168955
- `STEP_FLOOR_REACHED`: 224045

## Timing

- `module_load_seconds`: 0.125155659014
- `warmup_seconds`: 3.01860208201
- `simulation_seconds`: 202.720305234
- `device_seconds`: 202.717429687
- `transfer_seconds`: 0.0240530839947
- `validation_seconds`: 8.15927022268
- `render_seconds`: 0.0134218580206
- `persistence_seconds`: 5.98411458598
- `max_stage_seconds`: 10.0717714844

## Amortized throughput

- `simulation_seconds`: attempted 1938.63165087 trials/s; GPU-feasible 1938.63165087 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 1938.65915035 trials/s; GPU-feasible 1938.65915035 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 393000,
  "experiment": "n16-s480-b131000-run-20261008T225441Z-b5c9ec306a8f",
  "experiment_name": "n16-s480-b131000-run-20261008T225441Z-b5c9ec306a8f",
  "experiment_slug": "n16-s480-b131000-run-20261008T225441Z-b5c9ec306a8f",
  "leaderboard": [
    {
      "accepted": 91,
      "attempts": 102,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7996121989952443e-05,
        "min_wall_clearance": 1.888401139016338e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000190258026123,
      "sweeps": 28663,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 93877,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 113,
      "attempts": 124,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8072287585246428e-05,
        "min_wall_clearance": 1.8992026300068687e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000192642211914,
      "sweeps": 35620,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 345360,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 60,
      "attempts": 71,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8233899545548563e-05,
        "min_wall_clearance": 1.8737714361449775e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 16,
      "proposals": 57,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 14091,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 58619,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 88,
      "attempts": 99,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799577109129534e-05,
        "min_wall_clearance": 1.8978578116612965e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 20805,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 137426,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 91,
      "attempts": 102,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8162566568264167e-05,
        "min_wall_clearance": 1.903051574325687e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 54,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 32170,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 224831,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 89,
      "attempts": 100,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.801432282624722e-05,
        "min_wall_clearance": 1.8916528353507545e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 17077,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 234984,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 60,
      "attempts": 71,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7995533961423504e-05,
        "min_wall_clearance": 1.8155982179468566e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 26,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 12572,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 298713,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 89,
      "attempts": 100,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7999333153439157e-05,
        "min_wall_clearance": 1.809795656537716e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194072723389,
      "sweeps": 19690,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 320003,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 92,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8003446361909487e-05,
        "min_wall_clearance": 1.8970379077387634e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000194549560547,
      "sweeps": 21571,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 121001,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 92,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8063379128032252e-05,
        "min_wall_clearance": 1.8203502100799795e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 16727,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 6611,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8064352256492017e-05,
        "min_wall_clearance": 1.8201273112250504e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 13142,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 25253,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 63,
      "attempts": 74,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.80755790762906e-05,
        "min_wall_clearance": 1.839597985231478e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 13838,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 53092,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8092673782943436e-05,
        "min_wall_clearance": 1.8228407053566542e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 46,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 11693,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 137893,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 92,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8011510600197507e-05,
        "min_wall_clearance": 1.891356963090729e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 23848,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 249887,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 77,
      "attempts": 88,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7964741343190482e-05,
        "min_wall_clearance": 1.8138882402318757e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 51,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 25220,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 252835,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 92,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8013649452752745e-05,
        "min_wall_clearance": 1.813990070598237e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 18702,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 280239,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8078587282656112e-05,
        "min_wall_clearance": 1.8960516804611416e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 45,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 13494,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 294516,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 92,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8002877126363093e-05,
        "min_wall_clearance": 1.8797319063956763e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 27,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 23521,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 298151,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 82,
      "attempts": 93,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8003111511486748e-05,
        "min_wall_clearance": 1.8563804392801586e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 49,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195026397705,
      "sweeps": 16507,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 389285,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 66,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8102530810342116e-05,
        "min_wall_clearance": 1.8498103694586376e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 16,
      "proposals": 44,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 14687,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 44858,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 84,
      "attempts": 95,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8055035985003418e-05,
        "min_wall_clearance": 1.8227373328461027e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 28244,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 93856,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 78,
      "attempts": 89,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7989917356826373e-05,
        "min_wall_clearance": 1.8675013743418845e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 19843,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 156651,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 69,
      "attempts": 80,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8087450600174853e-05,
        "min_wall_clearance": 1.8662221234144738e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 22919,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 209207,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 76,
      "attempts": 87,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.80842898491638e-05,
        "min_wall_clearance": 1.8992027059905325e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 51,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 15752,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 250672,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 77,
      "attempts": 88,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.817941686373854e-05,
        "min_wall_clearance": 1.8336375144478723e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 20496,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 292429,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.823495292407884e-05,
        "min_wall_clearance": 1.8110408039895276e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 36,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000195503234863,
      "sweeps": 11543,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 368711,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 84,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797333492791609e-05,
        "min_wall_clearance": 1.8916528353507545e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 36,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001959800720215,
      "sweeps": 22569,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 35377,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 73,
      "attempts": 84,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8023568731102543e-05,
        "min_wall_clearance": 1.857479361877523e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001959800720215,
      "sweeps": 16696,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 50162,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 54,
      "attempts": 65,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8026729590170376e-05,
        "min_wall_clearance": 1.8217170304701824e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001959800720215,
      "sweeps": 15019,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 70565,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 54,
      "attempts": 65,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8018369892569552e-05,
        "min_wall_clearance": 1.809795809393222e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001959800720215,
      "sweeps": 12823,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 83676,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 1000000,
  "retained_pose_count": 511,
  "run_id": "run-20261008T225441Z-b5c9ec306a8f",
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
  "stop_reason": "SIGINT"
}
```

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
