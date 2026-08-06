# OLMSmoother2 v2 key + Gamma Colors interaction

Verdict: `PASS_V2_NONINVERT_KEY_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT`

Non-invert keying clears a key-matching pixel alpha before decode/classification. Gamma Colors then compares RGB against ordered `[red, key]`, so the keyed pixel remains an RGB palette candidate despite alpha zero. Actual owner/classifier/worker and production are byte-exact for PF16/PF32, with LUTs and padding fixed.

Invert-key interaction, other palettes/geometries, and AE host remain unclaimed.
