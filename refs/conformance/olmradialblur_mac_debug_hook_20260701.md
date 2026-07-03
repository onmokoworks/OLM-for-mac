# OLMRadialBlur Mac Debug Hook

Date: 2026-07-01

`mac/OLMRadialBlur/OLMRadialBlur.cpp` now supports a narrow Mac AE witness dump
for specified output pixels without changing rendered output.

## Environment variables

- `OLMRADIALBLUR_DEBUG_DUMP_PATH=/tmp/olmradialblur_debug.log`
- `OLMRADIALBLUR_DEBUG_POINTS=6,0;1614,6`

## Emitted line format

Each matched point appends one line beginning with:

- `OLMRADIALBLUR_DEBUG_POINT`

Fields include:

- `kind=zoom|rotation`
- output `x,y`
- `radius_index`, `angle_index`, `fx`, `fy`
- contributing polar indices `(x0,x1,y0,y1)`
- `sample_rgba`
- `sample_u8`
- final `alpha`
- local bilinear `validity_alpha`
- `brightness_gain`
- `accum_rgba` (pre-normalized weighted RGB sum plus alpha)
- `normalized_rgba` (pre-gain normalized polar RGBA equivalent)
- four-cell `cell_valid`
- four-cell `cell_alpha`

This is intentionally closer to the active tiny Rotation anchor-watch contract:
`validity_alpha` is the local preserved-validity analogue, `accum_rgba`
matches the weighted pre-normalized promotion state, and `normalized_rgba`
captures the last local state before brightness gain / byte quantization.

## Parser

Use:

- `python3 scripts/analyze_radialblur_debug_points.py /path/to/radialblur_debug.log --output-json /tmp/radialblur_debug.json --output-md /tmp/radialblur_debug.md`

This is intended to mirror the existing narrow witness workflow already used by
KiraKira and DistanceGradation, but for the remaining RadialBlur Zoom/tiny
Rotation outer-lane residuals.

## 2026-07-02 source-boundary follow-up

- The current macOS source now routes both `RenderZoom8` and `RenderRotation8`
  outer-lane final sampling through a shared helper
  `ComputeRadialBlurOuterSampleState(...)`.
- This is intentionally a non-behavioral refactor: final output alpha is still
  written from the blurred outer alpha plane, while preserved validity remains
  a separate debug/inspection channel.
- The point of the helper is to keep the caller-collapse boundary explicit so a
  later Windows typed witness can swap only that rule instead of reopening the
  surrounding bilinear/writeback code.
- Verified after the refactor:
  - `python3 refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py`
  - `python3 refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py`
  - `xcodebuild -project mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj -configuration Debug build`
