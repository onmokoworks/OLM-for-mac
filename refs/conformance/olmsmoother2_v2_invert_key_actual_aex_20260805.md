# OLMSmoother2 v2 Invert Key boundary

Verdict: `PASS_V2_INVERT_KEY_PALETTE_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT`

Actual AEX `FUN_180002930` keeps alpha only for palette matches. PF32 inside remains alpha 1 while exact tie/outside become alpha 0; PF16 adjacent codes bracket the unrepresentable tie. Natural classifier, typed worker, production bytes, LUTs, and padding agree.

Multi-color palettes, Gamma UI modes, other geometry, and AE host are unclaimed.
