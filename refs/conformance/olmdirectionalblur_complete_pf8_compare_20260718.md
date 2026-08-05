# OLMDirectionalBlur Complete PF8 Compare 20260718

- Status: `pass`.
- Bounded case: `16x16 PF8`, angle `0`, brightness `1`, front strength `8`; alpha fade, sharp tail, back, size variation, and noise are all zero; render scale `1/1`.
- AEX, source image, source crop, and actual-AEX PF8 output identities are SHA-256 pinned.
- Same-run natural actual-AEX frame: `True`; callbacks: `['0x180006980', '0x180006b30']`.
- Production Mac dispatcher exact seam: `1`.
- Byte count: `1024`; mismatch count: `0`.
- AE exact claim: `False`. This proves the fixture/core/production-dispatch boundary only.

Artifacts: `refs/conformance/olmdirectionalblur_actual_aex_pf8_frame_20260718.argb8`, `refs/conformance/olmdirectionalblur_mac_adapter_pf8_frame_20260718.argb8`, `refs/conformance/olmdirectionalblur_complete_pf8_compare_20260718.json`.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_complete_pf8_compare_20260718.py`
