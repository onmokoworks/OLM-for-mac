# OLMDirectionalBlur Front Sharp Tail PF8 Production Differential

- Status: `pass`.
- Scope: deterministic 16x16 straight ARGB with alpha 0/64/128/192/255; Front Strength 8 and Front Sharp Tail 25; other algorithm controls zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `e7ecfb76bbb79e73197b7e0c191e1c21d9a6400e8bcac22ef3f53eab5f008ca2`.
- This proves the hash-bound fixture/core/production-dispatch boundary only; Mac AE and other tail values are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_front_sharp_tail_pf8_production_20260805.py`
