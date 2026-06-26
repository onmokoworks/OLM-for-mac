# DistanceGradation 16bpc Focus Cases - 2026-06-26

Witness-based summary of the current extended-case residual families.

## Cases

| Case | Family | Witness | Candidate RGB | Reference RGB | Reading |
| --- | --- | --- | --- | --- | --- |
| `case_0020` | `constant-bg-binary` | `(951,417)` | `[65535, 0, 0]` | `[6940, 0, 60910]` | candidate BG-like, reference Grad-like; inside=1.000000 outside=0.000000 max->0 min->1 |
| `case_0021` | `constant-bg-binary` | `(951,417)` | `[65535, 0, 0]` | `[6940, 0, 60910]` | candidate BG-like, reference Grad-like; inside=1.000000 outside=0.000000 max->0 min->1 |
| `case_0022` | `constant-bg-binary` | `(4,0)` | `[65535, 0, 0]` | `[6940, 0, 60910]` | candidate BG-like, reference Grad-like; inside=0.000000 outside=1.000000 max->0 min->1 |
| `case_0023` | `constant-bg-binary` | `(1699,7)` | `[6940, 0, 60910]` | `[65535, 0, 0]` | candidate Grad-like, reference BG-like; inside=0.027778 outside=0.000000 max->1 min->1 |
| `case_0027` | `layer-bg-fractional` | `(3,0)` | `[0, 0, 0]` | `[3376, 0, 0]` | candidate pins source-zero RGB |
| `case_0028` | `layer-bg-fractional` | `(3,0)` | `[0, 0, 0]` | `[4360, 0, 0]` | candidate pins source-zero RGB |

## Conclusions

- `case_0020..0023` are BG-like vs Grad-like binary decisions at the sampled pixels.
- For `case_0021/0022`, the current Mac `Both=max(inside,outside)` witness behavior lands on the Mac candidate side, while `min(inside,outside)` would land on the Windows witness side.
- `case_0023` still disagrees even under the simple `min` witness, and the distinguishing parameter is `Outside Threshold=0`; this suggests a threshold-zero special case or another upstream field-prep branch is still missing.
- These are field-prep / constant-mode questions, not simple channel-order or color-space issues.
- A 2026-06-26 Mac AE host debug rerun confirmed the packaged `case_0027` parameters are being applied exactly inside After Effects (`Invert=1`, `Render Mode=2`, `Use Background Color=1`, `Interpolation Mode=4`, `Power=2.5974...`, expected colors). So this residual is not request drift.
- A same-day four-variant Mac AE probe, decoded as native 16-bit PNG, corrected the earlier 8-bit-read misinterpretation: the background-compose branch is active. The remaining mismatch is upstream in the field `X`, not in a missing `Use Background Color` branch.
- `case_0027/0028` therefore stay classified as field-prep / X-shape failures. The Windows Software reference keeps more background-red contribution because the live Mac field stays much closer to `1.0` than the current distance model predicts.
