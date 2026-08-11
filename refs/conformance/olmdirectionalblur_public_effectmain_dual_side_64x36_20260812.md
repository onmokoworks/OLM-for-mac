# OLMDirectionalBlur public EffectMain dual-side 64×36 — 2026-08-12

All four proven dual-side tuples pass public `EffectMain` SmartPreRender→SmartRender at PF8/PF16/PF32 (12/12 raw exact) on padded 64×36. The proof covers all 21 non-input parameter checkouts/checkins, input/output lifecycle, optional Noise Layer absence for Type 1/2, active bytes, and padding. The 32×18 matrix remains the control; other geometry and Type 3 are not generalized.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_public_effectmain_dual_side_64x36_20260812.py`
