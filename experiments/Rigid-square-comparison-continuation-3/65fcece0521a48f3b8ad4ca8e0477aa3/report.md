# Rigid-square comparison · continuation 3

State: **COMPLETED**. Square count: 11.

Completed candidate evaluations: 26632/1000000.
Scientific episode executions: 1704960. Submitted attempts: 1704960.
Diagnostic replays: 8; cached-parent reuse: 26.

Every ranked best pose is independently CPU validated. Native NPZ chunks preserve exact FP32 best/current geometry and defined VM/result fields.
Training winners are frozen before untouched holdout. A valid construction supports an upper bound; this functional pilot makes no optimality or method-superiority claim.

| Program | Arm | Training mean L | Holdout mean L | Valid/total |
|---|---|---|---|---|
| legacy_compress | controls | 4.241176798939705 | 4.308025993406773 | 64/64 |
| pulse_rotate | controls | 4.2808723375201225 | 4.310613334178925 | 64/64 |
| Mutated world strategy | one_plus_lambda | 4.0261267982423306 | 4.1073108576238155 | 64/64 |

Open `report.html` with the network disabled for programs, durable history, actual curves and embedded selected trajectories.
Native replay comparison checks best/current endpoints, defined fields, RNG and work; it does not certify unrecorded intermediate states.
