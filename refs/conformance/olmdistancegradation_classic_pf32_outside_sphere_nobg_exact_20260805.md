# OLMDistanceGradation classic PF32 Outside/Sphere/no-bg exact

The actual classic PF32 whole-render owner `FUN_181172a10` is executed for
Outside/RGB/Sphere/no-background with invert off and on. This path does not use
PF8/PF16 staging or their quantization rules.

- Geometry: 17x11 float pixels.
- Input/output rowbytes: 280/288 (active row 272 bytes).
- Input remains byte-identical and all output `0xA5` padding is unchanged.
- Internal float field SHA-256:
  `f6b4ff5a65f7b09d502c82d3e043eac3ac133069e831d27e1f686e1ac1f95229`.
- Active output SHA-256, both invert states:
  `a145dd5cbdd93a765465d0a2c2ed8a749a152a1f35b571e431641a5d9628f76a`.
- Padded output SHA-256, both invert states:
  `c5ec4239fd858adb3a9f307f547c01168e63bfa816bc8374a9a9ee8e5dddc67b`.
- Production comparison: 3,168/3,168 bytes, zero mismatches for each state.

At discriminator pixels the owner copies the raw float field to alpha and all
three RGB channels. It bypasses integer-style Sphere/invert/color composition,
which is why both invert states are byte-identical. Production implements this
only for classic PF32 Outside/RGB/no-bg. No PF32 Smart support is claimed.
