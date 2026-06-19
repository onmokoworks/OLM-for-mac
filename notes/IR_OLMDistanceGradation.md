# Binary-Grounded IR: OLMDistanceGradation

## Feature

- Plug-in: Distance Gradation
- Feature/path: 8bpc alpha-mask distance gradation, interpolation, optional blur
- Bit depth: 8bpc documented here; 16/32bpc still need references
- Reference set: `refs/win_references/20260605_extra/OLMDistanceGradation`
- Current status: `guarded residual`; not `CLI exact`, not `AE exact`

## Source Evidence

| Rule | Evidence | Confidence |
| --- | --- | --- |
| Generates gradation inside/outside an alpha-channel mask. | Official manual text in `refs/upstream_official/20260619_olm_official_zips/pdf_text/OLMDistanceGradation__OLMDistanceGradation__doc__DistanceGradationUserManualEN.txt`. | manual-backed |
| Local description says distance transform. | `mac/OLMDistanceGradation/OLMDistanceGradation_Strings.cpp`. | manual/local-backed |
| Current mac port implements exact Euclidean distance transform equivalent to OpenCV `distanceTransform(DIST_L2, DIST_MASK_PRECISE)`. | Comments and code in `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`. | implementation-grounded |
| Distance field is thresholded then normalized by actual max, not always by threshold. | Current mac implementation comments and CLI behavior. | implementation-grounded / guarded |
| Gaussian blur uses OpenCV-style separable kernel with `BORDER_REFLECT_101` and default sigma formula. | Current mac implementation comments and Python CLI. | implementation-grounded |
| Constant+Blur first thresholds the normalized field to a binary full-distance field and uses doubled radius. | Current mac/Python implementation and guarded `case_0029` result. | guarded / inferred |
| Windows AEX embeds OpenCV 4.5.5. | `decomp/DistanceGradation.aex.c.txt` contains OpenCV 4.5.5 build strings and source paths. | binary-grounded |
| Per-pixel compose path implements Sphere with `sqrt(1 - (1 - X)^2)` and Power with `powf(X, power)`. | `decomp/DistanceGradation.aex.c.txt` around `FUN_181170870` and sibling 16/float compose functions. | binary-grounded |
| 8bpc compose reads the distance field from the green byte of the field pixel and applies invert/interpolation in `FUN_181170870`. | `decomp/DistanceGradation.aex.c.txt` `FUN_181170870`: `_X = field_pixel[green] / 255`, then optional `1 - X`, Sphere/Power, and final RGBA byte cast. | binary-grounded |
| 8bpc compose is an AE iterate callback over a prebuilt field world. | `FUN_181170380` requests `PF Iterate8 Suite` and passes callback `FUN_181170870` with user data `param_4 + 0x2c`; `FUN_181170870` then reads the field world through `param_1[1]`. | binary-grounded |
| 16bpc and float compose use sibling iterate callbacks. | `FUN_181170280` requests `PF iterate16 Suite` and passes `FUN_181170480`; float path stores callback `FUN_181170c90`. | binary-grounded |
| OpenCV border names including `BORDER_REFLECT_101` are present in the AEX. | `decomp/DistanceGradation.aex.c.txt` contains `cv::copyMakeBorder` and border-name table strings. | binary-grounded for availability, not final blur branch proof |

## Parameters

| UI / manifest name | Internal meaning | Normalization | Evidence |
| --- | --- | --- | --- |
| `In/ Out` | Selects inside, outside, or both regions. | enum: Inside, Outside, Both. | official manual + implementation |
| `Inside Threshold` | Maximum inside distance before normalization. | `max(1, threshold * ds_scale)`; threshold `0` becomes `1`. | implementation |
| `Outside Threshold` | Maximum outside distance before normalization. | `max(1, threshold * ds_scale)`; threshold `0` becomes `1`. | implementation |
| `Render Mode` | RGB color ramp or source layer color. | enum: RGB, Layer. | official manual + implementation |
| `Use Background Color` | Selects color+opaque-background ramp vs alpha gradation. | Boolean. | official manual + implementation |
| `Gradation Color` | Primary gradation color. | RGBA float color. | implementation |
| `BG Color` | Background color when background mode is enabled. | RGBA float color. | implementation |
| `Invert` | Inverts alpha/color ramp meaning. | Current implementation flips `X` when off before interpolation. | implementation |
| `Interpolation Mode` | Constant, Linear, Sphere, Power. | enum. | official manual + implementation |
| `Power` | Exponent for Power interpolation. | `pow(X, power)`. | implementation |
| `Blur Mode` | No Blur, Blur No Scale, Blur. | enum. | official manual + implementation |
| `Blur Size` | Gaussian blur radius base. | No Scale uses size as-is; Blur scales by `ds`. Constant+Blur doubles radius. | guarded / implementation |

## Kernel / Loop Shape

1. Convert source alpha to a binary mask: `alpha > 0`.
2. Build `d_alpha` as the binary nonzero-alpha mask.
3. Compute `ds = (ds_x + ds_y) * 0.5`, with fallback `1.0`.
4. Build normalized distance field `X`:
   - Inside: distance in mask.
   - Outside: distance in inverted mask.
   - Both: max of inside and outside normalized fields.
5. If Constant interpolation plus blur is active, convert `X` to
   `X >= 1.0 ? 1.0 : 0.0`.
6. If blur is active, apply separable Gaussian blur to `X`.
7. Compose each pixel:
   - if `Invert` is off, replace `X` with `1 - X`;
   - apply interpolation transform;
   - derive output alpha from In/Out mode;
   - choose RGB from Gradation Color or source layer;
   - write premultiplied-looking PNG output according to background mode.

## Distance / Boundary

Current port model:

- Distance primitive: exact Euclidean distance transform equivalent to OpenCV
  `DIST_L2`, precise mask.
- Threshold: truncate distances to threshold before normalization.
- Normalization: divide by actual maximum after truncation, with denominator at
  least `1.0`.
- Blur boundary: Reflect101/mirror.

These rules are plausible and guarded, but the remaining residual means exact
Windows OpenCV/helper details are not fully proven.

## Interpolation

- Linear: pass `X` through.
- Constant without blur: current port uses `X > 0 ? 1 : 0`, but this is now
  understood as a field-prep behavior, not a `FUN_181170870` compose behavior.
- Constant with blur: binary field is prepared before blur; no post-blur
  threshold is applied.
- Sphere: `sqrt(max(1 - (1 - X)^2, 0))`.
- Power: `pow(X, Power)`.

`FUN_181170870` and its 16/float sibling compose functions in the Windows AEX
confirm the Sphere and Power math shape. They also show the default invert
behavior: when the invert byte is zero, the distance value used for composition
is `1 - X`.

2026-06-19 negative probe:

- Removing the current non-blur Constant binarization to match only the visible
  `FUN_181170870` compose body badly worsened Constant+Background cases:
  `case_0020 mean 0.0561 -> 6.9951`, `case_0021 0.0562 -> 23.8661`,
  `case_0022 0.5240 -> 21.6286`, and `case_0023 0.0778 -> 4.5740`.
- Interpretation: the binary-visible compose function is not the whole
  Constant story. Constant-mode binarization likely happens upstream during
  field construction/packing, before `FUN_181170870` reads the field pixel.
  Do not remove the current Constant binarization without a runtime trace of
  that upstream stage.

## Binary Notes

- The AEX is statically linked with OpenCV 4.5.5; the decomp contains OpenCV
  source paths such as `C:\Users\devbuild\Documents\4.5.5\sources\...`.
- `FUN_181170380`/`FUN_181170280` prove the visible compose stage runs after a
  separate field-prep stage. The 8bpc wrapper passes `param_4 + 0x2c` to
  `FUN_181170870`, and the callback reads the distance value from the green
  byte of the field world. Therefore Constant interpolation and blur ownership
  must be proven upstream of compose.
- The presence of `cv::copyMakeBorder` and border-name strings proves OpenCV
  border helpers are available in the binary, but it does not by itself prove
  the exact DistanceGradation blur branch. Treat the current Reflect101 blur as
  an implementation-grounded hypothesis until a call/trace pins the arguments.
- The compose functions are stronger evidence than the blur/distance helpers:
  they directly show `powf`, `sqrt`, invert, render-mode color selection, and
  output scaling.

## Conformance Cases

| Case group | Bit depth | Expected status | Current result | Next evidence |
| --- | --- | --- | --- | --- |
| basic 12-case smoke | 8bpc | guarded | 2026-06-19 rerun passes current guard: worst `case_0007/0009 max=7 mean=0.0909`; residual remains | binary-ground distance normalization and compare against normalized Software refs |
| extended non-blur 16-case smoke | 8bpc | guarded | 2026-06-19 rerun passes current loose guard, but with large non-exact residuals: `case_0008 max=254`, `case_0011 max=254`, `case_0012 max=251`, `case_0020..0023 max=238` | binary-ground interpolation, Constant field-prep, and render-mode branch details before tuning |
| blur `case_0029` | 8bpc | guarded | 2026-06-19 rerun: `max=23 mean=0.2827`; tiny non-grounded improvement from Constant+Blur binary-field handling | trace/OpenCV 4.5.5 `distanceTransform` / `GaussianBlur` behavior |
| Constant field-prep witnesses `case_0020/0022/0029` | 8bpc | blocked on runtime proof | current Constant binarization is much closer than compose-pass-through, but not exact | Windows runtime trace package `distancegradation-field-prep` |

## Validation Packages

- Runtime trace request:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip`.
  This is the next implementation-proof artifact; use it before changing
  Distance/Constant/Blur semantics.
- Mac AE exact check, basic normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip`.
- Mac AE exact check, extended normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip`.
- Mac AE exact check, blur normalized Software refs:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip`.

The AE exact packages intentionally use zero thresholds. They are not evidence
of completion until returned Mac AE renders verify with `max_diff=0`.

## Open Questions

- Whether Windows AEX uses OpenCV `distanceTransform` directly or equivalent
  helper with subtle border/minmax differences.
- Exact threshold/minmax behavior on masks where threshold is not reached.
- Exact Gaussian blur kernel, anchor, radius, and border mode for every Blur
  Mode.
- Exact location and scope of Constant-mode field binarization before
  `FUN_181170870`.
- Whether PNG export premultiplication is masking AE-world straight/premul
  differences.
- 16bpc and 32bpc output rules.
