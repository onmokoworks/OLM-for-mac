# OLMSmoother v1 colored fractional-alpha boundary

Verdict: `PASS_V1_COLORED_FRACTIONAL_ALPHA_16_CELLS_EXACT`

A premultiplied, non-grayscale padded 7×5 fixture crosses twelve alpha codes, effective Color Key off/on, four representative smoothing tolerances, and PF8/PF16. All sixteen exported Windows AEX versus production EffectMain cells are byte-exact after replacing the reconstructed PF16 classifier with its full actual-AEX CFG. This does not claim native PF32 behavior.
