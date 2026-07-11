# OpenCV Detour Current Gate - 2026-07-08

## Verdict

`cvDistTransform` P1 is already implemented and currently passes the local
detour gate. Treat "implement P1" as a stale task.

## FACTS

- `tools/emulation/opencv_impls.py` registers `dist_transform` for
  DistanceGradation `FUN_1812b15a0`.
- `tools/emulation/test_opencv_detour.py` validates:
  - `cvThreshold`
  - `cvDistTransform(DIST_L2, DIST_MASK_PRECISE)`
  - limited same-shape `cvResize`
  - limited `cvNormalize(NORM_MINMAX)`
- `python3 refs/scripts/smoke_emulation_opencv_detours.py` passed on
  2026-07-08 in the current workspace.
- The smoke also completes the synthetic `FUN_181174760` DistanceGradation
  fieldgen probe with callbacks:
  - `cv::dist_transform` x1
  - `cv::threshold` x1
  - `cv::resize_same_shape` x2
  - `cv::normalize_minmax` x1

## Current Boundary

- P1 is not a general OpenCV shim. It covers the observed DG call shape:
  `src_8u -> dst_32f`, `DIST_L2`, `DIST_MASK_PRECISE`, no labels/mask.
- The current `FUN_1812aef70` detour is only same-shape copy. Real resize,
  especially LINEAR, still needs separate validation and Windows gating.
- For current DG conformance work, the active lane is not "build P1"; it is the
  narrower 16bpc store/export rounding proof already queued for Windows.

## Verification

Command:

```bash
python3 refs/scripts/smoke_emulation_opencv_detours.py
```

Result summary:

```text
RESULT: all detour + bridge gates PASS (GATE A+B). GATE C blocked as documented.
[OK] emulation OpenCV detour smoke passed
```
