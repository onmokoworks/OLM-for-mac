# OLMDirectionalBlur Noise Type 2 PF8 Production Differential

- Status: `pass`.
- Scope: deterministic nonopaque 16x16 ARGB; Front Strength 8, Noise Variation 25, Type 2, Seed 1, Offset 0, Thickness 10; other controls zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `e57d7510a5debaf977f78e2f0764063847bdffefe6dc02c8a1fc7c1c43bc28f9`.
- This proves this PRNG/block-noise-plane/production-dispatch boundary only; other seeds/types and Mac AE are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type2_pf8_production_20260805.py`
