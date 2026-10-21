# OLMDistanceGradation PF32 SmartRender boundary

Status: **PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_STATIC_AND_BOUNDED_PRODUCTION**.

This document supersedes its earlier `not_an_aex_path` conclusion. That audit
mistook exported command `0x0b` for SmartRender. The actual public
`PF_Cmd_SMART_RENDER` selector is command `0x18`, which calls
`FUN_181173d20`. Its bitdepth-`0x20` branch checks out the input and output
worlds, calls PF32 whole owner `FUN_181172a10`, acquires `PF iterateFloat
Suite` v1, and composes through `FUN_181170c90`.

The Mac public adapter therefore keeps PF32 Smart support. It validates the
declared depth against both world formats, requires equal non-null dimensions
and sufficient rowbytes, balances successful parameter and layer checkouts,
and admits PF32 only through the fixed 17×11 exported-owner matrix predicate.
Twenty-four non-Power fixed17x11 PF32 cells are admitted and raw exact. This includes
six non-Power Mode 5 cells after reproducing the IPP direct-`expf`, L/T/R/B, late
spatial-multiply and noncontracting-product order. Eight PF32 Power cells fail closed
because no native Windows UCRT `powf` result is retained. All unlisted PF32 Smart
tuples still fail closed with `PF_Err_BAD_CALLBACK_PARAM`; Classic PF32 remains
a separate owner. Project/global arbitrary fast-math codegen is not promoted.

`tools/emulation/audit_olmdistancegradation_pf32_smartrender_boundary_20260805.py`
pins the corrected AEX dispatch and production boundary. The previous weak
substring checks are removed.

The Mode 5 arithmetic, public padding/lifecycle closure and both-slice
Universal codegen proof are bound by
`olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.{json,md}` and
`olmdistancegradation_pf32_mode5_universal_codegen_20260812.{json,md}`.
