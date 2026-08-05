# OLMDirectionalBlur Type 3 Layer Origin PF8 Differential

- Status: `pass`.
- Source extent `[0,0,16,16]`; Layer extent `[2,1,18,17]`; rowbytes 76 and 92 respectively.
- Actual AEX treats the equal-dimension checked-out Layer buffer as render-local; the differing extent origin does not translate its field samples.
- Actual-AEX and production: `True`; 0 differing bytes out of 1024; SHA-256 `8668620ad73809172d03a6def3a46a19a5c40ef5529722b97c696bb51b92ef5d`.
- Before the binding fix, translating by the Layer extent caused 363 differing bytes; the first was R at pixel (3,0), actual 148 versus 145.
- Different Layer size and Mac AE remain unclaimed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805.py`
