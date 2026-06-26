# 16bpc Mac AE validation - 2026-06-26 ColorKey Force Lower Precision

Status: not AE exact.

Mac AE 2026 rerendered the ColorKey 16bpc slice after implementing the binary-grounded `Force Lower Precision` key epsilon rule in `mac/OLMColorKey`.

Overall current slice: 16/45 exact.

| Request | Exact | Fail | Max diff max | Report |
| --- | ---: | ---: | ---: | --- |
| bitdepth16_olmblur_exact | 0/7 | 7 | 65023 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1123_colorkey_force_precision/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmcolorkey_exact | 8/9 | 1 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1123_colorkey_force_precision/bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmdistancegradation_basic_exact | 7/12 | 5 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1123_colorkey_force_precision/bitdepth16_olmdistancegradation_basic_exact/reports/ae_pixel_16bpc_basic_exact.json` |
| bitdepth16_olmdistancegradation_blur_exact | 0/1 | 1 | 65293 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1123_colorkey_force_precision/bitdepth16_olmdistancegradation_blur_exact/reports/ae_pixel_16bpc_blur_exact.json` |
| bitdepth16_olmdistancegradation_extended_exact | 1/16 | 15 | 65525 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1123_colorkey_force_precision/bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json` |

Important notes:
- ColorKey improved from 7/9 to 8/9 exact; `olmcolorkey__case_0008` is now exact.
- The rule is grounded in Windows AEX `FUN_18000a3d0`: `Force Lower Precision` at ctx `+0x3c` selects key epsilon at ctx `+0x54`.
- Remaining ColorKey residual is `olmcolorkey__case_0009`, which now looks like the Edge Thin / border path rather than a broad color-space epsilon issue.
- `AE exact` still means `max_diff=0` for the target bit depth.
