# OLMKiraKira ASM Facts

This page records objdump-first facts for the OLMKiraKira port. Treat Ghidra
decompilation as a map, not as proof. Treat Windows PNGs as verification data,
not as an algorithm source.

## 2026-06-14 Single-Ray References (DISENTANGLED AXES)

New software single-ray refs in
`refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira/`
finally separated the entangled axes. Case matrix (all Channel=2, Blur Mode=2,
Merge mode=1, Glow Opacity/Source Opacity=100, comp 1920x1080):

- `kk_{vertical,horizontal,diagonal,diagonal2}_len50_brightness1_strength100`:
  exactly ONE ray active at length 50, Brightness Gain=1, Strength=100.
- `kk_{...}_len50_brightness94_strength0`: one ray length 50 but Strength=0
  (so NO ray), Brightness Gain=9.4 (the "94" label = 9.4, not 94).
- `kk_diagonal_len50_rotation13`: diagonal ray, Glow Rotation=13.

(Note: GPU Rendering=1 even in the SOFTWARE render set — the usual reference
caveat. The matches below are still byte-exact on the strength=0 compose, so
the software path is faithful there.)

### CONFIRMED: compose is a screen blend, alpha passthrough

The merge-mode-1 compose is, per channel:

```
out_rgb = 1 - (1 - src_rgb) * (1 - glow_rgb * glow_a)   // SCREEN
out_a   = src_a                                          // glow does NOT add alpha
```

Proof: the four `strength=0` refs are spatially AND channel uniform with an
effective screen-glow of 0.498 regardless of source color; feeding glow=0.498
into the screen formula reproduces every pixel to `max_diff=0` (exact window
0.498..0.4995). The old `aex-premul` (divide-by `src_a+glow_a`) was wrong.
Implemented as CLI `--compose-mode aex-screen-over` and made the default.

### CONFIRMED: zero-length rays contribute nothing

`FUN_18114f4a0` @ 3524019 guards each ray with `if (iVar6 != 0) { build ray }`
where `iVar6` is the per-ray length. A length-0 ray is skipped entirely. The
previous CLI box-blurred with length 0, which returns the raw seed, so all four
ray buffers were active simultaneously and the glow was ~quadrupled
(1-(1-x)^4). Fix: emit an all-zero buffer for any ray with raw length <= 0
(`make_ray` lambda in `apply_kirakira`). This alone moved the strength100 ray
cases from max~135/mean~26 to max~13/mean~1.4.

### CONFIRMED: per-ray helper scalar is NOT used by merge-mode-1 aggregator

`FUN_18114f4a0` stores `*pfVar8 = FUN_181150790(...)` into the `local_2a8`
scalar array and the `length^2` square only into the layer-4 (highlight)
entry, but the aggregator dispatch passes the RAY POINTER array `local_290`
(plus brightness) — `local_2a8` is never handed to `FUN_18114fd90`. So the
helper-return scalar / `length^2` does not affect merge-mode-1 output. This
removes a long-standing ambiguity.

### CONFIRMED .rdata constants (binary read, image base 0x180000000)

- `DAT_181486c20 = 1.0f` — fd90 RGB normalize numerator (`rgb *= 1.0/alpha`).
- `DAT_181489990 = 0.001` (double) — fd90 skip epsilon (`ray <= 0.001`).
  (CLI currently uses 1e-6; immaterial at 8-bit but should be 0.001.)
- `DAT_181486c1c = 0.5f` — helper half-size center factor.
- `DAT_18148b840 = 0x7fffffff` — abs-value mask for cos/sin in canvas sizing.
- `DAT_18148b830 = 4.0f` — used in the rotate-canvas dimension formula.

### fd90 brightness arg

`FUN_18114fd90` param_10 (the `ray * param_10` gain before clamp) is loaded in
asm at `18114fc34: MOVSS XMM0,[RBP+0x608]` and passed at `[RSP+0x48]` for both
the `+0x08` and `+0x10` dispatch. `[rbp+0x608]` is set earlier in
`FUN_18114f4a0` from the effect params; its exact transform from Brightness
Gain was not fully traced this pass (see blocker below).

### MEASURED (software cases) before -> after this pass

Command: `--seed-mode aex --falloff box3 --gain-scale 0.62 --ray-mode
axis-rotate --compose-mode aex-screen-over --filter-border mirror
--auto-length-scale --comp-width 1920`

| case | before max/mean | after max/mean |
|---|---|---|
| vertical   b1 s100 | 135/25.88 | 13/1.39 |
| horizontal b1 s100 | 133/26.11 | 13/1.42 |
| diagonal   b1 s100 | 142/25.71 | 43/1.70 |
| diagonal2  b1 s100 | 138/25.71 | 45/1.69 |
| rotation13         | 139/25.76 | 76/1.84 |
| vertical   b9.4 s0 | 113/27.76 | 113/27.76 |
| horizontal b9.4 s0 | 113/27.76 | 113/27.76 |
| diagonal   b9.4 s0 | 113/27.76 | 113/27.76 |
| diagonal2  b9.4 s0 | 113/27.76 | 113/27.76 |

The axis-aligned ray residual (max~13) is now the box-blur shape (3-pass
uniform box vs OpenCV `boxFilter` REFLECT_101/anchor) — an OpenCV-primitive
residual, not a compose/seed error. An offline numpy reimplementation of the
exact CLI box reproduces the CLI ray to the float, and the screen model then
lands mean~1.3, confirming the residual is the box approximation. Diagonal /
rotation residual (43-76) is the warp path, still the hardest axis.

### REMAINING BLOCKER: strength=0 uniform glow = 0.498

With Strength=0, AEX emits a uniform glow of 0.498 (white RGB, alpha 0.498),
independent of source. In our model seed = `luma^exponent * a`; exponent 0 =>
seed=1 uniform, so `glow = clamp01(1 * scale)`. To hit 0.498 the effective
`scale` at strength=0 must be ~0.498, NOT Brightness Gain (9.4) and NOT
`9.4 * gain_scale` (which would clamp to 1 = white). The CLI still produces
white here, so the 4 strength0 cases stay at max=113.

This cannot be resolved from the refs in hand: there is only ONE
brightness/strength=0 sample (9.4 -> 0.498), so the Brightness-Gain ->
fd90-`param_10` transform at strength=0 is underdetermined (0.498 fits b/(b+9.5),
1-exp(-ln2), and many others equally). Resolving it requires either (a) tracing
the `[rbp+0x608]` write in `FUN_18114f4a0` to the exact Brightness-Gain
expression, or (b) a second strength=0 reference at a different Brightness Gain.
Do NOT PNG-fit a single 0.498 constant — it would silently hardcode one
brightness value.

## Current Reference Slice

Current C++ smoke command:

```sh
python3 refs/scripts/smoke_olmkirakira_cpp_cli.py
```

Current expected-red measurements:

- `case_0001`: `max=22 mean=0.8381 nz=302781/518400`
- `case_0002`: `max=24 mean=1.1623 nz=1373909/2073600`
- `case_0003`: `max=60 mean=1.7003 nz=1367180/2073600`

The current reference cases are all `Blur Mode=2`, `Channel=2`,
`Merge mode=1`, `Highlight Radius=0`, `Glow Rotation=0`, and ray lengths
`50/50/50/50`.

## FUN_181150790: Ray Helper Overview

`FUN_181150790` is the ray helper used by the four directional rays.

Caller setup in `FUN_18114f4a0`:

- `18114f90f..18114f929` calls `FUN_181150790`.
- Windows x64 ABI mapping:
  - `RCX = RSI`: first source/working descriptor.
  - `RDX = RBP`: source image descriptor.
  - `R8 = RBP+0xc0`: rotated/intermediate descriptor.
  - `R9 = R13`: destination ray descriptor.
  - `[rsp+0x20] = RBP+0x60`: second rotated/intermediate descriptor.
  - `[rsp+0x28] = first length value from R15[0]`.
  - `[rsp+0x30] = per-ray length value from R15[...]`.
  - `[rsp+0x38] = RBP+0x5d8`: Blur Mode.
  - `[rsp+0x40] = byte [rsp+0x50]`: one-byte flag later passed to boxFilter.
- `18114f65e..18114f667` sets that caller byte once per core invocation:
  it loads the seed/descriptor vtable from `R14`, calls function pointer
  `+0x20`, and stores the returned `AL` into `[rsp+0x50]`.
- For the current `Channel=2` references, the vtable notes identify that
  `+0x20` function as `FUN_18114ed90`, which returns `1`. This supports the
  current normalized boxFilter path without treating `normalize=true` as a
  magic CLI-only constant.

Inside `FUN_181150790`:

- `181150805..18115081f` converts two descriptor dimensions to floats and
  multiplies by `DAT_181486c1c`.
- `.rdata 181486c10` shows `DAT_181486c1c = 0.5f`.
- `181150852..18115086b` builds an ROI-like rectangle and calls
  `FUN_181156cd0`.
- The first ROI rectangle is centered in the descriptor passed as `param_3`,
  but its width/height come from `param_2`:

```c
rect.x = (int)(param_3->cols * 0.5f) - param_2->cols / 2;
rect.y = (int)(param_3->rows * 0.5f) - param_2->rows / 2;
rect.width = param_2->cols;
rect.height = param_2->rows;
```

  The integer conversions are `cvttss2si` for the half-sized source dimension
  and signed integer half (`(n - signbit(n)) >> 1`) for the temp dimension; for
  the positive image sizes here this is trunc/floor half. This ROI is then
  copied into `param_2`.
- `181150874..181150892` copies the source into an intermediate via
  `FUN_18115cfb0`.
- `1811508a1..1811508c3` calls `FUN_1811512a0` to build a transform matrix.
- `1811508d7..181150941` calls `FUN_181297ac0`, which contains OpenCV
  `cv::warpAffine` strings and argument checks.
- `181150f3d..18115105d` rotates back through another `FUN_1811512a0`,
  `FUN_181157ed0`, `FUN_181297ac0`, and `FUN_18115cfb0` sequence.
- The `FUN_181297ac0` call signature follows OpenCV
  `warpAffine(src, dst, M, dsize, flags, borderMode, borderValue)`. In the call
  wrappers, `0x1010000` is the InputArray Mat wrapper and `0x2010000` is the
  OutputArray Mat wrapper. The first call at `1811508d7..181150941` passes an
  InputArray and OutputArray that both wrap `R14`, plus the matrix at
  `[rbp+0x60]` and `dsize=(R14.cols, R14.rows)`. The rotate-back call at
  `181150f89..181150ff8` passes an InputArray and OutputArray that both wrap
  `param_5`/`R12`, plus the matrix at `local_f8`, and
  `dsize=(R12.cols, R12.rows)`.
- `FUN_181157ed0` is not a transform adjustment helper. It matches
  `cv::Mat::operator=(Mat&&)` / move-assignment shape: copy header fields,
  move external `step` storage when dimensions exceed the inline buffer, and
  clear the source header to `0x42ff0000`.
- `FUN_1811512a0` delegates matrix construction to `FUN_1812943d0`, which
  matches OpenCV `cv::getRotationMatrix2D_`:
  `angle *= pi/180`, `alpha = scale * cos(angle)`,
  `beta = scale * sin(angle)`, then it writes
  `[alpha, beta, (1-alpha)*cx - beta*cy; -beta, alpha,
  beta*cx + (1-alpha)*cy]`.
- `FUN_181156cd0` is an ROI/header constructor. It receives a source Mat
  descriptor plus a 4-int rectangle and creates a sub-Mat header. The rectangle
  layout is OpenCV `Rect(x, y, width, height)` in memory, because it writes
  output `rows = rect.height` from `[r8+0xc]`, `cols = rect.width` from
  `[r8+0x8]`, advances the data pointer by `rect.y * step[0]`, and then by
  `rect.x * elemSize`.
- `FUN_18115cfb0` is not KiraKira-specific copy/crop logic. Its checks and
  assertion strings match OpenCV 4.5.5 `cv::Mat::copyTo`: it validates channel
  compatibility, routes type conversion through `FUN_1811705a0` when needed,
  creates/resizes the destination, and otherwise copies rows with `memcpy`.
  Therefore the KiraKira placement question lives in the caller-built
  `Rect(x, y, width, height)` and `warpAffine` destination Mat dimensions, not
  inside `FUN_18115cfb0`.

## Blur Mode 2: cv::boxFilter Calls

The `Blur Mode=2` path branches at `18115095e..18115110a`.

The first pass:

- `18115110a`: `RDI = RSI | 0x100000000`.
- `18115111a..18115111e`: `R8D = dword [R12] & 7`, i.e. destination depth
  inherited from the destination Mat descriptor.
- `181151122..181151141`: source descriptor is `R14`, destination descriptor
  is `R12`.
- `181151146`: stack `[rsp+0x30] = 4`.
- `18115114e..181151155`: stack `[rsp+0x28] = byte [RBP+0x1a0]`.
  `RBP+0x1a0` is the helper's incoming `param_9`, populated by the caller
  from the `AL` value saved at `[rsp+0x50]`.
- `181151159`: stack `[rsp+0x20] = -1`.
- `181151162`: `R9 = RDI = (1 << 32) | length`, i.e.
  `ksize=(length,1)` in OpenCV `Size(width,height)` packing.
- `181151165..18115116f`: `RCX/RDX/R8/R9` are set and `FUN_181280bc0` is
  called.

The second and third passes at `181151174..1811511c2` and
`1811511c7..181151215` repeat the same call shape, but use `R12` as both
source and destination.

`FUN_181280bc0` decomp signature is:

```c
void FUN_181280bc0(src, dst, ddepth, ksize, anchor, normalize, borderType)
```

Confirmed by callee prologue:

- `181280bc0`: stores `R9` at caller stack shadow, preserving `ksize`.
- `181280be9..181280bff`: `R8D` is kept as `ddepth`.
- `181280c04`: reads byte at stack offset for `normalize`.
- `181280c12..181280c19`: reads stack dword for `borderType`.
- `181280d86..181280d9b`: reads `anchor` from the caller stack object.

Therefore the current ray path is:

- `ddepth = dst.type & 7`, effectively same-depth / `-1`-style output for the
  current float ray buffers.
- `ksize = (length, 1)`, not `(length, length)` and not
  `(2 * length + 1, 1)`.
- `anchor = (-1, -1)`.
- `normalize = param_9`, copied from the caller's seed/descriptor vtable
  `+0x20` return byte; for current `Channel=2` refs this is `1`. The
  normalize=false probes are strongly negative, so there is no evidence that
  current references exercise a false normalize path.
- `borderType = 4`, which is OpenCV `BORDER_REFLECT_101`.

Current port alignment:

- `cli/OLMKiraKira/main.cpp` rotates the ray into the horizontal axis and then
  applies a one-dimensional horizontal box. Its default `--box-size-mode
  length` matches `ksize=(length,1)`.
- `--box-anchor-mode opencv` matches `anchor=(-1,-1)`.
- `--filter-border mirror` matches `BORDER_REFLECT_101`.
- `--box-normalize true` matches the observed refs and the negative
  normalize=false probe.
- `--box-output-depth float` remains plausible; `u8-each` worsened and
  `u16-each` was neutral in existing probes.

Helper return scalar:

- `FUN_181150790` returns a scalar in `XMM0`; in the Blur Mode 2 path the helper
  multiplies that scalar by `length^2` before returning. The caller stores the
  value per ray before later passing the ray/scalar arrays into the vtable
  aggregation path.
- Existing `fd90-exact` aggregation probes clear the basic five-buffer
  alpha/RGB formula, but the exact use of this helper-return scalar remains
  underdetermined by the current references because all tracked cases have the
  same `Vertical/Horizontal/Diagonal Length=50` and `Glow Rotation=0`.
- `refs/reference_requests/kirakira_single_ray_20260606.json` asks for isolated
  ray references so this scalar/ray-order ambiguity can be tested without
  further image-only tuning.

## cv::warpAffine Calls

`FUN_181297ac0` is the OpenCV `cv::warpAffine` wrapper:

- Decomp contains `cv::warpAffine` and
  an OpenCV `modules/imgproc/src/imgwarp.cpp` build path.
- It checks `_src.channels() <= 4 || (interpolation != INTER_LANCZOS4 &&
  interpolation != INTER_CUBIC)`.
- It checks matrix shape `(M0.type() == CV_32F || M0.type() == CV_64F) &&
  M0.rows == 2 && M0.cols == 3`.
- `1811508d7..181150941` passes flags `[rsp+0x20]=1`, `[rsp+0x28]=0`, and
  size from the destination descriptor before calling `FUN_181297ac0`.
- `181150f80..181150ff8` performs the rotate-back call with the same flag
  shape.
- Inside `FUN_181297ac0`, `param_5 & 7` selects interpolation and `param_5 &
  0x10` controls whether the affine matrix is inverted internally. The
  KiraKira calls pass `param_5=1`, so this is OpenCV `INTER_LINEAR` without
  `WARP_INVERSE_MAP`.
- KiraKira passes `param_6=0` and a zero scalar pointer as `param_7`, matching
  `borderMode=BORDER_CONSTANT` and `borderValue=0`. This is separate from the
  `boxFilter` calls, which use `borderType=4` (`BORDER_REFLECT_101`).

Current interpretation:

- Existing probes show `rotate_border=constant` is slightly better than the old
  edge-clamp rule, and `rotate_filter=bilinear` beats the C++ bicubic proxy.
- A C++ diagnostic `--warp-mode aex-getrot` implements the observed
  `getRotationMatrix2D_` formula with an output-center hypothesis and
  `warpAffine`-style inverse mapping. It is strongly negative on current refs:
  `case_0001 mean=5.9449`, `case_0002 mean=6.6790`,
  `case_0003 mean=27.6616`, versus baseline
  `0.8381/1.1623/1.7003`.
- A C++ diagnostic `--warp-mode aex-frame` writes both forward and rotate-back
  warps directly into the original frame dimensions using center
  `(width*0.5, height*0.5)`. It is negative:
  `case_0001 mean=1.4465`, `case_0002 mean=1.9139`,
  `case_0003 mean=6.9617`. So the AEX dsize observations cannot be modeled as
  a simple full-frame direct warp without the caller's ROI/temp-Mat placement.
- A C++ diagnostic `--warp-mode aex-roi-temp` models the first centered ROI
  copy into the AEX-sized temp buffer before warping. The naive version is also
  strongly negative: `case_0001 mean=5.1944`, `case_0002 mean=5.9919`,
  `case_0003 mean=26.1768`. This rules out the simple interpretation
  "centered ROI copy + full-frame dsize + original-frame center" and points
  back to exact source/destination Mat orientation around the two
  `FUN_181297ac0` calls.
- A C++ diagnostic `--warp-mode aex-inplace-temp` models the observed first
  `warpAffine` wrapper as an in-place temp-buffer warp, then blurs the temp and
  rotates it back to the full frame. It is the worst tested warp hypothesis:
  `case_0001 mean=8.7256`, `case_0002 mean=9.1471`,
  `case_0003 mean=33.4284`. Do not adopt this model; the observed same
  src/dst wrapper at the call site is not explained by a simple centered ROI
  temp copy followed by in-place rotation.
- A C++ diagnostic `--warp-mode aex-two-temp` models the corrected two-temp
  choreography: centered ROI into `R14`, in-place forward warp on `R14`, blur
  into `R12`, in-place rotate-back on `R12`, then centered ROI copy to the
  final output size. It is mixed but useful evidence:
  `case_0001 mean=0.8531`, `case_0002 mean=1.1555`,
  `case_0003 mean=1.1870` versus default `0.8381/1.1623/1.7003`.
  This improves the Strength=0 case substantially without solving case1, so
  keep it as a probe; the default port still stays on `current`.
- Follow-up probes on `aex-two-temp` did not identify a better `boxFilter`
  setup. `--rotate-filter bilinear-fixed5` only nudges case3
  (`0.8531/1.1555/1.1822`). Anchor sweep keeps OpenCV's default anchor best:
  `opencv 0.8531/1.1555/1.1870`, `floor-left 0.8531/1.2134/2.1904`,
  `origin 7.6422/8.5897/41.1816`, `end 7.7674/8.6221/41.2038`.
  Border sweep is mixed: `mirror 0.8531/1.1555/1.1870` versus
  `reflect 0.8531/1.1558/1.1818`. This points away from anchor/border as the
  main residual and back toward exact `warpAffine`/ROI/copyTo placement.
- Final ROI placement sweep on `aex-two-temp` is strongly negative in all
  one-pixel directions, so the last `R12` -> final-ray `copyTo` rectangle is
  unlikely to be the remaining issue. Results: baseline
  `0.8531/1.1555/1.1870`; final `x-1` `1.1336/1.3811/6.1233`;
  final `x+1` `1.1276/1.3447/5.9795`; final `y-1`
  `1.1166/1.3516/5.9944`; final `y+1` `1.1166/1.3708/6.0968`.
  Next target is forward/rotate-back `warpAffine` in-place behavior or the
  exact matrix center/scale details, not final ROI position.
- A C++ diagnostic `--warp-mode aex-two-temp-direct-back` keeps the corrected
  two-temp setup but writes the rotate-back warp directly to the final ray
  size. It is strongly negative: `10.9852/11.6630/50.6637` versus
  `aex-two-temp` `0.8506/1.1570/1.0563`. So the final descriptor/dsize
  evidence is not explained by a naive final-size rotate-back using the
  rotated temp center.
- A follow-up `--warp-mode aex-two-temp-center-minus-half` subtracts 0.5 from
  the two-temp forward and rotate-back matrix center. It improves only
  `case_0001` (`0.8531 -> 0.8266`) while worsening `case_0002`
  (`1.1555 -> 1.1637`) and `case_0003` (`1.1870 -> 1.7709`). Keep it as a
  diagnostic probe, but do not adopt the half-pixel center shift as the default
  model.
- The decomp/asm shape shows the rotate-back `warpAffine` dsize is the final
  ray descriptor (`param_5`) rather than a larger temporary canvas followed by
  an obvious center crop. A C++ diagnostic `--warp-mode aex-direct-back`
  approximates that direct writeback using the observed rotated-buffer center.
  It is also negative: `case_0001 mean=0.9928`, `case_0002 mean=1.3755`,
  `case_0003 mean=4.4660`.
- The remaining residual is more likely exact OpenCV 4.5.5 `warpAffine`
  destination canvas / dsize behavior, sampling/rounding, final composition, or
  another pre/post ray detail than a simple boxFilter argument mismatch, naive
  getRotationMatrix2D center swap, `FUN_181157ed0` matrix adjustment, direct
  rotate-back approximation, or simple Mat ROI / same-destination aliasing.
- Existing C++ crop probes (`floor`, `ceil`, `round`) all produce the same
  baseline residual (`case_0001 mean=0.8381`, `case_0002 mean=1.1623`,
  `case_0003 mean=1.7003`), so the current mismatch is not explained by a
  trivial final center-crop rounding choice.
- A C++ diagnostic `--rotate-filter bilinear-fixed5` quantizes bilinear
  fractions to an OpenCV-style 5-bit subpixel grid. It does not improve the
  refs: `case_0001 mean=0.8384`, `case_0002 mean=1.1624`,
  `case_0003 mean=1.7034`, versus baseline `0.8381/1.1623/1.7003`.
  So the current residual is not explained by adding 1/32 interpolation-table
  quantization alone.
- A C++ diagnostic `--aggregation-mode fd90-exact` now spells out the
  `FUN_18114fd90`-style five-layer aggregation order: skip `ray <= epsilon`,
  clamp `ray * brightness`, add RGB as `color * alpha`, update alpha with the
  union formula, then normalize RGB by final alpha. It is effectively identical
  to `fd90-five` and current on the tracked refs:
  `case_0001 mean=0.8381`, `case_0002 mean=1.1623`,
  `case_0003 mean=1.7003`. This further clears final five-buffer aggregation
  as the active residual source; keep focus on `FUN_181150790` intermediate
  forward-warp / boxFilter / rotate-back behavior or per-ray isolation refs.

## Rotate Canvas / dsize

`FUN_18114f4a0` computes the intermediate ray canvas before calling
`FUN_181150790`.

Address facts:

- `18114f78b`: calls `FUN_18132b2e0`, then masks both returned float lanes
  with an absolute-value mask.
- `18114f7a0..18114f7e4`: computes two dimensions with the shape:

```c
tmp_w = (int)(src_w * abs(cos) + src_h * abs(sin) + 0.5f);
tmp_h = (int)(src_w * abs(sin) + src_h * abs(cos) + 0.5f);
```

- `18114f7e8..18114f7f5`: clamps these to at least `src_w + 4` and
  `src_h + 4`.
- `18114f7f8..18114f81c`: passes those dimensions to `FUN_181231b80`.

CLI probe results:

- `--rotate-size-mode aex-min4` implements the formula above for rotated
  intermediate sizes. On the current refs it is identical to the default:
  `case_0001 mean=0.8381`, `case_0002 mean=1.1623`,
  `case_0003 mean=1.7003`.
- `--axis-fast-path false --rotate-size-mode aex-min4` on the older/default
  warp path forces 0/90-degree rays through the rotate/crop path too. It is
  mixed/negative:
  `case_0001 mean=0.8354`, `case_0002 mean=1.1847`,
  `case_0003 mean=2.0123`.
- `--axis-fast-path false` with the older/default round sizing is also
  negative:
  `case_0001 mean=0.8381`, `case_0002 mean=1.1847`,
  `case_0003 mean=2.1189`.
- Later two-temp correction changes this interpretation: with
  `--warp-mode aex-two-temp --axis-fast-path false`, C++ reports
  `case_0001 mean=0.8506`, `case_0002 mean=1.1570`,
  `case_0003 mean=1.0563`, nearly matching the Python OpenCV primitive probe
  `0.8504/1.1570/1.0514`.

There is currently no asm evidence for a 0/90-degree fast path in AEX:
the caller sets up temp Mats and calls `FUN_181150790`, and the helper contains
the forward warp, Blur Mode work, and rotate-back path. Treat the CLI fast path
as a portability shortcut/diagnostic, not as confirmed AEX behavior.

OpenCV 4.5.5 `dst=` / ROI aliasing has been reproduced locally and is neutral:
`opencv-two-temp-alias-roi` matches ordinary `opencv-two-temp` at
`0.8504/1.1570/1.0514`. Do not adopt any new warp/crop change without a direct
asm argument mapping or a faithful local OpenCV 4.5.5 reproduction;
image-diff-only tuning is too easy to overfit here.

## Temp Mat Creation / Caller Placement

`FUN_18114f4a0` creates the two temporary ray Mats passed into
`FUN_181150790`.

Address facts:

- `18114f7f8..18114f830`: creates the first PF-backed temp descriptor at
  `[rbp+0x190]` with `FUN_181231b80`, then copy-constructs it into
  `[rbp+0xc0]` via `FUN_181156b90`.
- `18114f836..18114f873`: immediately zeros the copied temp's data pointer
  (`[rbp+0xd0]`). The byte count is
  `tmp_w * tmp_h * channel_count * sizeof(float)`.
- `18114f87c..18114f8ae`: creates a second same-sized PF-backed temp descriptor
  at `[rbp+0x120]`, then copy-constructs it into `[rbp+0x60]`.
- `18114f8b4..18114f8e4`: immediately zeros the second copied temp's data
  pointer (`[rbp+0x70]`) with the same byte count.
- `18114f90f..18114f929`: calls `FUN_181150790` with
  `RCX = host/context`, `RDX = [rbp]` source Mat, `R8 = [rbp+0xc0]`,
  `R9 = current ray descriptor`, and stack arg `[rsp+0x20] = [rbp+0x60]`.
  Ghidra's decomp elides some of this stack-argument shape, so prefer this asm
  mapping when reasoning about `param_5`.
- `18114f932..18114f95d`: destructs `[rbp+0x60]`, releases `[rbp+0x120]`,
  destructs `[rbp+0xc0]`, then releases `[rbp+0x190]`.

Helper facts:

- `FUN_181231b80` is a PF-backed Mat allocator/wrapper initializer: it clears
  the destination Mat-like header, stores the AE/context pointer at `+0x68`,
  and calls `FUN_181231ec0(rows/cols/type/channel-count)` to allocate/create
  the backing data.
- `FUN_181156b90` is a `cv::Mat` copy-constructor shape, not a raw data clone:
  it copies flags/dims/rows/cols/data/step/refcount pointers, sets local step
  pointers, and increments the refcount at `u + 0x14` when present.

Implication: the caller passes two distinct zero-filled Mat headers that share
the PF-backed allocation through copy construction. `FUN_181150790` then uses
the first temp (`R14`/`param_3`) for the initial centered ROI copy and in-place
forward warp, and the second temp (`R12`/`param_5`) as the blur/output and
in-place rotate-back canvas before copying a centered ROI into the final ray
descriptor (`param_4`). The simple `aex-inplace-temp` probe was still wrong
because it modeled a one-temp blur/rotate-back path rather than this R14-to-R12
two-temp choreography.

## 2026-06-06 Subagent IR Review

Independent read-only review of KiraKira confirmed the current state as a
high-precision red probe rather than a validated port. The all-ray
two-temp/no-fastpath path is still around `case_0001/0002/0003
mean=0.8506/1.1570/1.0563`, and the broad structure is fairly stable:
Brightness and Strength are separated, luminance seed is understood, the
five-layer aggregation order is known, and the repeated-box/warp path is close
to OpenCV behavior.

Next address-level facts to lock before more tuning:

- In `FUN_181150790`, confirm both `warpAffine` calls' exact
  InputArray/OutputArray Mat headers and whether the second `dsize` is derived
  from R14, R12, or `param_4`.
- Confirm the `FUN_181156cd0` ROI rectangles and the `FUN_18115cfb0`/`copyTo`
  direction: source-to-temp center versus temp-ROI-to-ray.
- Confirm how the helper return scalar, `length^2` correction, and ray-scalar
  array reach final aggregation. The current references use equal ray lengths,
  so image diffs alone cannot separate this.
- Confirm merge-mode dispatch and source/glow opacity ordering for
  `+0x08 FUN_18114fd90` and `+0x10 FUN_18114ffd0`.
- Keep `0/90` axis fast path as a portability shortcut only; no AEX branch fact
  currently proves it.

IR components to keep separate:

- `KiraRayHelper`: temp canvas sizing, ROI copy, forward warp, three-pass
  `boxFilter`, rotate-back, final ROI copy.
- `KiraSeed`: Channel enum seed functions; Strength is seed exponent;
  Brightness is final scale.
- `KiraAggregate`: five buffer order, ray scalar handling, alpha union, and RGB
  normalization.
- `KiraCompose`: merge-mode and opacity application order.

If the next objdump/Ghidra pass confirms these facts but the residual remains
near the current level, use `refs/reference_requests/kirakira_single_ray_20260606.json`.
The current three references cannot isolate ray order, angle mapping, or scalar
handling by themselves.

### 2026-06-06 stop condition review

Subagent review of the current KiraKira probes found that the remaining
image-only hypotheses are mostly already covered:

- `boxFilter`: `ksize=(length,1)`, OpenCV anchor, `normalize=true`,
  `BORDER_REFLECT_101`, and output-depth candidates.
- rotate/warp: constant border, bilinear sampling, canvas size, crop
  floor/ceil/round, final ROI one-pixel shifts, direct-back, two-temp,
  no-fastpath, and center-minus-half.
- composition/aggregation: `fd90-exact` five-layer aggregation, RGB normalize,
  and merge candidates are already broad red/neutral probes.
- Python OpenCV two-temp alias ROI probe is neutral, so simple Mat/ROI
  same-destination aliasing is not the residual by itself.

One theoretical local probe remains: a C++ build that links real OpenCV and
calls `warpAffine(srcMat, srcMat, ...)` twice in the exact two-temp order.
Given the Python OpenCV alias result and the current equal-ray references, this
is lower priority than getting isolated rays.

Stop condition: do not keep adding KiraKira image-diff toggles against the
current three references. They all use equal ray lengths and rotation zero, so
they cannot separate ray order, angle mapping, helper scalar / `length^2`, or
single-ray crop behavior. Use
`refs/reference_requests/kirakira_single_ray_20260606.json` before promoting
another KiraKira implementation change.

### FUN_181150790 warp/ROI argument audit

2026-06-06 subagent audit confirmed the two-temp helper mapping:

- Function arguments: `R14 = param_3` first temp, `R12 = param_5` second temp,
  and `R9/RBX = param_4` final ray Mat.
- First `warpAffine` at `1811508d7..181150941` wraps `R14` for both
  `InputArray(0x1010000)` and `OutputArray(0x2010000)`. Its dsize is loaded
  from `R14+0x8/+0xc` at `18115090e..18115091a`, so it uses the first temp's
  size.
- Second `warpAffine` at `181150f89..181150ff8` wraps `R12` for both
  `InputArray(0x1010000)` and `OutputArray(0x2010000)`. Its dsize is loaded
  from `R12+0x8/+0xc` at `181150fc3..181150fd1`, not from `param_4`.
- Initial ROI copy: `181150852..18115086b` builds an ROI in `R14`, then
  `181150874..181150892` copies `param_2` into `ROI(R14)`.
- Final ROI copy: `181151019..181151024` builds an ROI in `R12`, then
  `181151033..181151049` copies `ROI(R12)` into `param_4/RBX`.
- `FUN_181156cd0` constructs `Rect(x,y,width,height)`: `181156d08..181156d12`
  writes rows from rect height `[r8+0xc]` and columns from rect width
  `[r8+0x8]`.

Next C++ probe should minimize the current `aex-two-temp` path and force both
warps to call OpenCV with the same Mat as source and destination:
`param_2 -> ROI(R14)`, `warpAffine(R14, R14, dsize=R14.size())`,
`blur R14 -> R12`, `warpAffine(R12, R12, dsize=R12.size())`, then
`ROI(R12) -> param_4`.

### 2026-06-06 parallel audit refresh

Sub-agent Goodall reconfirmed that `FUN_181150790` is the four-ray helper and
that there is no current asm evidence for a special 0/90-degree fast path. Keep
the CLI axis fast path diagnostic-only.

Current recorded status remains:

- Default C++ smoke: `case_0001 mean=0.8381`, `case_0002 mean=1.1623`,
  `case_0003 mean=1.7003`.
- Python OpenCV two-temp: `0.8504/1.1570/1.0514`.
- Python explicit ROI/`dst=` alias is identical to the OpenCV two-temp probe,
  so simple Mat ROI aliasing is not the residual.
- C++ all-ray two-temp/no-fastpath: `0.8506/1.1570/1.0563`.
- `fd90-exact` five-layer aggregation is effectively unchanged at
  `0.8381/1.1623/1.7003`, so final five-buffer aggregation is not the active
  main residual.

Stop condition still holds: the current three refs use equal ray lengths and
`Glow Rotation=0`, so ray order, angle mapping, helper scalar / `length^2`, and
single-ray crop behavior cannot be separated. Parent action is to render/import
`refs/reference_requests/kirakira_single_ray_20260606.json` in Software mode
before promoting another KiraKira implementation change.
