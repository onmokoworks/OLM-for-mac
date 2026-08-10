# OLM RadialBlur PF32 opaque Size Variation family — 2026-08-10

Status: **PASS (bounded actual-AEX exact)**

For the pinned 9×7 PF32 Rotation fixture whose alpha is everywhere 0.5 or 1.0, Size Variation 1, 25, and 100 produce the same polar/source-scalar/accum/max/final-coordinate planes and padded output as Size Variation 0, byte-for-byte. Production may admit this semantic-noop family only after checking every input alpha is strictly positive.

This does not cover inputs containing alpha zero, Noise Variation, other bit depths/geometries, or other parameter tuples.
