# OLMDirectionalBlur PF32 Sharp/Back families — 2026-08-10

Actual Windows AEX and the production full PF32 worker are raw-byte exact on the pinned 16×16 route for Front Sharp Tail 0/50/100, Back Alpha Fade 0/50/100, Back Sharp Tail 0/50/100, and the natural Back Fade 50 × Back Sharp 50 cross. Admission is enumeration-bounded.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_sharp_back_families_actual_aex_20260810.py`
