# OLMDistanceGradation Depth-gate Near-miss Witness - 2026-07-08

This follows `refs/conformance/olmdistancegradation_depthgate_nearmiss_family_20260708.md`.

## FACT

Mac AE 16bpc single-case debug was run for the clean pair:

- `case_0026`: `refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0026`
- `case_0027`: `refs/reports/ae_single_case_distancegradation_depthgate_nearmiss_20260708/case_0027`

Both runs completed with `AE single case status: ok`.

The sampled witness pixels are all `max=1` PNG-channel deltas against the Windows Software reference. The logged field and shade values are continuous, not binary endpoint flips.

Representative `case_0026` samples:

| XY | Windows RGBA8 | Mac RGBA8 | Ref-Mac | field_x | out R | out B | store R | store B |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `(907,222)` | `[255,0,0,255]` | `[255,0,1,255]` | `[0,0,-1,0]` | `0.121742934` | `0.996250153` | `0.00393153122` | `32645` | `129` |
| `(395,477)` | `[253,0,2,255]` | `[254,0,2,255]` | `[-1,0,0,0]` | `0.161361381` | `0.992204964` | `0.00817277841` | `32513` | `268` |
| `(1589,579)` | `[134,0,126,255]` | `[135,0,126,255]` | `[-1,0,0,0]` | `0.783686459` | `0.52736038` | `0.495543033` | `17281` | `16238` |
| `(898,670)` | `[88,0,175,255]` | `[88,0,176,255]` | `[0,0,-1,0]` | `0.888987124` | `0.344237924` | `0.687539339` | `11280` | `22529` |

Representative `case_0027` samples:

| XY | Windows RGBA8 | Mac RGBA8 | Ref-Mac | field_x | out R | out G | out B | store R | store G | store B |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `(1234,443)` | `[249,6,0,255]` | `[249,6,1,255]` | `[0,0,-1,0]` | `0.237236261` | `0.976171851` | `0.0238281712` | `0.00392458029` | `31987` | `781` | `129` |
| `(410,624)` | `[241,0,13,255]` | `[241,0,14,255]` | `[0,0,-1,0]` | `0.32673189` | `0.945278585` | `0` | `0.0547214374` | `30975` | `0` | `1793` |
| `(906,668)` | `[43,0,0,255]` | `[44,0,0,255]` | `[-1,0,0,0]` | `0.929949105` | `0.171913624` | `0` | `0` | `5633` | `0` | `0` |
| `(533,734)` | `[188,65,65,255]` | `[188,66,66,255]` | `[0,-1,-1,0]` | `0.778481007` | `0.736012816` | `0.257840157` | `0.257840157` | `24118` | `8449` | `8449` |

## Store-to-PNG Quantization Check

For the sampled Mac AE points, the exported Mac PNG byte usually matches `PF_Pixel16_word // 128`.
The corresponding Windows PNG byte often matches the lower `floor(PF_Pixel16_word * 255 / 32768)` value if the same Mac store word is assumed.

Examples:

| Case | XY | Channel | Store word | Mac PNG rule | Windows-like rule | Mac byte | Windows byte |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `0026` | `(395,477)` | R | `32513` | `254` | `253` | `254` | `253` |
| `0026` | `(1589,579)` | R | `17281` | `135` | `134` | `135` | `134` |
| `0026` | `(907,222)` | B | `129` | `1` | `1` | `1` | `0` |
| `0027` | `(533,734)` | G/B | `8449` | `66` | `65` or `66` depending on rounding | `66` | `65` |

This does not prove Windows and Mac have identical pre-store words. It proves the next witness must distinguish:

1. Windows pre-store float/store word is slightly lower than Mac near the byte boundary.
2. Windows and Mac store words match, but AE PNG export quantizes 16bpc words differently on this path.

## INFERENCE

- The near-miss family is not a field-topology failure like the old `case_0023` 73px lane. The sampled `field_x` values are smooth floats and the visible residuals are one-channel `1`-unit quantization boundaries.
- The next proof should focus on compose/interpolation quantization, PF_Pixel16 store words, and the PF_Pixel16-to-PNG export boundary. A broad distance-field or source-mask retune is not justified by these witnesses.
- `case_0026` remains the best first witness because it has enough samples (`2570` changed pixels) and pairs with `case_0027` by only `Render Mode`.

## Next Proof

Ask for or locally emulate the Windows value immediately before final 16bpc store/export for selected `case_0026` points, especially `(907,222)`, `(395,477)`, `(1589,579)`, and `(898,670)`. The question is whether Windows differs in:

- interpolation output float,
- PF_Pixel16 store rounding/clamp,
- or AE PNG export quantization.

Do not tune distance field generation from this witness without a contradictory field value.
