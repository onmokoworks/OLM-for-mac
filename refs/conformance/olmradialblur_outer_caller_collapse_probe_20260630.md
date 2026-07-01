# OLMRadialBlur Outer Caller-Collapse Probe

Date: 2026-06-30

Bounded CLI experiment:

- Added `--outer-caller-collapse-mode binary-validity` to
  `cli/OLMRadialBlur/olmradialblur_cli`
- Added `--outer-caller-collapse-mode zero-rgb-on-invalid` as a weaker
  follow-up probe
- Probe intent: test the narrow AEX-grounded hypothesis that the missing outer
  lane is primarily "caller collapse uses preserved validity as final alpha"
  by replacing the final inverse-sampled alpha plane with a binary preserved
  validity plane and zeroing RGB when preserved validity is zero

Baseline reference:

- `case_0009` Zoom baseline stays within the existing guard:
  `max=1 mean=0.0046`
- `case_0010` tiny Rotation baseline stays at the known residual:
  `max=255 mean=0.0103`

Probe result:

- `case_0009` with `--outer-caller-collapse-mode binary-validity`:
  `max=255 mean=0.11455873842592593 nonzero_px=40411 (1.9488%)`
- `case_0010` with `--outer-caller-collapse-mode binary-validity`:
  `max=255 mean=0.12039592978395061 nonzero_px=42893 (2.0685%)`
- `case_0009` with `--outer-caller-collapse-mode zero-rgb-on-invalid`:
  `max=91 mean=0.025998384452160492 nonzero_px=40050 (1.9314%)`
- `case_0010` with `--outer-caller-collapse-mode zero-rgb-on-invalid`:
  `max=255 mean=0.014437451774691358 nonzero_px=34148 (1.6468%)`

What changed:

- The probe creates a large top-edge alpha staircase rather than the narrow
  existing witness. Representative samples:
  - Zoom `case_0009`:
    `(1,0) [20,3,3,97] vs [20,2,2,255]`,
    `(6,0) [21,3,3,112] vs [20,3,3,254]`
  - tiny Rotation `case_0010`:
    `(1,0) [0,0,0,97] vs [0,0,0,255]`,
    `(6,0) [0,0,0,112] vs [0,0,0,254]`
- The weaker `zero-rgb-on-invalid` follow-up keeps alpha near the old output
  but still over-zeros top-edge RGB:
  - Zoom `case_0009`:
    `(0,0) [0,0,0,255] vs [20,2,2,255]`,
    `(7,0) [6,0,0,255] vs [21,3,3,254]`
  - tiny Rotation `case_0010`:
    `(14,0) [0,0,0,255] vs [24,24,24,255]`,
    `(16,0) [0,0,0,255] vs [65,65,65,255]`

Conclusion:

- Directly substituting a binary preserved-validity plane as the caller
  collapse alpha is too strong and is rejected.
- Even the weaker "keep alpha, but zero RGB when preserved validity is zero"
  model is rejected. It broadens Zoom and slightly worsens tiny Rotation by
  erasing top-edge RGB that Windows keeps.
- The caller-collapse hypothesis itself remains live, but the surviving
  AEX-side rule is more specific than either `0/1 validity -> final alpha` or
  `0/1 validity -> RGB keep/drop`.
- The next useful local model is therefore not "binary validity collapse" but a
  typed split between preserved validity, accumulated RGBA, and the normalized
  final polar plane consumed by inverse sampling.

Follow-up witness dump:

- A new local CLI witness dump was added on 2026-06-30 to capture the exact
  inverse-sampled float and bilinear weights for one output pixel.
- Zoom `case_0009` at `(6,0)` now reproduces the frozen Windows witness shape
  locally:
  `sample_rgba=[0.0822407,0.0141302,0.0141302,1.0]`,
  `sample_u8=[20,3,3,255]`,
  with `radius_index=1096.23`, `angle_index=1047.56`, and bilinear weights
  `w00/w10/w01/w11 = 0.341602 / 0.100903 / 0.430371 / 0.127124`.
- Re-running the same witness with
  `--rgba-sampler-alpha-mode repeat-raw` produces the same captured floats and
  bytes. So the surviving Zoom `254 vs 255` delta is not explained by the
  narrow repeat-border raw-alpha switch alone; the remaining error is still in
  caller-side polar alpha/sample collapse upstream of final byte packing.
