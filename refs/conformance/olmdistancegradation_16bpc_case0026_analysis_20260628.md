# OLMDistanceGradation 16bpc case_0026 analysis (2026-06-28)

## Summary

- Case: `olmdistancegradation_extended__case_0026`
- Classification: `candidate_x_saturated_to_gradation_color_while_reference_ramps`
- Metrics: `max_diff=61165`, `mean_diff=11754.576950`, `nonzero_px=1123575/2073600` (`54.18%`)
- This is not a narrow 16bpc writer/rounding residual. The Mac candidate is already at the Gradation Color for most changed pixels, while Windows Software ramps between Background Color and Gradation Color.

## Color Model Used For Classification

For this request, `Render Mode=1`, `Use Background Color=1`, `Invert=1`, `Interpolation Mode=4`, `Power=2.59740734100342`.

- Gradation color, RGBA16: `[7195, 0, 61165, 65535]`
- Background color, RGBA16: `[65535, 0, 0, 65535]`
- Inferred compose coefficient: `out = BG * (1 - X) + Grad * X`, estimated from red and blue.

## Pixel Classes

- `candidate_grad_ref_not_grad`: `880796`
- `candidate_bg_ref_not_bg`: `0`
- `candidate_grad_total`: `1830821`
- `candidate_bg_total`: `0`
- `reference_grad_total`: `950025`
- `reference_bg_total`: `29358`

On changed pixels, candidate `X` is essentially saturated:

- Reference X: min `0.000017`, mean `0.273864`, max `0.999850`
- Candidate X: min `0.999799`, mean `0.999976`, max `1.000000`

## Row 0 Witness

| x | before RGBA16 | reference RGBA16 | candidate RGBA16 | ref X | cand X |
| --- | --- | --- | --- | --- | --- |
| 0 | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `1.0` | `1.0` |
| 1 | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `1.0` | `1.0` |
| 2 | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `1.0` | `1.0` |
| 3 | `[0, 0, 0, 0]` | `[18147, 0, 49681, 65535]` | `[7195, 0, 61165, 65535]` | `0.812259` | `1.0` |
| 4 | `[0, 0, 0, 0]` | `[27731, 0, 39633, 65535]` | `[7195, 0, 61165, 65535]` | `0.647982` | `1.0` |
| 5 | `[0, 0, 0, 0]` | `[36021, 0, 30941, 65535]` | `[7195, 0, 61165, 65535]` | `0.505879` | `1.0` |
| 6 | `[0, 0, 0, 0]` | `[43085, 0, 23533, 65535]` | `[7195, 0, 61165, 65535]` | `0.38478` | `1.0` |
| 7 | `[0, 0, 0, 0]` | `[49003, 0, 17331, 65535]` | `[7195, 0, 61165, 65535]` | `0.283361` | `1.0` |
| 8 | `[0, 0, 0, 0]` | `[53849, 0, 12249, 65535]` | `[7195, 0, 61165, 65535]` | `0.200285` | `1.0` |
| 9 | `[0, 0, 0, 0]` | `[57703, 0, 8209, 65535]` | `[7195, 0, 61165, 65535]` | `0.134229` | `1.0` |
| 10 | `[0, 0, 0, 0]` | `[60657, 0, 5111, 65535]` | `[7195, 0, 61165, 65535]` | `0.083587` | `1.0` |
| 11 | `[0, 0, 0, 0]` | `[62803, 0, 2861, 65535]` | `[7195, 0, 61165, 65535]` | `0.046802` | `1.0` |
| 12 | `[0, 0, 0, 0]` | `[64241, 0, 1355, 65535]` | `[7195, 0, 61165, 65535]` | `0.022167` | `1.0` |
| 13 | `[0, 0, 0, 0]` | `[65083, 0, 471, 65535]` | `[7195, 0, 61165, 65535]` | `0.007724` | `1.0` |
| 14 | `[0, 0, 0, 0]` | `[65459, 0, 77, 65535]` | `[7195, 0, 61165, 65535]` | `0.001281` | `1.0` |

## Interpretation

- Pixels `x=0..2,y=0` match because both Windows and Mac produce the Gradation Color.
- From `x=3` onward, Windows Software ramps rapidly toward the Background Color (`X≈0.812 -> 0.001`), while Mac remains at `X=1.0`.
- The input pixels in this row are transparent black, so the visible mismatch is not caused by source RGB passthrough.
- The next useful proof is a bounded binary/runtime witness for the 16bpc field value immediately before compose/interpolation, not broad PNG tuning.

## Next Witness Request Shape

- Target case: `olmdistancegradation_extended__case_0026`.
- Probe pixels: row `y=0`, `x=0..14`, especially `x=3..14`.
- Capture field-world green/16bpc value before `FUN_181170480` applies invert/interpolation, and final `X` after `Invert` + `Power`.
- If the Windows pre-compose field already ramps, the bug is in Mac 16bpc field prep / threshold ownership. If the field is saturated and only final `X` ramps in Windows, the bug is in invert/power/compose parameter ownership.

## Paths

- `before_effects`: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026_before_effects.png`
- `candidate`: `refs/reports/ae_pixel_validation_16bpc_mac_20260626_2335_endian_fix/bitdepth16_olmdistancegradation_extended_exact/candidate/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026.png`
- `reference`: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026.png`
