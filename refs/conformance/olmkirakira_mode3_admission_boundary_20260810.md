# OLMKiraKira Mode 3 admission boundary — 2026-08-10

Mode 3 has a bounded geometry-general contract for rotated leaves at least
`9×7` and Length `3` or UI-default `50`. Production also retains the smaller
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
`0°`, `45°`, `-45°`, and oblique `17°`, and Length `3/50`. Across 14 complete
actual-AEX chains, forward warp, Gaussian, and inverse warp compare 104,850 of
104,850 float32 words exactly. Odd/even, square/non-square, and multiple width
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

Still unproven: geometry-general behavior for Lengths other than `3` and `50`,
leaf dimensions below `9×7` except listed tuples, and native-AE final rendering.
