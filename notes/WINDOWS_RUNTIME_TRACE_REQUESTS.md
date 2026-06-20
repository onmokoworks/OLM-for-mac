# Windows Runtime Trace Requests

This page records debugger/runtime traces that are more useful than another
PNG render set. Use these only when static Ghidra/objdump facts and existing
Windows reference PNGs cannot distinguish a real port bug from an unmodeled
runtime state.

## OLMSmoother2 Legacy Key/Gamma Witness

Status: pending external Windows debugger trace.

Why this trace exists:

- The 2026-06-20 AE pixel rerun made standalone `OLMSmoother` v1 exact and kept
  the `OLMSmoother2` no-key grid exact, but legacy key/gamma slices still fail
  `0/7`.
- The failing legacy cases are not small edge residuals. They include full
  keep/drop polarity differences (`max=254`) and a no-key-looking case where
  alpha matches but RGB is too low in the Mac candidate.
- The recurring witnesses are top-edge pixels such as `(15,0)`, `(16,0)`,
  `(438,0)`, and `(439,0)`. That pattern points at legacy setup, mask polarity,
  premultiply/unpremultiply, gamma setup, or final writeback rather than the
  already exact no-key smoothing geometry.
- PNG-only tuning is especially risky here because the observed cases can be
  explained by several mutually incompatible rules. The trace must identify the
  active runtime state before implementation changes.

Reference report:

- `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json`

Priority witness cases:

| case | expected setup | witness | Mac candidate | Windows reference | why |
| --- | --- | --- | --- | --- | --- |
| `case_0001` | Color Key off, Smoothness 100, Range 2 | `(15,0)` | `[25,25,25,75]` | `[75,75,75,75]` | alpha matches, RGB ownership differs |
| `case_0002` | Color Key on, Invert on, Smoothness 100, Range 2 | `(15,0)` | `[0,0,0,0]` | `[75,75,75,75]` | Mac drops a pixel Windows keeps |
| `case_0003` | Color Key on, Invert off, Smoothness 0, Range 2 | `(15,0)` | `[75,75,75,75]` | `[0,0,0,0]` | Mac keeps a pixel Windows drops |
| `case_0010` | Color Key on, Extra 40, Range 22 | `(15,0)` | `[75,75,75,75]` | `[0,0,0,0]` | gamma/extra/range stress keeps wrong pixels |

Static addresses from image base `0x180000000`:

- Render/writeback loop: `FUN_1800036e0`, VA `0x1800036e0`
- Polygon builder: `FUN_18000c280`, VA `0x18000c280`
- Post unpremul/gamma/clamp: `FUN_18000b120`, VA `0x18000b120`
- Active-palette / scalar-key routines are documented in
  `notes/OLMSmoother2_ASM_FACTS.md`; if the exact symbol offset differs in the
  open Ghidra database, record the resolved address in the return.

Trace target:

1. Render `case_0001`, `case_0002`, `case_0003`, and `case_0010` with Windows
   AE Software renderer.
2. For each case, record the runtime parameter struct values:
   - Enable Color Key;
   - Color Key packed/decoded value;
   - Invert Color Key;
   - Smoothness;
   - Extra Smooth;
   - Smooth Range;
   - Smoother Version;
   - Gamma Correction / Num Gamma Colors;
   - any observed flags/offsets controlling premultiply or gamma.
3. For each witness pixel, record:
   - input RGBA before the effect;
   - RGBA after any unpremultiply step;
   - active-palette filter hit/value if that path is used;
   - scalar-key filter hit/value if that path is used;
   - whether the invert branch flips the keep/drop decision;
   - class-plane byte at the pixel and a small neighbor window;
   - whether `FUN_18000c280` runs and the switch index if it does.
4. Around final processing/writeback, record:
   - RGBA float values before `FUN_1800036e0`;
   - gamma or sRGB decode/encode steps hit for the case;
   - premultiply/unpremultiply step, if hit;
   - final byte conversion operation;
   - final 8bpc RGBA written by the AEX.

Interpretation:

- If `case_0002` keep/drop is inverted before smoothing, patch Color Key
  polarity or active-palette/scalar-key setup.
- If `case_0001` matches alpha but not RGB until final processing, patch
  premultiply/unpremultiply or gamma/writeback, not polygon geometry.
- If `case_0003` and `case_0010` differ before any smoothing call, patch mask
  classification before touching weights.
- If class-plane bytes and final floats match but final bytes differ, patch only
  final byte conversion.

## OLMSmoother2 No-Key Grid Polygon Witness

Status: optional external Windows debugger trace. The AE-host no-key grid is
already exact; this request is now for binary-grounding only, not for active
Smoother prioritization.

Why this trace exists:

- The no-key grid has three exact zero-smoothness cases, but nonzero
  smoothness cases still have small residuals (`max=4/8/9`).
- Static Ghidra confirms the residual hot cases `idx=0x08` and `idx=0x10`
  enter `FUN_180010820` (`cardinal3`) and then `FUN_1800105f0`
  (`cardinal12`).
- Mac diagnostic traces show those pixels emit two duplicate integer samples:
  - `idx=0x10`: source `(x-1,y)` with weights `0.40000001` and `0.2`
  - `idx=0x08`: source `(x+1,y)` with weights `0.32000002` and `0.2`
- The Windows Software reference is consistently stronger than the Mac
  candidate at these witness pixels. PNG-only tuning cannot safely decide
  whether Windows emits another duplicate sample, uses a different span formula,
  or matches the polygon and differs later in composite/writeback.
- Mac baseline trace for these four pixels is saved under
  `refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/`.
  Compare the returned Windows trace against those logs line-by-line before
  changing any implementation.

Witness case:

- Request: `smoother2_no_key_grid_20260606`
- Case id: `sm2_no_key_s100_r3`
- Reference frame:
  `refs/win_references/20260605_extra/OLMSmoother2/smoother2_no_key_grid_20260606__software__fr24__sm2_no_key_s100_r3.png`
- Before-effects frame:
  `refs/win_references/20260605_extra/OLMSmoother2/smoother2_no_key_grid_20260606__software__fr24__sm2_no_key_s100_r3_before_effects.png`

Trace pixels:

| pixel | Mac idx | Mac candidate | Windows reference | Mac observed appends |
| --- | --- | --- | --- | --- |
| `(211,139)` | `0x10` | `[203,66,66,255]` | `[212,68,68,255]` | `(210,139) w=0.40000001`, `(210,139) w=0.2` |
| `(215,145)` | `0x08` | `[54,34,34,255]` | `[46,32,32,255]` | `(216,145) w=0.32000002`, `(216,145) w=0.2` |
| `(991,139)` | `0x10` | `[212,194,57,255]` | `[221,202,59,255]` | `(990,139) w=0.40000001`, `(990,139) w=0.2` |
| `(995,145)` | `0x08` | `[56,53,33,255]` | `[47,45,32,255]` | `(996,145) w=0.32000002`, `(996,145) w=0.2` |

Static addresses from image base `0x180000000`:

- Polygon builder: `FUN_18000c280`, VA `0x18000c280`
- 3 o'clock cardinal entry: `FUN_180010820`, VA `0x180010820`
- 12 o'clock cardinal entry: `FUN_1800105f0`, VA `0x1800105f0`
- 12 o'clock dispatcher: `FUN_18000fbf0`, VA `0x18000fbf0`
- 3 o'clock dispatcher: `FUN_1800101e0`, VA `0x1800101e0`
- Append sample: `FUN_1800104d0`, VA `0x1800104d0`
- Scan helpers:
  - `FUN_18000d520`, VA `0x18000d520`
  - `FUN_18000dbd0`, VA `0x18000dbd0`
  - `FUN_18000d230`, VA `0x18000d230`
  - `FUN_18000d800`, VA `0x18000d800`
- Composite: `FUN_18000ab00`, VA `0x18000ab00`
- Post unpremul/gamma/clamp: `FUN_18000b120`, VA `0x18000b120`
- Render/writeback loop: `FUN_1800036e0`, VA `0x1800036e0`

Trace target:

1. Render `sm2_no_key_s100_r3` with Windows AE Software renderer.
2. For each trace pixel, record the `FUN_18000c280` switch index.
3. In `FUN_180010820`, record:
   - `FUN_18000d520` return `{x, y, class}`;
   - `FUN_18000dbd0` return `{x, y, class}`;
   - resulting `FUN_1800101e0` key.
4. In `FUN_1800105f0`, record:
   - `FUN_18000d230` return `{x, y, class}`;
   - `FUN_18000d800` return `{x, y, class}`;
   - resulting `FUN_18000fbf0` key.
5. For every scan helper call above, also record the boolean inputs and
   context around `FUN_180010550`:
   - index inputs `p1=CL`, `p2=DL`, `p3=R8B`;
   - idx=7 context values `p4=R9B`, `p5=[rsp+0x20]` / effective stack slot;
   - returned class.
   Current static reading says `FUN_180010550` indexes `p1 + p3*2 + p2*4`;
   idx `7` then jumps to a target that uses `p4 + p5*2` to return classes
   `6..9`. This is the highest-value place to catch a remaining descriptor
   mismatch.
6. Break on `FUN_1800104d0` for the current pixel and record every append:
   - source `(x,y)`;
   - sampled RGBA as raw float hex and decoded float;
   - weight as raw float hex and decoded float;
   - count before append.
7. Break around `FUN_18000ab00` and record:
   - center RGBA;
   - sample count and weights;
   - total sample weight;
   - output RGBA before `FUN_18000b120`.
8. Break around `FUN_18000b120` and record output RGBA after post-processing.
9. Break around `FUN_1800036e0` and record:
   - pre-sRGB RGB;
   - post-sRGB RGB;
   - final 8bpc RGBA written by the AEX.

Interpretation:

- If Windows emits three appends or a larger second weight, patch the relevant
  cardinal leaf/dispatcher path.
- If Windows polygon/composite matches Mac but final floats or final bytes
  differ, patch output color/writeback instead.
- If Windows switch index or descriptor differs, patch class-plane/scanner
  generation before touching weights.

## OLMDistanceGradation Field Prep / Constant Mode Witness

Status: pending external Windows debugger trace.

Why this trace exists:

- `OLMDistanceGradation` basic and extended smokes are guarded, but not exact.
- The largest extended residuals are concentrated in Constant interpolation,
  Background Color, Layer/RGB render-mode, and Both/Inside field ownership.
- Static compose decomp (`FUN_181170870`) shows Constant and Linear do not
  transform `X` inside the compose function. However, removing the current
  non-blur Constant binarization from the Python/Mac ports badly worsens the
  background Constant cases:
  - `case_0020 mean 0.0561 -> 6.9951`
  - `case_0021 mean 0.0562 -> 23.8661`
  - `case_0022 mean 0.5240 -> 21.6286`
  - `case_0023 mean 0.0778 -> 4.5740`
- Therefore Constant-mode binarization is probably upstream of
  `FUN_181170870`, in the field-prep path, not in the compose function itself.
  PNG-only tuning cannot prove where this happens or which channel carries the
  distance value.

Witness cases:

- Reference root:
  `refs/win_references/20260605_extra/OLMDistanceGradation`
- `case_0020`: Constant + Background + Inside, no blur.
- `case_0022`: Constant + Background + Both, small thresholds, no blur.
- `case_0029`: Constant + Blur, current binary-field-before-blur is guarded
  but not exact.

Trace pixels:

| case | pixel | Windows reference | current Mac/CLI candidate | why |
| --- | --- | --- | --- | --- |
| `case_0020` | `(951,417)` | `[28,0,238,255]` | `[255,0,0,255]` | Constant/background binary ownership |
| `case_0020` | `(952,417)` | `[28,0,238,255]` | `[255,0,0,255]` | nearby sanity |
| `case_0022` | `(4,0)` | `[28,0,238,255]` | `[255,0,0,255]` | Both + small threshold boundary |
| `case_0022` | `(28,0)` | `[28,0,238,255]` | `[255,0,0,255]` | nearby sanity |
| `case_0029` | `(524,783)` | `[15,0,126,135]` | `[17,0,147,158]` | Constant+Blur residual |
| `case_0029` | `(525,783)` | `[15,0,129,138]` | `[18,0,150,161]` | blur-neighborhood sanity |

Static addresses from image base `0x180000000`:

- 8bpc compose callback: `FUN_181170870`, VA `0x181170870`
- 8bpc iterate wrapper: `FUN_181170380`, VA `0x181170380`
  - requests `PF Iterate8 Suite`
  - passes user data `param_4 + 0x2c`
  - passes callback `FUN_181170870`
- 16bpc compose callback: `FUN_181170480`, VA `0x181170480`
- 16bpc iterate wrapper: `FUN_181170280`, VA `0x181170280`
  - requests `PF iterate16 Suite`
  - passes user data `param_4 + 0x2c`
  - passes callback `FUN_181170480`
- float compose callback: `FUN_181170c90`, VA `0x181170c90`
- OpenCV `distanceTransform` symbols/trace strings are present in the AEX.
- OpenCV `GaussianBlur` symbols/trace strings are present in the AEX.

Trace target:

1. Render `case_0020`, `case_0022`, and `case_0029` with Windows AE Software
   renderer.
2. For each listed pixel, record:
   - source input RGBA;
   - normalized distance field value before Constant-mode handling;
   - field value after Constant-mode handling;
   - for `case_0029`, field value before and after GaussianBlur;
   - the actual RGBA/Mat pixel consumed by `FUN_181170870`.
3. At `FUN_181170870`, record for each pixel:
   - field pixel bytes read from `param_1[1]` before `_X` is computed;
   - `_X` before invert, after invert, and after interpolation;
   - alpha base (`fVar16`) before final multiplication/write;
   - output RGBA floats before byte cast;
   - final RGBA bytes.
4. Record the exact branch that performs Constant-mode binarization, if hit:
   - before distance normalization;
   - after distance normalization;
   - only before blur;
   - or some other place.
5. Record the OpenCV/helper call arguments that create the field world:
   - `distanceTransform` input Mat type/size/channels;
   - `distanceTransform` distType, maskSize, dstType;
   - min/max or normalization denominator after thresholding;
   - whether thresholding clamps to UI threshold before min/max;
   - whether normalization divides by UI threshold or by actual max.
6. For `case_0029`, record the blur call arguments:
   - GaussianBlur input/output Mat type/size/channels;
   - ksize, sigmaX, sigmaY, borderType, anchor if traceable;
   - whether the blur radius is `Blur Size`, scaled by downsample, or doubled
     because Constant interpolation is active.
7. Record the field world pointer/rowbytes/dimensions passed into
   `FUN_181170870` through the iterate user data, and the field pixel bytes
   at each witness both immediately before the callback and after any blur.

Interpretation:

- If Constant non-blur is binarized upstream for all cases, keep the current
  non-blur Constant binarization and update the IR to describe the upstream
  stage, not compose.
- If only Background Color cases are binarized, split the current Constant
  rule by `Use Background Color`.
- If `FUN_181170870` consumes a channel other than green for the distance field
  in some modes, patch field packing/channel reads instead of interpolation.
- If `case_0029` confirms the current binary-before-blur shape, keep the blur
  residual focused on GaussianBlur kernel/radius/border, not Constant logic.

## OLMBlur Repeat Threshold Witness

Status: pending external Windows debugger trace.

Why this trace exists:

- Normalized Windows AE Software references now make `OLMBlur case_0001..0005`
  CLI exact.
- Matching the AEX non-Legacy radius path (`decay = powf(...)`, then
  per-iteration `pow(double,double)` and float sigma) reduced `case_0006` from
  6 residual pixels to 1.
- The remaining `case_0006` pixel is exactly on a float `.5` tie in the CLI:
  `(498,940)` has pre-writeback red `185.5` (`0x1.73p+7`) and writes `186`,
  while the Windows Software reference is `185`.
- `case_0007` is Legacy and remains 3 pixels off. Two tempting Legacy changes
  are rejected locally: initializing `all_same` from `-1` worsens to
  `max=16 / 21px`, and including border coordinate `0` worsens to
  `max=15 / 5412px`.
- Therefore the next useful proof is runtime pre-writeback / writeback /
  Legacy helper state at the residual coordinates, not another PNG render.
- Mac baseline trace for the normalized Software witnesses is saved under
  `refs/reports/olmblur_trace_baseline_20260619_030633_mac/` and should be
  compared line-by-line against the returned Windows trace.

Witness root:

- Normalized reference root:
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur`

Witness cases:

- `case_0006`: `Blur Amount=5`, `Blur Smoothness=100`, `Repeat=10`,
  `Bias Direction=1`, `Legacy=0`.
- `case_0007`: same parameters but `Legacy=1`.

Static facts:

- AEX writeback constant: `DAT_18000d24c == 0.5` (`0x3f000000`).
- AEX decomp writeback for 8/16bpc: `floorf(value + 0.5)`.
- Non-Legacy radius path:
  - `decay = powf(3.0 / blur_amount, 1.0 / (repeat - 1))`
  - `radius_d = (double)blur_amount * pow((double)decay, (double)iter)`
  - `radius = (int)radius_d`
  - `sigma = (float)radius_d / 3.0`
- Legacy helper border check appears to exclude coordinate `0`
  (`0 < coord < limit`) and should not be changed without runtime evidence.

Trace target:

1. Render `OLMBlur case_0006` with Windows AE Software renderer.
2. Break near the post-blur/pre-writeback buffer for 8bpc output, immediately
   before the `floorf(value + 0.5)` stores.
3. Record for `(498,940)`:
   - raw pre-writeback float RGB as hex and decoded float;
   - the actual writeback operation used by the CPU path;
   - final RGBA written by AEX.
4. Render `OLMBlur case_0007` with Windows AE Software renderer.
5. Record for `(0,0)`, `(488,941)`, `(488,942)`:
   - raw pre-writeback float RGB as hex and decoded float;
   - whether the Legacy horizontal/vertical helper includes border coordinate
     `0` for the relevant pass;
   - `all_same` state for the relevant helper invocation if practical;
   - final RGBA written by AEX.

Interpretation:

- If `case_0006 (498,940)` AEX pre-writeback red is below `185.5`, continue
  auditing accumulation order.
- If it is exactly `185.5` but writes `185`, the CPU writeback tie behavior is
  not the current CLI's `nearbyint` compatibility shim and must be modeled
  explicitly.
- If `case_0007` confirms `0 < coord < limit` and current `all_same` behavior,
  the remaining Legacy error is a narrower accumulation/writeback ordering
  issue. Do not patch border inclusion from PNG evidence alone.

Mac baseline values:

- `case_0006 (498,940)`: RGB
  `(185.5, 0.079257749, 0.079257749)`,
  hex `(0x1.73p+7, 0x1.44a3c6p-4, 0x1.44a3c6p-4)`.
- `case_0007 (0,0)`: RGB
  `(1.49396968, 1.49396968, 1.49396968)`,
  hex `(0x1.7e74ccp+0, 0x1.7e74ccp+0, 0x1.7e74ccp+0)`.
- `case_0007 (488,941)`: RGB
  `(250.499954, 0.00161030458, 0.00161030458)`,
  hex `(0x1.f4fffap+7, 0x1.a621b6p-10, 0x1.a621b6p-10)`.
- `case_0007 (488,942)`: RGB
  `(250.499985, 0.00162608409, 0.00162608409)`,
  hex `(0x1.f4fffep+7, 0x1.aa44a8p-10, 0x1.aa44a8p-10)`.

## OLMColorKey Edge Thin / Edge Blur Witness

Status: pending external Windows debugger trace.

Why this trace exists:

- Core RGB/color-space/Replace paths are exact in the returned Software
  references, but Edge Thin erode and Edge Blur still have residuals.
- Static Ghidra confirms Edge Blur distance dispatch by `ctx+0x44` and rejects
  the old PNG-fit `Distance Type 1 == Euclidean` hypothesis.
- Static Ghidra also shows positive Edge Thin copies when `dist <= amount`;
  changing that to `< amount` improves one PNG but contradicts the observed
  branch unless the runtime ctx amount or distance scale differs.
- Therefore the next useful proof is runtime ctx/local buffer ownership around
  the residual case, not another PNG-only tuning pass.
- Mac baseline trace logs for the normalized Software edge witnesses are saved
  under `refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/`.
  Compare Windows trace values against those logs before changing Edge Thin or
  Edge Blur semantics.

Witness cases:

- Normalized reference root:
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey`
- Edge Thin erode legacy cases:
  - `case_0005`: high-diff top-edge alpha witness `(34,0)` where current C++
    candidate is transparent but Windows reference is opaque.
  - `case_0006`: paired color-keep polarity witness `(34,0)` where current C++
    candidate is opaque but Windows reference is transparent.
  - Also useful: `(421,0)`, `(993,0)`, `(421,1)` if batch tracing is easy.
- Edge Blur cases:
  - `case_0008`: alpha/RGB contour witness around `(1111,628)` and top-edge
    alpha witness around `(464,0)`.
  - `case_0009`: known high-diff opaque/transparent neighborhood around
    `(1116,136)`.
  - Extra top-edge sanity sample: around `(1699,7)`.

Static addresses from image base `0x180000000`:

- Edge Thin / Edge Blur orchestration: `FUN_1800094b0`, VA `0x1800094b0`
- Boundary seed builder: `FUN_180008c90`, VA `0x180008c90`
- Edge Thin erode/dilate helper: `FUN_180008320`, VA `0x180008320`
- Edge Blur apply helper: `FUN_1800085b0`, VA `0x1800085b0`
- Edge Blur weight helper: `FUN_1800049a0`, VA `0x1800049a0`
- Distance dispatch targets:
  - `ctx+0x44 == 1` -> `FUN_180006e20`
  - `ctx+0x44 == 2` -> `FUN_180005d60`
  - `ctx+0x44 == 3` -> `FUN_180007ec0`

Trace target:

1. Render `OLMColorKey case_0005`, `case_0006`, `case_0008`, and `case_0009`
   with Windows AE Software renderer.
2. Break on `OLMColorKey.aex + 0x94b0`.
3. Record ctx fields from the `FUN_1800094b0` ctx pointer:
   - `ctx+0x28`
   - `ctx+0x2c`
   - `ctx+0x40` as raw float hex and decoded float
   - `ctx+0x44`
   - `ctx+0x48` as raw float hex and decoded float
4. For `case_0005` and `case_0006`, break around `FUN_180008320` and record
   at `(34,0)` plus one non-edge witness if practical:
   - input matched/keep matte byte;
   - distance transform input seed byte;
   - distance value;
   - ctx amount as decoded float;
   - branch decision and final output matte/alpha.
5. Step or break around `FUN_180008c90` for `case_0008` and `case_0009` and
   record the input matte and output boundary-seed values at:
   - `(1111,628)` and a 3x3 neighborhood if practical;
   - `(1116,136)` and a 3x3 neighborhood if practical;
   - `(1699,7)` and a 3x3 neighborhood if practical.
6. Break on the selected distance transform branch and record the distance
   value written for the same coordinates.
7. Break around the positive Edge Thin copy test and record whether the actual
   runtime branch copies for `dist == amount`, or only for `dist < amount`.
8. Break around `FUN_1800085b0` / `FUN_1800049a0` and record, for the same
   coordinates:
   - whether the pixel is considered inside/keep at the weight function input;
   - the distance consumed by the weight function;
   - the returned weight;
   - the source RGBA and final output RGBA.

Interpretation:

- If ctx amount or distance values differ from the manifest by one pixel or by
  downsample scaling, patch parameter normalization.
- If `FUN_180008c90` seed ownership differs from the static read, patch boundary
  construction.
- If `FUN_1800085b0` applies the weight to unpremultiplied RGB or preserves a
  minimum RGB differently, patch Edge Blur application.
- If the trace confirms current static facts and no missing runtime state, the
  remaining work is deeper decomp of `FUN_1800085b0`, not PNG fitting.

Mac baseline highlights:

- Edge Thin `case_0005` / `case_0006` top-edge witnesses have
  `matched0=1`, `matched1=0`, `edge_thin_amount=-16`,
  `edge_thin_limit=17`, and `edge_thin_dist=17`.
  This is exactly the ambiguous equality boundary.
- Edge Blur `case_0008 (1111,628)` has `keep=1`, `boundary=0`,
  `edge_blur_dist=14`, `edge_blur_weight=0.447735757`, final
  `(114,0,0,114)`.
- Edge Blur `case_0009 (1116,136)` has `keep=1`, `boundary=0`,
  `edge_blur_dist=25`, `edge_blur_weight=1`, final `(0,0,0,255)`.

## OLMRadialBlur Inner Span Witness

Status: pending external Windows debugger trace.

Why this trace exists:

- `radialblur_inner_20260605` and the filtered/full SOFTWARE returns already
  cover the useful PNG evidence for Inner.
- Static Ghidra reads show no `span - 1` rule in the helper, but the
  diagnostic `--inner-scatter-span-minus-one` improves the low-span witness by
  removing exactly one neighbor write per active source.
- The next useful fact is therefore the runtime value entering the helper, not
  another render.

Witness case:

- Request: `refs/reference_requests/radialblur_inner_20260605.json`
- Case id: `rb_inner_only_strength_small`
- Reference frame:
  `refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_filtered_software/OLMRadialBlur/radialblur_inner_20260605__software__fr24__rb_inner_only_strength_small.png`
- Before-effects frame:
  `refs/win_references/olm_reference_return_windows_20260617_radialblur_inner_filtered_software/OLMRadialBlur/radialblur_inner_20260605__software__fr24__rb_inner_only_strength_small_before_effects.png`

Static addresses from image base `0x180000000`:

- Helper: `RadialBlur_scatter_tail_by_direction`, VA `0x180001c90`, RVA
  `0x1c90`
- Caller: `RadialBlur_scatter_valid_polar_cells`, VA `0x1800024c0`, RVA
  `0x24c0`
- Outer call: VA `0x180002689`, RVA `0x2689`
- Inner call: VA `0x1800026e5`, RVA `0x26e5`
- Inner caller distance compute: VA `0x1800025d6..0x1800025e1`, RVA
  `0x25d6..0x25e1`
- Effective span compute in helper: VA `0x180001d0f..0x180001d18`, RVA
  `0x1d0f..0x1d18`
- Gaussian table divisor: VA `0x180001d33..0x180001d43`, RVA
  `0x1d33..0x1d43`

Trace target:

1. Break on `OLMRadialBlur.aex + 0x26e5` for the `rb_inner_only_strength_small`
   render.
2. When hit, record:
   - actual module base for `OLMRadialBlur.aex`
   - `R8D`
   - `[rsp+0x138]`
   - `EDX`
   - `R9D`
   - `[rsp+0x48]` as float (`source_alpha`)
   - `[rsp+0x28]` as float (`span_gate` / param10)
   - `dword ptr [RCX+0x2c]` (`inner offset mode`)
   - `dword ptr [RCX+0x3a9ec]` (`inner base span`)
3. Step into this exact inner call (`EDX == 1`) at
   `OLMRadialBlur.aex + 0x1c90`. Do not use a broad helper breakpoint unless it
   is filtered to the inner direction; the outer call immediately before it also
   enters the same helper.
4. Run to after `OLMRadialBlur.aex + 0x1d18` inside that inner invocation and
   record `R14D`. At this point `EBP` should still identify the direction copied
   from entry `EDX`, so `EBP == 1` is a useful sanity check that the captured
   helper instance is the inner path.
5. Optional: run to after `OLMRadialBlur.aex + 0x1d43` and record `EAX` /
   `XMM7` as the table step (`30000 / R14D` converted to float).

Interpretation:

- If `R14D == 31`, the C++ caller/setup is missing a runtime adjustment before
  or inside the helper. Patch the caller/span setup, not the helper loop blindly.
- If `R14D == 32`, keep `--inner-scatter-span-minus-one` diagnostic-only and
  look for an unmodeled write/pointer/edge detail instead of promoting a span
  decrement.

Manual WinDbg sketch:

```text
lm m OLMRadialBlur
bp OLMRadialBlur+0x26e5
g
r r8d edx r9d
dd @rsp+0x138 L1
dd @rsp+0x48 L1
dd @rsp+0x28 L1
dd @rcx+0x2c L1
dd @rcx+0x3a9ec L1
t
bp OLMRadialBlur+0x1d18
g
r ebp r14d eax
```

The `dd @rsp+0x48 L1` and `dd @rsp+0x28 L1` outputs are raw IEEE-754 float
hex for `source_alpha` and `span_gate`. Raw hex is preferred over a brittle
`.printf %f` expression because WinDbg float formatting varies by evaluator.
If the helper breakpoint at `+0x1d18` is left enabled globally, ignore hits
where `EBP != 1`.

## OLMKiraKira OpenCV 4.5.5 Primitive Witness

Status: first branch fact answered; next trace is `FUN_181150790` stage values.

Why this exists:

- `kirakira_single_ray_20260606` and `kirakira_strength0_brightness_20260614`
  are already covered.
- Current refs separate ray order, angle table, merge mode, zero-length rays,
  Strength=0 brightness scale, and helper-scalar non-use for merge mode 1.
- Static Ghidra/objdump facts reject the broad remaining toggles: centered
  Rect/copy/dsize swaps, simple `boxFilter` ksize/anchor/border/normalize
  changes, map/remap fixed-point split alone, box accumulation precision, and
  final one-pixel crop offsets.
- The active residual is now likely inside exact OpenCV 4.5.5 FilterEngine /
  `boxFilter` behavior, or a small pre/post ray detail not covered by current
  toggles. Same-Mat `warpAffine` alias destruction is rejected: `FUN_181297ac0`
  compares source/destination data pointers and clones/redirects the source
  before fallback sampling when they alias.
- Baseline CV_32F `boxFilter` accumulator precision is also pinned:
  `FUN_181280fa0` uses `RowSum<float,double>` plus
  `ColumnSum<double,float>`, so the current C++ double-accumulator path is the
  right baseline model. Do not spend the Windows pass re-testing float vs double
  box accumulation.

Useful evidence sources:

1. Open `OLMKiraKira.aex` in Ghidra and continue the embedded OpenCV 4.5.5
   primitive audit around:
   - `FUN_181150790`: OLM ray helper choreography
   - `FUN_181297ac0`: `cv::warpAffine`
   - `FUN_181293ad0`: `WarpAffineInvoker::operator()`
   - `FUN_181297270`: `cv::remap`
   - `FUN_181288940`: float `remapBilinear`
   - `FUN_181280bc0`: `cv::boxFilter` wrapper
   - `FUN_181281260`: FilterEngine CPU feature dispatch
   - `FUN_1812e39d0` / `FUN_1812d7c40` / `FUN_181280fa0`: optimized vs
     baseline FilterEngine constructors
2. Or build a separate OpenCV **4.5.5-linked** microprobe that runs exactly:
   - centered ROI copy into tempA
   - API-level `cv::warpAffine(tempA, tempA, M, tempA.size(), INTER_LINEAR,
     BORDER_CONSTANT)`, expecting OpenCV's internal alias-safe source clone
   - `cv::boxFilter(tempA, tempB, ddepth=-1, ksize=(length,1),
     anchor=(-1,-1), normalize=true, borderType=BORDER_REFLECT_101)`
   - subsequent blur passes in the same temp choreography used by the AEX
   - API-level `cv::warpAffine(tempB, tempB, inverseM, tempB.size(),
     INTER_LINEAR, BORDER_CONSTANT)`, again expecting alias-safe source clone
   - centered ROI copy from tempB to the ray output

If tracing/debugging the AEX directly, record which `FUN_181281260` branch is
used for the first `boxFilter` pass on the single-ray diagonal case:

- feature `0xb` true -> `FUN_1812e39d0`
- feature `6` true -> `FUN_1812d7c40`
- neither -> baseline `FUN_181280fa0`

Also record whether the selected branch constructs the same logical
`RowSum<float,double>` / `ColumnSum<double,float>` filters or a SIMD-specialized
equivalent.

Current Mac environment note:

- default `python3` has no `cv2`
- `/tmp/olm_cv_probe_venv` has OpenCV `4.13.0`, which is shape evidence only
- stale `/tmp/olm-opencv455-venv` no longer imports `cv2`
- no local `pkg-config opencv4` or Homebrew C++ OpenCV libraries were found

Interpretation:

- If an exact OpenCV 4.5.5 microprobe reproduces the AEX residual pattern
  better than the hand-written C++ `aex-two-temp` path, port that primitive
  behavior into the CLI/Mac implementation.
- If exact 4.5.5 still matches the current residual, keep `aex-two-temp`
  diagnostic and inspect pre/post ray details around `FUN_181150790` and the
  aggregation call sites instead of adding more high-level warp/box toggles.

2026-06-20 status update:

- The first `boxFilter` branch is already answered by runtime trace:
  `FUN_1812e39d0` / OpenCV 4.5.5 AVX2.
- Recreated `/tmp/olm_cv455_probe_venv` and reran the OpenCV 4.5.5 probes.
  The single-ray guarded residual remains `max=13/23/66`, and old three-case
  OpenCV two-temp remains `case_0003 max=26 mean=1.0477`.
- `opencv-two-temp-alias-roi` is byte-equivalent to ordinary two-temp for the
  old three-case set, so same-ROI aliasing remains rejected.
- The new overnight package is:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip`.
- The focused Windows action bundle is:
  `handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`.

Next trace target:

1. Render `kirakira_single_ray_20260606` case
   `kk_vertical_len50_brightness1_strength100` with Windows AE Software.
2. Trace `FUN_181150790`.
3. Record both `warpAffine` Mat headers, `dsize`, affine matrices, and
   source/final ROI copy rectangles.
4. Record witness float values before/after center-copy, forward warp, each of
   the three horizontal `boxFilter` passes, rotate-back, and final center-copy.
5. Record `FUN_18114fd90` aggregation inputs/outputs and final merge-mode-1
   compose samples.

Template note:

- The 2026-06-20 package keeps legacy `xy` fields but also asks for
  `source_xy`, `tmp1_xy`, `tmp2_xy`, and `ray_xy` so Windows stage samples can
  be compared against the Mac trace baseline without guessing which coordinate
  space a value came from.

Interpretation for this newer trace:

- If stage values diverge immediately after forward `warpAffine`, the port
  should focus on Mat header/dsize/ROI or affine matrix placement.
- If values first diverge inside the three box passes, the remaining gap is the
  AVX2 OpenCV helper behavior.
- If the ray buffer matches but final output differs, focus on aggregation or
  merge-mode compose instead of the ray helper.
