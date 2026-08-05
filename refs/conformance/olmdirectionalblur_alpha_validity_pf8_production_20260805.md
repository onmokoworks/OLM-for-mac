# OLMDirectionalBlur Alpha/Validity PF8 Production Differential

- Status: `pass`.
- Input: deterministic 16x16 straight ARGB with alpha 0, 64, 128, 192, and 255, including nonzero RGB at alpha zero.
- Actual-AEX and production Mac: `True`; 0 differing bytes out of 1024.
- Input SHA-256: `ff3ec821b6f91993890ac82ca6a9da8f931c3b4e2b459bee4d6cebf4e7f24f70`.
- Actual-AEX PF8 SHA-256: `a92780c3b814a8bf496257f824fe534b7b64703362aee3c15d64033abda9febc`.
- This proves the fixture/core/production-dispatch boundary only; Mac AE and other alpha/parameter families are not claimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_alpha_validity_pf8_production_20260805.py`
