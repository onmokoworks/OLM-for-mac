# OLMDirectionalBlur PF32 Front Alpha Fade family — 2026-08-10

## Result

The PF32 production route accepts `Front Alpha Fade` from `0..100` for the
following fixed boundary: 16x16 padded ARGB128, angle 45, brightness gain 1,
front strength 8, back strength 0, Size Variation/Sharp Tail/noise disabled,
and render scale 1/1.

Actual-AEX typed output and the production worker are raw-byte identical at
`0`, `50`, and `100`, covering the public endpoints and midpoint. The public
production dispatcher is independently exercised at `50` and `100`, with row
padding preserved. Values `-1` and `101` remain fail-closed and leave output
untouched.

The implementation adds the missing PF32 prepass table/count plumbing. It uses
the same binary-grounded Gaussian builder and rowdriver prepass contract already
used by the exact PF8 route; the prior zero-fade wrapper remains ABI-compatible.

## Evidence

- `tools/emulation/test_olmdirectionalblur_pf32_front_alpha_fade_family_actual_aex_20260810.py`
- `refs/conformance/olmdirectionalblur_pf32_front_alpha_fade_family_actual_aex_20260810.json`
- `tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py`
- `core/dblur_frontonly.cpp`
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`

## Boundary

PF16, Sharp Tail, Back Alpha Fade, combinations with Size Variation/noise/back
blur/other angles or strengths/downsample, and native AE export remain unproven.
