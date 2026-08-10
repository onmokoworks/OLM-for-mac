# OLM RadialBlur PF32 Edge Fade intersections — 2026-08-11

Status: **exact**

Outer and Inner Edge Fade50 crossed with opaque Size Variation50 or Type1 Noise Variation25 are exact across polar, source scalar, prepass, accumulation, max alpha, final RGBA, coordinates, and padded output. Radial noise interpolation uses the AEX scalar float32 instruction order. At the Inner angular boundary, the prepass reads the adjacent source-scalar allocation once before repairing the wrap.
