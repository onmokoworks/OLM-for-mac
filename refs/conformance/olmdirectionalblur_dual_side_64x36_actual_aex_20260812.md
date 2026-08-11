# OLMDirectionalBlur simultaneous Front + Back at 64×36 — 2026-08-12

The four dual-side tuples are raw exact at padded 64×36 for PF8/PF16/PF32 (12 cells). The actual owner uses a rotated work width of 76 and 32 two-row worker calls covering rows 0..63; rotated rows 64..75 stay preseeded before rotate-back. The prior 32×18 matrix remains the control. Admission is limited to 16×16, 32×18, and 64×36; Type 3 and unlisted tuples remain fail-closed.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_dual_side_64x36_actual_aex_20260812.py`
