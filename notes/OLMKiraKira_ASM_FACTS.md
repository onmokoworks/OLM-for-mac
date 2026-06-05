# OLMKiraKira ASM Facts

This page records objdump-first facts for the OLMKiraKira port. Treat Ghidra
decompilation as a map, not as proof. Treat Windows PNGs as verification data,
not as an algorithm source.

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

## cv::warpAffine Calls

`FUN_181297ac0` is the OpenCV `cv::warpAffine` wrapper:

- Decomp contains `cv::warpAffine` and
  `C:\Users\devbuild\Documents\4.5.5\sources\modules\imgproc\src\imgwarp.cpp`.
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
- The decomp/asm shape shows the rotate-back `warpAffine` dsize is the final
  ray descriptor (`param_5`) rather than a larger temporary canvas followed by
  an obvious center crop. A C++ diagnostic `--warp-mode aex-direct-back`
  approximates that direct writeback using the observed rotated-buffer center.
  It is also negative: `case_0001 mean=0.9928`, `case_0002 mean=1.3755`,
  `case_0003 mean=4.4660`.
- The remaining residual is more likely exact OpenCV 4.5.5 `warpAffine`
  source/destination Mat/ROI placement, dsize/crop behavior, sampling/rounding,
  or another pre/post ray detail than a simple boxFilter argument mismatch,
  naive getRotationMatrix2D center swap, `FUN_181157ed0` matrix adjustment, or
  direct rotate-back approximation.
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
- `--axis-fast-path false --rotate-size-mode aex-min4` forces 0/90-degree rays
  through the rotate/crop path too. It is mixed/negative:
  `case_0001 mean=0.8354`, `case_0002 mean=1.1847`,
  `case_0003 mean=2.0123`.
- `--axis-fast-path false` with the default round sizing is also negative:
  `case_0001 mean=0.8381`, `case_0002 mean=1.1847`,
  `case_0003 mean=2.1189`.

Keep the default axis fast path for current references. The no-axis-fast probe
is useful diagnostic evidence for future refs, but the current refs do not
support adopting it globally.

Do not adopt any new warp/crop change without a direct asm argument mapping or
a faithful local OpenCV 4.5.5 reproduction; image-diff-only tuning is too easy
to overfit here.
