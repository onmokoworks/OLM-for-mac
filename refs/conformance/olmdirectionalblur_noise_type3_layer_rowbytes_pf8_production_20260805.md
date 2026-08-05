# OLMDirectionalBlur Type 3 Layer Rowbytes PF8 Differential

- Status: `pass`.
- Source world rowbytes: 76; controlled Layer world rowbytes: 92; packed rowbytes: 64. Dimensions and origins remain equal.
- Actual-AEX natural checkout and production: `True`; 0 differing bytes out of 1024.
- PF8 SHA-256: `8668620ad73809172d03a6def3a46a19a5c40ef5529722b97c696bb51b92ef5d`.
- This proves independent Layer stride only. Different Layer size/origin and Mac AE remain unclaimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_rowbytes_pf8_production_20260805.py`
