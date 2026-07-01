# OLMDistanceGradation 16bpc Constant Threshold Bias - 2026-06-30

Whole-frame comparison of small Constant/no-blur threshold-bias variants on the focused boundary cases.

| Case | Best variant | Best nonzero px | Current nonzero px | Best mean | Current mean |
| --- | --- | ---: | ---: | ---: | ---: |
| `case_0020` | `bias_0.0_current` | 304210 | 304210 | 0.090347 | 0.090347 |
| `case_0021` | `bias_0.0_current` | 1406979 | 1406979 | 0.353668 | 0.353668 |
| `case_0022` | `bias_0.0_current` | 702720 | 702720 | 2.935718 | 2.935718 |
| `case_0023` | `bias_0.0_current` | 203213 | 203213 | 295.305436 | 295.305436 |

## Reading

- Cases improved by any bias variant: `0/4`.
- This is only a bounded threshold-ownership probe for Constant/no-blur slices.
- If no bias variant wins decisively, the remaining lane is probably not a simple `>` vs `> + eps` ownership tweak.
