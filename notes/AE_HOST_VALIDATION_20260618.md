# AE Host Validation 2026-06-18

Source return:
`handoffs/ae_host_validation_returns/ae_host_validation_return_20260618_232926_windows.zip`

Reports:

- `refs/reports/ae_host_validation_20260618_232926/exact_return/AE_HOST_EXACT_SUMMARY.md`
- `refs/reports/ae_host_validation_20260618_232926/exact_return/reports/AE_VALIDATION_EXACT_REPORT.md`

Render context:

- Host: Windows AE
- Renderer: Software (`project_gpu_accel_type.current_name=SOFTWARE`, raw `1816`)
- Exact policy: `max_diff == 0` only

## Exact Result

Overall exact result: `33/48` cases exact.

| Request | Exact | Cases | Interpretation |
| --- | ---: | ---: | --- |
| `ae_pixel_olmblur_20260606` | 3 | 7 | Mixed. `case_0005/0006/0007` exact; `case_0001/0002/0003/0004` fail. |
| `ae_pixel_olmcolorkey_20260606` | 8 | 9 | Strong. Core and Edge Thin exact; Edge Blur `case_0009` fails. |
| `ae_pixel_olmdistancegradation_20260606` | 11 | 12 | Strong. Only `case_0017` has tiny nonzero diff (`max=2`). |
| `ae_pixel_olmdistancegradation_blur_20260618` | 1 | 1 | Exact. |
| `ae_pixel_olmdistancegradation_extended_20260618` | 10 | 16 | Mixed. Several contour/extended cases still nonzero. |
| `ae_pixel_olmtoondilate_20260606` | 0 | 3 | Not exact; all cases have `max=255`. |

## Failure Buckets

- `OLMBlur`: `case_0001..0004` are stale-reference/package-reference drift,
  not an immediate algorithm failure. After normalizing the returned Windows
  AE Software PNGs as the reference, the current C++ CLI is exact on
  `case_0001..0004`; `case_0005..0007` remain tiny `max=1` CLI residuals.
- `OLMColorKey`: Windows AE-host exact proves old-reference agreement for
  `case_0001..0008`, with only Edge Blur `case_0009` differing from the old
  packaged expected PNG. Current CLI against normalized Software refs is exact
  only for `case_0001..0004` and `case_0007`; Edge Thin erode and Edge Blur
  still need binary-grounded work before Mac AE exact can be claimed.
- `OLMToonDilate`: all returned cases fail exact. This should be binary-grounded
  before more tuning; likely boundary/nearest-color or host context mismatch.
- `OLMDistanceGradation`: the AE-host exact failures mix stale-reference drift
  and real CLI residual. Normalized Software refs reduce some large old-reference
  failures (`case_0012` becomes CLI `max=7`), but the CLI is still not exact in
  the basic, extended, or Blur slices.

## Normalized Software Reference CLI Checks

The returned Windows AE Software PNGs were normalized into local reference
folders under:

- `refs/reports/ae_host_validation_20260618_232926/normalized_refs/`

The CLI checks are stored under:

- `refs/reports/ae_host_validation_20260618_232926/cli_checks/`

Exact CLI result against these normalized refs:

| Plug-in / slice | CLI exact cases | Residual summary |
| --- | ---: | --- |
| `OLMBlur` | 5 / 7 | `case_0001..0005` exact after non-Legacy round-to-nearest-even writeback; `case_0006..0007 max=1`. |
| `OLMColorKey` | 5 / 9 | `case_0001..0004` and `case_0007` exact; erode/Edge Blur residual remains. |
| `OLMToonDilate` C++ | 3 / 3 | Exact after replacing BFS with AEX-style two-pass chamfer propagation and premultiplying semi-alpha RGB. |
| `OLMDistanceGradation` basic | 0 / 12 | Small but nonzero residuals across all cases (`max=1..7`). |
| `OLMDistanceGradation` extended | 0 / 16 | Mixed residuals; some sparse high max values remain (`max=238..254`). |
| `OLMDistanceGradation` Blur | 0 / 1 | `case_0029 max=23 mean=0.2827`; still guarded only. |

This normalized-reference check is evidence for triage only. It is not a final
completion criterion; final completion remains Mac AE render exact against the
Windows Software reference.

## Next Action

Do not send another AE-host package before classifying these failures. The next
local action is to compare the failing cases against their packaged expected
PNGs and decide whether each failure is:

- package/request mismatch,
- AE render context mismatch,
- current implementation mismatch,
- or a known guarded residual.

Current classification:

- `OLMBlur case_0001..0004`: package/reference drift.
- `OLMBlur case_0005`: currently exact in CLI by using round-to-nearest-even
  (`nearbyint`) for non-Legacy 8/16bpc writeback while keeping Legacy
  `floor(x+0.5)`. Treat this as a compatibility shim, not the final binary
  proof: `.rdata` shows `DAT_18000d24c = 0.5`, and decomp writeback is
  `floorf(value + 0.5)`.
- `OLMBlur case_0006..0007`: tiny CLI residual (`max=1`) against normalized
  Software refs. Matching the AEX non-Legacy radius path (`pow(double,double)`
  then float sigma) reduces `case_0006` from 6 residual pixels to 1. The
  remaining `case_0006` pixel is exactly `185.5` before writeback (`%a`
  `0x1.73p+7`), and `case_0007` is still Legacy border/threshold behavior, so
  the next proof is accumulation/writeback ordering and Legacy border ownership
  rather than another global rounding tweak. Negative probes reject two tempting
  Legacy changes: initializing `all_same` from `-1` worsens `case_0007` to
  `max=16 / 21px`, and including border coordinate `0` worsens it to
  `max=15 / 5412px`.
- `OLMColorKey case_0005/0006/0008/0009`: implementation/spec residual in
  Edge Thin erode and Edge Blur paths.
- `OLMToonDilate case_0001..0003`: resolved for the normalized Windows
  Software references in C++ CLI and mirrored into the Mac plug-in core. The
  old packaged refs remain a separate guarded compatibility slice.
- `OLMDistanceGradation`: implementation/spec residual remains after removing
  stale-reference drift.

## ToonDilate Resolution

The AE-host exact report originally showed `0/3` exact for `OLMToonDilate`
against the stale packaged expected PNGs. Normalizing the returned Windows AE
Software PNGs and rerunning the local CLI isolated two issues:

- the local check had incorrectly forced `--comp-width 1920` for 960px cases;
- the implementation used BFS/nearest-source propagation, while the AEX
  `FUN_1801a6150` uses forward/backward raster passes and immediately copies
  the winning neighbour pixel.

After changing the C++ CLI and Mac plug-in core to the two-pass propagation
model, remaining `max=64` residuals were confined to pre-existing semi-alpha
pixels. The returned Software PNGs premultiply semi-alpha RGB as
`round(rgb * alpha / 255)`, so the port now mirrors that writeback.

Verification:

```sh
refs/scripts/build_olmtoondilate_cli.sh
python3 refs/scripts/smoke_olmtoondilate_cpp_normalized_ae_host_cli.py
xcodebuild -project mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj -configuration Debug build
```

## DistanceGradation Blur Probe

`OLMDistanceGradation` Blur Mode `case_0029` was probed locally against the
normalized Windows AE Software reference without changing production code.

Probe artifacts:

- `refs/reports/ae_host_validation_20260618_232926/distancegradation_blur_probe/probe_summary.md`
- `refs/reports/ae_host_validation_20260618_232926/distancegradation_blur_probe/probe_summary.json`

The current model is effectively `radius=60`, `mode=mirror`, OpenCV default
kernel (`max=23`, `mean=0.282702`). The best local sweep candidate was
`radius=55`, `ksize_over_6` (`max=23`, `mean=0.279377`). This is only a tiny
improvement and is not binary-grounded, so it should not be promoted. The next
useful proof is an actual OpenCV 4.5.5 `GaussianBlur`/kernel trace or a tighter
decomp fact for the Blur Size to kernel-size mapping.

## DistanceGradation Constant Probe

`OLMDistanceGradation` extended Constant interpolation cases were also checked
against the normalized Windows AE Software reference without changing
production code.

The tempting high-max failure is `case_0022`: the candidate writes gradation
red at a sparse set of pixels where the reference keeps the background color.
This initially looked like a Constant interpolation threshold issue, but local
probes rejected the alternate binary rules:

| Case | Current `X > 0` mean | `X >= 1` mean | `X == 0` mean | raw `X` mean |
| --- | ---: | ---: | ---: | ---: |
| `case_0020` | 0.056118 | 16.645927 | 53.961863 | 6.995106 |
| `case_0021` | 0.056174 | 78.877946 | 116.193826 | 23.866071 |
| `case_0022` | 0.524011 | 39.385518 | 115.725989 | 21.628636 |
| `case_0023` | 0.077814 | 10.244083 | 116.172186 | 4.574036 |

Conclusion: keep the current `X > 0` Constant rule. The remaining Constant
residual is more likely in the distance field itself, especially OpenCV
`distanceTransform(DIST_L2, DIST_MASK_PRECISE)` parity or border/minmax
normalization, not the Constant post-transform.
