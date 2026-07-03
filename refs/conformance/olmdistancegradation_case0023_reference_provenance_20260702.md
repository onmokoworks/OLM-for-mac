# OLMDistanceGradation case_0023 Reference Provenance - 2026-07-02

- Status: `threshold-family-reference-generation-split-candidate`
- Case: `olmdistancegradation_extended__case_0023`
- Live Mac AE rerun:
  [refs/reports/ae_single_case_distancegradation_case0023_live_20260702/AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_distancegradation_case0023_live_20260702/AE_SINGLE_CASE_RESULT.json)
- Packaged expected PNG:
  [expected PNG](/Users/onmk/Documents/Projects/Personal/OLM%20as/handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/expected/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0023.png)
- Latest Windows typed evidence:
  [olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702 return](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/returns/windows/20260702_1531_distancegradation_refcon_stack_wordmap_followup/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702_return_windows.zip)

## Durable facts

- Live Mac AE single-case rerun succeeded on `2026-07-02` under AE `26.3x87`.
- Against the packaged expected PNG, the live output is still the known `73px`
  residual (`max_diff=238`, `mean_diff=0.0040925202546296295`).
- But the threshold triplet is no longer symmetric evidence against the Mac
  implementation:
  - `(414,393)` live Mac = packaged expected = Windows typed final blue
  - `(415,393)` live Mac = Windows typed final red, while packaged expected is blue
  - `(416,393)` live Mac = packaged expected = Windows typed final red

## Why this matters

The latest Windows runtime return explicitly preserved final stored `RGBA16`
facts for the threshold triplet:

- `(414,393)` -> `[7195,0,61165,65535]`
- `(415,393)` -> `[65535,0,0,65535]`
- `(416,393)` -> `[65535,0,0,65535]`

The packaged expected PNG still shows the older blue endpoint at `(415,393)`.
So the expected PNG in
`ae_single_distancegradation_case0023_probe_20260701/expected/`
cannot be treated as authoritative for the threshold-family slice anymore.

## Local field witness

The live Mac debug dump at
[field_debug.txt](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_distancegradation_case0023_live_20260702/field_debug.txt)
also stays internally consistent with the Windows triplet:

- `(414,393)`: `raw_inside=35.0142822`, `field_x=0`
- `(415,393)`: `raw_inside=36.0138855`, `field_x=1`
- `(416,393)`: `raw_inside=37.0135117`, `field_x=1`

That is the exact `35.014 -> 36.013 -> 37.013` threshold crossing already
described in the binary-proof lane.

## Boundary of the claim

This does **not** prove that the whole remaining `73px` residual is just stale
reference data.

In particular, edge-family witnesses like `(1699,7)` still differ:

- live Mac: `[28,0,238,255]`
- packaged expected: `[255,0,0,255]`

The latest Windows runtime return did not preserve equally strong current-AEX
typed output for that edge-family witness, so that part remains unresolved.

## Decision

- Treat the threshold-family triplet as a `reference-generation split` candidate.
- Do not retune compose/writeback from the packaged expected PNG at
  `(415,393)`.
- The next durable closeout for this lane is a current Windows Software export
  or equivalent typed witness for the remaining edge-family pixels, not a broad
  Mac-side threshold rewrite.
