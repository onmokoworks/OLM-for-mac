# OLMDistanceGradation 16bpc case_0026 no-bg probe (2026-06-29)

Status: `AE-host-grounded diagnostic`, not `AE exact`.

## What Changed

The Mac AE runner now completes the bounded single-case probe after changing
`scripts/ae_render_single_case.jsx` to use `eval("(" + text + ")")` for local
manifest parsing. AE 26.3 `JSON.parse` hangs on the generated 1.7MB
`reference_manifest.json`, while the legacy ExtendScript parser returns
immediately for the same local artifact.

Probe output:

- `refs/reports/ae_single_case_olmdistancegradation_case0026_no_bg_20260629_1408/`
- AE version: `26.3x87`
- Override: `Use Background Color=0`

## Result

The no-background probe does **not** move the Mac result toward the Windows
Software ramp. It stays at, or within a few 16bpc units of, the Gradation Color
endpoint on the row-0 witness.

Compared against the Windows bg-on Software reference:

| Candidate | max_diff | mean_diff | nonzero_px |
| --- | ---: | ---: | ---: |
| old bg candidate | 61165 | 11754.576950 | 1123575 |
| no-bg probe | 61155 | 11755.145866 | 1123575 |

## Row 0 Witness

| x | Windows reference | old bg candidate | no-bg probe |
| ---: | --- | --- | --- |
| 0 | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 1 | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 2 | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 3 | `[18147,0,49681,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 4 | `[27731,0,39633,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 5 | `[36021,0,30941,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 6 | `[43085,0,23533,65535]` | `[7195,0,61165,65535]` | `[7195,0,61165,65535]` |
| 7 | `[49003,0,17331,65535]` | `[7195,0,61165,65535]` | `[7193,0,61163,65533]` |
| 8 | `[53849,0,12249,65535]` | `[7195,0,61165,65535]` | `[7193,0,61163,65533]` |
| 9 | `[57703,0,8209,65535]` | `[7195,0,61165,65535]` | `[7193,0,61163,65533]` |
| 10 | `[60657,0,5111,65535]` | `[7195,0,61165,65535]` | `[7193,0,61163,65533]` |
| 11 | `[62803,0,2861,65535]` | `[7195,0,61165,65535]` | `[7193,0,61161,65531]` |
| 12 | `[64241,0,1355,65535]` | `[7195,0,61165,65535]` | `[7193,0,61161,65531]` |
| 13 | `[65083,0,471,65535]` | `[7195,0,61165,65535]` | `[7193,0,61161,65531]` |
| 14 | `[65459,0,77,65535]` | `[7195,0,61165,65535]` | `[7193,0,61159,65529]` |

## Interpretation

The Windows runtime trace already proves `case_0026` has a field ramp before
compose. This Mac no-bg probe shows the current Mac AE path remains saturated
even when the background toggle is disabled. The next proof belongs in the Mac
16bpc field-prep / installed-binary path, not in background compose retuning.
