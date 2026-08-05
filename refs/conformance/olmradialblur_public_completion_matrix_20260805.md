# OLMRadialBlur public completion matrix (2026-08-05)

Status: `partial_with_new_structural_exact_boundary`

The public command surface (`ABOUT`, `GLOBAL_SETUP`, `PARAMS_SETUP`, classic
`RENDER`, `SMART_PRE_RENDER`, and `SMART_RENDER`) is implemented. Actual-AEX
render equivalence remains bounded to the fixture rows recorded in the JSON
matrix; setup/UI command equivalence has not been independently proved.

The strongest completed render areas are PF8 full-frame Rotation case0010,
reduced padded PF16/PF32 Rotation cases, PF32 Zoom case0009 internal evidence,
and reduced padded PF16 Zoom Strength 4/5. The largest structural hole selected
this round was PF16 Zoom outer offset mode 3/UI 2. It previously entered the
generic nonzero-offset worker and mismatched after an exact pre-blur plane.

The new bounded production route now matches the actual AEX pre-blur plane,
post-blur plane, final PF16 bytes, and row padding exactly. The proof does not
extend to broader mode-2 values/geometries, other mode-3 values/geometries, nonzero inner blur,
edge fade, ellipse/angle/quality variants, repeat-border off, or noise/size
variation.

The next matrix-gap pass additionally proves the bounded PF16 Zoom mode 2/UI 2
path. Broader mode-2 values and geometries remain outside the claim.

The following typed-gap pass proves PF8 Zoom Strength 4/mode 1 on an independent
ARGB8 padded source. Its pre-blur plane, post-blur plane, output bytes, and row
padding match the actual AEX exactly after aligning the PF8 reader with the
AEX's rounded reciprocal `MULSS` sequence.

The next connection audit proves an independent reduced PF32 Zoom path from
owner `0x180007d30` through the pre/post float planes and direct float writer to
the current installed Universal bundle. This closes the previously split PF32
internal-plane versus installed-runner evidence chain without operating AE.

The public `PF_Cmd_SMART_RENDER` edge is now connected compositionally: the
adapter's callback/parameter/bit-depth route is fail-closed source-audited, and
its exact `RenderWorld(bitdepth=32)` destination is executed against the PF32
actual-AEX fixture through the direct-float writer. This is not a dynamic AE
callback-ABI claim.

Evidence: `olmradialblur_zoom_pf16_offset_mode3_ui2_small_actual_aex_20260805.json`.
