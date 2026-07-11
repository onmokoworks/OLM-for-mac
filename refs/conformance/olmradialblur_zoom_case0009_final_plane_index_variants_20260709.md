# OLMRadialBlur Zoom Final-Plane Index Variant Probe

- Case: `case_0009`
- Target alpha=254 x positions: `[6, 7, 12]`
- Candidates tested: `486`

## Top Candidates

| Rank | source mode | fraction mode | angle bias | radius bias | quantizer | emitted 254 | TP | FP | FN |
| ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | `cpp-double` | `double-before-floor` | -0.5 | 0.5 | `truncate` | `[6, 7, 14, 15, 16, 29, 30]` | `[6, 7]` | `[14, 15, 16, 29, 30]` | `[12]` |
| 2 | `cpp-double` | `f32-before-floor` | -0.5 | 0.5 | `truncate` | `[6, 7, 14, 15, 16, 29, 30]` | `[6, 7]` | `[14, 15, 16, 29, 30]` | `[12]` |
| 3 | `cpp-aex-float` | `double-before-floor` | -0.5 | 1.0 | `truncate` | `[2, 6, 7, 14, 16, 17, 21]` | `[6, 7]` | `[2, 14, 16, 17, 21]` | `[12]` |
| 4 | `cpp-aex-float` | `f32-before-floor` | -0.5 | 1.0 | `truncate` | `[2, 6, 7, 14, 16, 17, 21]` | `[6, 7]` | `[2, 14, 16, 17, 21]` | `[12]` |
| 5 | `python-prefill-f32` | `double-before-floor` | -0.5 | 1.0 | `truncate` | `[2, 6, 7, 14, 16, 17, 21]` | `[6, 7]` | `[2, 14, 16, 17, 21]` | `[12]` |
| 6 | `python-prefill-f32` | `f32-before-floor` | -0.5 | 1.0 | `truncate` | `[2, 6, 7, 14, 16, 17, 21]` | `[6, 7]` | `[2, 14, 16, 17, 21]` | `[12]` |
| 7 | `cpp-double` | `double-before-floor` | 0.0 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 8 | `cpp-double` | `f32-before-floor` | 0.0 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 9 | `cpp-double` | `double-before-floor` | -0.0001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 10 | `cpp-double` | `double-before-floor` | 0.0001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 11 | `cpp-double` | `f32-before-floor` | -0.0001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 12 | `cpp-double` | `f32-before-floor` | 0.0001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 13 | `cpp-double` | `double-before-floor` | -0.001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 14 | `cpp-double` | `double-before-floor` | 0.001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 15 | `cpp-double` | `f32-before-floor` | -0.001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 16 | `cpp-double` | `f32-before-floor` | 0.001 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 17 | `cpp-double` | `double-before-floor` | 0.5 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 18 | `cpp-double` | `f32-before-floor` | 0.5 | 1.0 | `truncate` | `[7, 10, 11, 12, 14, 15, 16, 28, 29, 30]` | `[7, 12]` | `[10, 11, 14, 15, 16, 28, 29, 30]` | `[6]` |
| 19 | `cpp-double` | `double-before-floor` | 0.0 | -0.5 | `truncate` | `[5, 6, 10, 12, 13, 14, 26, 27, 28, 29, 30]` | `[6, 12]` | `[5, 10, 13, 14, 26, 27, 28, 29, 30]` | `[7]` |
| 20 | `cpp-double` | `f32-before-floor` | 0.0 | -0.5 | `truncate` | `[5, 6, 10, 12, 13, 14, 26, 27, 28, 29, 30]` | `[6, 12]` | `[5, 10, 13, 14, 26, 27, 28, 29, 30]` | `[7]` |

## Best Target Details

- Best: mode=`cpp-double`, fraction=`double-before-floor`, angle_bias=`-0.5`, radius_bias=`0.5`
- x=6: alpha=`0.9999999990679569`, radius_index=`1096.728027`, angle_index=`1047.057495`, cells=`[[1047, 1096], [1047, 1097], [1048, 1096], [1048, 1097]]`, cell_alphas=`[1.0, 1.0, 0.9999999403953552, 1.0]`
- x=7: alpha=`0.999999993629823`, radius_index=`1095.85791`, angle_index=`1047.186279`, cells=`[[1047, 1095], [1047, 1096], [1048, 1095], [1048, 1096]]`, cell_alphas=`[1.0, 1.0, 1.0000001192092896, 0.9999999403953552]`
- x=12: alpha=`1.0`, radius_index=`1091.510498`, angle_index=`1047.833618`, cells=`[[1047, 1091], [1047, 1092], [1048, 1091], [1048, 1092]]`, cell_alphas=`[1.0, 1.0, 1.0, 1.0]`

## Interpretation

This probes only final-plane index arithmetic. A candidate is implementation-worthy only if it hits x=[6,7,12] with no or very few false positives and is later grounded by asm/runtime witness. Current best emits [6, 7, 14, 15, 16, 29, 30]; keep this as analysis evidence, not a Mac source change.
