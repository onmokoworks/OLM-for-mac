# OLMSmoother2 PF8 Gamma All Colors boundary

Verdict: `PASS_PF8_V2_GAMMA_ALL_NATURAL_AEX_TO_PRODUCTION_EXACT`

For the declared padded 3x2 fixture, the checked-in AEX naturally generates a nonzero class plane, executes its PF8 worker with the captured decode/inverse LUT contract, and matches production `RenderBits<PF_Pixel8>` byte-for-byte. Five padding bytes per row remain unchanged.

This does not claim other gamma values, geometry, smoothing combinations, key interaction, or AE-host execution.
