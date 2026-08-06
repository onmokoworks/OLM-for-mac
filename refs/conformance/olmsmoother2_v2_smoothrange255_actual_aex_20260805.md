# OLMSmoother2 v2 Smooth Range 255 internal fixture

Verdict: `PASS_V2_SMOOTH_RANGE_255_INTERNAL_OUT_OF_UI_RANGE_TO_PRODUCTION_EXACT`

The actual AEX public UI contract is `0..100` with default `2`. Value `255` is retained only as a direct internal worker fixture outside that UI range. With Smoothness `100` and Extra Smooth `0`, PF16/PF32 actual classifier/worker and production bytes are exact with LUTs and padding fixed. The output differs from both Range 0 and Range 1 at both depths, proving an independent internal-range effect.

This makes no claim that `255` is reachable through the public AE UI. Other parameter combinations and AE-host execution are also unclaimed.
