# OLMDistanceGradation 16bpc Layer/no-bg source fix: case_0012 probe

- Date: 2026-06-29
- Case: `olmdistancegradation_extended__case_0012`
- Request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Windows runtime witness:
  `olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629`

## Context

Windows runtime/reference evidence now says the Layer/no-background 16bpc path
is consistent with:

- `straight_source_rgb * output_alpha`

and inconsistent with:

- `premultiplied_source_rgb * output_alpha`

The Mac port previously kept source RGB directly on the `render_mode=Layer`,
`use_bg=0` path, which matched the rejected premultiplied-looking witness.

## Narrow implementation change

The Mac compose path was changed only for:

- `render_mode == RENDER_MODE_LAYER`
- `use_bg == 0`
- `src_a > 0`

New rule:

1. unpremultiply source RGB by source alpha
2. clamp straight RGB to `[0,1]`
3. multiply straight RGB by final `out_a = d_alpha * X`

No background-mode path was changed.

## Local AE single-case evidence

The rebuilt plug-in was installed into MediaCore from:

- `/tmp/olm_mac_plugins_Debug_clean_20260629.zip`

Probe output:

- `refs/reports/ae_single_case_olmdistancegradation_case0012_layer_no_bg_source_fix_installed_20260629/`

Comparison against the Windows 16bpc Software reference PNG:

- global `max=65`
- global `mean=1.3002979118441358`
- `nonzero_px=279551`

Runtime-witness coordinates:

- `(462,7)`:
  - Windows ref `[126,126,126,253]`
  - Mac current `[125,125,125,253]`
  - delta `[-1,-1,-1,0]`
- `(72,8)`:
  - Windows ref `[126,126,126,253]`
  - Mac current `[125,125,125,253]`
  - delta `[-1,-1,-1,0]`
- `(106,19)`:
  - Windows ref `[169,169,169,253]`
  - Mac current `[167,167,167,253]`
  - delta `[-2,-2,-2,0]`

## Interpretation

- The Windows source-ownership rule is now reflected at the primary
  `case_0012` witnesses.
- This is a major improvement from the prior factor-of-two failure at the same
  coordinates.
- `case_0012` is still not `AE exact`, so the fix should be treated as a
  grounded improvement, not closure.
- The next high-value follow-up is a rerun of the full 16bpc
  `OLMDistanceGradation` extended batch with the newly installed build.
