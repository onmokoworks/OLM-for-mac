# OLMSmoother2 PF8 nonuniform production boundary

Verdict: `PASS_PF8_NATURAL_AEX_CLASSIFIER_C280_TYPED_WORKER_TO_PRODUCTION_EXACT`

The checked-in Windows AEX naturally generated nonzero class planes and ran its PF8 typed worker for both v1 and v2. Production `RenderBits<PF_Pixel8>` matches every output byte and preserves five padding bytes per row on both declared 3x2 fixtures. The v2 path also consumes the captured 10,000-entry decode/inverse LUT pair.

- v1 class-plane nonzero bytes: `10 / 24`
- v2 class-plane nonzero bytes: `10 / 24`

This closes only the listed PF8 fixtures. Other geometry, parameter combinations, and AE-host execution remain outside this evidence boundary.
