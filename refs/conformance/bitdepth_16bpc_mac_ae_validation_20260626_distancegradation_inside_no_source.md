# 16bpc Mac AE validation - 2026-06-26 DistanceGradation Inside No-Source

Status: not AE exact.

Mac AE 2026 rerendered the 16bpc slices after a clean OLMDistanceGradation build with the Inside/all-opaque no-source distance-field rule. The active port keeps round-to-nearest 16bpc writeback; the direct truncation experiment was rejected because it did not improve conformance overall.

Overall current slice: 17/45 exact.

| Request | Exact | Fail | Max diff max | Report |
| --- | ---: | ---: | ---: | --- |
| bitdepth16_olmblur_exact | 0/7 | 7 | 65023 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/bitdepth16_olmblur_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmcolorkey_exact | 8/9 | 1 | 65535 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/bitdepth16_olmcolorkey_exact/reports/ae_pixel_16bpc_all_exact.json` |
| bitdepth16_olmdistancegradation_basic_exact | 8/12 | 4 | 65023 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/bitdepth16_olmdistancegradation_basic_exact/reports/ae_pixel_16bpc_basic_exact.json` |
| bitdepth16_olmdistancegradation_blur_exact | 0/1 | 1 | 65293 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/bitdepth16_olmdistancegradation_blur_exact/reports/ae_pixel_16bpc_blur_exact.json` |
| bitdepth16_olmdistancegradation_extended_exact | 1/16 | 15 | 65525 | `refs/reports/ae_pixel_validation_16bpc_mac_20260626_1247_distancegradation_clean_stable/bitdepth16_olmdistancegradation_extended_exact/reports/ae_pixel_16bpc_extended_exact.json` |

Important notes:
- `olmdistancegradation_basic__case_0002` is exact.
- DistanceGradation basic is 8/12 exact; DistanceGradation total is 9/29 exact.
- Overall 16bpc slice is 17/45 exact.
- Remaining DistanceGradation residuals are non-all-opaque cases and blur/extended paths.
- The Windows callback still has a tracked binary `CVTTSS2SI` writeback fact, but adopting truncation globally in the Mac port worsened the measured 16bpc residual set.
