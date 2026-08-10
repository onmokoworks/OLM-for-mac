# OLMBlur downsample_x × downsample_y cross

- Status: `exact_composition`
- Geometry: constant `24×24`
- Matrix: PF8/PF16/PF32 × Amount `5, 129.4` × Repeat `1, 2` × Legacy off/on × x `1/2, 2/1` × y `1/2, 2/1`
- Cases: 96 complete typed buffers

The expected buffers are the hash-pinned actual-AEX worker outputs for
`effective Amount = UI Amount × downsample_x`. Each x-specific oracle is reused
at both y ratios. Production receives the original UI Amount and both
`PF_InData` rationals through `EffectMain(PF_Cmd_SMART_PRE_RENDER)` →
`EffectMain(PF_Cmd_SMART_RENDER)` while source and destination dimensions remain
exactly `24×24`.

All 96 active buffers and padding guards match. The two independently proven
rules compose when both ratios are non-unit:

1. `downsample_x` scales Amount exactly once.
2. `downsample_y` does not affect Amount, geometry, or kernel in a fixed world.

No production change is required. Native AE preview world sizing, host-changed
dimensions, non-square pixel aspect, and other controls remain outside this
claim.

```sh
python3 tools/emulation/test_olmblur_downsample_xy_cross_actual_aex_20260811.py
python3 tools/emulation/test_olmblur_downsample_xy_cross_actual_aex_20260811.py --export
```
