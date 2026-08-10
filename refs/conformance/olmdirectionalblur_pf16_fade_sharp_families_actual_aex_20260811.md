# OLMDirectionalBlur PF16 Fade/Sharp families — 2026-08-11

Actual Windows AEX and the production ARGB64 worker are raw-byte exact for Front/Back Fade and Sharp Tail 0/50/100 plus Back Fade 50 × Back Sharp 50 on the pinned 16×16 route. The worker preserves PF16 normalization, float accumulation/max, and truncating 32768 quantization. Admission is enumeration-bounded.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf16_fade_sharp_families_actual_aex_20260811.py`
