# OLMSmoother2 v2 Gamma Value 1.0 identity endpoint

Verdict: `PASS_V2_GAMMA_COLORS_GAMMA_VALUE_1_IDENTITY_ENDPOINT_TO_PRODUCTION_EXACT`

The public Gamma Value lower endpoint `1.0` is exercised in Gamma Colors mode with ordered `[white, red]`. Palette membership remains active, while the selected exponent is the identity endpoint. PF16/PF32 actual classifier/worker and production bytes agree exactly with captured LUTs and preserved padding.

Values outside 1.0..2.4, key interaction, and AE-host execution are unclaimed.
