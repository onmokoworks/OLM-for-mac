# OLMRadialBlur tiny Rotation Source-Polar Probe

Date: 2026-07-01

- Case: `case_0010`
- Witness XY: `[1614, 6]`
- Sample indices `[x0,x1,y0,y1]`: `[1603, 1604, 844, 845]`
- Source-probe origin: `[1598, 838]`
- Source-probe size: `[11, 13]`
- Witness sample RGBA: `[-0.00408606, -0.00408606, -0.00408606, 1]`
- Witness sample U8: `[0, 0, 0, 255]`

## Strongest positive source-polar cells

| XY | luma | RGBA |
| - | -: | - |
| `[1608, 838]` | `0.452643` | `[0.452643, 0.452643, 0.452643, 1]` |
| `[1601, 843]` | `0.168253` | `[0.168253, 0.168253, 0.168253, 1]` |
| `[1602, 843]` | `0.089347` | `[0.0893472, 0.0893472, 0.0893472, 1]` |
| `[1608, 839]` | `0.035579` | `[0.0355792, 0.0355792, 0.0355792, 1]` |

## Dominant local positive cluster near the witness rows

| XY | luma | RGBA |
| - | -: | - |
| `[1601, 843]` | `0.168253` | `[0.168253, 0.168253, 0.168253, 1]` |
| `[1602, 843]` | `0.089347` | `[0.0893472, 0.0893472, 0.0893472, 1]` |

## Strongest negative source-polar cells

| XY | luma | RGBA |
| - | -: | - |
| `[1601, 845]` | `-0.624861` | `[-0.624861, -0.624861, -0.624861, 1]` |
| `[1601, 844]` | `-0.189342` | `[-0.189342, -0.189342, -0.189342, 1]` |

## Direct source cells for the final witness bilinear sample

| XY | RGBA |
| - | - |
| `[1603, 844]` | `[0, 0, 0, 1]` |
| `[1604, 844]` | `[0, 0, 0, 1]` |
| `[1603, 845]` | `[0, 0, 0, 1]` |
| `[1604, 845]` | `[0, 0, 0, 1]` |

## Interpretation

The dominant local positive source-polar family sits above the witness rows, centered at row 843 / angles 1601..1602, while the four direct source cells for rows 844/845 are all black. There is one farther bright outlier at (1608,838), but it is spatially separated from the local cluster that can plausibly feed the witness.

The current same-row support can sample negative or zero cells at the witness, but it has no mechanism to carry the row-843 bright family into the rows that dominate the final bilinear mix.

- This keeps the active lane on upstream contribution ownership / neighboring-row
  geometry, not on final alpha collapse or a uniform source-grid shift.
