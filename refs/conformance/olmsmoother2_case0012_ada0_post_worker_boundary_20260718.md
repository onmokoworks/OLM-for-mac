# OLMSmoother2 ADA0 post-worker boundary - 2026-07-18

- Verdict: `PASS_NO_POST_WORKER_DIVERGENCE_IN_COMPARED_WINDOW`

## Boundary

The ADA0 input witness was replayed into the actual AEX. The comparison stops immediately after the natural `FUN_18000ac00` worker and its `FUN_18000ae10` classifier writes, before c280 or any later helper.

- Compared window: `[(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1), (-1, 2), (0, 2), (1, 2)]`.
- Actual worker calls: `1` worker, `256` classifier entries.
- First divergence: none; every compared byte is equal.

## Result

The current Mac helper and the actual worker agree byte-for-byte across the retained 3x4 window. This local boundary does not justify a production edit; any remaining mismatch is downstream of the compared worker boundary or requires a live Windows post-worker capture.

## Claims Not Made

- No Windows/After Effects execution claim.
- No production source or ledger change.
- No c280, cce0, f130, or writer attribution.
