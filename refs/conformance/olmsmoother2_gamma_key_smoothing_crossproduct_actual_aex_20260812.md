# OLMSmoother2 Gamma/key/smoothing bounded cross-product

Verdict: `PASS_53_EXACT_ONE_PF8_GAMMA_ALL_MIXED_FAIL_CLOSED`

A padded 9x7 non-uniform fixture crosses public Gamma Value endpoints `1.0/2.4`, Gamma All and Gamma Colors with both key polarities, three smoothing boundary tuples, and PF8/PF16/PF32. 53 of 54 actual-AEX owner/classifier/typed-worker outputs match production raw bytes exactly, with row padding preserved.

The sole unsupported seam is PF8 Gamma All at 2.4 with the mixed `(Smoothness, Range, Extra Smooth) = (50, 50, 50)` tuple: five output bytes differ. It remains fail-closed pending a focused typed-writer witness; no rounding rule is inferred from it. Other key colors, palettes, arbitrary parameter products, and AE-host execution also remain unclaimed.
