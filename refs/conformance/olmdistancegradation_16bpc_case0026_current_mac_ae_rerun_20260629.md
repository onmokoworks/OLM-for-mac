# OLMDistanceGradation 16bpc case_0026 current Mac AE rerun (2026-06-29)

- Case: `olmdistancegradation_extended__case_0026`
- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Runner: `python3 scripts/run_ae_single_case.py`
- AE version reported by JSX: `26.3x87`
- Result JSON: `refs/conformance/olmdistancegradation_16bpc_case0026_current_mac_ae_rerun_20260629.json`
- Candidate output during run: `/private/tmp/olm_dg_case0026_current_ae_retry_20260629_114101/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0026.png`

## Result

The current installed Mac AE plug-in still does not match the Windows Software
16bpc reference for this case.

- `max_diff=61157`
- `mean_diff=11754.422780309607`
- `nonzero_px=1123575 / 2073600`
- `nonzero_px_percent=54.184751157407405`

The first row preserves the same failure family as the prior analysis: Windows
ramps, while the Mac candidate stays at the gradation color endpoint. Sample at
`(x=3, y=0)`:

- reference: `[18147, 0, 49681, 65535]`
- candidate: `[7195, 0, 61165, 65535]`
- delta: `[10952, 0, 11484, 0]`

The candidate values are effectively the selected Gradation Color endpoint, so
the old saturated Mac candidate was not just stale. Combined with the
2026-06-29 Windows runtime trace, the active question moves to the Mac host
field-prep / installed-binary path before `FUN_181170480`-equivalent compose,
not the Windows compose branch.
