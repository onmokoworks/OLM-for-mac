# OLMSmoother2 v2 Smooth Range 255 endpoint

Verdict: `PASS_V2_SMOOTH_RANGE_255_UPPER_ENDPOINT_TO_PRODUCTION_EXACT`

The public Smooth Range upper endpoint `255` is isolated with Smoothness `100` and Extra Smooth `0`. PF16/PF32 actual classifier/worker and production bytes are exact with LUTs and padding fixed. The output differs from both Range 0 and Range 1 at both depths, proving an independent endpoint effect.

Other parameter combinations and AE-host execution are unclaimed.
