# OLM RadialBlur PF32 Rotation Edge Fade — 2026-08-11

Status: **exact**

The actual AEX and production agree through polar, source scalar, the separate prepass-alpha plane, accum/max-alpha, final RGBA, coordinates, and padded output for Outer/Inner Fade 50/100. The recovered rule uses zero-based spans 49/99, direct span-sized Gaussian tables, and one linear cross-row tap before within-row wrapping.
