# Rigid-square comparison

State: **COMPLETED**. Square count: 51.

Completed candidate evaluations: 904/1000000.
Scientific episode executions: 58176. Submitted attempts: 58176.
Diagnostic replays: 5; cached-parent reuse: 4.

Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.
Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.

| Program | Arm | Training mean L | Holdout mean L | Valid/total |
|---|---|---|---|---|
| legacy_compress | controls | 9.110759988427162 | 9.047432869672775 | 64/64 |
| pulse_rotate | controls | 9.185718908905983 | 9.1673244535923 | 64/64 |
| Mutated world strategy | one_plus_lambda | 8.915610998868942 | 8.908522829413414 | 64/64 |

Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.
Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.
