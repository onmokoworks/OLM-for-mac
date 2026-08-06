# OLMDistanceGradation case_0023 Neighborhood Probe Result - 2026-07-26

- Case: `olmdistancegradation_extended__case_0023`
- Probe dir: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707`
- Points: `18`
- Debug fields match between bg modes: `True`
- Shade stores match Mac PNG: `True`
- Shade source matches input PNG: `True`
- Safe claim: The 3x3 neighborhoods around the two live case_0023 witnesses reproduce the same 73px full-frame residual while all logged shade sources match the request input PNG under AE PF_Pixel16 promotion and all logged shade stores match the Mac PNG. The newly logged neighboring points show the mismatch is still confined to the previously live boundary representatives in this neighborhood; this supports continuing with Windows final/source-ownership proof rather than broad field-helper or compose retuning.

## PNG Comparisons

| Pair | Nonzero px | Max diff | Mean diff |
| --- | ---: | ---: | ---: |
| `win_bg_on_vs_mac_bg_on` | `73` | `61165` | `1.0517777054398147` |
| `win_bg_off_vs_mac_bg_off` | `73` | `65535` | `1.1784258053626544` |

## Neighborhood Rows

| XY | alpha | raw_inside | field_x | source match | bg_on win | bg_on mac | bg_on match | bg_off win | bg_off mac | bg_off match |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| `(414,392)` | `1.0` | `34.9284973` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(414,393)` | `1.0` | `35.0142822` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(414,394)` | `1.0` | `35.0570946` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,392)` | `1.0` | `35.9026451` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `1.0` | `36.0138855` | `1.0` | `True` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `False` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `False` |
| `(415,394)` | `1.0` | `36.0555115` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(416,392)` | `1.0` | `36.8781776` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(416,393)` | `1.0` | `37.0135117` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(416,394)` | `1.0` | `37.0540161` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(1698,6)` | `0.0` | `0.0` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(1698,7)` | `0.0274658203` | `1.0` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1698,8)` | `0.784301758` | `1.41421354` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1699,6)` | `0.0` | `0.0` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(1699,7)` | `0.00393676758` | `1.0` | `0.0` | `True` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `False` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `False` |
| `(1699,8)` | `0.756866455` | `1.41421354` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1700,6)` | `0.0` | `0.0` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(1700,7)` | `0.0` | `0.0` | `1.0` | `True` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(1700,8)` | `0.384307861` | `1.0` | `0.0` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |

## Mismatch Points

- bg_on: (415,393), (1699,7)
- bg_off: (415,393), (1699,7)

## Inputs

- before_effects: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/request/input/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023_before_effects.png`
- bg_on_field: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_on/field_debug_report.json`
- bg_off_field: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_off/field_debug_report.json`
- bg_on_shade: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_on/shade_debug.txt`
- bg_off_shade: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_off/shade_debug.txt`
- mac_bg_on: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_on/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png`
- mac_bg_off: `refs/reports/ae_single_case_distancegradation_case0023_neighborhood_probe_20260707/bg_off/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png`
- win_bg_on: `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex.png`
- win_bg_off: `refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__olmdistancegradation_case_0023_bg_off_variant.png`
