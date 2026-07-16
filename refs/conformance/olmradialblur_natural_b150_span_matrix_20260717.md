# OLMRadialBlur natural B150 span matrix (2026-07-17)

- Status: `pass`
- Classification: `bounded-natural-b150-span-2-3-and-inner-1-oracle-match`
- Scope: actual Mac AEX natural reader-owned B150 matrix for Outer Edge Fade 2/3 plus an Inner Edge Fade reachability attempt; no Windows or AE-exact claim.

- Gates: `{'outer_span_2': True, 'outer_span_3': True, 'inner_span_1': True, 'outer_matrix_generalizes': True}`
- Outer spans 2 and 3 and reachable Inner Edge Fade=1 match the independent Gaussian-table and per-cell float32 oracle. The observed spans are `[2,0]`, `[3,0]`, and `[0,1]` respectively.
