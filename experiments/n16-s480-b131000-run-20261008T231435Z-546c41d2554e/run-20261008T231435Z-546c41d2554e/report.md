# n16-s480-b131000-run-20261008T231435Z-546c41d2554e compression run report

This report is generated from the persisted trial records. GPU acceptance and independent numerical validation are reported as separate populations.

## Outcome

- Attempted trials: 393000
- GPU-feasible trials: 393000
- Trials without an accepted pose: 0
- Budget-exhausted trials: 215674
- Other initialization failures: 0
- Numerical failures: 0

## Container-side statistics

| subset | count | best | median | q05 | q95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPU accepted | 393000 | 4.00009489059 | 5.05158400536 | 4.7931589365 | 5.4722676754 |
| Independently numerically validated | 507 | 4.00009489059 | 5.03905153275 | 4.00009679794 | 5.50892114639 |

## Solver iteration statistics

| metric | count | min | median | q95 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Attempts | 393000 | 31 | 128 | 128 | 128 |
| Sweeps | 393000 | 6134 | 41526 | 48144 | 52502 |

## Independent validation coverage

- Audited trials: 507 / 393000 (0.001)
- Numerically validated: 507
- Indeterminate: 0
- Invalid: 0
- Not checked: 392493

## Termination reasons

- `BUDGET_EXHAUSTED`: 215674
- `STEP_FLOOR_REACHED`: 177326

## Timing

- `module_load_seconds`: 0.159446213016
- `warmup_seconds`: 4.97976339702
- `simulation_seconds`: 231.866273427
- `device_seconds`: 231.863882813
- `transfer_seconds`: 0.0340305459977
- `validation_seconds`: 9.53566611998
- `render_seconds`: 0.0139365420036
- `persistence_seconds`: 6.48931434895
- `max_stage_seconds`: 18.2568671875

## Amortized throughput

- `simulation_seconds`: attempted 1694.94249505 trials/s; GPU-feasible 1694.94249505 trials/s. Amortized throughput over the synchronized simulation interval; not individual-trial latency.
- `device_seconds`: attempted 1694.95997062 trials/s; GPU-feasible 1694.95997062 trials/s. Amortized throughput over the synchronized device timing interval; not individual-trial latency.

The accompanying `histogram.svg` contains only the observed final accepted sides. Failed trials and records without an accepted side are excluded from those histograms and remain counted above.

## Metadata

```json
{
  "completed_trials": 393000,
  "experiment": "n16-s480-b131000-run-20261008T231435Z-546c41d2554e",
  "experiment_name": "n16-s480-b131000-run-20261008T231435Z-546c41d2554e",
  "experiment_slug": "n16-s480-b131000-run-20261008T231435Z-546c41d2554e",
  "leaderboard": [
    {
      "accepted": 82,
      "attempts": 94,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.798091921919796e-05,
        "min_wall_clearance": 1.8102426923682913e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 34,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094890594482,
      "sweeps": 17267,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 6611,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 78,
      "attempts": 90,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8052759019226983e-05,
        "min_wall_clearance": 1.820127250784509e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 51,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000094890594482,
      "sweeps": 25782,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 252835,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 56,
      "attempts": 68,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797894322845922e-05,
        "min_wall_clearance": 1.8097976884234868e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 44,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095367431641,
      "sweeps": 15348,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 44858,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 78,
      "attempts": 90,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800060273751931e-05,
        "min_wall_clearance": 1.806182844488191e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095367431641,
      "sweeps": 21014,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 292429,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 67,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8031162188902883e-05,
        "min_wall_clearance": 1.8000293679154566e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.800060272216797e-05,
      "n": 16,
      "proposals": 42,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 15570,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 70565,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 67,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800060209876259e-05,
        "min_wall_clearance": 1.8336376094385543e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 13367,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 83676,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 67,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8119811166239966e-05,
        "min_wall_clearance": 1.815756096812393e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.817941665649414e-05,
      "min_wall_clearance_gpu": 1.817941665649414e-05,
      "n": 16,
      "proposals": 45,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 14252,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 217683,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 75,
      "attempts": 87,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7977666688559533e-05,
        "min_wall_clearance": 1.8515997105339466e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 45,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 19478,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 225251,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 75,
      "attempts": 87,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7951993073579053e-05,
        "min_wall_clearance": 1.833733366307655e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8358230590820312e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 18606,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 303982,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 55,
      "attempts": 67,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8020051682472382e-05,
        "min_wall_clearance": 1.80376329410592e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.806020736694336e-05,
      "n": 16,
      "proposals": 41,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000095844268799,
      "sweeps": 14075,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 343155,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 71,
      "attempts": 83,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.809252017612193e-05,
        "min_wall_clearance": 1.8447383419051278e-05,
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
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 20142,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 18270,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 53,
      "attempts": 65,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7950634779939634e-05,
        "min_wall_clearance": 1.8260877864495484e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.823902130126953e-05,
      "n": 16,
      "proposals": 52,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 13671,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 70204,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 93,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7995163306759726e-05,
        "min_wall_clearance": 1.8574793723580285e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 16,
      "proposals": 35,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 28108,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 82836,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 81,
      "attempts": 93,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800169482796587e-05,
        "min_wall_clearance": 1.8515189141865562e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8537044525146484e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 28152,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 137415,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 78,
      "attempts": 90,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.797653955460228e-05,
        "min_wall_clearance": 1.82821366827568e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8298625946044922e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 27403,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 199662,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 78,
      "attempts": 90,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7983094393381194e-05,
        "min_wall_clearance": 1.8119128484705982e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 54,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 26904,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 200909,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 79,
      "attempts": 91,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.809643379735362e-05,
        "min_wall_clearance": 1.8455584434029504e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 16,
      "proposals": 63,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 27715,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 221299,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 79,
      "attempts": 91,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799387262637691e-05,
        "min_wall_clearance": 1.8570004696183418e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8596649169921875e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 24462,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 268479,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 53,
      "attempts": 65,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8051850942421646e-05,
        "min_wall_clearance": 1.8395979733298873e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096321105957,
      "sweeps": 12785,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 304503,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 68,
      "attempts": 80,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8000597523881723e-05,
        "min_wall_clearance": 1.8426534205584488e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8417835235595703e-05,
      "n": 16,
      "proposals": 32,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 16492,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 19489,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 68,
      "attempts": 80,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.801928097786483e-05,
        "min_wall_clearance": 1.878050630743644e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 38,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 14315,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 32326,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 52,
      "attempts": 64,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8023859710345285e-05,
        "min_wall_clearance": 1.8499295782348213e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8477439880371094e-05,
      "n": 16,
      "proposals": 66,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 14141,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 32806,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 69,
      "attempts": 81,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7986092009901644e-05,
        "min_wall_clearance": 1.8806879977795177e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 39,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 17391,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 63160,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 74,
      "attempts": 86,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7971195802495892e-05,
        "min_wall_clearance": 1.8856923651000557e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8835067749023438e-05,
      "n": 16,
      "proposals": 53,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 24755,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 69951,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 61,
      "attempts": 73,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7987411609252517e-05,
        "min_wall_clearance": 1.8737714361449775e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 19674,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 83614,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 68,
      "attempts": 80,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.800060207580097e-05,
        "min_wall_clearance": 1.8694003013131066e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8715858459472656e-05,
      "n": 16,
      "proposals": 30,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 15108,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 99148,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 67,
      "attempts": 79,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.799015472338628e-05,
        "min_wall_clearance": 1.879731920073624e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 31,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 17360,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 102351,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 68,
      "attempts": 80,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8000602180033005e-05,
        "min_wall_clearance": 1.8664824481096076e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.806020736694336e-05,
      "min_wall_clearance_gpu": 1.8656253814697266e-05,
      "n": 16,
      "proposals": 33,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 17823,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 119346,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 75,
      "attempts": 87,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.7996481247697514e-05,
        "min_wall_clearance": 1.8775807066884198e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.800060272216797e-05,
      "min_wall_clearance_gpu": 1.8775463104248047e-05,
      "n": 16,
      "proposals": 37,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 25231,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 119543,
      "validation_status": "NUMERICALLY_VALIDATED"
    },
    {
      "accepted": 68,
      "attempts": 80,
      "final_step": 9.999999747378752e-05,
      "gpu_status": "GPU_FEASIBLE",
      "independent_validation": {
        "max_penetration": 0.0,
        "min_pair_separation": 1.8150372960993863e-05,
        "min_wall_clearance": 1.809795656537716e-05,
        "nonfinite": false,
        "status": "NUMERICALLY_VALIDATED",
        "tolerance": 1e-08,
        "validator_version": "cpu-f64-projection-v2"
      },
      "max_penetration": 0.0,
      "min_pair_separation_gpu": 1.811981201171875e-05,
      "min_wall_clearance_gpu": 1.811981201171875e-05,
      "n": 16,
      "proposals": 29,
      "rejected": 12,
      "rng_scheme": "splitmix64-counter-v1",
      "seed": 20261008,
      "side": 4.000096797943115,
      "sweeps": 16326,
      "termination_reason": "STEP_FLOOR_REACHED",
      "trial_id": 127448,
      "validation_status": "NUMERICALLY_VALIDATED"
    }
  ],
  "persistence_timing_boundary": "Includes config, initial environment, audit IDs, scalar JSONL, gzip closure, pose/validation JSON, and final environment writes; report_seconds includes report, histogram, and summary persistence.",
  "requested_trials": 1000000,
  "retained_pose_count": 507,
  "run_id": "run-20261008T231435Z-546c41d2554e",
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
