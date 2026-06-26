# 16bpc Mac AE validation - 2026-06-26 Fresh All After ColorKey Force Lower Precision

Status: not AE exact.

Mac AE 2026 rendered all five 16bpc request zips locally after implementing the binary-grounded `Force Lower Precision` key epsilon rule in `mac/OLMColorKey`.

Overall current slice: 0/0 exact.

| Request | Exact | Fail | Max diff max | Report |
| --- | ---: | ---: | ---: | --- |
| bitdepth16_olmblur_exact | 0/0 | 0 | 65023 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1132_fresh_all_after_colorkey_force_precision/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmcolorkey_exact | 0/0 | 0 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1132_fresh_all_after_colorkey_force_precision/bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmdistancegradation_basic_exact | 0/0 | 0 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1132_fresh_all_after_colorkey_force_precision/bitdepth16_olmdistancegradation_basic_exact/reports/ae_pixel_16bpc_basic_exact.json` |
| bitdepth16_olmdistancegradation_blur_exact | 0/0 | 0 | 65293 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1132_fresh_all_after_colorkey_force_precision/bitdepth16_olmdistancegradation_blur_exact/reports/ae_pixel_16bpc_blur_exact.json` |
| bitdepth16_olmdistancegradation_extended_exact | 0/0 | 0 | 65525 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1132_fresh_all_after_colorkey_force_precision/bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json` |

Important notes:
- This is a fresh all-request Mac AE render, not a mixed carry-forward ledger.
- ColorKey is 8/9 exact; `olmcolorkey__case_0008` remains exact after the Force Lower Precision epsilon fix.
- Remaining ColorKey residual is `olmcolorkey__case_0009`, which still points at Edge Thin / border behavior rather than broad color-space epsilon.
- `AE exact` still means `max_diff=0` for the target bit depth.
