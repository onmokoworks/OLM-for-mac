# OLMDirectionalBlur PF8 Size Variation — 2026-08-11

Actual Windows AEX and the production PF8 full worker are raw-byte exact for Size 0/25/50/100 and Size 50 × Front Fade 50 on the pinned 16×16 route. Nonzero Size uses the connected-component area/divisor and continuous `pow(alpha, Size/100)` path. The writer converts float channels with multiplication by 255 followed by integer truncation. Values outside the public 0..100 range fail closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.py`
