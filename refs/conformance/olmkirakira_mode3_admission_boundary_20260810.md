# OLMKiraKira Mode 3 admission boundary — 2026-08-10

Mode 3 does not promote witnessed kernel lengths to arbitrary image
geometry. Production admits only complete rotated-leaf tuples whose actual 2025
AEX output is raw-FLOAT32 exact:

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

The dimensions are the `rw`/`rh` dimensions at the Gaussian leaf after the
rotated extent and centered-copy stages, not necessarily the source comp size.

For every other geometry/length tuple, Mode 3 returns the unblurred input ray.
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

Still unproven: arbitrary geometry for a witnessed length, other values at the
9x9 geometry, and practical-resolution native-AE Mode 3 rendering.
