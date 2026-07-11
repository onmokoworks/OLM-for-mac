# DistanceGradation 16bpc field probe summary - 2026-06-26

These cases were rerendered on Mac AE with `Use Background Color=0` so
the current plug-in exposes the live field through output alpha.

| Case | Witness | Observed X | Max-model X | Add-model X | Candidate RGB | Reference RGB | Reading |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `case_0020` | `(951,417)` | 0.000000 | 0.000000 | 0.000000 | `[65535, 0, 0]` | `[7195, 0, 61165]` | Mac no_bg probe matches current model; Windows reference is opposite color on bg-on render |
| `case_0021` | `(951,417)` | 0.000000 | 0.000000 | 0.000000 | `[65535, 0, 0]` | `[7195, 0, 61165]` | Mac no_bg probe matches current model; Windows reference is opposite color on bg-on render |
| `case_0022` | `(4,0)` | 0.000000 | 0.000000 | 0.000000 | `[65535, 0, 0]` | `[7195, 0, 61165]` | Mac no_bg probe matches current model; Windows reference is opposite color on bg-on render |
| `case_0023` | `(1699,7)` | 1.000000 | 1.000000 | 1.000000 | `[65535, 0, 0]` | `[65535, 0, 0]` | Mac no_bg probe matches current model; Windows reference is opposite color on bg-on render |
| `case_0027` | `(3,0)` | 1.000000 | 0.812285 | 0.812285 | `[0, 0, 0]` | `[12301, 0, 0]` | Observed X stays much higher than both max and add models |
| `case_0028` | `(3,0)` | 1.000000 | 0.968477 | 0.968477 | `[0, 0, 0]` | `[2065, 0, 0]` | Observed X stays much higher than both max and add models |

## Conclusions

- `case_0020..0023`: the Mac `no_bg` probe agrees with the current constant/binary model at the witness pixels. The mismatch against Windows appears only once `Use Background Color=1` is involved, so these four cases likely need Windows-side evidence about how Constant mode and background compose interact.
- `case_0027/0028`: the Mac `no_bg` probe directly contradicts both the old `max(...)` shorthand and the binary-grounded `inside + outside` Both model. These remain live Mac-side field-prep / normalization problems.
