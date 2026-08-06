# OLMSmoother2 v2 nonuniform LUT boundary

Verdict: `PASS_V2_NATURAL_AEX_CLASSIFIER_TYPED_LUT_TO_PRODUCTION_PADDED_3X2_EXACT`

The actual AEX consumes a naturally generated class plane and the captured 10,000-entry input/output LUT contract. PF16/PF32 production output and row padding are exact for the independent 3x2 fixture.

Class plane: `00000000ff000000ff00000000ff00ffffffff00ffffff00` (10/24 nonzero).

Key, gamma UI modes, other geometry, and AE host remain unclaimed.
