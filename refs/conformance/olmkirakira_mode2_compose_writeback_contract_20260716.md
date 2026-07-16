# OLMKiraKira Mode 2 compose/writeback witness contract

This request is a Windows/After Effects witness only. It uses the canonical
Software 32bpc case `kk_vertical_len50_brightness1_strength100` with Blur Mode
2 and requires one fresh run to bind the complete chain:

`FUN_18114ffd0` accumulation -> four clamps -> return float RGBA -> host
compose -> typed pre-writeback RGBA -> selected PF8/PF16/PF32 writer entry ->
post-store words.

Every event must carry the same `run_id`, `ae_pid`, `module_base`, pinned AEX
SHA-256, `project_bpc=32`, `renderer=Software`, and `case_id`. A return is
`answered` only when all required events occur exactly once and the selected
writer is corroborated by its post-store words in that same run. Missing,
duplicate, identity-drifted, or ambiguous writer evidence is
`exact_bind_failure`.

Required evidence includes the pinned threshold `0.001`, target and dispatch
RVAs, output pointer, clamped float RGBA, compose inputs/formula, typed
pre-writeback RGBA, selected writer family/entry and conversion scale, plus
destination address and after-store words. Mode3 Gaussian, PNG tuning, and
production/ledger changes are outside scope.
