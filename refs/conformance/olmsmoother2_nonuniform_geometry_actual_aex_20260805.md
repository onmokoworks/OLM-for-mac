# OLMSmoother2 nonuniform classifier/c280 3x2 boundary

Verdict: `PASS_NATURAL_AEX_CLASSIFIER_C280_TO_PRODUCTION_PADDED_3X2_EXACT`

Actual AEX naturally generates the nonzero class plane and its typed worker consumes it. PF16/PF32 production `RenderBits` matches every output and preserves row padding.

- Class plane: `00000000ff000000ff00000000ff00ffffffff00ffffff00`
- Nonzero class bytes: `10 / 24`

This is limited to the declared nonuniform 3x2 fixture; v2, key, gamma, other geometry, and AE host are unclaimed.
