# OLM RadialBlur simultaneous Outer and Inner Strength — 2026-08-11

Status: **PASS (bounded actual-AEX exact)**

The centered 32×18 fixture was rendered in Zoom and Rotation at PF8, PF16,
and PF32 with Outer Strength 4 and Inner Strength 2 or 4. Offset, edge fade,
ellipse, Size Variation, and Noise Variation are neutral; Quality is 5 and
Repeat Border is enabled. All 12 production renders match the actual AEX
internal planes and padded output byte-for-byte.

Outer and Inner are not separately normalized and composited. They contribute
to the same RGBA accumulation and maximum-alpha planes, followed by one RGB
normalization. Output alpha is the greatest single contribution rather than
the accumulated alpha.

Zoom processes the outward taps and then the inward taps for each source
radius. Its captured pre-blur and combined post-blur planes and typed output are
exact in all six cells. Rotation calls the outward direction before the inward
direction; polar, source scalar, prepass alpha, accumulation, maximum alpha,
final RGBA, coordinates, and typed output are exact in all six cells.

The production gate is limited to this geometry and parameter tuple. It does
not generalize other strengths, edge/offset interaction, unusual alpha values,
or other geometry.

Machine-readable evidence:

- `olmradialblur_zoom_dual_strength_32x18_actual_aex_20260811.json`
- `olmradialblur_rotation_dual_strength_32x18_probe_20260811.json`
