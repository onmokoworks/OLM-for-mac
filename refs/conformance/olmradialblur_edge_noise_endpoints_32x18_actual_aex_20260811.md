# OLM RadialBlur Edge Fade × procedural Noise endpoints — 2026-08-11

Status: **72/72 consumed-plane/output exact with known inactive Rotation Type1 source-scalar boundary**

Centered 32x18 PF8/PF16/PF32; Zoom Outer and Rotation Outer/Inner Strength4; Edge Fade50/100 x Noise Variation25/100 x procedural Type1/2; Seed1 Offset0 Thickness10; Size Variation0 and neutral remaining tuple.

Edge Fade prepass consumes the independent size-factor slot. With Size Variation 0 it is exactly 1.0. The Type1/2 noise-composed source span is consumed only by the later strength scatter.

Evidence boundary: Only the 72 enumerated fixed-fixture cells are admitted. Rotation Type1 retains previously documented one-ULP sampled source-scalar differences only in inactive allocation-boundary cells; every consumed plane and output is exact. Zoom actual B150-only alpha is not separately exported, so its evidence is the independent size-factor/source-span inputs plus actual pre/post worker planes, not a claimed hidden-plane comparison. Other values, Type3, Size Variation intersections, geometry, seed/offset/thickness, and AE-host behavior remain unproved.
