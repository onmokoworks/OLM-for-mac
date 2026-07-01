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
- four-cell `cell_valid`
- four-cell `cell_alpha`

## Parser

Use:

- `python3 scripts/analyze_radialblur_debug_points.py /path/to/radialblur_debug.log --output-json /tmp/radialblur_debug.json --output-md /tmp/radialblur_debug.md`

This is intended to mirror the existing narrow witness workflow already used by
KiraKira and DistanceGradation, but for the remaining RadialBlur Zoom/tiny
Rotation outer-lane residuals.
