# OLMDistanceGradation classic PF16 Outside/Sphere/no-bg invert exact

This is an independent invert-on discriminator for the classic PF16
Outside/RGB/Sphere/no-background branch. It uses the same actual AEX outside
field so the composition effect of inversion is isolated.

- Geometry: 17x11; 187 actual `FUN_181170480` calls.
- Input/output rowbytes: 146/150; all `0xA5` padding unchanged.
- Field SHA-256:
  `f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229`.
- Invert-on active output SHA-256:
  `ef941acc83ffe9432b37d5307d0143a8a374711853a0d422c72e1235de7963df`.
- Invert-off output SHA-256 for the same source/field:
  `71b62987c22b93b09db49b238a767eac6797686f1cab365baed15aac0997f391`.
- Production comparison: all 1,650 output bytes, including padding, zero
  mismatches.

The differing output hashes prove that this is not a duplicate execution of
the invert-off case. No PF32 Smart path is claimed.
