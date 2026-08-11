# OLM RadialBlur Rotation Edge Fade × Offset × Noise — 2026-08-11

Status: **exact** (96/96)

Rotation centered 32x18 component fixture; PF8/PF16/PF32; Outer/Inner Strength4; Edge Fade50/100; Offset Mode2/3 UI4; Noise Variation25/100; Noise Type1/2; SV0, Seed1, Noise Offset0, Thickness10.

Edge prepass consumes independent size factor 1.0; per-radius Mode2/3 span is multiplied by the procedural noise-composed source span before truncation and scatter.

Evidence boundary: Only these 96 fixed-fixture cells are admitted. PF8 source-span is unavailable; all available consumed planes and padded output must be byte exact. Rotation Type1 sampled source-scalar may retain only the documented inactive allocation-boundary 1-ULP differences. Other values, Type3, Size Variation, geometry, and AE-host behavior remain fail-closed/unproved.
