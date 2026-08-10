# OLM RadialBlur typed Size Variation 32×18 — 2026-08-11

Status: **PASS (bounded actual-AEX exact)**

The centered 32×18 fixture was rendered as Zoom and Rotation at PF8, PF16,
and PF32 with Size Variation 1, 25, and 100. Outer Strength is 4, Inner
Strength is 0, Quality is 5, Repeat Border is on, and offset, edge, noise,
ellipse, and brightness controls are neutral. All 18 production renders match
the actual AEX internal consumer planes and padded output byte-for-byte.

Every source pixel in this fixture has alpha greater than zero. The actual AEX
labels the positive-alpha mask with `FUN_180008930`, stores each connected
component's area, and computes the typed source factor in float32 order as:

```
SV = float32(SizeVariation * 0.01)
factor = float32(float32(float32(area * float32(1 / max_area)) * SV)
                 + float32(1 - SV))
```

An auxiliary 32×18 component fixture with areas 1, 4, 16, and 64 confirms the
same producer in PF8, PF16, and PF32. At Size Variation 100 its factors are
1/64, 1/16, 1/4, and 1. With Noise Variation zero, `FUN_1800065c0` forwards
the factor as the span source, and the blur consumer derives its effective
length from it.

For the admitted render fixture the whole positive-alpha frame is one connected
component. Rotation's captured owner size-factor plane contains harmless
near-one float32 interpolation values, while the consumed PF16/PF32 span is
bitwise 1.0; all captured downstream planes and outputs are exact. Zoom's
pre-blur, post-blur, and output planes are identical to its Size Variation zero
control and exact against production.

Production admission is intentionally restricted to this 32×18 tuple, the
three witnessed Size Variation values, and a runtime scan requiring every typed
source alpha to be strictly greater than zero. It does not cover alpha zero,
negative alpha, PF32 NaN/Infinity, disconnected components, other geometry, or
other parameter combinations.

Machine-readable evidence:

- `olmradialblur_zoom_size_variation_32x18_probe_20260811.json`
- `olmradialblur_rotation_size_variation_32x18_actual_aex_20260811.json`
