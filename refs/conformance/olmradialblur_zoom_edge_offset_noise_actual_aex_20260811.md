# OLM RadialBlur Zoom Edge Fade × Offset × procedural Noise — 2026-08-11

Status: **48/48 exact**

Centered 32x18 PF8/PF16/PF32 Zoom Outer Strength4; Edge Fade50/100 x ignored Offset Mode2/3 UI4 x Noise Variation25/100 x procedural Type1/2; Seed1 Offset0 Thickness10, Size Variation0 and neutral remaining tuple.

The owner source size-factor is exactly 1 at Size Variation0. Procedural noise produces the independent source span; the Zoom B150 Edge Fade prepass consumes size-factor before the length-4 strength scatter consumes the noise span. Offset controls are ignored by the Zoom owner.

Every actual-AEX crossed cell is byte-identical to the same depth/Fade/NV/Type Mode1 Offset0 capture across all captured source/worker/final planes.

Evidence boundary: Only these 48 fixed-fixture cells are proven. Zoom B150-only faded alpha is not separately exported; direct post-worker/final/output equality plus exact independent source inputs forms the evidence. Other offsets, values, Type3, Size Variation intersections, geometry, seed/noise offset/thickness, and AE-host behavior remain unproved.
