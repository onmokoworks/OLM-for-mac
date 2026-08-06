# OLMSmoother2 v2 Smoothness 0 endpoint

Verdict: `PASS_V2_SMOOTHNESS_ZERO_LOWER_ENDPOINT_TO_PRODUCTION_EXACT`

The public Smoothness lower endpoint `0` is exercised on a nonuniform 3x2 frame with Smooth Range 1. PF16/PF32 actual classifier/worker and production bytes agree exactly; classifier plane, captured LUTs, and row padding are fixed.

Other Smoothness/Range combinations, key/gamma interaction, and AE-host execution are unclaimed.
