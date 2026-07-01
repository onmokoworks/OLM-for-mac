# OLMDistanceGradation 16bpc Constant Two-Stage Variants - 2026-06-30

Whole-frame comparison of plausible AEX-shaped two-stage Constant helper variants on the focused boundary cases.

| Case | Best by nonzero | Best by mean | Current nonzero px | Current mean | Reading |
| --- | --- | --- | ---: | ---: | --- |
| `case_0020` | `current_constant` (304210) | `current_constant` (0.090347) | 304210 | 0.090347 | current stays best |
| `case_0021` | `current_constant` (1406979) | `current_constant` (0.353668) | 1406979 | 0.353668 | current stays best |
| `case_0022` | `trunc_plateau_binary` (702677) | `current_constant` (2.935718) | 702720 | 2.935718 | nonzero improves only |
| `case_0023` | `trunc_plateau_binary` (182793) | `trunc_plateau_binary` (20.041926) | 203213 | 295.305436 | both improve |

## Reading

- Cases with a better nonzero count under some two-stage variant: `2/4`.
- Cases with a better mean error under some two-stage variant: `1/4`.
- These are only plausible helper-shape probes, not claims about the true AEX internals.
- If a variant only improves nonzero count while worsening mean substantially, treat that as partial structure-similarity, not as an implementation-ready fix.
- A decisive improvement would justify implementing the best shape in the AE-free model or the Mac port; a flat or split result pushes the investigation back toward exact helper staging and temp-size ownership.
