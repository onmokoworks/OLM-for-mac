# OLMDirectionalBlur Noise Type 1 PF8 Production Differential

- Status: `pass`.
- Scope: deterministic nonopaque 16x16 ARGB; Front Strength 8, Noise Variation 25, Type 1, Seed 1, Offset 0, Thickness 10; other controls zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `5c69970a5b28d1c2ac89919d5ea7617d360113109df18a942aa61bab41348ec4`.
- This proves this PRNG/noise-plane/production-dispatch boundary only; other seeds/types and Mac AE are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type1_pf8_production_20260805.py`
