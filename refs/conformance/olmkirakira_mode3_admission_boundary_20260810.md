# OLMKiraKira Mode 3 admission boundary — 2026-08-10

Mode 3 no longer promotes four witnessed kernel lengths to arbitrary image
geometry. Production admits only complete rotated-leaf tuples whose actual 2025
AEX output is raw-FLOAT32 exact:

| width | height | length | exact words |
| ---: | ---: | ---: | ---: |
| 11 | 6 | 3 | 66 |
| 9 | 7 | 5 | 63 |
| 13 | 5 | 7 | 65 |
| 15 | 6 | 9 | 90 |

The dimensions are the `rw`/`rh` dimensions at the Gaussian leaf after the
rotated extent and centered-copy stages, not necessarily the source comp size.

For every other geometry/length tuple, Mode 3 returns the unblurred input ray.
It does not silently use Mode 2's three-pass box approximation. This is a
fail-closed evidence boundary, not a claim that unsupported Mode 3 is complete.

The focused regression checks all four admitted tuples and rejects unwitnessed
geometry, swapped geometry/length pairs, lengths `1` and `11`, and invalid
dimensions. Each of the four actual-AEX output fixtures is independently
replayed against the portable non-fused Gaussian implementation with zero word
difference. The full Kira Kira fixed-fixture regression also passes.

Still unproven: arbitrary geometry for a witnessed length, a different length at
a witnessed geometry, and practical-resolution native-AE Mode 3 rendering.
