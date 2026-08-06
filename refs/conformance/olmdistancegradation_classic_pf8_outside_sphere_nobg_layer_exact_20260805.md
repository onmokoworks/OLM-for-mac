# OLMDistanceGradation classic PF8 Layer mode exact

The shipped UI exposes only `RGB|Layer`; Alpha and Luminance are not render
modes in this plug-in version. This test therefore covers the previously
unverified Layer mode using actual PF8 `FUN_181170870`, independently of the
Outside RGB fixture output.

- Parameters: Outside, Layer, Sphere, no background; invert off and on.
- Geometry: 17x11; 187 actual callbacks per invert state.
- Input/output rowbytes: 75/79; all `0xA5` padding unchanged.
- Internal field SHA-256:
  `f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229`.
- Layer invert-off active SHA-256:
  `13a74e7dc8897b6489f66b39e0e4505a4e46a943f3635b5b0c68bbe571b682cf`.
- Layer invert-on active SHA-256:
  `e75997a208f073394cb11b7ce5a1f44f19f9af312f378fdcce2963c814d0d090`.
- Production comparison: 869/869 bytes including padding, zero mismatches for
  each invert state.

The hashes differ from both RGB outputs and preserve source-layer color and
alpha behavior. No production change was required. No PF32 Smart path is
claimed.
