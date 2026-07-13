# OLMDistanceGradation case_0023 Mac Probe Result - 2026-07-13

- Case: `olmdistancegradation_extended__case_0023`
- Probe dir: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707`
- Debug points match between bg modes: `True`
- Shade stores match Mac PNG: `True`
- Safe claim: Mac AE bg_on and bg_off probe runs produce identical debug fields at the witness points, but at least one exported PNG still differs from the corresponding Windows Software reference. The shade debug logs capture source RGBA, x_row/a_row, compose output floats, and 16bpc stores at the same points, and those stores match the Mac PNG values after transparent-RGB zeroing. Keep the remaining lane on mismatch-neighborhood shade/source ownership or same-run raw output provenance, not broad field-helper retuning.

## PNG Comparisons

| Pair | Nonzero px | Max diff | Mean diff |
| --- | ---: | ---: | ---: |
| `win_bg_on_vs_mac_bg_on` | `73` | `61165` | `1.0517777054398147` |
| `win_bg_off_vs_mac_bg_off` | `73` | `65535` | `1.1784258053626544` |

## Debug Point Equality

| XY | match | field_x | raw_inside | alpha |
| --- | ---: | ---: | ---: | ---: |
| `(1698,7)` | `True` | `0.0` | `1.0` | `0.0274658203` |
| `(1699,7)` | `True` | `0.0` | `1.0` | `0.00393676758` |
| `(1700,7)` | `True` | `1.0` | `0.0` | `0.0` |
| `(414,393)` | `True` | `0.0` | `35.0142822` | `1.0` |
| `(415,393)` | `True` | `1.0` | `36.0138855` | `1.0` |
| `(416,393)` | `True` | `1.0` | `37.0135117` | `1.0` |

## Shade Points: bg_on

| XY | src_a | field_x | d_alpha | out RGBA float | promoted RGBA16 | Mac PNG RGBA16 | store match |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| `(1698,7)` | `0.0274658203` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1699,7)` | `0.00393676758` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1700,7)` | `0.0` | `1.0` | `0.0` | `[1.0, 0.0, 0.0, 1.0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |
| `(414,393)` | `1.0` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `1.0` | `1.0` | `1.0` | `[1.0, 0.0, 0.0, 1.0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |
| `(416,393)` | `1.0` | `1.0` | `1.0` | `[1.0, 0.0, 0.0, 1.0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |

## Shade Points: bg_off

| XY | src_a | field_x | d_alpha | out RGBA float | promoted RGBA16 | Mac PNG RGBA16 | store match |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: |
| `(1698,7)` | `0.0274658203` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1699,7)` | `0.00393676758` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1700,7)` | `0.0` | `1.0` | `0.0` | `[0.109804153, 0.0, 0.933333397, 0.0]` | `[7195, 0, 61165, 0]` | `[0, 0, 0, 0]` | `True` |
| `(414,393)` | `1.0` | `0.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 1.0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `1.0` | `1.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 0.0]` | `[7195, 0, 61165, 0]` | `[0, 0, 0, 0]` | `True` |
| `(416,393)` | `1.0` | `1.0` | `1.0` | `[0.109804153, 0.0, 0.933333397, 0.0]` | `[7195, 0, 61165, 0]` | `[0, 0, 0, 0]` | `True` |

## Sample Pixels: bg_on

| XY | Windows RGBA16 | Mac RGBA16 | match |
| --- | --- | --- | ---: |
| `(1698,7)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1699,7)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `False` |
| `(1700,7)` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |
| `(414,393)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `False` |
| `(416,393)` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |

## Sample Pixels: bg_off

| XY | Windows RGBA16 | Mac RGBA16 | match |
| --- | --- | --- | ---: |
| `(1698,7)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(1699,7)` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `False` |
| `(1700,7)` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |
| `(414,393)` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` | `False` |
| `(416,393)` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `True` |

## Inputs

- bg_on: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on/field_debug_report.json`
- bg_off: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off/field_debug_report.json`
- bg_on_shade: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on/shade_debug.txt`
- bg_off_shade: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off/shade_debug.txt`
- mac_bg_on: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_on/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png`
- mac_bg_off: `refs/reports/ae_single_case_distancegradation_case0023_mac_probe_20260707/bg_off/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png`
- win_bg_on: `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex.png`
- win_bg_off: `refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__olmdistancegradation_case_0023_bg_off_variant.png`
