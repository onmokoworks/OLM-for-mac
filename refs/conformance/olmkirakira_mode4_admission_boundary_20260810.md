# OLMKiraKira Mode 4 admission boundary — 2026-08-10

The complete actual-AEX directional Mode 4 fixtures cover radius/length `5` at
the original `9×7 / 5°` leaf and the default-rotation canonical ray family:
`9×7 / 0°`, plus `9×9 / 45°`, `9×9 / -45°`, and `9×9 / 90°`.
Forward warp, scalar recurrence, and inverse warp compare every raw FLOAT32
word exactly in each case (63 words per 9×7 stage, 81 per 9×9 stage).

Production admits precisely those five tuples. Every other Mode 4
directional tuple returns the unblurred input ray. It does not run the recovered
recurrence outside its evidence boundary and does not substitute Mode 1, 2, or
3 behavior.

The canonical public-route regression also verifies that source work geometry
`5×3`, Glow Rotation `0°`, and the four named directional controls route to
`0°`, `45°`, `-45°`, and `90°` with the admitted `9×7`/`9×9` leaves.
Adjacent radii, mismatched geometry/angle pairs, practical `1920×1080`, invalid
width, and `-5°` remain rejected.
The existing exact recurrence/helper-chain fixture remains unchanged.

The downstream `9×7/5` centered-crop and PF8/PF16/PF32 writer fixture remains
valid. The full-caller `4×1` fixture has all four directional lengths set to
zero and exercises the separately proven Highlight path, so it does not claim
or require a second directional Mode 4 tuple.

Still unproven: arbitrary rotated geometry, lengths other than `5`, other
angles at the complete helper-chain boundary, and practical-resolution native
AE directional Mode 4.
