# n16-s480-b128-run-20261008T224508Z-8b7d829dc2a6 compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 512
- GPU-feasible trials: 512
- Trials without an accepted pose: 0
- Budget-exhausted trials: 241
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 512 | 4.00020074844 | 5.06797742844 | 4.81378026009 | 5.465127635 |
| Independently numerically validated | 95 | 4.00020074844 | 4.89707517624 | 4.00020074844 | 5.00869846344 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 512 | 36 | 115.5 | 128 | 128 |
| Sweeps | 512 | 6120 | 37320.5 | 48047.4 | 49767 |

## Independent validation coverage

- Audited trials: 95 / 512 (0.186)
- Numerically validated: 95
- Indeterminate: 0
- Invalid: 0
- Not checked: 417

## Termination reasons

- `BUDGET_EXHAUSTED`: 241
- `STEP_FLOOR_REACHED`: 271

## Timing

- `module_load_seconds`: 0.109927699988
- `warmup_seconds`: 3.02723840901
- `simulation_seconds`: 30.757064392
- `device_seconds`: 30.7563569336
- `transfer_seconds`: 0.0118404850364
- `validation_seconds`: 1.79354453311
- `render_seconds`: 0.0139064569958
- `persistence_seconds`: 0.376388075029
- `max_stage_seconds`: 1.1297199707

## Amortized throughput

- `simulation_seconds`: attempted 16.6465821794 trials/s; GPU-feasible 16.6465821794 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 16.6469650845 trials/s; GPU-feasible 16.6469650845 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 512,
  "experiment": "n16-s480-b128-run-20261008T224508Z-8b7d829dc2a6",
  "experiment_name": "n16-s480-b128-run-20261008T224508Z-8b7d829dc2a6",
  "experiment_slug": "n16-s480-b128-run-20261008T224508Z-8b7d829dc2a6",
  "leaderboard": [
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8062782809853212e-05,
        "min_wall_clearance": 1.8872817537651798e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 44,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9557,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 11,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.806455832411272e-05,
        "min_wall_clearance": 1.8872817010517906e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8518,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 106,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8064016877828706e-05,
        "min_wall_clearance": 1.8852942580416254e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 76,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8854,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 261,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.81188722055399e-05,
        "min_wall_clearance": 1.8753607720967125e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9116,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 306,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8003213064473586e-05,
        "min_wall_clearance": 1.865904835129939e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9214,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 482,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.79905642286008e-05,
        "min_wall_clearance": 1.8515189141865562e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 30,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9437,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 489,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 35,
      "attempts": 46,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7955586517570676e-05,
        "min_wall_clearance": 1.8201276135165756e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.412895679473877,
      "sweeps": 7348,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 320,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 97,
      "attempts": 108,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797472367626174e-05,
        "min_wall_clearance": 1.901442282470356e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 64,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.684970378875732,
      "sweeps": 34333,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 129,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 33,
      "attempts": 44,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8056007305533583e-05,
        "min_wall_clearance": 1.891652816521372e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.708207607269287,
      "sweeps": 7688,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 274,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 97,
      "attempts": 108,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.795434382501071e-05,
        "min_wall_clearance": 1.866514765858085e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 43,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.7082200050354,
      "sweeps": 34497,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 199,
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
      "sweeps": 6720,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 20,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 43,
      "attempts": 54,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.821365598464464e-05,
        "min_wall_clearance": 1.8072139844171886e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 16,
      "proposals": 50,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.719534873962402,
      "sweeps": 14762,
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
        "min_pair_separation": 1.7934843777656084e-05,
        "min_wall_clearance": 1.893242159223263e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.7220587730407715,
      "sweeps": 45030,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 302,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.801739997853158e-05,
        "min_wall_clearance": 1.9051630776978357e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.9073486328125e-05,
      "n": 16,
      "proposals": 49,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.734955310821533,
      "sweeps": 45240,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 266,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 122,
      "attempts": 128,
      "final_step": 0.0031250000465661287,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.810455776003056e-05,
        "min_wall_clearance": 1.9017890134698234e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 6,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.743738174438477,
      "sweeps": 28943,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 219,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 46,
      "attempts": 57,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8021333219597757e-05,
        "min_wall_clearance": 1.8009370299942873e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 54,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.755277156829834,
      "sweeps": 15317,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 190,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 31,
      "attempts": 42,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.807089414951335e-05,
        "min_wall_clearance": 1.8409197348745465e-05,
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
      "side": 4.758793830871582,
      "sweeps": 7495,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 208,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 62,
      "attempts": 73,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8012901074504484e-05,
        "min_wall_clearance": 1.8678109774405982e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.78476619720459,
      "sweeps": 21379,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 48,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8023070889411352e-05,
        "min_wall_clearance": 1.8881183526886502e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.793355464935303,
      "sweeps": 39763,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 24,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 121,
      "attempts": 128,
      "final_step": 0.0015625000232830644,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.795914328900361e-05,
        "min_wall_clearance": 1.894374389799225e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.895427703857422e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 7,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.796870708465576,
      "sweeps": 45800,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 498,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 28,
      "attempts": 39,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8051098189697523e-05,
        "min_wall_clearance": 1.8560473542539313e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 57,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.796879768371582,
      "sweeps": 7685,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 401,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 60,
      "attempts": 71,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7973634074242018e-05,
        "min_wall_clearance": 1.826087720324665e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 28,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.800389766693115,
      "sweeps": 19045,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 111,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 118,
      "attempts": 128,
      "final_step": 0.00019531250291038305,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.796000154287436e-05,
        "min_wall_clearance": 1.8872817010517906e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8090009689331055e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 10,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.804100036621094,
      "sweeps": 45520,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 313,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 54,
      "attempts": 65,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800453432343474e-05,
        "min_wall_clearance": 1.8163746420718496e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 25,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.804296970367432,
      "sweeps": 18131,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 474,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 109,
      "attempts": 120,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7943940698872396e-05,
        "min_wall_clearance": 1.832048190575364e-05,
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
      "side": 4.806833267211914,
      "sweeps": 38082,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 392,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 31,
      "attempts": 42,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.824034955988374e-05,
        "min_wall_clearance": 1.797874727582638e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.823902130126953e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 45,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.809380054473877,
      "sweeps": 8897,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 493,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 79,
      "attempts": 90,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8050396284552406e-05,
        "min_wall_clearance": 1.8883034913486085e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 53,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.817380428314209,
      "sweeps": 26637,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 81,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 32,
      "attempts": 43,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8093222467152614e-05,
        "min_wall_clearance": 1.8415533936000372e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.817387580871582,
      "sweeps": 8377,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 289,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 46,
      "attempts": 57,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7927620709734526e-05,
        "min_wall_clearance": 1.8423576143788978e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 30,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.817389011383057,
      "sweeps": 14810,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 50,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 119,
      "attempts": 128,
      "final_step": 0.0003906250058207661,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.810320146394817e-05,
        "min_wall_clearance": 1.898379095166547e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.901388168334961e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 9,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.821107387542725,
      "sweeps": 44160,
      "termination_reason": "BUDGET_EXHAUSTED",
      "trial_id": 395,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 10000,
  "retained_pose_count": 95,
  "run_id": "run-20261008T224508Z-8b7d829dc2a6",
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
