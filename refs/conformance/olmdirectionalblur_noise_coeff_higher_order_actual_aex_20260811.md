# OLMDirectionalBlur Fade/Sharp × Noise × Size — 2026-08-11

Actual Windows AEX and production are exact for four bounded higher-order tuples on each of Front and Back at PF8/PF16/PF32 (24 cells total). The matrix covers Fade 50/100, Sharp 50/100, Noise Variation 25/100, Noise Type 1/2, and Size 0/50 on the pinned 16×16 route. PF8/PF16 are raw-byte exact and PF32 is raw-float-word exact. Unlisted Size-nonzero higher-order tuples, geometry, Type 3, and simultaneous Front+Back remain fail-closed; pre-existing independently proven families are unchanged.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_noise_coeff_higher_order_actual_aex_20260811.py`
