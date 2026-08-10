# OLMDirectionalBlur Size × Back coefficients — 2026-08-11

PF8 and PF16 actual Windows AEX outputs are raw-byte exact with production for Size 25/50/100 × Back Fade 50/100 and Size 50 × Back Sharp 50/100 on the fixed front0/back8 16×16 route. Component map/divisor is shared; Back prepass/Sharp coefficients enter afterward. PF8 truncates float×255 and PF16 truncates float×32768. Only these eight tuples per depth are admitted.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_size_back_crosses_all_depths_actual_aex_20260811.py`
