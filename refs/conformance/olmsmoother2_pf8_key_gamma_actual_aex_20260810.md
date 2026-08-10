# OLMSmoother2 PF8 key + Gamma Colors boundary

Verdict: `PASS_PF8_V2_KEY_AND_INVERT_PLUS_GAMMA_COLORS_TO_PRODUCTION_EXACT`

The checked-in AEX and production are byte-exact for both non-invert and invert key ownership followed by ordered `[red, key]` Gamma Colors processing. Both paths naturally generate nonzero class planes, use the captured LUT pair, execute the PF8 typed worker, and preserve five padding bytes per row.

This evidence is limited to the declared 3x2 fixtures and does not claim other key colors, palettes, geometry, or AE-host execution.
