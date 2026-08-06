# OLMSmoother2 v2 invert-white Key Color endpoint

Verdict: `PASS_V2_INVERT_WHITE_KEY_ENDPOINT_TO_PRODUCTION_EXACT`

The public white Key Color endpoint now covers the invert owner for exact, inside, outside, and far pixels before the natural classifier/worker. PF16/PF32 actual-AEX paths and production are byte-exact with LUTs and padding fixed.

Gamma interaction, multi-color key palettes, an exact PF16 tolerance tie, and AE-host execution remain unclaimed.
