# OLMDirectionalBlur PF16 back-only exact boundary

- Status: `exact`
- Depth: PF16 / ARGB64
- Geometry: 16x16 with 16 bytes of host row padding
- Parameters: angle 45, brightness gain 1, front strength 0, back strength 1;
  fade, sharp tail, size variation, and noise all zero; render scale 1
- Actual-AEX callbacks: populate `0x1800068e0`, output `0x180006a90`
- Active output: 2,048 bytes / 1,024 words
- Actual-AEX and Mac production SHA-256:
  `2545772bed5562452123c265cc52abd8a7c3ff5c8bf9f920f72270447bec7ec7`

`tools/emulation/test_olmdirectionalblur_minimal_pf16_production_20260805.py`
captures the output from the retained AEX on every run and compares every word
with `olm_dblur_minimal_argb16`. The public production dispatcher is exercised
separately by
`tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py`;
it verifies the bounded predicate, active bytes, and untouched row padding.

No other back strength, simultaneous front/back, angle, gain, render scale,
fade/tail/size/noise combination, AE host render, or Windows AE export is
promoted by this witness. All other unsupported PF16 combinations remain
fail-closed.
