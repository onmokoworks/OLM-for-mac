# OLMSmoother2 v2 invert-key + Gamma Colors interaction

Verdict: `PASS_V2_INVERT_KEY_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT`

The actual invert-key palette owner retains alpha only for key matches before decode/classification. Gamma Colors then compares RGB independently: red has alpha cleared but still matches ordered palette index 0, while key RGB retains alpha and matches index 1. PF16/PF32 owner/classifier/worker and production are byte-exact with LUTs and padding fixed.

Other palettes/geometries and AE host remain unclaimed.
