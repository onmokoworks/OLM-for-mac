# OLMDistanceGradation embedded OpenCV GATE C

- Date: `2026-07-17`
- AEX: `plugins_2025/DistanceGradation.aex`
- SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Status: bounded embedded-body gate passes; no `AE exact` promotion.

## FACT

- `WindowsOpenCVRuntime` supplies an opt-in single-thread TEB TLS epoch, FLS
  value store, and aligned allocator. It does not change global `AexLoader`
  policy.
- The embedded `cvThreshold` body completes in `11,084` instructions, creates
  its OpenCV FLS value, and is bit-identical to the independent OpenCV 4.5.5
  sidecar fixture.
- The embedded `cvDistTransform` body completes in `30,571..69,243`
  instructions across ten deterministic geometries. Six cases are bit-exact
  with the arm64 OpenCV 4.5.5 sidecar.
- `single_zero` and `box` have respectively `44` and `19` float32 words exactly
  one ULP below the arm64 sidecar. Runtime instruction hooks reach the AEX SIMD
  path at `0x181449a1f` (`RSQRTPS`) and its refinement/fallback block; this is
  not modeled as a tolerance or promoted to Windows host truth.
- No-source `all_nonzero` and `one_by_one_nonzero` produce the pinned embedded
  sentinel `0x5f7fffff` (`sqrtf(FLT_MAX)`), while the arm64 sidecar produces
  `0x4bf1433c` (`float32(sqrt(1e15))`).
- Three complete `FUN_181174760` field-generator fixtures run with no OpenCV
  detours and match the validated-detour final float32 arrays byte-for-byte:
  single source/Constant, three stripes/Power, and all foreground/Power.
- The embedded field generator takes more than `10,000` instructions, creates
  FLS state, and records no `cv::*` host callback. The paired baseline records
  exactly the five expected detours in binary call order.

## Bounded Host Contract

The current loader still returns zero for explicitly reported Windows/CRT
imports such as single-thread locks, optional environment and dynamic-library
queries, timers, and formatted diagnostics. Each GATE C result prints the exact
reached set as `bounded_stub_imports`. Therefore this proves bounded AEX body
execution and exposes SIMD/control-flow semantics; it is not full Windows CRT,
Windows AE, or `AE exact` evidence.

## INFERENCE

- The raw one-ULP and no-source differences do not affect the three checked
  field-generator outputs because the later threshold/normalization stages
  collapse them in those fixtures. Other thresholds and bit depths still need
  witness coverage before changing the production EDT.
- A production change must not apply a blanket `nextafter` rule. Any x86 SIMD
  compatibility model must be grounded against the executed refinement block
  and a Windows host discriminator if the difference reaches a final pixel.

## Verification

- `python3 tools/emulation/test_windows_runtime.py`
  - `Ran 5 tests ... OK`
- `python3 tools/emulation/test_dg_fieldgen_embedded_opencv.py`
  - `Ran 3 tests ... OK`
- `python3 tools/emulation/test_opencv_detour.py`
  - all detour and bridge gates pass
  - ten embedded distance-transform relations pass
  - embedded threshold GATE C passes
