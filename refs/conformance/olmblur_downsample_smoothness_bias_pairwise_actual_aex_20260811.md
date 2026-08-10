# OLMBlur downsample × Smoothness/Bias pairwise matrix

- Status: `exact_pairwise`
- Geometry: constant `24×24`
- Depths: PF8/PF16/PF32
- Values: x `1/2, 2/1`; y `1/1, 2/1`; Amount `5, 129.4`; Repeat `1, 2`; Smoothness `25, 100`; Bias `1, 2`; Legacy off/on
- Cases: 48 rather than the 384-cell full Cartesian product

Each Legacy branch uses an independent strength-2 `OA(8,6,2)` covering matrix.
Within that branch, every pair of x, y, Amount, Repeat, Smoothness, and Bias
occurs in all four binary value combinations. Bias values follow the actual UI:
`1=Vertical` (horizontal then vertical) and `2=Horizontal` (vertical then
horizontal).

The first Legacy/non-default-Smoothness differential exposed an important
mode-specific scale rule. Actual AEX Legacy workers scale the integer radius by
`downsample_x`, but form Gaussian sigma from the unscaled UI Amount and
Smoothness. Non-Legacy scales Amount before its radius-decay schedule and does
not consume Smoothness. Production now passes UI Amount and render scale
separately into all three Legacy typed workers instead of pre-scaling Amount.

After that correction, all 48 actual-AEX complete buffers match production
`EffectMain` SmartPreRender → SmartRender byte-for-byte, including padding.
`downsample_y` remains inactive and neither axis transforms Smoothness or Bias.

The matrix proves all two-factor interactions inside each Legacy branch, not
arbitrary three-way combinations, native AE world resizing, or other values.

```sh
python3 tools/emulation/test_olmblur_downsample_smoothness_bias_pairwise_actual_aex_20260811.py
python3 tools/emulation/test_olmblur_downsample_smoothness_bias_pairwise_actual_aex_20260811.py --export
```
