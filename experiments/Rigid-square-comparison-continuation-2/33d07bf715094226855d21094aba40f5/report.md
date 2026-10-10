# Rigid-square comparison · continuation 2

State: **COMPLETED**. Square count: 51.

Completed candidate evaluations: 2576/1000000.
Scientific episode executions: 165312. Submitted attempts: 189376.
Diagnostic replays: 8; cached-parent reuse: 8.

Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.
Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.

| Program | Arm | Training mean L | Holdout mean L | Valid/total |
|---|---|---|---|---|
| legacy_compress | controls | 9.110759988427162 | 9.047432869672775 | 64/64 |
| pulse_rotate | controls | 9.185718908905983 | 9.1673244535923 | 64/64 |
| Mutated world strategy | one_plus_lambda | 8.687232613563538 | 8.725841909646988 | 64/64 |

Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.
Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.
