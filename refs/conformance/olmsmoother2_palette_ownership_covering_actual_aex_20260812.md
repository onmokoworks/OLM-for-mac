# OLMSmoother2 palette ownership covering matrix

Verdict: `PASS_18_PALETTE_OWNERSHIP_GAMMA_KEY_SMOOTHING_ALL_DEPTHS_EXACT`

Six covering tuples cross public palette counts 1/5, normal/reordered/duplicate ownership, Gamma Colors 1.0/2.4, key off/non-invert/invert, default/mixed smoothing, and PF8/PF16/PF32 on one padded 9x7 non-uniform fixture. All 18 actual-AEX owner/classifier/typed-worker outputs match production raw bytes exactly with padding preserved.

The prior 54-case two-entry palette matrix remains the control. Arbitrary palettes, arbitrary cross-products, and AE-host execution are not generalized.
