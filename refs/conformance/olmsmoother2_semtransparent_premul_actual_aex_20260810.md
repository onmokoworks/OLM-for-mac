# OLMSmoother2 semi-transparent premultiplication boundary

Verdict: `PASS_SEMITRANSPARENT_PREMUL_KEY_GAMMA_V1_V2_ALL_DEPTHS_ACTUAL_AEX_TO_PRODUCTION_EXACT`

A padded nonuniform 5x5 fixture crosses Version 1/2, PF8/PF16/PF32, and straight versus native-rounded premultiplied inputs at alpha 0, near-zero, 0.25, 0.5, 0.75, and 1. The base family uses key-off/Gamma None; representative Version 2 intersections add Gamma All with key off and with a non-invert colored key. Actual AEX classifier/core/writer bytes or float32 bits equal production in all 24 cells. The key intersection retains fractional-alpha pixels rather than collapsing the test to alpha 0/1.

The checked-in AEX setter initializes its two premultiplication-control bytes at setter `+0x20/+0x21` to zero and has no later write in `FUN_180004e10`; this supports production `keep_premul=false`. The fixture does not claim which world representation AE supplies.
