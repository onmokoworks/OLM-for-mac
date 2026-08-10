# OLMBlur downsample_y anisotropy

- Status: `exact_no_effect`
- Geometry: constant `24×24`
- Matrix: PF8/PF16/PF32 × Amount `5, 129.4` × Repeat `1, 2` × Legacy off/on × `downsample_y` `1/2, 1/1, 2/1`
- Fixed: `downsample_x=1/1`, Smoothness `100`, Bias Direction `1`
- Cases: 72

The six typed actual-AEX workers read one render-scale rational from context
offsets `+0x11c/+0x120`. Existing hash-pinned complete worker outputs at that
rational's `1/1` value are therefore reused as the expected output for all
three y ratios. No world dimension is reconstructed: source and destination
remain exactly `24×24` in every cell.

Production `EffectMain(PF_Cmd_SMART_PRE_RENDER)` →
`EffectMain(PF_Cmd_SMART_RENDER)` receives `downsample_x=1/1` and only varies
`PF_InData.downsample_y`. All active typed bytes remain actual-AEX exact and
all row-padding guards remain intact. For this bounded fixed-world family,
`downsample_y` affects neither Amount, geometry, nor the kernel. No production
change is required.

This does not generalize to native AE changing the checked-out world size,
non-square pixel aspect, or other geometry and parameter families.

```sh
python3 tools/emulation/test_olmblur_downsample_y_anisotropy_actual_aex_20260811.py
python3 tools/emulation/test_olmblur_downsample_y_anisotropy_actual_aex_20260811.py --export
```
