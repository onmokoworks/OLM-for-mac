# OLMDistanceGradation classic PF16 Outside/Sphere/no-bg exact

This adds a classic parameter branch independent of the existing
Inside/Linear/use-bg fixture. The actual AEX runs its field helper on the
outside mask with threshold 4, then runs `FUN_181170480` for all 187 pixels
using Outside, RGB, Sphere interpolation, no background, and no inversion.

- Geometry: 17x11.
- Input/output rowbytes: 146/150 (active row 136 bytes).
- Padding sentinel: `0xA5`, unchanged in all rows.
- Actual float field SHA-256:
  `f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229`.
- Actual active PF16 output SHA-256:
  `71b62987c22b93b09db49b238a767eac6797686f1cab365baed15aac0997f391`.
- Production comparison: all 1,650 output bytes, including padding, zero
  mismatches.

The discriminator exposed one bounded production difference: Windows clears
hidden RGB when PF16 Outside/RGB/no-bg has no source ownership, whereas the Mac
path retained the gradation color below zero alpha. The fix is restricted to
that typed parameter branch. PF8/PF16 Smart, the original classic PF8/PF16
fixture, and classic PF32 remain separate contracts.
