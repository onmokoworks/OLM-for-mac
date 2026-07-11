# OLMRadialBlur Zoom Final-Sample Float Sequence Probe

- Case: `case_0009`
- Target Windows alpha=254 x positions: `[6, 7, 12]`

## Classification

| Sequence | Quantizer | emitted 254 | TP | FP | FN |
| --- | --- | --- | --- | --- | --- |
| `current_double_sum` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `current_double_sum` | `truncate` | `[0, 1, 4, 5, 7, 11, 12, 15, 16, 18, 20, 21, 25]` | `[7, 12]` | `[0, 1, 4, 5, 11, 15, 16, 18, 20, 21, 25]` | `[6]` |
| `f32_products_sum_double` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `f32_products_sum_double` | `truncate` | `[0, 1, 2, 4, 5, 6, 7, 12, 15, 16, 17, 18, 21, 25]` | `[6, 7, 12]` | `[0, 1, 2, 4, 5, 15, 16, 17, 18, 21, 25]` | `[]` |
| `f32_sequential_sum` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `f32_sequential_sum` | `truncate` | `[1, 12, 15, 16]` | `[12]` | `[1, 15, 16]` | `[6, 7]` |
| `f32_grouped_sum` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `f32_grouped_sum` | `truncate` | `[1, 7, 15, 17]` | `[7]` | `[1, 15, 17]` | `[6, 12]` |
| `weight_sum_double` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `weight_sum_double` | `truncate` | `[0, 4, 5, 7, 15, 18, 20, 21, 25]` | `[7]` | `[0, 4, 5, 15, 18, 20, 21, 25]` | `[6, 12]` |
| `weight_sum_f32_products_double` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `weight_sum_f32_products_double` | `truncate` | `[0, 2, 4, 5, 7, 15, 17, 18, 21, 25]` | `[7]` | `[0, 2, 4, 5, 15, 17, 18, 21, 25]` | `[6, 12]` |
| `weight_sum_f32_sequential` | `epsilon` | `[]` | `[]` | `[]` | `[6, 7, 12]` |
| `weight_sum_f32_sequential` | `truncate` | `[]` | `[]` | `[]` | `[6, 7, 12]` |

## Target Points

| x | ref | cell_alpha | fx | fy | current alpha | f32 seq alpha | eps q | trunc q |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | `[20, 3, 3, 254]` | `[1.0, 1.0, 1.0, 0.9999999404]` | `0.22802700102329254` | `0.5574949979782104` | `1.000000007324576` | `1.0` | `255` | `255` |
| 7 | `[21, 3, 3, 254]` | `[1.0, 1.0, 1.0, 1.0]` | `0.35791000723838806` | `0.6862789988517761` | `0.9999999701976776` | `1.0` | `255` | `255` |
| 12 | `[21, 4, 4, 254]` | `[1.0, 1.0, 0.9999999404, 1.0]` | `0.01049800030887127` | `0.3336179852485657` | `0.9999999933636222` | `0.9999999403953552` | `255` | `254` |

## Interpretation

All epsilon-quantized final-sample arithmetic variants miss the Windows alpha=254 set, including the all-one x=7 spoiler. Truncate-only variants either miss target pixels or add broad false positives. Therefore weight/sum precision alone is rejected; the live lane must move to final-polar cell selection, coordinate generation, or source-plane population.
