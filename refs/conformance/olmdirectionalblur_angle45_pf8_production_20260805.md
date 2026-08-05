# OLMDirectionalBlur Angle 45 PF8 Production Differential

- Status: `pass`.
- Scope: 16x16 PF8, angle 45, brightness 1, front strength 8; all other algorithm controls zero; scale 1/1.
- Actual-AEX and production Mac output: `True`; 0 differing bytes out of 1024.
- Actual-AEX PF8 SHA-256: `ef5542e38f00b83d1f9135a9ace3511bbcd157f259436a6b261388ab1563b880`.
- This proves the hash-bound fixture/core/production-dispatch boundary, not Mac AE rendering or other parameter values.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_angle45_pf8_production_20260805.py`
