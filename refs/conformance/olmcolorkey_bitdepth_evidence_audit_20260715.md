# OLMColorKey Bit-Depth Evidence Audit - 2026-07-15

## FACT

- 8bpc normalized Software: 9/9 exact.
- Covered 16bpc AE slice: 9/9 exact.
- Windows 32bpc return: 9 effect/control pairs, uncompressed FLOAT EXR, SOFTWARE; this is reference evidence only.
- Color-space and Replace behavior is implementation-backed and exact in the existing CLI evidence; Edge Thin/Blur is exact for the declared 8bpc and 16bpc slices.

## INFERENCE

- No algorithm blocker is demonstrated by current normalized 8bpc or covered 16bpc evidence.
- The single narrowest remaining gate is the Mac paired FLOAT EXR and raw-float comparison; 32bpc remains forbidden from `AE exact` until that gate passes.
- The 2026-07-12 32bpc Mac pair is host/input provenance evidence, not a reason to tune ColorKey math.

## Scope Decision

No ColorKey source change is justified. Re-open Edge Thin/Blur or color-space/Replace implementation only after the Mac/Windows paired float comparison supplies a raw-float residual that survives control-world validation.
