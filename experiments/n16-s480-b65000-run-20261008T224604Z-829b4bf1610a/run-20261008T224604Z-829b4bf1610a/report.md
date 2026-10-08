# n16-s480-b65000-run-20261008T224604Z-829b4bf1610a compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 10000
- GPU-feasible trials: 10000
- Trials without an accepted pose: 0
- Budget-exhausted trials: 4289
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 10000 | 4.0001950264 | 5.05078434944 | 4.80078439713 | 5.47656116486 |
| Independently numerically validated | 168 | 4.0001950264 | 5.02705955505 | 4.00020074844 | 5.44947543144 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 10000 | 31 | 99 | 128 | 128 |
| Sweeps | 10000 | 5791 | 31837 | 48031.2 | 51080 |

## Independent validation coverage

- Audited trials: 168 / 10000 (0.017)
- Numerically validated: 168
- Indeterminate: 0
- Invalid: 0
- Not checked: 9832

## Termination reasons

- `BUDGET_EXHAUSTED`: 4289
- `STEP_FLOOR_REACHED`: 5711

## Timing

- `module_load_seconds`: 0.105676912004
- `warmup_seconds`: 3.04053881601
- `simulation_seconds`: 9.64130736399
- `device_seconds`: 9.64113964844
- `transfer_seconds`: 0.00748907300294
- `validation_seconds`: 4.798076604
- `render_seconds`: 0.0205251810257
- `persistence_seconds`: 1.04491833702
- `max_stage_seconds`: 1.41115393066

## Amortized throughput

- `simulation_seconds`: attempted 1037.20373415 trials/s; GPU-feasible 1037.20373415 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 1037.22177716 trials/s; GPU-feasible 1037.22177716 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 10000,
  "experiment": "n16-s480-b65000-run-20261008T224604Z-829b4bf1610a",
  "experiment_name": "n16-s480-b65000-run-20261008T224604Z-829b4bf1610a",
  "experiment_slug": "n16-s480-b65000-run-20261008T224604Z-829b4bf1610a",
  "leaderboard": [
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
      "accepted": 92,
      "attempts": 103,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8055329538980138e-05,
        "min_wall_clearance": 1.891653581465036e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.00019645690918,
      "sweeps": 33181,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 5483,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 62,
      "attempts": 73,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.807445510132989e-05,
        "min_wall_clearance": 1.8634398431416344e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000197410583496,
      "sweeps": 20680,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 5752,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 57,
      "attempts": 68,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7984584411983998e-05,
        "min_wall_clearance": 1.870217002197805e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 16,
      "proposals": 43,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 17381,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 934,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 60,
      "attempts": 71,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8099331566248907e-05,
        "min_wall_clearance": 1.8872817010517906e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0001983642578125,
      "sweeps": 19106,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 3978,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 45,
      "attempts": 56,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7995067487230898e-05,
        "min_wall_clearance": 1.826238336466446e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000198841094971,
      "sweeps": 11740,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 803,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
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
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8154369723594394e-05,
        "min_wall_clearance": 1.888909725789034e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 44,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8372,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 832,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7986053308659787e-05,
        "min_wall_clearance": 1.8672486585380454e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8694,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1046,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8063104905352213e-05,
        "min_wall_clearance": 1.835650351900142e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9136,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1228,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.806298634265957e-05,
        "min_wall_clearance": 1.8276770562764e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8188,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1324,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8212030142079765e-05,
        "min_wall_clearance": 1.881781789148107e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9530,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1446,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.809163615530572e-05,
        "min_wall_clearance": 1.8320481717459813e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 41,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8674,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1588,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 41,
      "attempts": 52,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.796954099775679e-05,
        "min_wall_clearance": 1.84396924431951e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8943,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1647,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8003238311198985e-05,
        "min_wall_clearance": 1.8320481665945465e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8251,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1709,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799509894254111e-05,
        "min_wall_clearance": 1.8685870480261713e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 48,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9064,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1751,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8156241265312023e-05,
        "min_wall_clearance": 1.88898750428379e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8894672393798828e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 7971,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 1789,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7975991942058376e-05,
        "min_wall_clearance": 1.8856923651000557e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8868,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2150,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8057034494779307e-05,
        "min_wall_clearance": 1.879007770577701e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 40,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8761,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2182,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8014588865557736e-05,
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
      "proposals": 46,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8441,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2335,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8019161772339466e-05,
        "min_wall_clearance": 1.8678109774405982e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8972,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2399,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8002168599088475e-05,
        "min_wall_clearance": 1.871775726369762e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9607,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2580,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8088085565581835e-05,
        "min_wall_clearance": 1.7990634499476243e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 9039,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2668,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8094801778492082e-05,
        "min_wall_clearance": 1.8276770257674713e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 8872,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2759,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 39,
      "attempts": 50,
      "final_step": 9.765625145519152e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.871862423930004e-05,
        "min_wall_clearance": 1.7986483399123898e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.8656253814697266e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 27,
      "rejected": 11,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.0002007484436035,
      "sweeps": 7513,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 2935,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 10000,
  "retained_pose_count": 168,
  "run_id": "run-20261008T224604Z-829b4bf1610a",
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

Final report and end-to-end timings are in `summary.json.gz`. Their boundary includes this report and histogram; it excludes the final summary's own serialization.
