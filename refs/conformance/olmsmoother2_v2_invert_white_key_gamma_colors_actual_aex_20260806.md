# OLMSmoother2 v2 invert-white key + Gamma Colors interaction

Verdict: `PASS_V2_INVERT_WHITE_KEY_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT`

The actual invert-key owner retains alpha for white-key tolerance matches before decode/classification. Gamma Colors then compares RGB independently: red loses alpha but remains palette index 0, while exact white retains alpha and matches index 1. PF16/PF32 owner, classifier, typed worker, production bytes, LUTs, and padding are exact.

Other key/palette endpoints, intermediate Gamma values, other geometry, and AE-host execution remain unclaimed.
