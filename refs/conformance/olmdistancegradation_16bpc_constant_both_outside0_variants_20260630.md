# OLMDistanceGradation 16bpc BOTH+Outside=0 Constant Variants - 2026-06-30

Targeted whole-frame probe that only changes the outside-side Constant helper in `In/Out=Both` cases.

| Case | Outside Threshold | Best by nonzero | Best by mean | Current nonzero px | Current mean | Reading |
| --- | ---: | --- | --- | ---: | ---: | --- |
| `case_0022` | 11 | `current_constant` (702720) | `current_constant` (2.935718) | 702720 | 2.935718 | current stays best |
| `case_0023` | 0 | `trunc_plateau_binary` (182793) | `trunc_plateau_binary` (1.095836) | 203213 | 295.305436 | both improve |

## Reading

- This does not change the inside-side helper or general compose logic.
- A win only on `case_0023` would strengthen the `Both + Outside Threshold=0` staging hypothesis without proving it globally.
- Flat results would push the next move back toward exact helper staging / threshold ownership proof from Windows rather than a Mac-side code experiment.
