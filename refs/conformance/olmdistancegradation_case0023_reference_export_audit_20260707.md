# OLMDistanceGradation case_0023 Reference Export Audit - 2026-07-13

- Case: `olmdistancegradation_extended__case_0023`
- Reference exact: `True`
- Safe claim: The packaged 2026-06-25 16bpc Windows Software reference is byte-identical to the 2026-07-03 and 2026-07-06 current-AEX Windows recaptures for case_0023. The old packaged-stale explanation is therefore not valid for the current files in this worktree.

## Reference Comparisons

| Pair | Status | Nonzero px | Max diff | Mean diff |
| --- | --- | ---: | ---: | ---: |
| `packaged_vs_current_win_20260703` | `compared` | `0` | `0` | `0.0` |
| `packaged_vs_current_win_20260706` | `compared` | `0` | `0` | `0.0` |
| `current_win_20260703_vs_20260706` | `compared` | `0` | `0` | `0.0` |
| `current_win_20260706_vs_mac_live_bg_on_20260703` | `compared` | `73` | `61165` | `1.0517777054398147` |
| `win_bg_off_vs_mac_bg_off_20260703` | `compared` | `73` | `65535` | `1.1784258053626544` |
| `win_bg_off_vs_mac_bg_off_refresh` | `compared` | `73` | `65535` | `1.1784258053626544` |

## Sample Pixels

| Image | (1698,7) | (1699,7) | (1700,7) | (414,393) | (415,393) | (416,393) |
| --- | --- | --- | --- | --- | --- | --- |
| `packaged_16bpc` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` |
| `current_win_20260703` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` |
| `current_win_20260706` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` |
| `mac_live_bg_on_20260703` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` |
| `win_bg_off` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `mac_bg_off_20260703` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |
| `mac_bg_off_refresh` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |

## Inputs

- packaged_16bpc: `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png` (`sha256:4ffcbd0015557e076067969ce364625e9aad12ffb8c96756a97d7dc6d8ad4910`)
- current_win_20260703: `refs/win_references/olm_reference_return_windows_20260703_combined/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex.png` (`sha256:4ffcbd0015557e076067969ce364625e9aad12ffb8c96756a97d7dc6d8ad4910`)
- current_win_20260706: `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex.png` (`sha256:4ffcbd0015557e076067969ce364625e9aad12ffb8c96756a97d7dc6d8ad4910`)
- mac_live_bg_on_20260703: `refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_on/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png` (`sha256:cc68fbe4645a6711ba1ea253885b8d84b2f55c09e30389f43d9ae48da95a4d67`)
- win_bg_off: `refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__olmdistancegradation_case_0023_bg_off_variant.png` (`sha256:933ea782e5781556b95cfb739abcfb8f0dfa021ff63d99a784ca2497262dbf64`)
- mac_bg_off_20260703: `refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_off/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png` (`sha256:28b2b3a99766f30665c5efe646cfbcb50cfba1bc614079140d38df3221cf5391`)
- mac_bg_off_refresh: `refs/reports/ae_single_case_distancegradation_case0023_live_refresh_bg_off/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png` (`sha256:28b2b3a99766f30665c5efe646cfbcb50cfba1bc614079140d38df3221cf5391`)
