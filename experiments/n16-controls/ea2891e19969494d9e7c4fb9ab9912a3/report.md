# n16-controls

State: **COMPLETED**. Square count: 16.

Completed candidate evaluations: 0/0.
Scientific episode executions: 64. Submitted attempts: 64.
Diagnostic replays: 2; cached-parent reuse: 0.

Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.
Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.

| Program | Arm | Training mean L | Holdout mean L | Valid/total |
|---|---|---|---|---|
| legacy_compress | controls | 5.006671458482742 | 5.083425730466843 | 16/16 |
| pulse_rotate | controls | 5.099857419729233 | 5.14994078874588 | 16/16 |

Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.
Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.
