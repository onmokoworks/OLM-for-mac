# OLMDirectionalBlur PF16 front+back exact boundary

- Status: `exact`
- Depth: PF16 / ARGB64
- Geometry: 16x16 with 16 bytes of host row padding
- Parameters: angle 45, brightness gain 1, back strength 1, front strength
  independently 1, 2, and 8; fade, sharp tail, size variation, and noise all
  zero; render scale 1
- Actual-AEX callbacks: populate `0x1800068e0`, output `0x180006a90`

| Front | Active output SHA-256 |
|---:|---|
| 1 | `2545772bed5562452123c265cc52abd8a7c3ff5c8bf9f920f72270447bec7ec7` |
| 2 | `07e05693b1fe8fc2516aa67f79b5700ff9a9c99a417e8e90228cd6d9bec5fa11` |
| 8 | `3b71a8e7c929b102d74142d778218db8ade316bdc2da60e9e204db5c9be7393c` |

`tools/emulation/test_olmdirectionalblur_minimal_pf16_production_20260805.py`
captures all three outputs from the retained AEX on every run and compares all
1,024 words with production. The source-included production dispatcher test
also executes front strengths 0, 1, 2, and 8 with back strength 1 and verifies
active output plus untouched row padding.

No other back strength, angle, gain, render scale, fade/tail/size/noise
combination, AE host render, or Windows AE export is claimed. Unsupported PF16
fade and noise combinations remain fail-closed.
