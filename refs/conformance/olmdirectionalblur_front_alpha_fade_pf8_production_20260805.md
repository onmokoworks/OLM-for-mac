# OLMDirectionalBlur Front Alpha Fade PF8 Production Differential

- Status: `pass`.
- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; Front Strength 8 and Front Alpha Fade 4; other algorithm controls zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `34be8aa0f98b7ee371de01499f3d17d8ff1c2fefdff8aeed91c4ed8569518978`.
- This proves the hash-bound fixture/core/production-dispatch boundary only; Mac AE and other fade values are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_front_alpha_fade_pf8_production_20260805.py`
