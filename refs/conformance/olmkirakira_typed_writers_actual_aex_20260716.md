# OLMKiraKira Actual-AEX Typed Writer Proof (2026-07-16)

## Result

The checked-in Windows AEX writer helpers were executed directly with Unicorn.
This proves helper-local conversion only; it does not bind Mode 2 to these helpers or claim AE exactness.

| Depth | Input RGBA f32 bits | Observed ARGB units/bits | Instructions | Result |
| --- | --- | --- | ---: | --- |
| PF8 | `0x3f000000, 0x3f800000, 0x3e800000, 0x3f400000` | `[191, 127, 255, 63]` | 15 | exact |
| PF8 | `0xbe800000, 0x3fc00000, 0x3b808081, 0x3f000000` | `[127, 193, 126, 1]` | 15 | exact |
| PF16 | `0x3b7f0000, 0x3f800000, 0xbe800000, 0x3bff8000` | `[255, 127, 32768, 57344]` | 15 | exact |
| PF32 | `0xbe800000, 0x3fc00000, 0x3dcccccd, 0x40000000` | `['0x40000000', '0xbe800000', '0x3fc00000', '0x3dcccccd']` | 6 | exact |

## Facts

- PF8 multiplies by `255.0f`, truncates toward zero with `CVTTSS2SI`, and stores ARGB bytes.
- PF16 multiplies by `32768.0f`, truncates toward zero with `CVTTSS2SI`, and stores ARGB words.
- PF32 stores the four incoming float bit patterns directly in ARGB order.
- The PF8/PF16 out-of-range case proves that these helpers do not clamp by themselves.

## Limit

The static caller graph still does not bind the Mode 2 intermediate float buffer to this writer wrapper.
Mac production rounding therefore remains unchanged until a same-run host/writeback witness exists.
