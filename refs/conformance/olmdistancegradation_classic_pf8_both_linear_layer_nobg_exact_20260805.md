# OLMDistanceGradation classic PF8 Both/Linear/Layer/no-bg exact

This fixture covers Linear interpolation in a configuration distinct from the
Inside/Constant and Outside/Sphere/Power cases. Actual inside and outside
fields are generated independently and combined with the Windows Both=max
ownership rule.

- Parameters: Both, Layer, Linear, no background, invert on.
- Thresholds: inside 6, outside 5.
- Geometry: 17x11; 187 actual `FUN_181170870` calls.
- Input/output rowbytes: 75/79; all `0xA5` padding unchanged.
- Inside field SHA-256: `061454ff2adc6e3fafc7a1558143b2da7d9eb1cb2641eda95c70ac97908d18dc`.
- Outside field SHA-256: `b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112`.
- Combined field SHA-256: `a84f59f33fe82263d86280a3bf48ff6fac47b5e98376b95b9418aec0c47c3f3d`.
- Active output SHA-256: `b9947fdf92cdae2fe6bcc4c0c4f117f677c1778d723d9e4086fcdae66ae19bcd`.
- Production comparison: 869/869 bytes including padding, zero mismatches.

The discriminator found that PF8 Both/Layer/no-bg keeps straight source RGB
while alpha carries the Linear field; production had multiplied RGB by alpha
again. The fix is restricted to PF8 Both in the Layer/no-bg branch. Other
depths retain their existing contracts. Because production changed, a new
Universal bundle installation is required; AE must not be controlled by this
test. No PF32 Smart support is claimed.
