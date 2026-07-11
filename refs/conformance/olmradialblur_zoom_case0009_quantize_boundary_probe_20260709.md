# OLMRadialBlur Zoom case_0009 Quantize Boundary Probe

Date: 2026-07-09

## Scope

Mac-local CLI witness only. This does not promote a Mac plugin behavior change.

Target:

- `refs/win_references/20260604_olm/OLMRadialBlur/case_0009`
- witness pixel `(6,0)`

The purpose is to separate the remaining Zoom alpha byte split from global
output quantization.

## Commands

The baseline guard was first re-run:

```bash
python3 refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py
```

Result:

```text
[OK] case_0009 max=1 mean=0.0046
```

Then the same witness pixel was rendered with the current CLI and three focused
candidate modes:

```bash
cli/OLMRadialBlur/olmradialblur_cli \
  --input /private/tmp/olmradialblur_cpp_zoom_smoke/reference/case_0009_before_effects.png \
  --params /private/tmp/olmradialblur_cpp_zoom_smoke/candidate/_params/case_0009.json \
  --output /tmp/olmrb_case0009_default.png \
  --witness-dump /tmp/olmrb_case0009_default_witness.json \
  --witness-x 6 --witness-y 0

cli/OLMRadialBlur/olmradialblur_cli \
  --input /private/tmp/olmradialblur_cpp_zoom_smoke/reference/case_0009_before_effects.png \
  --params /private/tmp/olmradialblur_cpp_zoom_smoke/candidate/_params/case_0009.json \
  --output /tmp/olmrb_case0009_aex_repeat.png \
  --zoom-grid-mode aex-float \
  --rgba-sampler-alpha-mode repeat-raw-f32 \
  --witness-dump /tmp/olmrb_case0009_aex_repeat_witness.json \
  --witness-x 6 --witness-y 0

cli/OLMRadialBlur/olmradialblur_cli \
  --input /private/tmp/olmradialblur_cpp_zoom_smoke/reference/case_0009_before_effects.png \
  --params /private/tmp/olmradialblur_cpp_zoom_smoke/candidate/_params/case_0009.json \
  --output /tmp/olmrb_case0009_polar_alpha.png \
  --zoom-grid-mode aex-float \
  --rgba-sampler-alpha-mode repeat-raw-f32 \
  --outer-caller-collapse-mode polar-alpha \
  --witness-dump /tmp/olmrb_case0009_polar_alpha_witness.json \
  --witness-x 6 --witness-y 0

cli/OLMRadialBlur/olmradialblur_cli \
  --input /private/tmp/olmradialblur_cpp_zoom_smoke/reference/case_0009_before_effects.png \
  --params /private/tmp/olmradialblur_cpp_zoom_smoke/candidate/_params/case_0009.json \
  --output /tmp/olmrb_case0009_polar_alpha_trunc.png \
  --zoom-grid-mode aex-float \
  --rgba-sampler-alpha-mode repeat-raw-f32 \
  --outer-caller-collapse-mode polar-alpha \
  --outer-alpha-quantize-mode truncate \
  --witness-dump /tmp/olmrb_case0009_polar_alpha_trunc_witness.json \
  --witness-x 6 --witness-y 0
```

## Witness Summary

| Candidate | `(6,0)` output | Windows `(6,0)` | max | nonzero_px | witness alpha | witness u8 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| default | `(20,3,3,255)` | `(20,3,3,254)` | 1 | 31119 | `1` | `[20,3,3,255]` |
| `aex-float + repeat-raw-f32` | `(20,3,3,255)` | `(20,3,3,254)` | 1 | 31097 | `1` | `[20,3,3,255]` |
| `polar-alpha` | `(20,3,3,255)` | `(20,3,3,254)` | 1 | 31097 | `0.9999999924` | `[20,3,3,255]` |
| `polar-alpha + truncate` | `(20,3,3,254)` | `(20,3,3,254)` | 1 | 567071 | `0.9999999924` | `[20,3,3,254]` |

For `polar-alpha`, the four final bilinear cell alpha contributions are:

```text
a00 = 0.3416016698
a10 = 0.100903213
a01 = 0.4303709865
a11 = 0.1271241231
alpha = 0.9999999924
cell alphas = [1, 1, 1, 0.9999999404]
cell valid = [1, 1, 0, 0]
```

## Interpretation

`polar-alpha` exposes the local floating-point reason the witness can become
254: one contributing final-polar cell is slightly below one, producing
`alpha=0.9999999924`.

However, global truncation is rejected again. It fixes `(6,0)` but broadens the
case to `567071` nonzero pixels, matching the earlier
`rejected_overbroad_alpha_truncation` finding. Therefore the remaining Zoom
rule is not a global output quantization switch.

The next Mac-local RadialBlur work should stay on exact polar cell coordinate /
float sequence or final plane selection. Do not patch `mac/OLMRadialBlur` from
this probe alone.
