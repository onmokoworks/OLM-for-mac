# OLMDirectionalBlur simultaneous Front + Back higher-order matrix — 2026-08-11

Actual Windows AEX and production are exact for four simultaneous Front+Back tuples at PF8/PF16/PF32 (12 cells). The fixed 16×16 route covers both-side Fade/Sharp 50/100 with Size 0/50, Noise Variation 25/100, and Noise Type 1/2. PF8/PF16 are raw-byte exact; PF32 is raw-float-word exact. Unlisted tuples, other geometry, and Type 3 remain fail-closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_higher_order_actual_aex_20260811.py`
