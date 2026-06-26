# 16bpc Mac AE validation - 2026-06-25

Status: not AE exact.

Mac AE 2026 rendered all 45 requested 16bpc PNGs, but native 16bit comparison against Windows AE Software references did not pass all exact thresholds.

| Request | Exact | Fail | Max diff max | Report |
| --- | ---: | ---: | ---: | --- |
| bitdepth16_olmblur_exact | 0/7 | 7 | 59796 | `refs/reports/ae_pixel_validation_16bpc_mac_20260625_2258_true16/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmcolorkey_exact | 3/9 | 6 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260625_2258_true16/bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmdistancegradation_basic_exact | 8/12 | 4 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260625_2258_true16/bitdepth16_olmdistancegradation_basic_exact/reports/ae_pixel_16bpc_basic_exact.json` |
| bitdepth16_olmdistancegradation_blur_exact | 0/1 | 1 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260625_2258_true16/bitdepth16_olmdistancegradation_blur_exact/reports/ae_pixel_16bpc_blur_exact.json` |
| bitdepth16_olmdistancegradation_extended_exact | 1/16 | 15 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260625_2258_true16/bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json` |

Important notes:
- `scripts/ae_pixel_validation_render.jsx` now sets `app.project.bitsPerChannel` from the reference manifest before rendering. Without this, AE emitted 8-bit PNGs.
- `refs/scripts/verify_manifest.py` now preserves native PNG 8/16bit RGBA values instead of forcing 8-bit Pillow RGBA conversion.
- This is a failure artifact, not a completion marker. `AE exact` still means `max_diff=0` for the target bit depth.
