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

Inside `FUN_181150790`:

- `181150805..18115081f` converts two descriptor dimensions to floats and
  multiplies by `DAT_181486c1c`.
- `.rdata 181486c10` shows `DAT_181486c1c = 0.5f`.
- `181150852..18115086b` builds an ROI-like rectangle and calls
  `FUN_181156cd0`.
- `181150874..181150892` copies the source into an intermediate via
  `FUN_18115cfb0`.
- `1811508a1..1811508c3` calls `FUN_1811512a0` to build a transform matrix.
- `1811508d7..181150941` calls `FUN_181297ac0`, which contains OpenCV
  `cv::warpAffine` strings and argument checks.
- `181150f3d..18115105d` rotates back through another `FUN_1811512a0`,
  `FUN_181157ed0`, `FUN_181297ac0`, and `FUN_18115cfb0` sequence.

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
- `normalize = byte [caller + 0x1a0]`; current refs have no evidence that this
  is false, and normalize=false probes are strongly negative.
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

Current interpretation:

- Existing probes show `rotate_border=constant` is slightly better than the old
  edge-clamp rule, and `rotate_filter=bilinear` beats the C++ bicubic proxy.
- The remaining residual is more likely exact OpenCV 4.5.5 `warpAffine`
  sampling/rounding or another pre/post ray detail than a simple boxFilter
  argument mismatch.

Do not adopt any new warp/crop change without a direct asm argument mapping or
a faithful local OpenCV 4.5.5 reproduction; image-diff-only tuning is too easy
to overfit here.
