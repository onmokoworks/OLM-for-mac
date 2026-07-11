# OLMDistanceGradation 0010/0011 OpenCV field-prep audit - 2026-07-09

This audit connects the new Windows PF16 writer witness to the AEX field-prep
shape. It is evidence classification only; it does not authorize a Mac source
change by itself.

- Decision: `field-prep-structural-boundary-not-final-writer`

## Source Facts

| Fact | Source | Marker | Status | Reading |
| --- | --- | --- | --- | --- |
| `fieldgen_entry` | `decomp/DistanceGradation.aex.c.txt:3542506` | `void FUN_181174760` | found | DistanceGradation field-prep helper entry. |
| `first_distance_transform` | `decomp/DistanceGradation.aex.c.txt:3542536` | `FUN_1812b15a0(local_48[0],local_88[0],2,0,0,0,0);` | found | First OpenCV distanceTransform call shape: uint8 source to float32 destination, DIST_L2, DIST_MASK_PRECISE. |
| `trunc_threshold` | `decomp/DistanceGradation.aex.c.txt:3542540` | `uVar2 = 2;` | found | Non-constant path starts with THRESH_TRUNC mode for the later threshold/normalize wrapper. |
| `constant_switch` | `decomp/DistanceGradation.aex.c.txt:3542544` | `if (param_8 == 1)` | found | Constant interpolation switches the mode used by the final wrapper. |
| `final_wrapper_call` | `decomp/DistanceGradation.aex.c.txt:3542553` | `FUN_1812b6a40(local_68[0],local_a8[0],(double)fVar4,(double)fVar3,CONCAT44(uVar5,uVar2));` | found | The helper emits the field through the wrapper fed by fVar4/fVar3 and threshold mode. |
| `cvthreshold_string` | `decomp/DistanceGradation.aex.c.txt:3797673` | `"cvThreshold"` | found | FUN_1812b6a40 assertion path names cvThreshold. |
| `cvnormalize_path` | `tools/emulation/opencv_impls.py:227` | `def cvnormalize_minmax_native` | found | The repo already has a limited cvNormalize NORM_MINMAX detour and sidecar gate for the fieldgen path. |
| `current_mac_dt` | `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:484` | `static void dt_to_normalized` | found | Current Mac source computes EDT, clamps to threshold, finds raw max, then divides in float. |

## Witness Families

| Case | XY | Family | Mac raw | Mac field | Required field word | Windows store A |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `olmdistancegradation_extended__case_0010` | `(6,40)` | `outside_actual_max` | 41 | 0.900283873081 | 29500 | 3268 |
| `olmdistancegradation_extended__case_0010` | `(901,394)` | `inside_threshold_half_boundary` | 44.0113639832 | 0.698593080044 | 22892 | 9876 |
| `olmdistancegradation_extended__case_0011` | `(915,392)` | `inside_threshold_half_boundary` | 46.8187980652 | 0.134536772966 | 4409 | 28359 |

## Reading

- The accepted Windows return already proves the final output address/writeback formula for the sampled PF16 pixels, so the current residual should not be treated as a broad final-writer bug.
- The sign-flipped one-word residuals reject a single global output rounding rule.
- Current Mac EDT and the repository OpenCV-compatible `cvDistTransform` agree at the checked local fields, so the remaining difference is narrower than simply replacing Meijster with the current detour.
- The remaining open boundary is how the AEX/OpenCV field-prep path clamps, normalizes, and stores/feeds the field world before `FUN_181170480` consumes it.

## Next Proof

Run the DG AEX CPU fieldgen probe for `case_0010` and `case_0011` with the existing OpenCV detours registered through `normalize_minmax`, then sample the emitted field words at `(6,40)`, `(901,394)`, and `(915,392)`. If the emulated helper reproduces the Windows-required field words, patch the Mac source to mirror that helper. If it reproduces the current Mac values, request a Windows primitive trace for the field-prep max/normalize/pack boundary instead of changing compose/writeback.
