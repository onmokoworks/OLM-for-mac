# OLMRadialBlur reconstructed B150 portable oracle (2026-07-17)

- Status: `pass`
- Classification: `bounded-reconstructed-b150-equivalence-proven`
- The oracle is independent of actual AEX output: it derives expected words from the six seed RGBA values and zero-span decomp operations.
- Promotion requires all six cells and both RGBA/scalar raw float32 word sets to match.

- All six raw-word sets match: `True`.
