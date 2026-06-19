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
  Implemented in the C++ CLI and Mac plugin as `kFd90RayEpsilon`; this is
  mostly immaterial at the current 8-bit references but keeps the merge path
  aligned with `FUN_18114fd90`.
- `DAT_181486c1c = 0.5f` — helper half-size center factor.
- `DAT_18148b840 = 0x7fffffff` — abs-value mask for cos/sin in canvas sizing.
- `DAT_18148b830 = 4.0f` — used in the rotate-canvas dimension formula.

### CONFIRMED: rotated temp extents use `+4.0`, not rounded `+0.5`

`FUN_18114f4a0` computes each four-ray temp canvas before calling
`FUN_181150790`:

```c
temp_w = max(src_w + 4, int(src_w * abs(cos) + src_h * abs(sin) + 4.0f));
temp_h = max(src_h + 4, int(src_w * abs(sin) + src_h * abs(cos) + 4.0f));
```

The relevant instructions are `ADDSS XMM?, DAT_18148b830` followed by
`CVTTSS2SI`, so this is truncation after adding `4.0`, not nearest rounding.
The C++ CLI and Mac plugin now use this formula for their AEX two-temp path,
and the CLI default warp mode is the binary-backed `aex-two-temp` path.

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
| diagonal   b1 s100 | 142/25.71 | 23/1.26 |
| diagonal2  b1 s100 | 138/25.71 | 23/1.30 |
| rotation13         | 139/25.76 | 66/1.66 |
| vertical   b9.4 s0 | 113/27.76 | 113/27.76 |
| horizontal b9.4 s0 | 113/27.76 | 113/27.76 |
| diagonal   b9.4 s0 | 113/27.76 | 113/27.76 |
| diagonal2  b9.4 s0 | 113/27.76 | 113/27.76 |

The axis-aligned ray residual (max~13) is now the box-blur shape (3-pass
uniform box vs OpenCV `boxFilter` REFLECT_101/anchor) — an OpenCV-primitive
residual, not a compose/seed error. An offline numpy reimplementation of the
exact CLI box reproduces the CLI ray to the float, and the screen model then
lands mean~1.3, confirming the residual is the box approximation. Diagonal /
rotation residual improved after switching to the binary-backed two-temp
canvas formula, but remains the hardest axis.

### RESOLVED: strength=0 uses the half-gain fd90 path

The 2026-06-15 recapture
`refs/win_references/olm_reference_return_windows_recapture_20260615/OLMKiraKira/`
adds Strength=0 cases at Brightness Gain 1, 25, 50, and 94. All four use the
same one-ray setup, so the seed is uniform (`luma^0 * a`) and the output directly
identifies the fd90 gain.

Measured with `--compose-mode aex-screen-over`:

- `--scale-override 0.5`: saturated brightness cases stay near but not exact
  (`max=1 mean=0.4336`).
- `--scale-override 127/255`: Brightness 25/50/94 are exact, and Brightness 1 is
  `max=1 mean=0.0397`.

So the C++ CLI now maps `Strength multiplier <= 0` to `scale = 127/255` before
the fd90 aggregation. This is not a single-point PNG fit anymore: it is supported
by four Brightness anchors and agrees with the binary-observed half constant
(`DAT_181486c1c = 0.5f`) plus final 8-bit quantization.

## Current Reference Slice

Current C++ smoke command:

```sh
python3 refs/scripts/smoke_olmkirakira_cpp_cli.py
```

Current expected-red measurements:

- `case_0001`: `max=21 mean=0.8291 nz=296977/518400`
- `case_0002`: `max=24 mean=1.1609 nz=1366956/2073600`
- `case_0003`: `max=233 mean=53.8132 nz=1821785/2073600`

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

2026-06-18 callee audit:

- `FUN_181280bc0` is the OpenCV `boxFilter` wrapper and reaches the normal CPU
  FilterEngine setup after destination creation.
- `FUN_181281260` is not a single fixed baseline call. It checks CPU feature
  gates before choosing the implementation: feature `0xb` calls
  `FUN_1812e39d0`, feature `6` calls `FUN_1812d7c40`, and only when both are
  unavailable does it call the baseline `FUN_181280fa0`
  (`decomp/OLMKiraKira.aex.c.txt:3759979..3759990`). Windows runtime trace or
  a 4.5.5-linked microprobe should record which branch is actually used.
- In the normalized float path, `FUN_181280fa0` computes the scale as
  `1.0 / (ksize.width * ksize.height)` at `181281087..18128109a`. For the
  observed ray pass (`ksize=(length,1)`), this is exactly `1.0 / length`.
- In the baseline CV_32F path, `FUN_181280fa0` leaves the buffer/sum format as
  `6` for source depth `5` (`CV_32F`) (`decomp/OLMKiraKira.aex.c.txt:3759842`),
  then creates `RowSum<float,double>` and `ColumnSum<double,float>`
  (`decomp/OLMKiraKira.aex.c.txt:3760724..3760730` and
  `decomp/OLMKiraKira.aex.c.txt:3760352..3760359`). This pins a double
  intermediate accumulator with float output for the baseline float boxFilter.
  The current C++ default `--box-accum-mode double` already matches this;
  `--box-accum-mode float` remains a negative diagnostic.
- The port's `mirror_index` border helper implements OpenCV
  `BORDER_REFLECT_101`: negative indices map with `-i`, and high indices map
  with `2*n-i-2`. This matches the wrapper call's `borderType=4`.
- Therefore the simple boxFilter argument set and normalization are now
  binary-grounded, and baseline float accumulator precision is pinned.
  Remaining KiraKira residuals should be investigated in the exact OpenCV
  4.5.5 optimized FilterEngine branch actually used on Windows, in
  `warpAffine` interpolation details, or in pre/post ray aggregation rather
  than by guessing different box size, border, normalize, or accumulator
  settings from PNGs.

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

### 2026-06-19 probe refresh / IR split

`notes/IR_OLMKiraKira.md` now carries the compact binary-grounded IR. The
refresh did not find a new implementation change:

- `refs/scripts/smoke_olmkirakira_cpp_cli.py` remains an expected-red legacy
  measurement on `20260604_olm`: `case_0001 max=21 mean=0.8291`,
  `case_0002 max=24 mean=1.1609`, `case_0003 max=233 mean=53.8132`. This
  script still uses the older `aex-premul` command shape and should not be
  read as a current AE exact gate.
- C++ micro diagnostics for the OpenCV-style remap path pass:
  `diag_remap_bilinear_f32`, `diag_warpaffine_map_f32`, and
  `diag_warpaffine_remap_f32`.
- Anchor refresh confirms the existing conclusion: `box-anchor opencv` is the
  least bad tested anchor; `floor-left` worsens `case_0002`, and `origin` /
  `end` are strongly negative.
- Rotate-filter refresh confirms bilinear is still the least bad tested mode.
  Bicubic and nearest are strongly negative, while fixed-table variants are
  neutral/slightly worse and do not explain the residual.
- Local Python OpenCV probes can now run from `/tmp/olm_cv455_probe_venv`
  (`opencv-python-headless==4.5.5.64`, `numpy==1.26.4`, arm64 wheel rather
  than the traced Windows AVX2 branch):
  - `OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python python3 refs/scripts/smoke_olmkirakira_opencv_screenover_probe_cli.py`
    passes its measurement guard on the 2026-06-14 single-ray set with
    `max=13/23/66` on strength-100 rays and `max=0..3` on strength-0 anchors.
  - `OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python python3 refs/scripts/smoke_olmkirakira_opencv_two_temp_probe_cli.py`
    remains expected-red on the older three-case set, but reports
    `case_0001 max=21 mean=0.8239`, `case_0002 max=24 mean=1.1568`,
    `case_0003 max=26 mean=1.0477`.
  - `OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python python3 refs/scripts/smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py`
    is byte-identical to the ordinary OpenCV two-temp probe for those three
    cases, so explicit ROI aliasing is not a leading residual explanation.
  The earlier OpenCV 4.10.0 local wheel produced the same measurements, so the
  residual is unlikely to be a broad 4.5.5-vs-newer OpenCV version difference.
  These probes are still not completion evidence because they do not execute
  the Windows AVX2 `FUN_1812e39d0` branch. They move the likely residual source
  away from broad boxFilter args and toward exact AVX2 primitive behavior,
  `warpAffine` Mat/ROI placement, or final ray aggregation details.

Next KiraKira work should be an exact AVX2 `FUN_1812e39d0` microprobe or a
Windows runtime trace of `FUN_181150790` stage values
(`warpAffine` Mat headers/dsize/matrix, ROI rectangles, selected `boxFilter`
function, and a few float witnesses after each helper stage). Do not spend the
next pass on more broad PNG toggles.

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

### 2026-06-17 returned single-ray / strength0 brightness audit

The old single-ray and strength0 brightness stop conditions are lifted:
`kirakira_single_ray_20260606` and `kirakira_strength0_brightness_20260614`
are covered and imported.

Current best-supported IR checkpoints:

- Merge mode 1 is `aex-screen-over`: screen source RGB with glow RGB multiplied
  by glow alpha, and keep source alpha.
- Zero-length rays are skipped rather than blurred as the raw seed.
- Ray order/angles are `{vertical=90+rotation, horizontal=0+rotation,
  diagonal=45+rotation, highlight_zero, diagonal2=-45+rotation}`.
- `FUN_181150790`'s helper scalar is not needed by merge-mode-1
  `FUN_18114fd90`; final aggregation consumes ray buffers plus Brightness/Gain.
- Strength=0 Brightness maps `fd90`'s trailing `param_10` to `127/255`.
- Axis fast-path is diagnostic only. Disabling it does not solve the main
  residual.

Measured status:

- `python3 refs/scripts/smoke_reference_requests_after_import.py --request
  kirakira_strength0_brightness_20260614`: `kk_s0_brightness1 max=1
  mean=0.0397`; brightness25/50/94 are exact.
- `kirakira_single_ray_20260606` with `--warp-mode aex-two-temp`:
  vertical/horizontal strength100 `max=13 mean=1.3931/1.4214`;
  diagonal/diagonal2 `max=23 mean=1.2602/1.2959`; strength0
  vertical/horizontal exact; strength0 diagonal/diagonal2 `max=3
  mean=0.0238`; rotation13 `max=66 mean=1.6628`.
- `--warp-mode current` worsens diagonal and rotation13
  (`max=43/45`, rotation13 `max=76 mean=1.8365`), so keep `aex-two-temp` as
  the better current hypothesis.

Next parent action: compare the hand-written box/warp path against actual
OpenCV `boxFilter(..., ksize=(length,1), anchor=(-1,-1), normalize=1,
BORDER_REFLECT_101)` plus `warpAffine` two-temp canvas with the binary-backed
`+4.0` truncation. Do not chase more brightness/scalar/ray-order refs unless
that OpenCV primitive pass still leaves an unexplained pattern.

### 2026-06-17 OpenCV primitive with current screen-over compose

Added Python probe support for the current C++ best hypothesis:

- `--compose-mode aex-screen-over`: screen source RGB against
  `glow_rgb * glow_alpha`, preserve source alpha.
- `--scale-mode aex-screen-over`: normal strength uses
  `Brightness Gain * 0.62`; Strength=0 uses `127/255`.
- `--zero-ray-skip`: length-0 rays contribute zero, not the raw seed.
- `refs/scripts/smoke_olmkirakira_opencv_screenover_probe_cli.py` runs the
  imported `kirakira_single_ray_20260606` refs through Python cv2
  `warpAffine` + `boxFilter` + two-temp canvas. It requires
  `OLM_PROBE_PYTHON` to point at a Python with `cv2`.

Measurement command used locally:

```text
refs/scripts/setup_olmkirakira_opencv455_probe_env.sh
python3 refs/scripts/smoke_olmkirakira_opencv455_probe_env.py --require
OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python \
  python3 refs/scripts/smoke_olmkirakira_opencv_screenover_probe_cli.py
```

Environment caveat: the local probe now uses OpenCV 4.5.5.64, but it is an
arm64 Python wheel, not the Windows AVX2 branch selected inside the AEX. Treat
this as stronger primitive-shape evidence, not as a bit-exact AVX2 proof.

Result on `kirakira_single_ray_20260606`:

| case | max | mean |
| --- | ---: | ---: |
| vertical strength100 | 13 | 1.3508 |
| horizontal strength100 | 13 | 1.4214 |
| diagonal strength100 | 23 | 1.2605 |
| diagonal2 strength100 | 23 | 1.2960 |
| vertical strength0 | 3 | 0.0227 |
| horizontal strength0 | 0 | 0.0000 |
| diagonal strength0 | 3 | 0.0237 |
| diagonal2 strength0 | 3 | 0.0237 |
| diagonal rotation13 | 66 | 1.6628 |

The explicit `opencv-two-temp-alias-roi` variant is identical to
`opencv-two-temp` under these screen-over conditions.

Implication: swapping the hand-written C++ two-temp approximation for actual
OpenCV primitives is not enough by itself. It slightly improves the vertical
strength100 case relative to C++ (`1.3931 -> 1.3508`) but leaves horizontal,
diagonal, diagonal2, and rotation13 effectively unchanged. The active residual
is therefore more likely exact `FUN_1811512a0` matrix/center/dsize semantics,
OpenCV 4.5.5 interpolation details, or a small pre/post ROI copy convention
than brightness, scalar aggregation, ray order, zero-ray handling, or ordinary
boxFilter border/anchor settings.

### 2026-06-17 getRotationMatrix2D center audit

Read-only sub-agent audit and local decomp review confirm that
`FUN_1812943d0 @ 1812943d0` is OpenCV `cv::getRotationMatrix2D_`:

```text
angle_rad = angle_deg * (pi / 180)
alpha = cos(angle_rad) * scale
beta  = sin(angle_rad) * scale

[ alpha   beta   (1-alpha)*cx - beta*cy
 -beta    alpha   beta*cx + (1-alpha)*cy ]
```

`FUN_181150790` passes the rotated temp Mat center to `FUN_1811512a0`:
`cx = cols * 0.5f`, `cy = rows * 0.5f`. This matches current C++ two-temp
`temp_cx = rw * 0.5`, `temp_cy = rh * 0.5`; it is not `(w-1)/2`.
`FUN_181297ac0` receives `param_5=1`, so OpenCV uses `INTER_LINEAR` without
`WARP_INVERSE_MAP`; the existing CLI's inverse sampling convention is the right
shape for default `warpAffine`.

Added Python OpenCV probe option `--opencv-center-mode` to isolate only the
binary-plausible center ambiguities (`normal`, `swapped`, `minus-half`,
`swapped-minus-half`). Measured against `kirakira_single_ray_20260606` with
screen-over / zero-ray skip:

| center mode | vertical | horizontal | diagonal | diagonal2 | strength0 V/H/D/D2 | rotation13 |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| normal | 1.3508 | 1.4214 | 1.2605 | 1.2960 | 0.0227 / 0 / 0.0237 / 0.0237 | 1.6628 |
| swapped | 1.3508 | 1.4214 | 1.2605 | 1.2960 | 0.0227 / 0 / 0.0237 / 0.0237 | 1.6878 |
| minus-half | 1.3500 | 1.4214 | 1.2607 | 1.2978 | 0.0215 / 0 / 0.0237 / 0.0237 | 1.6628 |
| swapped-minus-half | 1.3500 | 1.4214 | 1.2607 | 1.2978 | 0.0215 / 0 / 0.0237 / 0.0237 | 1.6878 |

The half-pixel variants only make tiny local movements and do not improve the
hard rotation13 case; swapped center worsens rotation13. Combined with the
binary call-site evidence, keep the standard temp-center model pinned.

2026-06-17 follow-up: the Python OpenCV probe originally used the old
`+0.5` extent formula even though the C++/Mac path and binary facts already use
`+4.0` plus truncation. `refs/scripts/olmkirakira_cli.py` now mirrors the AEX
temp extent:

```text
rw = max(width + 4, int(width * abs(cos) + height * abs(sin) + 4.0))
rh = max(height + 4, int(width * abs(sin) + height * abs(cos) + 4.0))
```

Re-running `OLM_PROBE_PYTHON=/tmp/olm_cv455_probe_venv/bin/python python3
refs/scripts/smoke_olmkirakira_opencv_screenover_probe_cli.py` with OpenCV
4.5.5.64 gives software and CUDA duplicate rows with the same metrics:
vertical strength100 `max=13 mean=1.3500`, horizontal `13/1.4214`,
diagonal `23/1.2604`, diagonal2 `23/1.2959`, strength0 V/H/D/D2
`1/0.0215`, `0/0.0000`, `3/0.0238`, `3/0.0238`, and rotation13
`66/1.6628`. The extent correction is therefore a measurement hygiene fix, not
a closing model change; it keeps the residual localized to exact warpAffine /
OpenCV-version behavior or a still-unseen pre/post ray detail.

### 2026-06-17 actual objdump scale-register audit

`objdump` against `plugins_2025/OLMKiraKira.aex` closes the remaining
matrix-side scale ambiguity. The first forward-rotation call at
`1811508a1..1811508c3` passes:

```text
1811508a1  movd    %r15d,%xmm2
1811508a6  cvtdq2pd %xmm2,%xmm2
1811508aa  movsd   0x33cdc6(%rip),%xmm3  # 0x18148d678
1811508b2  movaps  %xmm6,%xmm10
1811508b6  unpcklps %xmm7,%xmm10
1811508ba  movq    %xmm10,%rdx
1811508bf  leaq    0x60(%rbp),%rcx
1811508c3  callq   0x1811512a0
```

Interpretation under Windows x64 ABI:

- `xmm2` is `(double)r15d`, i.e. the forward angle in degrees.
- `xmm3` is loaded from `0x18148d678`, the same `1.0` constant used inside the
  OpenCV matrix helper.
- `rdx` is the packed `{cx, cy}` center from `xmm6/xmm7`.
- `rcx` points to the destination matrix at `rbp+0x60`.

The rotate-back call at `181150f3d..181150f5a` is the symmetric inverse:

```text
181150f3d  negl    %r15d
181150f40  movd    %r15d,%xmm2
181150f45  cvtdq2pd %xmm2,%xmm2
181150f49  movsd   0x33c727(%rip),%xmm3  # 0x18148d678
181150f51  movq    %xmm10,%rdx
181150f56  leaq    (%rbp),%rcx
181150f5a  callq   0x1811512a0
```

`FUN_1811512a0` changes `rcx` to a stack-local matrix before calling
`FUN_1812943d0`, but does not rewrite `rdx`, `xmm2`, or `xmm3` before that
call. Those registers therefore flow through to OpenCV
`getRotationMatrix2D_`. The direct disassembly of `FUN_1812943d0` confirms it
copies `xmm3` to its scale register, converts angle via the `pi/180` constant,
then writes the standard OpenCV 2x3 matrix.

Implication: KiraKira's matrix scale is pinned at `1.0` for both forward and
rotate-back passes. The current residual should no longer be chased as a
center/scale/sign ambiguity; likely remaining causes are OpenCV 4.5.5
interpolation/rounding behavior, a small ROI copy convention, or another
pre/post ray detail.

An objdump read of `FUN_181297ac0 @ 0x181297ac0` shows the wrapper checking
input/output descriptors, wrapping InputArray/OutputArray, and forwarding
`flags=1` into the OpenCV `warpAffine` implementation. Around
`181297eeb..181297fbc` it builds/inverts a 2x3 matrix when the inverse-map bit
is not set, matching standard OpenCV forward-matrix behavior for
`INTER_LINEAR`. No evidence was found for a KiraKira-specific center/scale
rewrite in this wrapper. The next useful binary audit is below the wrapper:
follow the calls reached from `FUN_181297ac0` with `flags=1`,
`borderMode=BORDER_CONSTANT`, and same Mat src/dst to identify the exact
OpenCV 4.5.5 interpolation/rounding/SIMD branch.

Follow-up objdump of `181297fbc..181298520` shows the wrapper calls
`0x181298180` after preparing the inverted matrix, source/destination data
pointers, strides, dimensions, and border arguments. That callee builds fixed
coordinate tables with `cvtsd2si`/`cvttsd2si`-style conversions, then calls into
an AVX-heavy loop beginning at `0x181298460`. This supports the current
conclusion that the remaining C++ residual is likely the exact OpenCV 4.5.5
linear-interpolation fixed-point table / rounding branch, not another KiraKira
parameter mapping. A production change should wait for either a native OpenCV
4.5.5 helper probe or a more complete port of the `0x181298180` /
`0x181298460` interpolation path.

### 2026-06-17 single-ray returned reference triage

`kirakira_single_ray_20260606` and the strength0 recapture are now imported.
A read-only explorer remeasured the current best C++ path
(`--seed-mode aex --falloff box3 --gain-scale 0.62 --compose-mode
aex-screen-over --filter-border mirror --auto-length-scale --comp-width 1920
--aggregation-mode fd90-exact`) and found:

- single-ray strength100: vertical `max=13 mean=1.3931`, horizontal
  `13/1.4214`, diagonal `23/1.2602`, diagonal2 `23/1.2959`, rotation13
  `66/1.6628`;
- strength0 brightness 9.4: vertical/horizontal exact, diagonal/diagonal2
  `max=3 mean=0.0238`;
- strength0 recapture: brightness1 `max=1 mean=0.0397`, brightness25/50/94
  exact.

Current refs are sufficient to separate ray order, angle table, fd90 scalar
non-use, compose, and strength0 brightness scale. Do not request more equal-ray
sweeps. The next implementation target is the remaining `FUN_181150790` helper
fidelity: OpenCV-style centered ROI/copy, `getRotationMatrix2D`, `warpAffine`,
`boxFilter` border/anchor behavior, rotate-back, and final centered copy using
the confirmed `+4.0` temp extents.

### 2026-06-17 fixed-point warpAffine diagnostic

A second objdump/Ghidra pass below the `FUN_181297ac0` wrapper pinned the first
warpAffine table scale:

- `DAT_1814dee28 = 1024.0`.
- `DAT_1814d6750 = 1/65536`.
- `0x1814def00` is the dword reorder table `[0,2,4,6,1,3,5,7]`.
- `0x1814def20` is the byte shuffle pattern
  `00 01 04 05 02 03 06 07 08 09 0c 0d 0a 0b 0e 0f`, repeated.

`FUN_181298180` allocates two int32 x-coordinate tables with dst width and fills
them as:

```c
x_table0[x] = round((double)x * M0 * 1024.0);
x_table1[x] = round((double)x * M3 * 1024.0);
```

The y-side setup in `FUN_181298460` uses truncation plus a negative correction
to get floor-like behavior, then clamps the source row to `height - 1`. This
confirms the remaining warp residual is inside OpenCV 4.5.5 fixed-point
interpolation/table consumption, not matrix center, matrix scale, ray order, or
fd90 aggregation.

The C++ CLI now has diagnostic-only rotate filters:

- `--rotate-filter bilinear-fixed1024-floor5`
- `--rotate-filter bilinear-fixed1024-round5`

These apply the confirmed `1024.0` coordinate scale, then reduce the fractional
part to 5-bit bilinear weights. They are deliberately not the default. Measured
against `kirakira_single_ray_20260606`, the floor5 mode gives:

- vertical strength100 `max=13 mean=1.3931`;
- horizontal strength100 `max=13 mean=1.4214`;
- diagonal strength100 `max=23 mean=1.2603`;
- diagonal2 strength100 `max=23 mean=1.2956`;
- strength0 vertical/horizontal exact, diagonal/diagonal2 `max=3 mean=0.0238`;
- rotation13 `max=66 mean=1.6631`.

The round5 mode is effectively the current fixed5 result:

- vertical strength100 `max=13 mean=1.3931`;
- horizontal strength100 `max=13 mean=1.4214`;
- diagonal strength100 `max=23 mean=1.2604`;
- diagonal2 strength100 `max=23 mean=1.2959`;
- strength0 vertical/horizontal exact, diagonal/diagonal2 `max=3 mean=0.0238`;
- rotation13 `max=66 mean=1.6628`.

The older all-ray probe also stays red and essentially unchanged:

| rotate filter | case_0001 | case_0002 | case_0003 |
| --- | ---: | ---: | ---: |
| bilinear | `max=21 mean=0.8291` | `max=24 mean=1.1609` | `max=233 mean=53.8132` |
| bicubic | `max=120 mean=7.8864` | `max=120 mean=8.0026` | `max=229 mean=49.3128` |
| bilinear-fixed5 | `max=21 mean=0.8288` | `max=24 mean=1.1608` | `max=233 mean=53.8134` |
| bilinear-fixed1024-floor5 | `max=21 mean=0.8304` | `max=24 mean=1.1615` | `max=233 mean=53.8131` |
| bilinear-fixed1024-round5 | `max=21 mean=0.8288` | `max=24 mean=1.1609` | `max=233 mean=53.8134` |

Conclusion: simple coordinate quantization is rejected as a closing model. The
next useful KiraKira work is to inspect or port `FUN_1811d88c0` and the AVX
consumer path from `FUN_181298460`, including the weight table generated from
the `1/65536` scale and the shuffle/reorder tables above. Do not promote a
PNG-only rotate-filter tweak from these diagnostics.

2026-06-17 follow-up diagnostic: decomp of `FUN_181298460` shows the current
path writes `undefined2` elements, so the CLI gained three more diagnostic-only
rotate filters:

- `--rotate-filter bilinear-fixed5-u16`
- `--rotate-filter bilinear-fixed1024-round5-u16`
- `--rotate-filter bilinear-fixed1024-opencvtab`

The `u16` filters quantize each warp sample to a 16-bit value. The `opencvtab`
filter uses the confirmed `1024.0` coordinate scale, 5-bit `INTER_TAB_SIZE=32`
fractions, integer bilinear weights summing to 1024, and `(accum + 512) >> 10`
rounding on 16-bit samples. This tests the scalar version of the simple OpenCV
table hypothesis suggested by `FUN_181298180`/`FUN_181298460`; it is still not
a full port of the `VPGATHERDD` / `VPBLENDW` / `VPSHUFB` / `VPERMD` consumer.

Direct objdump of the aligned `FUN_181298460` vector branch pins the table
consumer more tightly:

```asm
181298563  VLDDQU YMM1,ymmword ptr [RAX + RCX*0x4 + 0x20]
181298569  VLDDQU YMM2,ymmword ptr [RAX + RCX*0x4]
18129856e  VPGATHERDD YMM3,dword ptr [R8 + YMM1*0x1 + -0x2],YMM0
181298579  VPGATHERDD YMM1,dword ptr [R8 + YMM2*0x1],YMM0
18129857f  VPBLENDW YMM0,YMM1,YMM3,0xaa
181298585  VPSHUFB YMM1,YMM0,YMM5
18129858a  VPERMD YMM2,YMM6,YMM1
18129858f  VPMASKMOVD ymmword ptr [RDI + -0x20],YMM4,YMM2
```

The unaligned destination branch repeats the same gather/blend/shuffle/reorder
sequence at `181298663..18129868f`, but stores with `VMOVDQU`. The scalar tail
still reads only `word ptr [row_base + x_table[i]]`. Therefore the vector path
is not a normal four-neighbor bilinear sampler in the shape implemented by
`bilinear-fixed1024-opencvtab`; it consumes an OpenCV internal 32-bit offset
layout, gathers two 8-lane dword groups, takes alternating 16-bit lanes via
`VPBLENDW 0xaa`, then uses `0x1814def20` and `0x1814def00` to pack/reorder 16
u16 outputs. A future closing diagnostic should port this table consumer
directly, instead of adding more high-level bilinear rounding variants.

A read-only subagent corrected one important interpretation: the `+0x20` load
is not the second table from `FUN_181298180`; it is the next eight dwords of the
same table. The aligned vector loop handles 16 destination pixels by loading
`x_table[x+8..x+15]` into `YMM1` and `x_table[x+0..x+7]` into `YMM2`, gathering
`[row + x_table[x+8..x+15] - 2]` and `[row + x_table[x+0..x+7]]`, then packing
the desired u16 halves. To test that instruction-shaped hypothesis without
promoting it, the CLI gained another diagnostic-only rotate filter:

- `--rotate-filter nearest-fixed1024-u16-byteoffset`

This samples a quantized u16 row by `round(x * 1024.0)` as a byte offset and
emulates unaligned little-endian u16 reads. It is deliberately a red diagnostic,
not a candidate default.

Measured against `kirakira_single_ray_20260606`:

- `bilinear-fixed1024-round5-u16`: vertical `max=13 mean=1.3931`,
  horizontal `13/1.4214`, diagonal `23/1.2603`, diagonal2 `23/1.2959`,
  strength0 diagonal/diagonal2 `max=3 mean=0.0238`, rotation13
  `max=66 mean=1.6628`.
- `bilinear-fixed1024-opencvtab`: vertical `max=13 mean=1.3931`,
  horizontal `13/1.4214`, diagonal `23/1.2602`, diagonal2 `23/1.2956`,
  strength0 diagonal/diagonal2 `max=3 mean=0.0238`, rotation13
  `max=66 mean=1.6631`.
- `nearest-fixed1024-u16-byteoffset`: vertical/horizontal strength100 stay at
  `max=13 mean=1.3931/1.4214`, but diagonal/diagonal2 worsen to
  `max=108 mean=18.9862/18.9838`; strength0 diagonal/diagonal2 worsen to
  `max=112 mean=27.0292`; rotation13 worsens to `max=107 mean=18.9528`.

Measured against the older all-ray rotate-filter probe:

| rotate filter | case_0001 | case_0002 | case_0003 |
| --- | ---: | ---: | ---: |
| bilinear-fixed5-u16 | `max=21 mean=0.8288` | `max=24 mean=1.1609` | `max=233 mean=53.8134` |
| bilinear-fixed1024-round5-u16 | `max=21 mean=0.8288` | `max=24 mean=1.1609` | `max=233 mean=53.8133` |
| nearest-fixed1024-u16-byteoffset | `max=63 mean=5.1635` | `max=68 mean=5.9661` | `max=255 mean=62.6839` |
| bilinear-fixed1024-opencvtab | `max=21 mean=0.8305` | `max=24 mean=1.1616` | `max=233 mean=53.8131` |

Conclusion: 16-bit sample quantization and the simple scalar OpenCV coefficient
table are also rejected as closing models. Direct byte-offset nearest sampling
is rejected as a standalone rotate sampler too. Keep these flags as diagnostics
only. The next useful binary-backed move is to recover the exact
`WarpAffineInvoker` dispatch/type path and its caller-side table layout, not to
add more high-level interpolation toggles.

2026-06-17 Ghidra MCP follow-up: `FUN_181297ac0` is the OpenCV 4.5.5
`cv::warpAffine` body. It takes `flags & 7` as interpolation at `181297b45..54`,
rejects channel-heavy cubic/lanczos paths at `181297b59..181297b73`, creates
the destination with the source type at `181297d57..181297d7c`, validates the
matrix as type 5/6 and shape 2x3 at `181297e58..181297e7f`, optionally inverts
the 2x3 matrix when `flags & 0x10` is clear at `181297ee1..181297fbc`, then
passes source/destination descriptors, dimensions, matrix pointer, interpolation
mode, border mode, and border value into `FUN_181298180` at
`181297fbc..18129803d`.

The nearby byte-offset functions are now separated by role:

- `FUN_181298180` builds a `cv::WarpAffineInvoker` (`decomp` names the vtable)
  and runs it through `FUN_1811d88c0`.
- `FUN_181298460` is the 16-bit/store-16-wide AVX implementation referenced by
  the `WarpAffineInvoker` table (`1814deee0` / `18190e854` data xrefs).
- `FUN_1812986f0` is the 32-bit/store-8-wide sibling referenced by the same
  invoker table (`1814deec8` / `18190e860` data xrefs).
- `FUN_181298930` and `FUN_1812989d0` are separate
  `cv::opt_AVX2::resizeNNInvokerAVX2/AVX4` wrappers, called from
  `FUN_1812656d0` at `18126595a` / `18126593c`; they should not be used as
  evidence that the KiraKira warpAffine residual is nearest-neighbor.

Implication: the `nearest-fixed1024-u16-byteoffset` diagnostic is useful only as
a negative control. It matches the gather/tail shape but not the complete
warpAffine branch. The next bounded task is to identify which `WarpAffineInvoker`
vtable entry is selected for KiraKira's temp Mat type and whether the 16-bit or
32-bit sibling is used in the actual helper path.

Subagent cross-check of the `FUN_181297ac0 -> FUN_181298180` call fixes the
argument map for that bounded task:

| `FUN_181298180` input | Source in `FUN_181297ac0` | Evidence |
| --- | --- | --- |
| `param_1` / `RCX` | `src.type & 0xfff` | `181297fbc..181297fc3` |
| `param_2` / `RDX` | `src.data` | `18129800d..181298035` |
| `param_3` / `R8` | `src.step` | `18129802d` |
| `param_4` / `R9D` | `src.cols` | `181298025` |
| stack `+0x20` | `src.rows` | `18129801a..181298021` |
| stack `+0x28` | `dst.data` | `18129800d..181298015` |
| stack `+0x30` | `dst.step` | `181298000..181298008` |
| stack `+0x38` | `dst.cols` | `181297ff5..181297ffc` |
| stack `+0x40` | `dst.rows` | `181297fea..181297ff1` |
| stack `+0x48` | inverted/ready 2x3 matrix pointer | `181297fdd..181297fea` |
| stack `+0x50` | normalized interpolation (`flags & 7`, with `3 -> 1`) | `181297fc9..181297fd9`, `181297e42..181297e4e` |
| stack `+0x58` | `borderMode` (`param_6`) | `181297fce..181297fd5` |
| stack `+0x60` | border value / pointer (`param_7`) | `181297fc9` |

Other caller-side facts:

- `flags & 7` is captured early as interpolation at `181297b45..181297b54`.
- `flags & 0x10` controls inverse-map behavior; when clear, the 2x3 matrix is
  inverted at `181297ee1..181297fbc`.
- The matrix input is required to be `CV_32F` or `CV_64F` and shaped 2x3 at
  `181297e51..181297e7f`.
- `FUN_1812969f0` / `FUN_181295e60` are earlier fast/IPP-like attempts; the
  analyzed fallback path reaches `FUN_181298180` at `181297cd2..18129803d`.

Do not treat `dst.cols` or `src.cols` as RGBA pixel count inside the AVX
consumer without checking `src.type`. `FUN_181298460` operates on 16-bit
elements with 16-wide stores (`AND R13,-0x10`, word tail
`1812985a4..1812985ad`), while `FUN_1812986f0` operates on 32-bit elements with
8-wide stores (`AND R13,-0x8`, dword tail `181298804..18129880c`). The next
diagnostic should log or reproduce this element-layout choice for KiraKira's
actual temp Mat type before any production warp sampler change.

Reading `FUN_181150790` through Ghidra MCP points the actual helper toward the
32-bit/float path:

- The first warp at `1811508d7..181150941` wraps `R14` as both input and output
  Mat, uses the matrix at `RBP+0x60`, passes `flags=1`, `borderMode=0`, and
  `dsize=(R14.width,R14.height)`. This is `warpAffine(R14, R14, M, R14.size(),
  INTER_LINEAR, BORDER_CONSTANT, ...)`.
- The second warp at `181150f80..181150ff8` wraps `R12` as both input and
  output Mat, again with `flags=1`, `borderMode=0`, and
  `dsize=(R12.width,R12.height)`.
- The intervening manual blur modes operate on the same `R14`/`R12` buffers with
  scalar float instructions (`MOVSS`, `MULSS`, `ADDSS`) throughout
  `1811509e0..181150f06`.

Implication: KiraKira's current residual should prioritize the 32-bit
`FUN_1812986f0` `WarpAffineInvoker` sibling and the exact OpenCV
INTER_LINEAR float temp behavior. The 16-bit `FUN_181298460` diagnostics remain
useful evidence about the shared dispatch family, but they are unlikely to be
the production path for the current float temp helper.

### 2026-06-18 Ghidra MCP vtable/operator correction

Ghidra MCP follow-up refined the `WarpAffineInvoker` dispatch target. In
`FUN_181298180`, the constructed invoker installs the active vtable at
`0x1814de968`, then runs through `FUN_1811d88c0`. The scheduler is a parallel
executor; in the direct/small-range case it calls vtable slot `+8`.

Important refs:

- `0x1814de968 + 0x08 -> FUN_181293ad0`.
- `FUN_1811d88c0` calls `(**(code **)(*param_2 + 8))(param_2,param_1)` when it
  does not split the range.
- `FUN_181293ad0` is the actual `WarpAffineInvoker::operator()` body. It builds
  tile-local coordinate maps, 5-bit interpolation coefficient indexes, and then
  calls `FUN_181297270`.
- `FUN_1812986f0` is a lower-level 32-bit/store-8 row gather sibling used by
  that dispatch family; it should not be treated as a standalone high-level
  warp sampler.

`FUN_181293ad0` shows two map-building paths around `param_1 + 0xc8`: one path
builds a `CV_16SC2`-style map, while the nonzero path also builds a type-2
coefficient/index map where each entry is shaped like
`((yfrac & 0x1f) << 5) + (xfrac & 0x1f)`. Both feed `FUN_181297270`, which is
now the better next binary target than more CLI interpolation toggles.

Revised next action: inspect/decompile `FUN_181297270` and the
`FUN_181293ad0 -> FUN_181297270` argument descriptors to determine the exact
OpenCV 4.5.5 remap/interpolation table path selected for KiraKira's float temp
Mats. Do not promote a production change based only on `FUN_1812986f0` row
gather shape or on another PNG-only rotate-filter probe.

`FUN_181297270` is confirmed as OpenCV 4.5.5 `cv::remap`
(`imgwarp.cpp`, assertion strings `cv::remap`, `!_map1.empty()`, and the map
type assertion are present). For KiraKira's `INTER_LINEAR` path it loads the
linear interpolation function table at `0x181824b70 + depth*8`; for float
depth 5 this resolves to `FUN_181288940`.

`FUN_181288940` is the float `remapBilinear` body. It:

- Computes channel count from Mat type with `((type >> 3) & 0x1ff) + 1`.
- Uses `map1` as packed signed 16-bit `(x,y)` pairs and `map2` as unsigned
  16-bit interpolation-table indexes.
- Loads four float weights from `coeff_table + map2[i] * 16`.
- For in-bounds pixels, computes the normal four-neighbor bilinear sum:
  `p00*w0 + p10*w1 + p01*w2 + p11*w3`, with specialized branches for 1, 2, 3,
  and 4 channels and a generic multi-channel branch.
- Handles out-of-bounds pixels through the `borderMode` argument, including the
  constant-border path used by KiraKira's `warpAffine(..., BORDER_CONSTANT)`.

This makes the next candidate implementation much less mysterious: porting the
`FUN_181293ad0` map builder plus the relevant `FUN_181288940` float bilinear
consumer should be closer than trying to infer remap behavior from ad hoc
rotate-filter switches.

The C++ CLI now has a layer-isolated diagnostic for that consumer:

```text
cli/OLMKiraKira/olmkirakira_cli --diag-remap-bilinear-f32
```

It builds a tiny synthetic float source, packed signed-16 `map1` coordinates,
unsigned-16 `map2` coefficient indexes, and the 1024-entry OpenCV 5-bit linear
coefficient table. It does not run a PNG render and deliberately does not hook
into `--rotate-filter`; it only verifies the `FUN_181288940` consumer rule and
constant-border tap substitution. Smoke wrapper:

```text
python3 refs/scripts/smoke_olmkirakira_cpp_remap_bilinear_f32_diag.py
```

Current result: all four synthetic cases pass (`integer`, `fractional`,
`right_bottom_constant`, `negative_constant`). The KiraKira single-ray render
smoke remains unchanged after adding the diagnostic: 18/18 OK with the current
known residuals (`vertical/horizontal max=13`, `diagonal/diagonal2 max=23`,
`rotation13 max=66`).

`FUN_181294950` is the interpolation coefficient-table initializer used by
`cv::remap`:

- `param_1=1` selects linear interpolation, with float table base
  `DAT_1818441a0` and short table base `DAT_1818481a0`.
- `param_1=2` selects cubic, and `param_1=4` selects Lanczos4.
- It builds a 32x32 table. The float table stores normalized products of the
  one-dimensional interpolation coefficients. The short table scales each row
  by `0x8000`, rounds with `CVTSS2SI`, then adjusts one coefficient so the row
  sum is exactly `0x8000`.
- At return, the second argument chooses table type: false returns the float
  table pointer, true returns the short table pointer.
- `FUN_181297270` passes `param_2 = (src_depth == 0)` into
  `FUN_181294950`. KiraKira's float temp path has depth 5, so it selects the
  float table, not the short table.

Implication: the previously added u16/short-table rotate diagnostics are useful
negative controls, but the production KiraKira helper should pursue
`FUN_181293ad0` map generation plus the float-table `FUN_181288940` consumer.

`FUN_181293ad0` map generation for the `INTER_LINEAR` path is now pinned as the
standard OpenCV fixed-point split with `AB_BITS=10` and `INTER_BITS=5`.

Per tile row:

```text
base_x = cvRound((M01 * dst_y + M02) * 1024.0) + 16
base_y = cvRound((M11 * dst_y + M12) * 1024.0) + 16
```

Per absolute destination x, using the x-tables built by `FUN_181298180`:

```text
X = base_x + x_table0[x]    // x_table0[x] = cvRound(M00 * x * 1024.0)
Y = base_y + x_table1[x]    // x_table1[x] = cvRound(M10 * x * 1024.0)

map1.x = saturate_i16(X >> 10)
map1.y = saturate_i16(Y >> 10)
map2   = (((Y >> 5) & 31) << 5) | ((X >> 5) & 31)
```

The scalar tail at `181294080..181294102` shows the formula directly:
`SAR edx,0x5`, `SAR ecx,0x5`, then `SAR r8d,0x5` for map1 and
`(y_frac5 << 5) + x_frac5` for map2. The vector path at
`181293f60..181294034` performs the same calculation in eight-pixel chunks
with `PSRAD 5`, `PAND 0x1f`, `PSLLD 5`, and `POR`.

The C++ CLI now has a matching layer-isolated map diagnostic:

```text
cli/OLMKiraKira/olmkirakira_cli --diag-warpaffine-map-f32
python3 refs/scripts/smoke_olmkirakira_cpp_warpaffine_map_f32_diag.py
```

Current diagnostic cases pass for integer, fractional, carry/wrap,
negative-fraction, positive-saturate, and negative-saturate coordinates. This
diagnostic intentionally tests only the fixed-point map split; it does not yet
replace the current hand-written warp in production rendering.

The C++ CLI also has a layer-joined diagnostic that runs the Ghidra-pinned
`FUN_181293ad0` map split into the `FUN_181288940` float remap consumer:

```text
cli/OLMKiraKira/olmkirakira_cli --diag-warpaffine-remap-f32
python3 refs/scripts/smoke_olmkirakira_cpp_warpaffine_remap_f32_diag.py
```

Current result: all synthetic cases pass. Covered cases are integer identity,
fractional translation, right/bottom constant-border substitution, and negative
constant-border substitution. This is still a diagnostic only; production PNG
rendering continues to use the existing experimental warp modes until the full
two-temp OpenCV/AEX choreography is wired to the same map/remap path.

2026-06-18 integration probe: the C++ CLI now exposes
`--warp-mode aex-two-temp-mapremap-f32`, which keeps the current two-temp
choreography but forces both `warp_getrot_direct` passes through the
Ghidra-pinned map/remap sampler (`FUN_181293ad0` map split plus
`FUN_181288940` float remap consumer). This mode is diagnostic only and is not
the default.

Single-ray software/cuda probe command:

```text
python3 refs/scripts/smoke_reference_request_cli_probe.py \
  --request-id kirakira_single_ray_20260606 \
  --expected-effect "OLM Kira Kira" \
  --build-script refs/scripts/build_olmkirakira_cli.sh \
  --command '"cli/OLMKiraKira/olmkirakira_cli" --input "{input}" --params "{params}" --output "{output}" --seed-mode aex --falloff box3 --gain-scale 0.62 --ray-mode axis-rotate --compose-mode aex-screen-over --filter-border mirror --warp-mode aex-two-temp-mapremap-f32 --auto-length-scale --comp-width 1920'
```

Result: 18/18 pass under the broad measurement thresholds, with essentially the
same residual as `aex-two-temp`: axis strength=100 `max=13`, diagonal
strength=100 `max=23`, strength=0 axis exact, strength=0 diagonal `max=3`, and
rotation13 `max=66`. This suggests the remaining KiraKira residual is not
explained solely by the per-pixel OpenCV map/remap fixed-point split.

The lower-level `--rotate-filter bilinear-warpaffine-remap-f32` path was also
measured on the same single-ray request. It keeps the current `aex-two-temp`
warp mode but swaps the per-pass sampler to the map/remap float diagnostic.
The result was effectively identical to the baseline: vertical/horizontal
strength100 stayed at `max=13 mean=1.3931/1.4214`, diagonal/diagonal2 stayed
near `max=23 mean=1.2604/1.2959`, strength0 axis cases stayed exact,
strength0 diagonal cases stayed `max=3 mean=0.0238`, and rotation13 stayed
`max=66 mean=1.6628`. The baseline diagonal mean was slightly lower
(`1.2602`), so this remains a negative diagnostic rather than a promotable
render path.

2026-06-18 follow-up diagnostics:

- `--box-accum-mode float` was added as a diagnostic for the hand-written
  `direction_box_blur` path. It changes each box pass to accumulate/divide in
  `float` instead of `double`, approximating a possible CV_32F OpenCV filter
  path. On `kirakira_single_ray_20260606` with `--warp-mode aex-two-temp`, the
  metrics were identical to the default (`vertical/horizontal max=13`,
  diagonal/diagonal2 max=23`, rotation13 max=66). Box accumulation precision is
  therefore not the visible residual source.
- `--warp-mode aex-two-temp-center-minus-half-forward-only` and
  `--warp-mode aex-two-temp-center-minus-half-back-only` were added as
  diagnostics after the symmetric center-minus-half probe gave mixed results.
  Forward-only: diagonal `max=24 mean=1.2627`, diagonal2 `max=23 mean=1.2865`,
  rotation13 `max=66 mean=1.6587`. Back-only: diagonal
  `max=24 mean=1.2584`, diagonal2 `max=23 mean=1.3061`, rotation13
  `max=66 mean=1.6583`. Both are mixed and should remain diagnostics, not
  defaults.

Implication: the broad `FUN_181150790` search space is now narrower:
box accumulation precision, final-copy one-pixel offsets, symmetric/asymmetric
center-minus-half, and the OpenCV map/remap fixed-point split are not sufficient
to explain the remaining residual. The next useful binary-backed target is the
caller-built temp `Rect` / Mat descriptor shape or a more exact reconstruction
of OpenCV 4.5.5 `boxFilter` internals beyond simple argument selection.

2026-06-18 live Ghidra / disasm Rect audit:

The caller-built `Rect` and `dsize` packing in `FUN_181150790` now match the
current C++ two-temp model:

- Initial centered copy into `R14`:
  - `181150805..18115081f` computes `cx = trunc(R14.rows * 0.5f)` and
    `cy = trunc(R14.cols * 0.5f)` into `xmm7/xmm6` using
    `DAT_181486c1c`.
  - `181150827..18115084f` computes
    `rect.y = trunc(R14.cols * 0.5f) - src.cols / 2` and
    `rect.x = trunc(R14.rows * 0.5f) - src.rows / 2` under the decompiler's
    row/col naming. Interpreted through `cv::Mat` layout (`rows` at `+0x8`,
    `cols` at `+0xc`) plus `FUN_181156cd0`'s `Rect(x,y,width,height)`
    constructor, this is the same centered ROI formula used by
    `copy_centered_roi`.
  - `181150852..18115086b` stores the four-int `Rect` and calls
    `FUN_181156cd0`; `181150874..181150892` copies `param_2` into that ROI via
    `cv::Mat::copyTo`.
- Forward `warpAffine` dsize:
  - `18115090e..18115091a` packs `R9 = (R14.rows << 32) | R14.cols`, which is
    OpenCV `Size(width=cols,height=rows)` under Windows x64 aggregate passing.
    This matches the current `warp_getrot_direct(..., dst_width=rw,
    dst_height=rh)` shape; no swapped dsize bug is visible here.
- Rotate-back `warpAffine` dsize:
  - `181150fc3..181150fd1` packs `R9 = (R12.rows << 32) | R12.cols`, again
    `Size(width=cols,height=rows)`.
- Final centered copy from `R12` into `param_4`:
  - `181151001..181151024` rebuilds the same `Rect` from the previously saved
    centered offsets (`local_1bc/local_1b8`) and destination frame dimensions,
    then calls `FUN_181156cd0`.
  - `18115102a..181151049` copies the ROI into `param_4` with `copyTo`.

Implication: the naive remaining "Rect/copy/dsize swapped" hypotheses are now
binary-rejected. The still-useful `FUN_181150790` target is not the centered
ROI formula itself; it is either a deeper OpenCV 4.5.5 primitive detail
(`boxFilter`/same-Mat `warpAffine` behavior) or another pre/post ray operation
outside these four `Rect` constructions.

Subagent read-only audit (2026-06-18) independently confirmed the same
descriptor IR from `FUN_18114f4a0` and `FUN_181150790`:

- The caller temp sizes are
  `tmp_w=max(src_w+4, trunc(src_w*abs(cos)+src_h*abs(sin)+4.0f))` and
  `tmp_h=max(src_h+4, trunc(src_w*abs(sin)+src_h*abs(cos)+4.0f))`.
- The caller builds two same-sized PF-backed temp Mats (`tempA`/`tempB`) plus
  the final ray Mat, then passes `tempB` as the helper's stack argument.
- `FUN_181156cd0` is confirmed as `Rect(x,y,width,height)`, with ROI `rows`
  loaded from rect height and `cols` from rect width.
- The current CLI `aex-two-temp` path matches that choreography: centered
  copy into `tempA`, same-Mat forward warp, three horizontal boxFilter passes
  into/within `tempB`, same-Mat rotate-back, and centered final crop.

2026-06-18 same-Mat `warpAffine` alias guard:

- `FUN_181297ac0` guards API-level same-Mat calls before the fallback
  `FUN_181298180` path samples the source. After destination creation it
  compares the resolved destination/source data pointers
  (`decomp/OLMKiraKira.aex.c.txt:3775537`).
- If the pointers match, it clones or redirects the source descriptor through
  `FUN_1811585b0` / `FUN_181157ed0` before continuing
  (`decomp/OLMKiraKira.aex.c.txt:3775538..3775539`).
- Therefore `warpAffine(R14, R14)` and `warpAffine(R12, R12)` are same-Mat at
  the API/choreography level, but OpenCV protects the source from destructive
  in-place sampling. Reject "destructive same-buffer warp sampling" as the
  residual explanation.
- The current CLI/Mac value-return `warp_getrot_direct` / `WarpGetRotDirect`
  already has equivalent source/destination separation. This fact sharpens the
  IR and request wording; it is not a production patch by itself.
- Remaining useful evidence is exact OpenCV 4.5.5 `boxFilter` / FilterEngine
  behavior or a small pre/post ray detail around `FUN_181150790`, not another
  same-Mat alias-destruction toggle.

2026-06-18/19 environment / next-evidence audit:

- `refs/scripts/setup_olmkirakira_opencv455_probe_env.sh` now creates a
  reproducible local probe environment at `/tmp/olm_cv455_probe_venv`
  (`opencv-python-headless==4.5.5.64`, `numpy==1.26.4`).
- The local 4.5.5 Python probe reproduces the earlier 4.10/4.13 metrics, so
  broad OpenCV version drift is not the leading residual explanation.
- This is still not a closing binary fact: the AEX-selected branch is the
  Windows AVX2 `FUN_1812e39d0` path, while the local probe is an arm64 Python
  wheel.
- The next useful KiraKira proof is either:
  1. Open `OLMKiraKira.aex` in Ghidra and continue reading the embedded
     OpenCV 4.5.5 `boxFilter` / FilterEngine path, especially the
     `FUN_181281260` optimized branch selected on the Windows host, or
  2. build a separate OpenCV **4.5.5-linked** microprobe that runs exactly the
     binary-backed choreography: centered ROI copy, alias-safe
     `cv::warpAffine(mat, mat)`, `cv::boxFilter` first pass from tempA to
     tempB, subsequent same-Mat passes, second alias-safe
     `cv::warpAffine(mat, mat)`, and final centered ROI copy.

Until one of those evidence sources exists, keep the C++ `aex-two-temp` /
map-remap modes diagnostic and avoid more high-level PNG-only toggles.

2026-06-18 Windows runtime trace return:

- Imported return package:
  `~/Downloads/olm_runtime_trace_return_windows_20260618.zip`.
  Normalized summary lives at `refs/reports/runtime_trace_summary.md`.
- The dispatcher `FUN_181281260` was confirmed in Ghidra to choose exactly one
  of:
  `FUN_1812e39d0` for feature `0xb`,
  `FUN_1812d7c40` for feature `6`, or
  `FUN_181280fa0` as baseline.
- OpenCV 4.5.5 feature mapping: `0xb = CV_CPU_AVX2`, `6 = CV_CPU_SSE4_1`.
- Live Windows `cdb` branch witness during the traced AE render hit
  `BRANCH_AVX2` first. Module base was `0x00007ffebda30000`, RIP was
  `0x00007ffebed139d0`, giving module-relative offset `0x12e39d0`, i.e.
  `FUN_1812e39d0`.
- Therefore the first `boxFilter` pass on the Windows reference machine uses
  the OpenCV 4.5.5 AVX2 FilterEngine constructor family. The high-level
  logical filter remains the same RowSum/ColumnSum pipeline already documented;
  the remaining residual should be treated as AVX2 helper fidelity or a narrow
  pre/post-ray detail, not an unknown dispatcher branch.
- Do not send another request asking which FilterEngine branch is selected.
  Next useful work is either reading/porting the selected AVX2 helper behavior
  or building an exact OpenCV 4.5.5-linked microprobe for the pinned helper
  choreography.
