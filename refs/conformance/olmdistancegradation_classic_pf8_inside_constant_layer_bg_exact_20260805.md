# OLMDistanceGradation classic PF8 Inside/Constant/Layer/use-bg exact

This fixture covers Constant interpolation in an ownership and render-mode
configuration distinct from the existing Outside/Sphere and Outside/Power
cases.

- Parameters: Inside, Layer, Constant, use background, invert off.
- Background RGB: `(16,160,48)`; source Layer RGB varies by coordinate.
- Geometry: 17x11; 187 actual `FUN_181170870` calls.
- Input/output rowbytes: 75/79; all `0xA5` padding unchanged.
- Constant field SHA-256:
  `564293cbd022462e7f24a4ba689fa0fa8804c33610992f675ece73d9c13e8de9`.
- Active output SHA-256:
  `70a2b85f348aafba232477630c32be346251b1a1c589cd5877b3dc766327aead`.
- Production comparison: 869/869 bytes including padding, zero mismatches.

The boundary includes binary Constant field generation, Layer source color,
background-color selection, alpha ownership, PF8 store, and row padding. No
production change or reinstall was required. Remaining meaningful public
coverage includes Linear under Layer/Outside or Both ownership and Constant
with blur enabled. No PF32 Smart support is claimed.
