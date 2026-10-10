# Rigid-square comparison

State: **PARTIAL**. Square count: 51.

Completed candidate evaluations: 0/2000000.
Scientific episode executions: 0. Submitted attempts: 128.
Diagnostic replays: 0; cached-parent reuse: 0.

Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.
Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.

| Program | Arm | Training mean L | Holdout mean L | Valid/total |
|---|---|---|---|---|
| legacy_compress | controls | 15.0 | None | 64/64 |
| pulse_rotate | controls | 15.0 | None | 64/64 |

Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.
Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.
