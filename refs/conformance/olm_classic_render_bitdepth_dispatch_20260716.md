# OLM Classic Render Bit-Depth Dispatch

Date: 2026-07-16

## Finding

The systemic defect was use of `PF_WORLD_IS_DEEP` in classic `PF_Cmd_RENDER`.
That flag only distinguishes a deep world from a non-deep world, so the old
contract collapsed classic render into an 8/16-bpc choice and could not select
the 32-bpc float path. This affected all eight Mac plugins in scope:
`OLMBlur`, `OLMColorKey`, `OLMDirectionalBlur`, `OLMDistanceGradation`,
`OLMKiraKira`, `OLMRadialBlur`, `OLMSmoother2`, and `OLMToonDilate`.

## Fix

Each classic render entry point now queries `PF_WorldSuite2::PF_GetPixelFormat`
on the input world and dispatches explicitly:

| AE pixel format | Dispatch |
| --- | --- |
| `PF_PixelFormat_ARGB32` | 8 bpc / `PF_Pixel8` where typed |
| `PF_PixelFormat_ARGB64` | 16 bpc / `PF_Pixel16` where typed |
| `PF_PixelFormat_ARGB128` | 32 bpc / `PF_PixelFloat` where typed |
| other format | `PF_Err_BAD_CALLBACK_PARAM` |

SmartRender remains on its existing `extra->input->bitdepth` typed paths,
including the copy-only fallbacks that already existed in DirectionalBlur and
RadialBlur. The change is limited to the eight classic render entry points.

## Adobe SDK Evidence

The local Adobe SDK headers define the three formats in
`Headers/AE_EffectPixelFormat.h`: ARGB32 is 8 bits per channel, ARGB64 is 16
bits per channel, and ARGB128 is 32-bit floating point per channel.
`Headers/AE_EffectCBSuites.h` defines `PF_WorldSuite2::PF_GetPixelFormat` as
the query returning one of those formats. `Headers/AE_Effect.h` defines
`PF_WORLD_IS_DEEP` only as a deep-world flag, which is insufficient for this
dispatch boundary.

## Verification

Four discoverable source-contract tests passed:

- `tests/test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_olmdg_toondilate_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_kirakira_smoother2_classic_render_bitdepth_dispatch_20260716.py`

Pairwise Debug builds also succeeded, with signing disabled:

- `OLMBlur` + `OLMColorKey`
- `OLMDirectionalBlur` + `OLMRadialBlur`
- `OLMDistanceGradation` + `OLMToonDilate`
- `OLMKiraKira` + `OLMSmoother2`

This is local source/build evidence only. No After Effects launch, plugin
installation, host render, or host comparison was performed. **No AE exact
claim is made.**
