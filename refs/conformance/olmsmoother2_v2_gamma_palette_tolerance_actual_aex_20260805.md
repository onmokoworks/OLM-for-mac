# OLMSmoother2 v2 Gamma Colors tolerance boundary

Verdict: `PASS_V2_GAMMA_COLORS_TOLERANCE_ORDERED_PALETTE_TO_PRODUCTION_EXACT`

The ordered palette `[red, black]` forces the boundary target through the second entry. Direct actual-AEX comparator isolation proves one-ULP-below matches while exact equality and one-ULP-above reject under strict `<`. The natural v2 owner/classifier/worker path is production-byte exact for PF16/PF32 with captured LUTs and padding. PF16 codes 64/65 bracket the non-representable exact tie.

Key interaction, other palettes/geometries, and AE host remain unclaimed.
