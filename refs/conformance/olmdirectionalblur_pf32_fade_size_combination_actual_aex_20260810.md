# OLMDirectionalBlur PF32 Fade × Size combination — 2026-08-10

On the pinned 16×16 PF32 route, actual Windows AEX and the production worker are raw-byte exact for Front Alpha Fade 50/100 crossed with Size Variation 25/100. Production admits the simultaneous-nonzero combination only for this geometry and otherwise continues to fail closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_fade_size_combination_actual_aex_20260810.py`
