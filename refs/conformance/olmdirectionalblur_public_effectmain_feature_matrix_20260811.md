# OLMDirectionalBlur public EffectMain feature matrix — 2026-08-11

Public `EffectMain` SmartPreRender→SmartRender is raw exact against actual AEX for PF8/PF16/PF32 on two nondefault routes: the proven 32×18 dual-side Type 2 tuple and a proven 16×16 same-size padded Type 3 Layer tuple (6 cases). All 21 non-input public parameters are checked out/in, input/noise/output world lifecycle and row padding are verified, and a missing Type 3 Layer returns `PF_Err_BAD_CALLBACK_PARAM` without touching output. The claim remains limited to the pinned case_0001 source crops; a synthetic PF32 source exposed a different owner result and was not generalized.

Reproduction: `python3 tools/emulation/test_olmdirectionalblur_public_effectmain_feature_matrix_20260811.py`
