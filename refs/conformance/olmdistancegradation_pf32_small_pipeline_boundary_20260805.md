# OLMDistanceGradation PF32 small-pipeline boundary

- Status: `capture_required`; PF32 exact is not claimed.

PF32 cannot reuse the PF8/PF16 compose fixtures. Static dispatch sends classic PF32 directly to `FUN_181172a10`, a whole-render owner. It calls shared fieldgen `FUN_181174760`, performs OpenCV-world operations, and copies 16-byte pixels back. Unlike PF8/PF16, no independent typed per-pixel compose callback exists in the retained disassembly/evidence.

The repository currently has zero typed PF32 field/compose fixtures. The 32bpc EXR references are host renders and cannot supply the missing internal field/compose boundary.

The minimal next Unicorn capture is therefore explicitly bounded to `FUN_181172a10`, `17x11`, PF32, no blur, same-shape. It must retain source float words, the field immediately after `FUN_181174760`, final float words, host callback topology, and the OpenCV detour sequence. It must not reuse PF8/PF16 staging or their callbacks.

`tools/emulation/audit_olmdistancegradation_pf32_small_pipeline_boundary_20260805.py` fails closed if dispatch/owner facts or the production no-staging boundary change.

No production or AEXCompat change is justified until this owner-level oracle exists.
