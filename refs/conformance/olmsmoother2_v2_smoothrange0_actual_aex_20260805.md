# OLMSmoother2 v2 Smooth Range 0 endpoint

Verdict: `PASS_V2_SMOOTH_RANGE_ZERO_LOWER_ENDPOINT_TO_PRODUCTION_EXACT`

The public Smooth Range range is `0..100` with default `2`; its lower endpoint `0` is isolated with Smoothness `100` on a nonuniform 3x2 frame. PF16/PF32 actual classifier/worker and production bytes agree exactly; classifier plane, captured LUTs, and padding are fixed. This is distinct from the Smoothness `0` fixture.

Other parameter combinations and AE-host execution are unclaimed.
