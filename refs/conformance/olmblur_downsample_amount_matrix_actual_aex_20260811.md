# OLMBlur downsample_x × Amount matrix

- Status: `exact`
- Geometry: constant `24×24`; no width/ref-width reconstruction
- Matrix: PF8/PF16/PF32 × Amount `5, 129.4` × Repeat `1, 2` × Legacy off/on × `downsample_x` `1/2, 1/1, 2/1`
- Fixed controls: Smoothness `100`, Bias Direction `1`, `downsample_y=1/1`
- Cases: 72 complete typed buffers

The oracle calls the pinned actual-AEX typed worker with its real context
rational. Non-Legacy mutates Amount by that x ratio. Legacy instead scales only
the integer radius while forming Gaussian sigma from the unscaled UI Amount.
The production comparison keeps both source and destination worlds at exactly
`24×24`, supplies the unscaled UI Amount through parameter checkout, and
supplies the rational only through `PF_InData.downsample_x`. Production
`EffectMain(PF_Cmd_SMART_PRE_RENDER)` →
`EffectMain(PF_Cmd_SMART_RENDER)` therefore has to read and apply that host
mode-specific contract to match.

All active bytes and row-padding guards match. This proves the rational scaling
contract for the bounded matrix; it does not claim native AE preview world
sizing, the actual AEX public SmartRender callback chain, `downsample_y`
anisotropy, or other geometry and controls.

```sh
python3 tools/emulation/test_olmblur_downsample_amount_matrix_actual_aex_20260811.py
python3 tools/emulation/test_olmblur_downsample_amount_matrix_actual_aex_20260811.py --export
```
