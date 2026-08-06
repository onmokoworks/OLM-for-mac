# OLMDistanceGradation classic PF16 Both/Power/Layer/no-bg exact

This closes the largest remaining supported AE-free matrix gap: PF16 Both
ownership. Actual inside and outside fields are generated independently with
thresholds 6 and 5, combined by max, staged through nearest-even PF16 words,
and consumed by 187 actual `FUN_181170480` calls.

- Parameters: Both, Layer, Power 2.5, no background, invert on.
- Geometry: 17x11; input/output rowbytes 146/150.
- All `0xA5` padding remains unchanged.
- Inside field SHA-256: `061454ff2adc6e3fafc7a1558143b2da7d9eb1cb2641eda95c70ac97908d18dc`.
- Outside field SHA-256: `b9df566485a5f2369cc8f6118c5a48290eff16f5097084a159d9d3fde7df3112`.
- Combined field SHA-256: `a84f59f33fe82263d86280a3bf48ff6fac47b5e98376b95b9418aec0c47c3f3d`.
- Active output SHA-256: `a8602dcead6cc882af398356a63a5d2806b426bb42bcc1e7c113f3e9e3a6295e`.
- Production comparison: 1,650/1,650 bytes including padding, zero mismatches.

The actual probe uses real libm `powf`; PF8 staging is not reused. No
production change or reinstall was required. Remaining matrix gaps are PF32
Power and Constant with blur. PF32 Smart remains unsupported by the actual AEX.
