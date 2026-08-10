# OLMRadialBlur PF8 Rotation Inner release boundary (2026-08-06)

> **Historical snapshot.** The statement below that PF16/PF32 are restricted
> to 9x7 was superseded by the 2026-08-07 typed-geometry implementation and
> evidence. See `olmradialblur_rotation_typed_inner_geometry_20260807.md`.

- Actual owner: `0x180007520` from AEX SHA-256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Independent PF8 input and PF8 writer were used; no PF16/PF32 source or quantization result was reused.
- The 9x7 padded fixture proves strengths `1,2,3,4,5,8,16,31,32,33,63,64`, including both boundaries and non-power-of-two transitions. Every polar/source-scalar/accum/max/final/output comparison is byte-exact.
- A second 64x36 Inner-32 run was exact across the same planes, rejecting the old 9x7-only geometry guard as an algorithm requirement.
- The practical 640x360 Inner-4 run contains 666,000 polar cells and is byte-exact through the padded PF8 output. Hashes are retained in `olmradialblur_rotation_pf8_inner_practical_geometry_20260806.json`.

The admitted production lane is PF8 Rotation, positive matching input/output geometry and safe rowbytes, center at the frame midpoint, comp dimensions equal to the frame, Inner Strength 1..64, ratio 1, angle 0, quality 5, repeat border enabled, and neutral outer blur/offset/edge-fade/noise/variation controls. The strength rule is grounded by boundary/non-power-of-two small fixtures and by the same geometry-independent worker structure at the practical geometry; it is not a claim for unlisted parameter families.

PF16/PF32 remain restricted to their independently proved 9x7 geometry. Off-center, non-unit ratio, nonzero angle, other quality, disabled repeat border, offsets, edge fades, noise, and variation remain outside this exact boundary and fail closed.
