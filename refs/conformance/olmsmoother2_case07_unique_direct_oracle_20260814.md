# OLMSmoother2 case-07 unique direct-output oracle

Status: `PASS_WINDOWS_FINAL_EXR_HAS_UNIQUE_STRAIGHT_PF32_PREIMAGE_MATCHING_CURRENT_SOURCE`

The retained Windows actual-AEX effect-on EXR contains 8,294,400
semantic ARGB float32 words. The current source independently emits straight
PF32 SHA `31bbdb17ef62802bc7d67fd66e552e5c0fd7d1e5a740d7aca923acb1d15bf65c`. Applying the observed output-module
operation, one float32 `RGB *= A` per channel while copying alpha, reproduces
all words with zero mismatch. Float32 division recovers every direct word, and
testing both adjacent float32 values gives
`0` alternative preimages.

This uniquely recovers the direct straight output for this finite fixture; it
is not a native output-world memory capture. Production admission is governed
by the separate real-SDK public Smart safety closure.
No After Effects process was launched.
