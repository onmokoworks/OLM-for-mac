# 16bpc Mac AE validation - 2026-06-26 paramfix

Status: not AE exact.

Mac AE 2026 rendered the 45-case 16bpc set after fixing path-only parameter replay in `scripts/ae_pixel_validation_render.jsx`.

Overall: 15/45 exact.

| Request | Exact | Fail | Max diff max | Report |
| --- | ---: | ---: | ---: | --- |
| bitdepth16_olmblur_exact | 0/7 | 7 | 65023 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1110_paramfix/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmcolorkey_exact | 7/9 | 2 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1110_paramfix/bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmdistancegradation_basic_exact | 7/12 | 5 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1110_paramfix/bitdepth16_olmdistancegradation_basic_exact/reports/ae_pixel_16bpc_basic_exact.json` |
| bitdepth16_olmdistancegradation_blur_exact | 0/1 | 1 | 65293 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1110_paramfix/bitdepth16_olmdistancegradation_blur_exact/reports/ae_pixel_16bpc_blur_exact.json` |
| bitdepth16_olmdistancegradation_extended_exact | 1/16 | 15 | 65525 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1110_paramfix/bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json` |

Important notes:
- The previous 2026-06-25 Mac AE run skipped manifest params that lacked `path_full`; keep it as superseded evidence, not the current residual baseline.
- OLMColorKey improved from 3/9 to 7/9 exact after the harness fix.
- OLMBlur remains 0/7 exact but the residual profile changed to sparse high-amplitude pixels for most cases.
- OLMDistanceGradation remains mostly non-exact in 16bpc; residuals are now much smaller for several cases but still not completion-grade.
- `AE exact` still means `max_diff=0` for the target bit depth.
