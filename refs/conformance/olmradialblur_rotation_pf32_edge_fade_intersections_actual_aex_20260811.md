# OLM RadialBlur PF32 Edge Fade intersections — 2026-08-11

Status: **exact_size50_noise_fail_closed**

Outer and Inner Edge Fade50 × opaque Size Variation50 are exact across every captured plane and are admitted narrowly. Noise Variation25 is localized separately: the Outer candidate reached exact prepass/output but retained source-scalar ULP differences; Inner also differed in prepass/max-alpha. Both Noise intersections therefore remain fail-closed. The AEX Edge Fade prepass consumes the sampled size-factor slot, while scatter later consumes the noise-composed span slot.
