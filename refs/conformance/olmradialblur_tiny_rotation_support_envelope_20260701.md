# OLMRadialBlur tiny Rotation Support Envelope Audit

- Case: `case_0010`
- Witness: `(1614, 6)`
- Positive cluster XY: `[[1601, 843], [1602, 843]]`
- Decision: `witness-cannot-directly-see-row843-cluster-in-current-branch`
- Reason: Within the probed neighborhood, the current same-row Rotation branch only gives direct row-843 cluster visibility to nearby outputs whose bilinear support includes radius row 843. The active witness `(1614,6)` samples rows 844/845 only, so it cannot directly receive the row-843 bright cluster under the current branch. The few nearby outputs that do directly see the cluster are still dim (`[5,5,5]`, `[1,1,1]`, `[0,0,0]`), which supports the existing reading that the missing white lobe needs upstream neighbor-row ownership or a substitute/fallback path.
- Forbidden action: Do not promote a same-row-only tweak, simple validity tweak, or final writeback tweak as the tiny-Rotation fix from this neighborhood alone.
- Next allowed action: Keep the Windows ask focused on substitute/fallback or upstream neighboring-row contribution ownership before final inverse sampling, now anchored from the stable inverse-sampler hit with sampled-cell / neighboring-row pointer-watch context.

## Neighborhood Visibility

| XY | sample_u8 | indices | directly sees row-843 cluster | supporting cells |
| - | - | - | - | - |
| `(1612, 6)` | `[5, 5, 5, 255]` | `[1603, 1604, 842, 843]` | `True` | x0y1 row=843 taps=[1601, 1602], x1y1 row=843 taps=[1602] |
| `(1613, 6)` | `[1, 1, 1, 255]` | `[1603, 1604, 843, 844]` | `True` | x0y0 row=843 taps=[1601, 1602], x1y0 row=843 taps=[1602] |
| `(1614, 5)` | `[0, 0, 0, 255]` | `[1603, 1604, 844, 845]` | `False` | - |
| `(1614, 6)` | `[0, 0, 0, 255]` | `[1603, 1604, 844, 845]` | `False` | - |
| `(1614, 7)` | `[0, 0, 0, 255]` | `[1604, 1605, 843, 844]` | `True` | x0y0 row=843 taps=[1602] |

## Reading

- outputs with direct cluster visibility: `3`
- outputs without direct cluster visibility: `2`
- witness has direct cluster visibility: `False`
- The row-843 bright cluster is not globally invisible; some nearby outputs can directly sample it in the current branch.
- But the active witness `(1614,6)` is not one of them, because its bilinear support stays on rows 844/845.
- So the current branch cannot explain the missing white witness as a same-row-only effect from that row-843 cluster.

