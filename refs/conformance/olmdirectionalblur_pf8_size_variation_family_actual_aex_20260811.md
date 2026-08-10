# OLMDirectionalBlur PF8 Size × Fade/Sharp — 2026-08-11

Actual Windows AEX and production are raw-byte exact for Size 25/50/100 × Front Fade 50/100 and Size 50 × Front Sharp 50/100 on the pinned 16×16 route, in addition to Size 0/25/50/100 alone. Component records/divisor are built before Fade prepass and Sharp coefficients enter the shared rowdriver. The writer uses float×255 integer truncation. Only listed crosses are admitted; the older 960×540 Size92×Sharp45 witness remains an explicit exception.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.py`
