# OLMSmoother2 v2 key threshold boundary

Verdict: `PASS_V2_KEY_THRESHOLD_NATURAL_AEX_TO_PRODUCTION_PADDED_3X2_EXACT`

Actual AEX `FUN_180002a70` runs before natural classifier/c280 and typed writeback. Production is raw exact with padding preserved. PF32 covers inside/equality/outside; equality follows `COMISS/JNC` and is not keyed. PF16 has no exactly representable tie for an 8-bit key color, so adjacent codes 65/64 bracket the threshold.

Invert key, Gamma UI modes, other key colors/geometry, and AE host are unclaimed.
