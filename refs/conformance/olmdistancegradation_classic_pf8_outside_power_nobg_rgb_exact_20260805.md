# OLMDistanceGradation classic PF8 Power interpolation exact

This covers the public Power interpolation branch independently of the prior
Sphere fixtures. A larger 9x7 transparent region produces non-binary field
values, so Power 2.5 is a real discriminator rather than a 0/1 no-op.

- Parameters: Outside, RGB, Power 2.5, no background; invert off and on.
- Geometry: 17x11; 187 actual `FUN_181170870` calls per state.
- Input/output rowbytes: 75/79; all `0xA5` padding unchanged.
- Actual field SHA-256:
  `b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112`.
- Invert-off active output SHA-256:
  `7e0dbb8fa472c312739a05818eb676142377219d969ae6028ad1ea664d4577ea`.
- Invert-on active output SHA-256:
  `8eb17bd878f953edb4139df5144bcd64a58e3bf9d80df87c67fe13236fdeea38`.
- Production comparison: 869/869 bytes including padding, zero mismatches for
  each state.

The actual probe explicitly installs the libm implementation used by `powf`;
an unresolved import stub is not accepted as an oracle. No production change
was needed. Remaining public interpolation coverage includes Constant and
Linear in additional ownership/render-mode combinations. No PF32 Smart support
is claimed.
