# OLMKiraKira Mode 4 admission boundary — 2026-08-10

The complete actual-AEX directional Mode 4 fixtures cover radius/length `5` at
the original `9×7 / 5°` leaf and the default-rotation canonical ray family:
`9×7 / 0°`, plus `9×9 / 45°`, `9×9 / -45°`, and `9×9 / 90°`.
Forward warp, scalar recurrence, and inverse warp compare every raw FLOAT32
word exactly in each case (63 words per 9×7 stage, 81 per 9×9 stage).

This document originally admitted only those five tuples. That narrow gate was
superseded by the bounded generalized contract in `core/kirakira_mode4.h`:
rotated work geometry at least `9×7`, Length `1..1000`, and arbitrary finite
angle representatives. The recovered scalar recurrence and shared warp are
used only inside that geometry/length boundary; invalid dimensions and lengths
outside the declared interval remain rejected.

The canonical public-route regression verifies that source work geometry
`5×3`, Glow Rotation `0°`, and the four named directional controls route to
`0°`, `45°`, `135°`, and `90°` with the admitted `9×7`/`9×9` leaves. The
standalone `-45°` recurrence leaf above remains a valid direct-helper fixture;
it is not the public Diagonal 2 owner representative.
The later natural-family evidence adds exact noncanonical representatives,
including public-owner Diagonal 2 at `124° / Length 9`. Invalid width and
Length outside `1..1000` remain rejected; practical-resolution native AE is a
separate host boundary.
The existing exact recurrence/helper-chain fixture remains unchanged.

The downstream `9×7/5` centered-crop and PF8/PF16/PF32 writer fixture remains
valid. The full-caller `4×1` fixture has all four directional lengths set to
zero and exercises the separately proven Highlight path, so it does not claim
or require a second directional Mode 4 tuple.

Still unproven: the full Cartesian product of arbitrary source, rotated
geometry, length, angle, colors, ramps and merge modes, plus
practical-resolution native AE directional Mode 4. The generalized helper
admission must not be read as public-output proof for every such combination.
