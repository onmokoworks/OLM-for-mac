# DistanceGradation 16bpc Mac AE Probe: case_0027 variants - 2026-06-26

Target: `olmdistancegradation_extended__case_0027`

Goal: check whether the installed Mac AE 16bpc plug-in path responds to
`Render Mode` and `Use Background Color` as expected on a case where the
Windows Software reference mixes visible background red into zero-alpha source
regions.

Artifacts:

- Summary JSON:
  `handoff/ae_pixel_validation_20260618/probes/distancegradation_case0027_variants/summary.json`
- Rendered probes:
  `handoff/ae_pixel_validation_20260618/probes/distancegradation_case0027_variants/*.png`

## Variants

Base packaged parameters were applied exactly, then only these two fields were
varied:

- `Render Mode` (`OLM Distance Gradation-0005`)
- `Use Background Color` (`OLM Distance Gradation-0006`)

Rendered variants:

- `layer_bg`: `Render Mode=2`, `Use Background Color=1`
- `layer_no_bg`: `Render Mode=2`, `Use Background Color=0`
- `grad_bg`: `Render Mode=1`, `Use Background Color=1`
- `grad_no_bg`: `Render Mode=1`, `Use Background Color=0`

## Witness pixels

Values below are the native 16-bit RGBA values from `refs/scripts/verify_manifest.py`
(`load_rgba`), not Pillow's lossy display conversion.

| Variant | `(3,0)` | `(14,0)` | `(397,281)` | `(438,1)` | Reading |
| --- | --- | --- | --- | --- | --- |
| `layer_bg` | `[0,0,0,65535]` | `[1280,0,0,65535]` | `[768,0,0,65535]` | `[61184,57600,57600,65535]` | source+background mix present |
| `layer_no_bg` | `[0,0,0,65535]` | `[0,0,0,63999]` | `[0,0,0,64511]` | `[57088,57088,57088,61951]` | alpha reveals observed field `X` |
| `grad_bg` | `[6940,0,60910,65535]` | `[8476,0,59374,65535]` | `[7964,0,60398,65535]` | `[10012,0,57838,65535]` | BG/gradation blend branch active |
| `grad_no_bg` | `[6940,0,60910,65535]` | `[6428,0,59374,63999]` | `[6428,0,59886,64511]` | `[6428,0,57326,61951]` | same field, no-BG alpha/output path |

## Pairwise diff

- `grad_bg` vs `grad_no_bg`: not identical in true 16-bit; RGB/alpha diverge once decoded natively.
- `layer_bg` vs `layer_no_bg`: materially different in true 16-bit; `layer_no_bg` alpha provides a usable observation of the internal field `X`.

## Conclusion

- On this 16bpc Mac AE probe, `Use Background Color` does participate in the
  final compose branch when the output is decoded as native 16-bit PNG.
- The earlier "background branch is ignored" reading came from inspecting the
  same files through Pillow's lossy 8-bit conversion and was incorrect.
- The durable finding is narrower: request-manifest drift is ruled out, and the
  remaining mismatch is upstream in the field `X` that drives the compose, not
  in a missing background-color branch.
- See the follow-up analysis
  `refs/conformance/olmdistancegradation_16bpc_case0027_probe_x_20260626.md`
  for the reconstructed observed `X`.
