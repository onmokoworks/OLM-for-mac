# OLM Plug-in Intent Map

This note is the fast-reading layer before decomp/asm work. It maps each
plug-in's user-facing intent and UI parameters to the likely algorithm family,
so reverse-engineering starts from "what this effect is supposed to do" instead
of raw functions only.

Source priority for this file:

1. Official OLM OpenTools pages and bundled PDF manuals under
   `refs/upstream_official/20260619_olm_official_zips/`.
2. Local plug-in string tables under `mac/*/*_Strings.cpp`.
3. PiPL names/match names under `mac/*/*PiPL.r`.
4. Decompiled AEX strings where they add a clearer product description.
5. Existing binary-grounded notes for current uncertainty.

Do not treat this as an exactness proof. It is a triage/index document.
For the policy on using this map before new PNG/runtime returns arrive, see
`notes/FORECAST_FIRST_PORTING_POLICY.md`.

## Overview

| Plug-in | Local description / product wording | Main UI controls | First algorithm model | Main RE value |
| --- | --- | --- | --- | --- |
| ColorKeep | Official manual: inverse color key; affects alpha by keeping only listed colors. | Enabled Color Num, Color | Multi-color equality/threshold keep mask; alpha becomes selected-color matte. | Small helper; useful for shared color handling expectations. |
| OLMBlur | Official manual: blurs pixels with `alpha > 0`; with Color Key, blurs only boundaries between specified colors. | Blur Amount, Blur Smoothness, Number of Repeat, Bias Direction, Legacy | Alpha-masked repeated blur, with bias direction and color-key boundary workflow. | Read radius/decay/repeat/writeback, then alpha/boundary behavior. |
| OLMColorKey | "Port of OLM Color Key." | Color Keep, Threshold, Premultiplied Color, Color Space, Per Color/Component, Edge Thin, Distance Type, Edge Blur, Replace colors | Multi-color keyer plus matte morphology/distance blur and optional replacement paint. | Split core keying from Edge Thin/Blur; edge path is separate. |
| OLMToonDilate | Official manual: dilates non-transparent regions toward transparent borders. | Search Radius | Radius-limited fill of transparent pixels from nearby non-transparent colors. | Small enough to ground with loop/order and alpha premultiply rules. |
| OLMDistanceGradation | Official manual: inside/outside mask gradation from alpha channel distance. | In/Out, thresholds, RGB/Layer, grad/BG colors, interpolation mode, Power, Blur Mode, Blur Size | Distance-map normalization, interpolation, optional post blur. | Start from distance primitive/interpolation parameters rather than pixel fitting. |
| OLMSmoother | Official manual: smoothing cel animation drawings. | Use Color Key, Color Key, Smooth Length Tolerance / Smooth Range | Cell-animation line smoothing with optional color key and gradation tolerance. | Likely covered through Smoother2 compatibility unless v1 AE exactness is required. |
| OLMSmoother2 | Official manual: v2 adds color space conversion, improved diagonal smoothing, gamma correction, 32-bit support. | Use Color Key, Smoothness, Extra Smooth, Smooth Range, Smoother Version, Gamma Correction, Gamma colors | Expanded line/image smoother with sRGB-linear path and gamma-aware blend. | Split key/no-key, v1/v2, smooth range, gamma modes. |
| OLMDirectionalBlur | Official manual: special anisotropic directional blur, ignores fully transparent pixels. | Angle, Brightness Gain, Size Variation, front/back strength, edge fade, sharp tail, noise variation | Two-sided directional blur over opaque pixel groups, with per-group size variation and per-pixel noise. | Treat as group-aware line sampling/scatter, not generic Gaussian blur. |
| OLMRadialBlur | Official manual: anisotropic zoom/rotation blur, ignores fully transparent pixels. | Blur Type Zoom/Rotation, Center, Outer/Inner Strength, Repeat Border, Ratio, Angle, Quality, Brightness Gain, Size/Noise Variation | Polar zoom/rotation blur with outward/clockwise and inward/counterclockwise components, group-aware variation, noise. | Split Zoom, Rotation, Inner, EdgeFade/variation; shared code can mislead. |
| OLMKiraKira | Official manual: generate glow from highlights using vertical, horizontal, and diagonal blur. | Channel, Blur Mode, Merge Mode, Approx Input, Threshold, Fade Out, lengths/colors/ramp, Highlight Radius, Glow Rotation | Star/glint generator: derive highlight channel, run directional blur passes, color/ramp, merge over source. | Read OpenCV/filter primitive choices before tuning ray order/scalar aggregation. |

## Plug-in Notes

### ColorKeep

- Official manual: affects alpha by keeping only the given color list; it is the
  inverse of color key.
- Params are minimal: enabled color count plus repeated color values.
- Likely not a hard algorithm path; useful mainly as a shared color-selection
  sanity check for ColorKey/Smoother semantics.

### OLMBlur

- Official manual says OLM Blur applies blur to not-fully-transparent pixels
  (`alpha > 0`). The Color Key workflow explains why boundary-only blur is
  possible: Color Key creates the relevant alpha/matte region, then Blur respects
  that region.
- UI already points to the important axes:
  - `Number of Repeat`: repeated application; current residual is repeat-10.
  - `Bias Direction`: vertical/horizontal path split.
  - `Legacy`: separate compatibility branch.
- Current RE focus:
  - radius decay formula,
  - per-repeat accumulation order,
  - border/division preservation,
  - final float-to-8bpc writeback.

### OLMColorKey

- This should be split into features before implementation:
  - core keying and keep/remove,
  - color-space distance,
  - per-component threshold,
  - replace color,
  - Edge Thin morphology,
  - Edge Blur distance/weighting.
- Official manual says color comparison supports `RGB`, `HSV`, `Lab`, `YUV`,
  and `YCrCb`, and `Force Lower Precision` intentionally reduces keying
  precision so low-precision preview and high-precision render can match.
- The UI's `Distance Type = Box|Approximate|Euclidean` is important: it points
  to distance-transform style matte processing, not just RGB thresholding.
- `Edge Thin` extends/reduces the keyed region; `Edge Blur` adjusts alpha around
  the keyed border and has `Inside`, `Outside`, and `Around` directions.
- Current hard part is not the core keyer; it is Edge Thin/Edge Blur.

### OLMToonDilate

- Official manual describes the effect as expanding non-transparent image
  regions toward transparent pixels. Single `Search Radius` UI is a strong hint
  that the core is a radius-limited propagation/dilation rather than many
  independent modes.
- The main exactness knobs are:
  - propagation pass order,
  - distance metric,
  - semi-alpha RGB/premultiply behavior,
  - boundary handling.

### OLMDistanceGradation

- Official manual describes gradation inside/outside the alpha-channel mask.
  Existing local description says distance transform. Anchor the IR around a
  distance map, normalization, interpolation, then optional blur.
- UI feature split:
  - mask side: Invert, In/Out, inside/outside thresholds,
  - output source: RGB vs Layer, gradation/BG colors,
  - interpolation: Constant, Linear, Sphere, Power,
  - postprocess: Blur Mode and Blur Size.
- Official manual says `Blur No Scale` is simple blur and `Blur` adds scaling to
  preserve more detail; this is a concrete branch to verify against binary
  constants/primitive calls.
- Fast path: identify OpenCV distance/blur primitive parameters first, then
  test interpolation and normalization.

### OLMSmoother / OLMSmoother2

- v1 official manual says cell-animation drawing smoothing. v2 official manual
  says v2 adds color space conversion, improved diagonal smoothing, Smoothness,
  Extra Smooth, Gamma Correction, MFR support, and 32-bit support.
- v2 manual says `Smoother Version = v1|v2` only affects how Gamma Correction is
  applied, and v1 does not linearize color before processing. That narrows the
  v1/v2 split; do not assume every smoothing branch differs.
- Feature split:
  - no-key smoothing,
  - color-key smoothing,
  - invert-key path,
  - gamma correction path,
  - v1/v2 mode path.
- `Smooth Range` treats nearby colors as same-color for gradated drawings; the
  manual states that `255` makes output identical to input, so this parameter
  has a hard short-circuit/identity case to verify.

### OLMDirectionalBlur

- Official manual says the effect is anisotropic, blurs both sides with
  different intensities, and ignores fully transparent pixels.
- Front/back controls mean the blur is directional and asymmetric:
  `Front Blur Strength` and `Back Blur Strength` should be modeled separately.
- `Size Variation` changes blur strength according to the size of each opaque
  pixel group, with overlapping opaque pixels considered one group. This implies
  a connected-component or equivalent grouping stage.
- `Edge Fade` is synchronized with size variation, and `Sharp Tail` is
  calculated for each opaque group. These are per-group/per-sample weight rules,
  not one convolution kernel.
- Noise modes are `Smooth`, `Block`, and `Layer`; layer noise maps brighter
  pixels to bigger blur strength. Keep procedural noise separate from the base
  line sampler while reading the binary.

### OLMRadialBlur

- Official manual says the effect is anisotropic: zoom blur uses different
  toward/outward-center strengths, rotation blur uses different clockwise and
  counterclockwise strengths, and both ignore fully transparent pixels.
- Product split is explicit: `Blur Type = Zoom|Rotation`.
- The UI has distinct outer and inner controls, so Inner should be its own
  feature path in the ledger. Outer means outward/clockwise; Inner means
  inward/counterclockwise.
- `Repeat Border` prevents boundary fading when `Edge Fade` is used; this makes
  edge behavior an explicit branch rather than a hidden clamp choice.
- `Ellipse` ratio/angle and `Quality` affect the polar-to-ellipse transform; keep
  them separate from the blur span until binary proof says otherwise.
- `Offset Mode = Add|Max|Replace` suggests dynamic per-pixel span/offset
  composition rather than a single global radius.
- `Quality` likely participates in span/table scaling; do not hide it in a
  generic "sample count" variable without binary proof.

### OLMKiraKira

- Official manual says KiraKira generates glow from picture highlights by
  combining vertical, horizontal, and diagonal blur from alpha, luminance, or
  RGBA-derived channels.
- UI tells a high-level pipeline:
  1. derive highlight strength from `Channel` (`Alpha`, `Luminance`, `RGB`,
     `Brightness`),
  2. apply `Threshold` / `Fade Out`,
  3. create vertical/horizontal/diagonal rays and highlight radius,
  4. apply per-direction color or ramp,
  5. apply glow/source opacity,
  6. merge by additive weighted sum or premultiplied weighted average.
- Official manual names `Blur Mode` choices: `Box`, `Approximated Gaussian`,
  `Gaussian`, and `Exponential`. This is the main primitive-discovery axis.
- Length/radius zero skips the corresponding process; preserve those skip
  branches as separate conformance cases.
- Because decomp shows embedded OpenCV strings and current residuals are helper
  fidelity issues, this should be read as an OpenCV primitive recreation problem
  for the ray blur/warp steps, not just a hand-written star filter.

## How To Use This

For each plug-in, do the fast pass in this order:

1. Read the row above and decide feature slices.
2. Build or update the binary-grounded IR per slice.
3. Locate parameter setup in decomp and match disk IDs/UI names.
4. Locate the render kernel and confirm the expected primitive family.
5. Implement the coarse C++ model only after the feature slice is named.
6. Use PNG differences to find the wrong slice, not to invent the whole spec.
7. Use runtime trace only for the final ambiguous values: rounding, bounds,
   selected OpenCV branch, helper span, or sample ordering.
