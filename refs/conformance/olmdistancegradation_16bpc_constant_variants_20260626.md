# DistanceGradation 16bpc Constant Variants - 2026-06-26

Whole-frame comparison of simple `Both` / threshold-zero variants on the focused extended cases.

| Case | Best variant | Best nonzero px | Current nonzero px | Note |
| --- | --- | ---: | ---: | --- |
| `case_0020` | `current_max` | 304210 | 304210 | current stays best or tied |
| `case_0021` | `both_inside` | 1406979 | 1406979 | variant beats current |
| `case_0022` | `current_max` | 702677 | 702677 | current stays best or tied |
| `case_0023` | `current_max` | 182793 | 182793 | current stays best or tied |

## Conclusion

- The witness-level `min(...)` hint is real, but it does not improve the whole frame by itself.
- Simple swaps such as `Both=min`, `Both=inside`, or `Both=outside` are not safe fixes.
- The remaining problem still looks like a narrower upstream field-prep rule, especially around Constant mode and `Outside Threshold=0`.
