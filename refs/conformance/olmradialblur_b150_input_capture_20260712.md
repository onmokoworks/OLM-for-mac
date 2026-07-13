# OLMRadialBlur B150 Input Capture

Date: 2026-07-12

## Scope

`tools/emulation/probe_radialblur_final_plane_small.py` now records the first
`FUN_18000b150` call in the bounded live-AEX probe. It is emulator evidence
only; it is not a substitute for the Windows case_0009 full-frame witness.

## FACT

- The probe reaches the live `0x18000b150` entry once before the
  `0x180005d99` final-plane boundary.
- The captured call exposes the Windows x64 ABI arguments: context, source
  RGBA plane, two scalar planes, width, row range, and output planes.
- The probe records the first four source/scalar words for the call and the
  context table/span fields when readable.
- The bounded smoke passes with `width=49`, `row_start=0`, `row_end=5`, and
  four captured source/scalar rows.
- The first bounded source word is `[0, 0, 0, 1]`; the two scalar inputs are
  finite float32 values.

## INFERENCE

- The local harness can now accept and replay typed B150 inputs once the
  Windows full-frame return supplies the corresponding case_0009 words.
- The bounded capture does not identify the case_0009 `fVar28` value or
  explain the 254/255 residual. No production source change is authorized by
  this result.

## Verification

```sh
python3 refs/scripts/smoke_radialblur_final_plane_small.py
```

Result: PASS.
