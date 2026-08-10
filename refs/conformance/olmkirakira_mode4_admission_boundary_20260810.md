# OLMKiraKira Mode 4 admission boundary — 2026-08-10

The only complete actual-AEX directional Mode 4 fixture is the rotated scalar
leaf at `9×7`, radius/length `5`, angle `5°`. Its forward warp, scalar
recurrence, and inverse warp each compare all 63 raw FLOAT32 words exactly.

Production now admits precisely `(rw=9, rh=7, length=5, angle=5°)`. Every other Mode 4
directional tuple returns the unblurred input ray. It does not run the recovered
recurrence outside its evidence boundary and does not substitute Mode 1, 2, or
3 behavior.

The admission regression positively checks `9×7/5` and negatively checks
adjacent radii, transposed geometry, practical `1920×1080`, invalid width, and
angles `0°` and `-5°`.
The existing exact recurrence/helper-chain fixture remains unchanged.

The downstream `9×7/5` centered-crop and PF8/PF16/PF32 writer fixture remains
valid. The full-caller `4×1` fixture has all four directional lengths set to
zero and exercises the separately proven Highlight path, so it does not claim
or require a second directional Mode 4 tuple.

Still unproven: arbitrary rotated geometry, lengths other than `5`, other
angles at the complete helper-chain boundary, and practical-resolution native
AE directional Mode 4.
