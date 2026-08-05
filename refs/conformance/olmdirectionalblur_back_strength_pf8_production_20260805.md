# OLMDirectionalBlur Back Strength PF8 Production Differential

- Status: `pass`.
- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; angle 0, brightness 1, front strength 0, back strength 8; all fade/tail/size/noise controls zero; scale 1/1.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `8151ac88bf148e6748f749012353e58d4654ba3df38020a5ee993f672844c088`.
- This proves the fixture/core/production-dispatch boundary only; Mac AE and other Back settings are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_back_strength_pf8_production_20260805.py`
