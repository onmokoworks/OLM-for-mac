# OLMDirectionalBlur PF32 Size × Fade/Sharp geometry matrix — 2026-08-11

Actual AEX and production are raw-float exact at 16×16 and 32×18 for front-only and back-only Size 25/50/100 × Fade 50/100, plus Size 50 × Sharp 50/100. Size component mapping precedes the selected front/back prepass or Sharp coefficient. For 32×18, the 40×40 work world is divided among 32 workers: rows 0..31 are overwritten and rows 32..39 retain the rotated-source destination contents before rotate-back. The new admission is limited to these 32 cells.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_size_coeff_geometry_matrix_actual_aex_20260811.py`
