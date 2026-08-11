# OLMSmoother2 Gamma/key/smoothing bounded cross-product

Verdict: `PASS_54_GAMMA_ENDPOINT_KEY_POLARITY_SMOOTHING_ALL_DEPTHS_ACTUAL_AEX_TO_PRODUCTION_EXACT`

A padded 9x7 non-uniform fixture crosses public Gamma Value endpoints `1.0/2.4`, Gamma All and Gamma Colors with both key polarities, three smoothing boundary tuples, and PF8/PF16/PF32. All 54 actual-AEX owner/classifier/typed-worker outputs match production raw bytes exactly, with row padding preserved.

The former five-byte PF8 Gamma All 2.4 / `(50,50,50)` seam was localized before the typed store: PF8 frame decode did not use the current-AEX 10,000-entry LUT, and arm64 contracted the scalar `MULSS` then `ADDSS` accumulation into FMADD. Applying the same LUT contract at every depth and retaining separate scalar accumulation closes the seam without expected-byte correction. Other key colors, palettes, arbitrary parameter products, and AE-host execution remain unclaimed.
