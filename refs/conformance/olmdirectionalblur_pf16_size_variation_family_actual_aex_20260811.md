# OLMDirectionalBlur PF16 Size × Fade/Sharp — 2026-08-11

Actual Windows AEX and production are raw-byte exact for Size 25/50/100 × Front Fade 50/100 and Size 50 × Front Sharp 50/100, plus Size 0/25/50/100 alone. Component map/divisor precedes Fade prepass and Sharp coefficient application in the rowdriver. ARGB64 output uses ×32768 integer truncation. Only listed crosses are admitted.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf16_size_variation_family_actual_aex_20260811.py`
