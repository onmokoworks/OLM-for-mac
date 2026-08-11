# OLMDirectionalBlur simultaneous Front + Back at 32×18 — 2026-08-11

The four dual-side higher-order tuples proven at 16×16 are raw exact at padded 32×18 for PF8/PF16/PF32 (12 cells). The rotated 40×40 work world follows the actual owner partition: 32 worker rows overwrite rows 0..31 while rows 32..39 retain the preseeded rotated destination before rotate-back. Admission remains tuple- and geometry-exact; Type 3 and other combinations remain fail-closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_32x18_actual_aex_20260811.py`
