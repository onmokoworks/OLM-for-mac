# OLMDirectionalBlur Noise Type 3 Layer PF8 Production Differential

- Status: `pass`.
- Scope: deterministic nonopaque 16x16 ARGB used as both source and controlled equal-origin Layer; Front Strength 8, Noise Variation 25, Type 3.
- Actual-AEX natural Layer field path and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `8668620ad73809172d03a6def3a46a19a5c40ef5529722b97c696bb51b92ef5d`.
- This proves this equal-size/equal-origin Layer field boundary only; arbitrary Layer geometry and Mac AE are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_pf8_production_20260805.py`
