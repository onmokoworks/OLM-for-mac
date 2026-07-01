# OLMRadialBlur Outer Propagated-Validity Probe

Date: 2026-07-01

Bounded diagnostic: replace the final outer alpha plane with a same-kernel propagated validity plane (`--outer-caller-collapse-mode propagated-validity-alpha`) and measure whether the focused outer witnesses improve.

## Zoom `case_0009`

- Witness XY: `[6, 0]`
- Sample RGBA: `[0.0822407, 0.0141302, 0.0141302, 1]`
- Sample u8: `[20, 3, 3, 255]`
- Diff stats: `max=1 mean=0.0046 nonzero_px=31119`

Replacing outer alpha with a same-kernel propagated validity plane leaves the current Zoom residual unchanged (`max=1 mean=0.0046`). This does not supply the missing 254/255 split by itself.

## tiny Rotation `case_0010`

- Witness XY: `[1614, 6]`
- Sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- Sample u8: `[0, 0, 0, 255]`
- Diff stats: `max=255 mean=0.0103 nonzero_px=33740`

The propagated-validity probe leaves tiny Rotation effectively unchanged (`max=255 mean=0.0103`). This supports the existing conclusion that the remaining blocker is RGB/substitute-path population, not a simple validity-plane collapse.

## Bottom line

- This rejects one more tempting outer-lane shortcut: a propagated validity plane alone is not enough.
- Zoom still needs a narrower caller-collapse / normalization fact between sampler return and final `+0xe` alpha.
- tiny Rotation still points upstream to the polar RGB / substitute path.

