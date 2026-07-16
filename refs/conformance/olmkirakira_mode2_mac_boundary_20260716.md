# OLMKiraKira Mode 2 Mac boundary fixture

Date: 2026-07-16
Scope: local Mac-source semantics only
AE exact: **false**

## Result

`tools/emulation/test_olmkirakira_mode2_mac_boundary_20260716.py` passes its
source anchors and replays one bounded chain:

`Mode-2 post-clamp float -> screen-over inputs/formula -> pre-writeback RGBA -> PF8/PF16/PF32 conversion`

The Mode-2 input is the checked-in `one_short_ray` post-clamp witness. The
source pixel is opaque gray `30/255` in each RGB channel. Both opacities are
`1.0`.

## Typed values

| Stage | RGBA |
| --- | --- |
| Mode-2 post-clamp float | `(0.25, 0.5, 0.75, 0.2)` |
| pre-writeback float | `(0.1617646813, 0.2058823705, 0.25, 1.0)` |
| PF8 | `(41, 53, 64, 255)` |
| PF16 | `(5301, 6746, 8192, 32768)` |
| PF32 | `(0x3e25a5a4, 0x3e52d2d4, 0x3e800000, 0x3f800000)` |

The compose formula is the Mac source form:

`rgb = 1 - (1 - source.rgb) * (1 - glow.rgb * clamp(glow.a * glow_opacity))`

`alpha = source.a * source_opacity`

## FACT

- FACT: the checked-in Mode-2 witness supplies the post-clamp float input and
  explicitly does not claim AE exactness.
- FACT: Mac `OLMKiraKira.cpp` reads PF8/PF16 channels as normalized values,
  reads PF32 as float channels, applies screen-over RGB, preserves source-alpha
  semantics, and writes PF8/PF16 with `lround` after clamp.
- FACT: checked-in AEX writer constants at `0x1814d65a8` and `0x1814d65ac`
  are `255.0` and `32768.0`; the Mac PF16 scale now uses `PF_MAX_CHAN16`.
- FACT: the test checks these source expressions and the Mode-2 witness status
  before emitting the derived values.

## INFERENCE and limits

- INFERENCE: the Python replay is a bounded local model of the operation order.
- INFERENCE: the three typed tuples are expected results for the supplied
  inputs under the checked-in Mac source semantics.
- This does not prove host binding, a selected writer address, Windows output,
  PNG bytes, or AE exactness.

## Verification

```text
python3 tools/emulation/test_olmkirakira_mode2_mac_boundary_20260716.py
=> exit 0; all 11 source/evidence/AEX-constant checks pass
```
