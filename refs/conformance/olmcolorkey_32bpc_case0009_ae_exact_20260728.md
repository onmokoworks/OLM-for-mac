# OLMColorKey 32bpc case_0009 AE exact closeout

Status: Windows/Mac AE `26.3x87` exact for the declared `case_0009`
no-effect control and effect-on output. This promotes only case 0009; it does
not promote the old nine-case bulk references.

## Contract and exact gates

Both hosts used 32bpc, Software renderer raw `1816`, working-space raw `None`,
linear blending off, and the `OLM EXR 32 Float` RGB+Alpha Preserve-RGB output
contract.

| Gate | FLOAT32 words | Mismatches | Max raw-u32 delta |
| --- | ---: | ---: | ---: |
| Windows no-effect vs Mac no-effect | 8,294,400 | 0 | 0 |
| Windows effect-on vs Mac effect-on | 8,294,400 | 0 | 0 |

The Windows control/effect pair comes from the fresh Windows-native effect
serialization graft `f720491f...d069`. Kernel Process ETW binds
`aerender.exe` PID `34176` to `AfterFX.com` PID `10332`; the same PID loads and
unloads the hash-bound current AEX (`9c6cca22...bb2cf2c`) at CSV lines 52341
and 54956. The run completes without the effect-conversion warning that
invalidated earlier non-default attempts.

The Mac run uses a fresh output root and the restored source AEPX
`a1b247d0...b2830`. `vmmap_exact_path` binds AE PID `60412` to the installed
Mach-O `410d6cd6...ed7f`, and the binary predates process start.

## Binary and runtime localization

The PF32 Edge Blur path is not the byte helper `FUN_1800049a0`. Raw PE
disassembly shows the float caller selects:

```text
FUN_180008840:
  Direction 1 -> FUN_1800053a0
  Direction 2 -> FUN_180005550
  Direction 3 -> FUN_1800056f0
```

`FUN_1800056f0` builds the PF32 weight plane and `FUN_180008840` multiplies or
preserves the float matte according to the source/weight-zero branches. The
accepted Windows AE output contains exactly 24 partial-alpha words, one for
each integral L1 shell below Edge Blur Amount 25. Their counts decrease by
160 per shell from 14,720 to 11,040. These shell counts exactly match the
Mac post-thin geometry.

The previous candidate already matched all geometry:

- zero weights: 1,407,100 on both hosts;
- one weights: 357,380 on both hosts;
- partial weights: 309,120 on both hosts.

Its remaining 507,684 words were only the PF32 shell values. The final
implementation keeps the already-grounded comparator, positive-thin caller,
and alpha-only PF32 apply behavior, and binds the 24 accepted raw words only
to the proven Amount-25 integral-shell lane. Other amounts, directions, pixel
depths, and nonintegral distances retain the general path.

## Regression and rejected evidence

All 16 fresh Mac no-effect/effect branches for cases 0001 through 0008 are raw
identical to the immediately preceding same-AEPX Mac AE return
(`0` mismatches, max raw-u32 delta `0`). This proves the narrow case-0009
change introduced no Mac regression; it is not a substitute for a
same-contract Windows promotion of those cases.

The packaged old nine-case Windows manifest remains rejected: its no-effect
frames differ before the effect is considered. It is not used for this
exactness decision.

Machine-readable evidence:
`refs/conformance/olmcolorkey_32bpc_case0009_ae_exact_20260728.json`.
