# OLMDistanceGradation PF16 boundary matrix

Date: 2026-07-17

## Result

`tools/emulation/test_dg_pf16_boundary_matrix_20260717.py` passed all six
fixtures against the hash-pinned `DistanceGradation.aex` and the current
production Mac source.

| Fixture family | Cases | Field raw words | Compose raw bytes | Padding |
| --- | ---: | ---: | ---: | ---: |
| PF16 raw threshold `n-1/n/n+1` (`32767/32768/32769`) | 3 | exact | exact | `0xA5` preserved |
| Transparent/opaque boundary (`0/1/32768`) | 1 | exact | exact | `0xA5` preserved |
| PF16 half-step and endpoint values | 2 | exact | exact | `0xA5` preserved |

The world is 8x5 PF16 with rowbytes 76: 64 active bytes and 12 canary bytes
per row. The AEX SHA-256 is
`a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

## Scope

This is bounded Mac-local actual-AEX versus production-source evidence for
field/staging and compose raw-word behavior. The source side calls the existing
production `RenderBits<PF_Pixel16>` bridge. It does not claim Windows execution,
After Effects host behavior, or AE exactness.

## Verification

```sh
python3 tools/emulation/test_dg_pf16_boundary_matrix_20260717.py
```
