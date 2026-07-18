# OLMKiraKira previously-unconsumed parameter audit (2026-07-18)

Status: **binary-grounded partial wiring**
AE exact: **false**

## Result

| Parameter | Windows binary semantics | Mac result |
| --- | --- | --- |
| Fade Out | Disk 27 is a float. `FUN_18114e860` multiplies it by `0.200000003` and Channel 2/4 use it as the knee threshold in `FUN_1811501b0`. | Standard and Smart reads plus the proven Channel 2/4 seed branches are wired. |
| Highlight Radius | Disk 6 is an integer fifth layer. Radius `r` becomes `(2r+1) x (2r+1)`; Mode 1 uses one box pass and Mode 2 uses three. | Mode 1/2 are wired to the existing portable isotropic box scaffold and Highlight Color. Mode 3/4 remain unresolved. |
| Approximated Input | Disk 10 controls a half-resolution pre/post-resize branch when render scale is above `0.5`. | Standard and Smart reads retain the flag, but non-identity resize is deliberately not implemented without an independent oracle. |

## Evidence boundary

The manifest facts come from the 2026-06-29 fresh Windows defaults/ranges captures. Reader offsets and branches are grounded in `FUN_18114e860`, the three typed owners, `FUN_18114f4a0`, and their checked-in assembly. This change does not use PNG tuning and does not claim AE exactness.

`Approximated Input` remains the sole blocked implementation boundary in this three-parameter task: the repository only has a same-shape resize detour, while this path requires non-identity OpenCV resize plus writeback.

## Re-run

`python3 tools/emulation/audit_olmkirakira_unconsumed_parameters_20260718.py`
