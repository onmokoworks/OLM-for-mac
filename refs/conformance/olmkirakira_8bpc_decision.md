# OLMKiraKira Decision Matrix

- Decision: `blocked-compose-or-final-quantization`
- Classification: `ray-helper-and-fd90-grounded`
- Recommended action: Do not reopen luma, boxFilter window, ray-helper choreography, or global compose scale. The remaining KiraKira residual belongs to merge-mode-1 compose/writeback/final quantization or a narrower residual hotspot.

## BT.709 Remeasure

- Software cases: `9`
- Exact cases: `1`
- Max diff max: `66`
- Mean sum: `8.215029`

| Group | Cases | Max | Mean sum | Exact |
| --- | ---: | ---: | ---: | ---: |
| `rotation13` | 1 | 66 | 1.880854 | 0 |
| `strength0_anchor` | 4 | 3 | 0.069035 | 1 |
| `strength100_single_ray` | 4 | 23 | 6.265140 | 0 |

## Grounded Stages

- Ray helper: `grounded-within-float-print-precision` (max delta `1.230990600564752e-07`)
- BoxFilter focus: `boxfilter-pass1-upstream-source-buffer-content`
- Aggregation: `fd90-grounded-compose-unisolated`
- Aggregation focus: `fd90-aggregation-grounded-compose-scale`
- Compose audit: `preserve-current-compose-model`
- Compose audit best by mean/max: `current_gain_0_62` / `current_gain_0_62`

## fd90 Samples

| Label | XY | Ray inputs | Glow RGBA |
| --- | --- | --- | --- |
| `center` | `[960, 540]` | `[0.71891218, 0, 0, 0, 0]` | `[1, 1, 1, 0.71891218]` |
| `ray_length_up` | `[960, 490]` | `[0.76832885, 0, 0, 0, 0]` | `[1, 1, 1, 0.76832885]` |
| `ray_length_right` | `[1010, 540]` | `[0.71564364, 0, 0, 0, 0]` | `[1, 1, 1, 0.71564364]` |

## Implied Screen Compose Scale

| Label | XY | fd90 alpha | implied alpha mean | implied scale mean | scale range |
| --- | --- | ---: | ---: | ---: | --- |
| `center` | `[960, 540]` | 0.71891218 | 0.41777778 | 0.58112491 | `0.58112491..0.58112491` |
| `ray_length_up` | `[960, 490]` | 0.76832885 | 0.41766382 | 0.54360033 | `0.52061041..0.56065737` |
| `ray_length_right` | `[1010, 540]` | 0.71564364 | 0.41333333 | 0.57756865 | `0.57756865..0.57756865` |

## Next Evidence

- Do not change global gain/premul compose unless new binary evidence contradicts the 2026-06-25 compose audit.
- If Windows is needed later, request a compose-site/pre-writeback witness at the BT.709 residual hotspot, not broad PNGs.
- Add 16/32bpc refs only after 8bpc compose/writeback behavior is stable.
