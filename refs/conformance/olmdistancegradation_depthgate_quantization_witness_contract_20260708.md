# OLMDistanceGradation Depth-gate Quantization Witness Contract - 2026-07-08

## Purpose

This request is for the Windows machine only. It follows:

- `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
- `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md`
- `refs/conformance/olmdistancegradation_depthgate_nearmiss_witness_20260708.md`

The depth-gated Mac build already closes `olmdistancegradation_extended__case_0023`.
The remaining clean family is `case_0024..0027`, where all observed deltas are `max=1`.

This request must classify the first stage where Windows and Mac differ for representative
`case_0026` / `case_0027` pixels:

1. interpolation/compose output float,
2. PF_Pixel16 store rounding/clamp,
3. or AE/PNG export quantization.

Do not use this request to retune the distance field, source mask, blur, or Both-combine path.

## Primary Case

`olmdistancegradation_extended__case_0026`

Parameters of interest:

- `Invert=1`
- `In/Out=3`
- `Inside Threshold=158`
- `Outside Threshold=13`
- `Render Mode=1`
- `Use Background Color=1`
- `Interpolation Mode=4`
- `Power=2.59740734100342`
- `Blur Mode=1`
- `Blur Size=0`
- `Gradation Color=[0.1098041459918,0,0.93333333730698,1]`
- `BG Color=[1,0,0,1]`

Representative pixels:

| XY | Windows PNG RGBA8 | Mac PNG RGBA8 | Mac field_x | Mac out R | Mac out B | Mac store R | Mac store B |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `(907,222)` | `[255,0,0,255]` | `[255,0,1,255]` | `0.121742934` | `0.996250153` | `0.00393153122` | `32645` | `129` |
| `(395,477)` | `[253,0,2,255]` | `[254,0,2,255]` | `0.161361381` | `0.992204964` | `0.00817277841` | `32513` | `268` |
| `(1589,579)` | `[134,0,126,255]` | `[135,0,126,255]` | `0.783686459` | `0.52736038` | `0.495543033` | `17281` | `16238` |
| `(898,670)` | `[88,0,175,255]` | `[88,0,176,255]` | `0.888987124` | `0.344237924` | `0.687539339` | `11280` | `22529` |

## Control Case

`olmdistancegradation_extended__case_0027`

This differs from `case_0026` mainly by `Render Mode=2`. Use it only as a control if the
same hook/watchpoint setup works.

Representative pixels:

| XY | Windows PNG RGBA8 | Mac PNG RGBA8 | Mac field_x | Mac out R | Mac out G | Mac out B | Mac store R | Mac store G | Mac store B |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(1234,443)` | `[249,6,0,255]` | `[249,6,1,255]` | `0.237236261` | `0.976171851` | `0.023828106` | `0.00392458029` | `31987` | `781` | `129` |
| `(410,624)` | `[241,0,13,255]` | `[241,0,14,255]` | `0.32673189` | `0.945278585` | `0` | `0.0547214374` | `30975` | `0` | `1793` |
| `(906,668)` | `[43,0,0,255]` | `[44,0,0,255]` | `0.929949105` | `0.171913624` | `0` | `0` | `5633` | `0` | `0` |
| `(533,734)` | `[188,65,65,255]` | `[188,66,66,255]` | `0.778481007` | `0.736012816` | `0.257840157` | `0.257840157` | `24118` | `8449` | `8449` |

## Required Observations

For each successfully isolated pixel, return:

- module base and exact hook/watchpoint address,
- case id and pixel xy,
- source/input RGBA16 seen by the effect,
- field value consumed by `FUN_181170480`,
- X before invert, after invert, and after interpolation/power,
- render-mode branch selected,
- BG color, gradation color, and source-layer RGB/A used by the compose path,
- output RGBA float immediately before PF_Pixel16 conversion,
- PF_Pixel16 words immediately after store,
- exported RGBA16 or exported PNG byte from the same run, if observable,
- exact failed hook/watchpoint reason if the pixel cannot be isolated.

## Suggested Hook

Start from `FUN_181170480` and/or the final output-word data breakpoint. If the compose
callback does not retain xy directly, bind the pixel from the output-world address or
the refcon/userdata mapping. Older case_0023 packages used wrapper `FUN_181170280` and
the `param_4+0x2c` user-data path; reuse only the address-binding method, not the old
case_0023 witness assumptions.

## Acceptance

`answered`:

- At least two `case_0026` representative pixels are classified as one of:
  interpolation/compose-float difference, PF_Pixel16 store rounding/clamp difference,
  or export/path quantization difference.
- The answer contains typed values, not final PNG bytes alone.

`answered_partial`:

- One representative pixel is fully classified, or callback-local output float and
  PF_Pixel16 store words are captured but export cannot be observed.

`failed`:

- Only final PNG values are returned.
- Only broad callback hit counts are returned.
- The run repeats the old `case_0023` source-mask/field proof.

## Forbidden

- Do not run broad distanceTransform/threshold tracing.
- Do not recapture framewide PNGs as the main answer.
- Do not tune source mask, Both-combine, blur, or field generation from this request.
- Do not use the AE-free CLI reimplementation as Windows truth for this lane.
