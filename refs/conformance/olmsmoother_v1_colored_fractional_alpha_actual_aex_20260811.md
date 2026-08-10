# OLMSmoother v1 colored fractional-alpha boundary

Verdict: `V1_COLORED_FRACTIONAL_ALPHA_BOUNDARY_RECORDED`

A premultiplied, non-grayscale padded 7×5 fixture crosses twelve alpha codes, effective Color Key off/on, four representative smoothing tolerances, and PF8/PF16. 14 of sixteen exported Windows AEX versus production EffectMain cells are byte-exact; the JSON preserves the remaining PF16 boundary instead of promoting it to an exactness claim. This does not claim native PF32 behavior.
