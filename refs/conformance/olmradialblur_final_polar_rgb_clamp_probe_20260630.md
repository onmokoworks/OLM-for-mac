# OLMRadialBlur Final Polar RGB Clamp Probe

Date: 2026-06-30

Probe:

- Added CLI-only option
  `--final-polar-rgb-mode clamp-nonnegative`
- Effect:
  - during the final inverse-sampling stage only
  - clamp each contributing polar RGB channel to `max(value, 0)`
  - leave alpha and sampling coordinates unchanged

Intent:

- Test whether the tiny Rotation high-max witness is mostly explained by
  negative local polar RGB values before final bilinear sampling.

## Results

Baseline:

- Zoom `case_0009`: `max=1 mean=0.004613474151234568 nonzero_px=31119`
- tiny Rotation `case_0010`: `max=255 mean=0.01032033661265432 nonzero_px=33740`

Probe:

- Zoom `case_0009` with `--final-polar-rgb-mode clamp-nonnegative`:
  - `max=1`
  - `mean=0.004613474151234568`
  - `nonzero_px=31119`
- tiny Rotation `case_0010` with `--final-polar-rgb-mode clamp-nonnegative`:
  - `max=255`
  - `mean=0.010301890432098766`
  - `nonzero_px=33746`

## Interpretation

- Zoom is unchanged. That is consistent with the local witness dump, where the
  remaining Zoom residual is alpha-only and the local RGB already matches the
  Windows pre-writeback float.
- tiny Rotation improves only marginally in mean diff and does not move the
  `max=255` blocker.
- Therefore, negative polar RGB values are part of the tiny Rotation witness
  story, but clamping them at the last inverse-sampling stage is not the main
  missing AEX rule.
- The active lane remains upstream:
  - how the polar RGB cells are populated and normalized
  - or which polar neighborhood / coordinates are selected before final
    inverse sampling
