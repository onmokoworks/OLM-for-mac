# OLMRadialBlur Caller-Collapse Plane Diagnostic

Date: 2026-07-01

Bounded Mac-side diagnostic using the existing C++ slice plus an expanded witness dump. Each witness now captures a 9-pixel same-row probe centered on the original witness so we can compare final inverse-sampled alpha against the local preserved-validity proxy.

## Zoom `case_0009`

- Witness XY: `[6, 0]`
- Probe half-span: `4`
- Largest `alpha_u8 - validity_alpha_u8` gap: `{'x': 8, 'gap': 208}`
- Largest RGB-vs-reference gap on the probe: `{'x': 2, 'mag': 0, 'delta': [0, 0, 0]}`

Representative row probe:

| x | sample_u8 | ref_u8 | alpha_u8 | validity_alpha_u8 | gap | cell_valid |
| - | - | - | - | - | - | - |
| 2 | `[20, 3, 3, 255]` | `[20, 3, 3, 255]` | 255 | 243 | 12 | `[1.0, 1.0, 0.0, 0.0]` |
| 3 | `[20, 3, 3, 255]` | `[20, 3, 3, 255]` | 255 | 211 | 44 | `[1.0, 1.0, 0.0, 0.0]` |
| 4 | `[20, 3, 3, 255]` | `[20, 3, 3, 255]` | 255 | 178 | 77 | `[1.0, 1.0, 0.0, 0.0]` |
| 5 | `[20, 3, 3, 255]` | `[20, 3, 3, 255]` | 255 | 145 | 110 | `[1.0, 1.0, 0.0, 0.0]` |
| 6 | `[20, 3, 3, 255]` | `[20, 3, 3, 254]` | 255 | 112 | 143 | `[1.0, 1.0, 0.0, 0.0]` |
| 7 | `[21, 3, 3, 255]` | `[21, 3, 3, 254]` | 255 | 79 | 176 | `[1.0, 1.0, 0.0, 0.0]` |
| 8 | `[21, 3, 3, 255]` | `[21, 3, 3, 255]` | 255 | 47 | 208 | `[1.0, 1.0, 0.0, 0.0]` |
| 9 | `[21, 4, 4, 255]` | `[21, 4, 4, 255]` | 255 | 106 | 149 | `[1.0, 1.0, 1.0, 0.0]` |
| 10 | `[21, 4, 4, 255]` | `[21, 4, 4, 255]` | 255 | 236 | 19 | `[1.0, 1.0, 0.0, 0.0]` |

Interpretation:

Across the bounded top-row probe, final inverse-sampled alpha stays near-opaque while the current preserved-validity proxy collapses much earlier. That makes the live Zoom caller-collapse lane narrower than direct sampling of the current validity plane.

## tiny Rotation `case_0010`

- Witness XY: `[1614, 6]`
- Probe half-span: `4`
- Largest `alpha_u8 - validity_alpha_u8` gap: `{'x': 1610, 'gap': 0}`
- Largest RGB-vs-reference gap on the probe: `{'x': 1614, 'mag': 255, 'delta': [-255, -255, -255]}`

Representative row probe:

| x | sample_u8 | ref_u8 | alpha_u8 | validity_alpha_u8 | gap | cell_valid |
| - | - | - | - | - | - | - |
| 1610 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1611 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1612 | `[5, 5, 5, 255]` | `[5, 5, 5, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1613 | `[1, 1, 1, 255]` | `[1, 1, 1, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1614 | `[0, 0, 0, 255]` | `[255, 255, 255, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1615 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1616 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1617 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |
| 1618 | `[0, 0, 0, 255]` | `[0, 0, 0, 255]` | 255 | 255 | 0 | `[1.0, 1.0, 1.0, 1.0]` |

Interpretation:

Across the bounded tiny Rotation probe, validity alpha stays fully live, so the remaining failure is not an alpha-plane collapse. The surviving gap stays in the polar RGB / substitute-path population that feeds the final inverse sample.

## Bottom line

- Zoom: the local validity plane collapses much faster than the final alpha plane, so the remaining caller-collapse behavior is not direct use of the current preserved-validity bits.
- tiny Rotation: the local validity plane is already fully live across the bounded probe, so the remaining failure stays in the RGB/substitute path rather than in a validity-only alpha collapse.

