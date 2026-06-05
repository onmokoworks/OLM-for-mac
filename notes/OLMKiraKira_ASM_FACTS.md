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
