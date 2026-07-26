# OLMSmoother2 Native vs Actual-AEX Checkpoint (2026-07-26)

## Status

The optimized Mac 8bpc implementation is byte-exact against the unchanged
Windows `OLMSmoother2.aex` and Windows AE Software for all 12 current-AEX
legacy/key/gamma cases.

- native CLI vs AEXCompat raw AEX plane: `12/12`, `max_diff=0`
- AEXCompat normalized AEX plane vs Windows AE Software PNG: `12/12`,
  `max_diff=0`
- Mac AE 26.3x87 vs Windows AE Software PNG: `12/12`, `max_diff=0`

This promotes the covered 8bpc lane to `AE exact`.

## Binary-Grounded Fix

The remaining low-code residual came from an incorrect sRGB linear-branch
constant. The AEX `.rdata` bytes at `0x1800226c0` are:

```text
80 b5 49 21 72 d0 b3 3f
```

Decoded as little-endian binary64, this is `0.07739938080495357`, exactly
`1 / 12.92`. The native port used `1 / 12.9216`.

The focused case 0011 witness at crop coordinate `(32,32)` showed:

| Stage | Actual AEX bits | Native before fix | Native after fix |
| --- | ---: | ---: | ---: |
| c0d0 input blue | `966730420` | `966729129` | `966730420` |
| c0d0 output blue | `1019468804` | `1019468071` | `1019468803` |
| ab00 output blue | `1055903576` | `1055903551` | `1055903576` |
| b120/cce0 output blue | `1044744467` | `1044744422` | `1044744467` |
| PF8 blue byte | `122` | `121` | `122` |

The one-ULP c0d0 intermediate difference cancels before the exact ab00 and
final results; no compensation was added.

The PF8 source load also follows the AEX instruction sequence
`CVTDQ2PS` then `MULSS DAT_180022690`, using float reciprocal
multiplication rather than division.

## Mac AE Optimization Boundary

The first Mac AE run used the Xcode project's only configuration at `-O0`.
It produced three exact cases and nine cases with `max_diff=1`, totalling 104
different pixels. A no-effect control was exact, so the residual was inside
the plug-in rather than PNG import/export.

AEXCompat occurrence watches then captured case 0001 source coordinate
`(21,129)` using an equivalent 9x9 crop:

| Stage | Windows AEX float32 bits | Mac `-O0` observation |
| --- | --- | --- |
| c0d0 input RGB | `0x3f337b6b` | one ULP higher |
| c0d0 output RGB | `0x3f19708a` | one ULP higher |
| ab00 output alpha | `0x3f3b3b3a` | `0x3f3b3b3b` |
| cce0 output alpha | `0x3f3b3b3a` | `0x3f3b3b3b` |

The optimized native CLI already produced AEX alpha `0x3f3b3b3a`. Rebuilding
the same AE plug-in source with `GCC_OPTIMIZATION_LEVEL=2` removed all 104
residual pixels. The Xcode project's sole configuration is therefore pinned
to optimization level 2; `-O0` is not a conformance build.

## Trace Infrastructure

AEXCompat Issue `#542` / PR `#545` added one-based
`--watch ...,occurrence=N`. The real AEX run selected only cce0 occurrence
2113, consumed one memory witness, and reported
`dropped_memory_witnesses=0`. The target output was ARGB
`[255,0,0,122]`.

The gamma-only inner stages were then captured independently. The target was
the 106th of 143 calls to c0d0, ab00, and b120.

## Harness Fix

The CLI color-array parser now accepts CR/LF whitespace inside pretty-printed
JSON arrays. Previously only compact one-line arrays loaded the five Gamma
Color values.

## Verification

```sh
refs/scripts/build_olmsmoother2_cli.sh
```

The 12 cases were rendered from the SHA-pinned straight source and compared
to:

```text
/tmp/olmsmoother2_aexcompat_oracle_20260726_c/*.raw.png
```

Result:

```text
legacy_case_0001_current_aex                  max=0 differing_px=0
legacy_case_0002_current_aex                  max=0 differing_px=0
legacy_case_0003_current_aex                  max=0 differing_px=0
legacy_case_0004_current_aex                  max=0 differing_px=0
legacy_case_0005_current_aex                  max=0 differing_px=0
legacy_case_0006_current_aex                  max=0 differing_px=0
legacy_case_0007_current_aex                  max=0 differing_px=0
legacy_case_0008_current_aex                  max=0 differing_px=0
legacy_case_0009_v1mode_current_aex           max=0 differing_px=0
legacy_case_0010_gamma3_current_aex           max=0 differing_px=0
legacy_case_0011_gamma5_blue_current_aex      max=0 differing_px=0
legacy_case_0012_gamma5_red_blue_current_aex  max=0 differing_px=0
```

The AEXCompat oracle's own
`AEXCOMPAT_REFERENCE_RESULT.json` records `comparison.exact=true`,
`max_diff=0` for all 12 normalized Windows AE comparisons.

The Mac AE validation used request
`ae_pixel_olmsmoother2_current_aex_20260726_r3`, explicit 8bpc, disabled
project color management, straight-alpha source input SHA-256
`9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265`,
and installed binary SHA-256
`d7abbd9dc16cc168f2c8ee8178d262f6fd8fceb618febf906e301e405b957d18`.

```text
legacy_case_0001_current_aex                  max=0
legacy_case_0002_current_aex                  max=0
legacy_case_0003_current_aex                  max=0
legacy_case_0004_current_aex                  max=0
legacy_case_0005_current_aex                  max=0
legacy_case_0006_current_aex                  max=0
legacy_case_0007_current_aex                  max=0
legacy_case_0008_current_aex                  max=0
legacy_case_0009_v1mode_current_aex           max=0
legacy_case_0010_gamma3_current_aex           max=0
legacy_case_0011_gamma5_blue_current_aex      max=0
legacy_case_0012_gamma5_red_blue_current_aex  max=0
```

## Next Action

Freeze the covered 8bpc implementation and expand the same contract to
16bpc, then 32bpc FLOAT EXR. Do not use `-O0` builds for conformance.
