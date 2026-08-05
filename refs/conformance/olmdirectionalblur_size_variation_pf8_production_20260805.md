# OLMDirectionalBlur Size Variation PF8 Production Differential

- Status: `pass`.
- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; Front Strength 8 and Size Variation 25; other algorithm controls zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `b4ad7954b48dfdef93ea9c970e2a39f511ecdf853af6dc9ba20949afaac3239d`.
- This proves the hash-bound fixture/core/production-dispatch boundary only; Mac AE and other variation values are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_size_variation_pf8_production_20260805.py`
