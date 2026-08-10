# OLMDirectionalBlur PF32 Size Variation family — 2026-08-10

## Result

The PF32 production route now accepts the public `Size Variation` slider family
`0..100%` for the already-proven fixed route:

- 16x16 padded ARGB128
- angle 45 degrees
- brightness gain 1
- front strength 8, back strength 0
- fade, sharp tail, and noise disabled
- render scale 1/1

Actual-AEX and production raw output are byte-identical at `0`, `25`, `50`,
and `100`. These representatives cover both public endpoints, a non-half
interior value, and the previously accepted midpoint. The public production
dispatcher is exercised separately at `25` and `100`, including row-padding
preservation. Values `-1` and `101` remain fail-closed with untouched output.

## Evidence

- Actual/worker focused gate:
  `tools/emulation/test_olmdirectionalblur_pf32_size_variation_family_actual_aex_20260810.py`
- Machine-readable results:
  `refs/conformance/olmdirectionalblur_pf32_size_variation_family_actual_aex_20260810.json`
- Public production dispatcher gate:
  `tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py`
- Production source:
  `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`

The actual path executes typed callbacks `0x180006a20` and `0x180006bd0`; only
host callbacks are modeled. Production uses `olm_dblur_minimal_argb32` through
the normal fail-closed `RenderWorld` predicate.

## Boundary

This does not generalize to PF16, other strength/angle/back combinations,
fade/tail/noise combinations, downsampled rendering, values outside `0..100`,
or native AE export.
