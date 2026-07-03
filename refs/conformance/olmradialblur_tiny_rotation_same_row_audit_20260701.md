# OLMRadialBlur tiny Rotation Same-Row Audit

Date: 2026-07-01

Goal:

- Tie the live Mac AE witness dump to the current `RenderRotation8` structure.
- Make explicit which same-row angular source taps the current port can use for the
  tiny-Rotation witness neighborhood.

Current structural facts:

- `outer_strength=4`
- `outer_offset_mode=1`
- `outer_offset=0`
- `quality=5.0` -> `angular_count=1800`
- `row_length=3`
- `row_weights=[1.0, 0.6065306823076752, 0.13533530340315494]`

This means the current small-length Rotation path uses only same-radius-row angular taps
for each blurred polar cell. There is no cross-row contribution in this branch.

## Witness neighborhood

| XY | sample_u8 | validity_alpha_u8 | indices | cell | same-row taps | cell_rgb | src_cell_rgba |
| - | - | -: | - | - | - | - | - |
| `(1612, 6)` | `[5, 5, 5, 255]` | 255 | `[1603, 1604, 842, 843]` | `x0y0` | `[1603, 1602, 1601]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y0` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x0y1` | `[1603, 1602, 1601]` | `[0.0441839024, 0.0441839024, 0.0441839024]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y1` | `[1604, 1603, 1602]` | `[0.00694188103, 0.00694188103, 0.00694188103]` | `[0.0, 0.0, 0.0, 1.0]` |
| `(1613, 6)` | `[1, 1, 1, 255]` | 255 | `[1603, 1604, 843, 844]` | `x0y0` | `[1603, 1602, 1601]` | `[0.0441839024, 0.0441839024, 0.0441839024]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y0` | `[1604, 1603, 1602]` | `[0.00694188103, 0.00694188103, 0.00694188103]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x0y1` | `[1603, 1602, 1601]` | `[-0.0147110438, -0.0147110438, -0.0147110438]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y1` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
| `(1614, 5)` | `[0, 0, 0, 255]` | 255 | `[1603, 1604, 844, 845]` | `x0y0` | `[1603, 1602, 1601]` | `[-0.0147110438, -0.0147110438, -0.0147110438]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y0` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x0y1` | `[1603, 1602, 1601]` | `[-0.0485489555, -0.0485489555, -0.0485489555]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y1` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
| `(1614, 6)` | `[0, 0, 0, 255]` | 255 | `[1603, 1604, 844, 845]` | `x0y0` | `[1603, 1602, 1601]` | `[-0.0147110438, -0.0147110438, -0.0147110438]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y0` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x0y1` | `[1603, 1602, 1601]` | `[-0.0485489555, -0.0485489555, -0.0485489555]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y1` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
| `(1614, 7)` | `[0, 0, 0, 255]` | 255 | `[1604, 1605, 843, 844]` | `x0y0` | `[1604, 1603, 1602]` | `[0.00694188103, 0.00694188103, 0.00694188103]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y0` | `[1605, 1604, 1603]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x0y1` | `[1604, 1603, 1602]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |
|  |  |  |  | `x1y1` | `[1605, 1604, 1603]` | `[0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 1.0]` |

## Interpretation

The current Mac Rotation path can only populate each blurred witness cell from same-radius-row angular taps. Around the tiny-Rotation witness, those direct source cells are all black while the surviving blurred cell_rgb values stay small or negative, so the missing bright lobe cannot come from those exact same-row direct source cells.

This tightens the next proof boundary to upstream neighbor/contribution geometry, AEX prepass/scatter structure, or a substitute/fallback branch that the current same-row convolution does not model.

- At `(1614,6)`, all four direct `src_cell_rgba` values are black, yet the blurred
  `cell_rgb` family is already small/negative. So the witness is not explained by
  direct-source brightness being present and then masked away later.
- Because the current branch uses only same-row angular taps, it also cannot express
  any AEX rule that depends on neighboring radius rows or a separate substitute path
  before the final inverse sample.
- This does not prove the exact AEX rule yet, but it does make one thing safer:
  broad final-sample validity or writeback tweaks are even less likely to be the real
  fix than the current docs already suggested.
