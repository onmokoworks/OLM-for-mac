# OLMKiraKira Mode 3 admission boundary — 2026-08-10

Mode 3 has a bounded geometry-general contract for rotated leaves at least
`9×7` and integer Length `1..1000`. This distinguishes the UI slider maximum
`300` from the parameter's hard legal maximum `1000`. Production also retains the smaller
or other-Length exact tuples below:

| width | height | length | exact words |
| ---: | ---: | ---: | ---: |
| 11 | 6 | 3 | 66 |
| 9 | 7 | 3 | 63 |
| 9 | 7 | 5 | 63 |
| 9 | 7 | 7 | 63 |
| 9 | 7 | 9 | 63 |
| 9 | 7 | 50 | 63 |
| 9 | 9 | 50 | 81 |
| 13 | 5 | 7 | 65 |
| 15 | 6 | 9 | 90 |

The general contract is backed by source geometries `32×18` and `64×36`, leaf
dimensions `36×22`, `39×30`, `39×39`, `68×40`, `74×74`, and `75×57`, angles
`0°`, `45°`, `-45°`, and oblique `17°`. Representative Lengths are
`1/2/3/5/7/9/11/25/50/100/200/300/301/1000`. Across 66 complete actual-AEX
chains, forward warp, Gaussian, and inverse warp compare 497,250 of 497,250
float32 words exactly. Odd/even, square/non-square, and multiple width
residue classes are represented. The actual-profile portable Gaussian has no
geometry-specific implementation branch.

The dimensions are the `rw`/`rh` dimensions at the Gaussian leaf after the
rotated extent and centered-copy stages, not necessarily the source comp size.

For every tuple outside the general contract and listed exact exceptions, Mode
3 returns the unblurred input ray.
It does not silently use Mode 2's three-pass box approximation. This is a
fail-closed evidence boundary, not a claim that unsupported Mode 3 is complete.

The focused regressions check all nine admitted tuples and reject unwitnessed
geometry, swapped geometry/length pairs, lengths `1` and `11`, and invalid
dimensions. Each actual-AEX output fixture is independently
replayed against the portable non-fused Gaussian implementation with zero word
difference. The full Kira Kira fixed-fixture regression also passes.

The additional Length-50 gate covers the UI-default ray length at source work
geometry 5x3 and Glow Rotation 0: Horizontal reaches 9x7 while Vertical and
both Diagonal rays reach 9x9. Each ray is exact through forward warp, actual
Gaussian return, and inverse warp. The public route and typed writer selection
are structurally connected; a native-AE four-ray final render is not claimed.

Length `0` remains the public zero-ray skip and never enters the helper. Length
`1` uses the actual five-tap small-kernel rounding path; Length `2..1000` uses
the recovered generic non-fused path. Length `1001+` is outside the hard range
and fails closed.

Still unproven: geometry-general behavior above the hard Length maximum `1000`,
leaf dimensions below `9×7` except listed tuples, and native-AE final rendering.
