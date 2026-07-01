# OLMDistanceGradation 16bpc Constant Case Correlations - 2026-06-30

Correlate the focused Constant boundary cases with the two-stage helper diagnostic.

| Case | In/Out | Inside | Outside | Best by nonzero | Best by mean | Reading |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `case_0020` | 1 | 78 | 204 | `current_constant` | `current_constant` | current stays best |
| `case_0021` | 3 | 78 | 402 | `current_constant` | `current_constant` | current stays best |
| `case_0022` | 3 | 36 | 11 | `trunc_plateau_binary` | `current_constant` | partial two-stage signal |
| `case_0023` | 3 | 36 | 0 | `trunc_plateau_binary` | `trunc_plateau_binary` | strongest two-stage signal |

## Reading

- `case_0023` is the only focused case where the same two-stage family wins on both nonzero count and mean.
- `case_0023` is also the only focused case with `Outside Threshold = 0`.
- `case_0022` suggests some shared structure, but not a safe implementation rule yet.
