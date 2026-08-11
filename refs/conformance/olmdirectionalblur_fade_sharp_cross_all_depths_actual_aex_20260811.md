# OLMDirectionalBlur Fade × Sharp Tail boundary matrix — 2026-08-11

Actual Windows AEX and production are exact for Front-only and Back-only Fade 50/100 × Sharp Tail 50/100 at PF8/PF16/PF32 on the pinned 16×16 route. PF8/PF16 are raw-byte exact; PF32 is raw-float-word exact. Admission is restricted to these 24 cells.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_fade_sharp_cross_all_depths_actual_aex_20260811.py`
