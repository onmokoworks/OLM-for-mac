# OLMKiraKira Mode4 recurrence boundary (2026-07-18)

Status: **PASS_MODE4_BOUNDED_RECURRENCE_GEOMETRY**
AE exact: **false**
Production edit: **none**

## Bounded semantic

For the fifth Highlight layer, the AEX Mode4 inline body uses
`fVar18 = r/(r+1)` and `fVar20 = r/(r+1)^2`, then updates each recurrence cell
as `fVar20*source + fVar18*prior`. The actual AEX reaches the inline scalar/
gain boundary for length 5. This is a recurrence/gain fact, not a claim about
edge policy or final normalization.

## Cross-check

- Decomp: `FUN_181150790` derives `fVar18 = r/(r+1)` and
  `fVar20 = r/(r+1)^2`, then updates each recurrence cell as
  `fVar20 * source + fVar18 * prior`.
- Assembly: `0x181150979` enters the inline Mode4 body, `0x181150987` and
  `0x181150999` form the two factors, and `0x181150f3d` is the recovered
  scalar/gain boundary.
- Actual AEX: direct helper invocation with only the mode selector changed to
  4 reaches both inline boundaries for length 5.

## Boundary and limits

The actual-AEX entry and gain hooks are inside the inline Mode4 body. Edge
handling, later pass outputs, gain numeric state beyond the recovered factors,
and final pixel writeback remain unproven. No production edit was made.

Verification: `python3 tools/emulation/test_olmkirakira_mode4_recurrence_boundary_20260718.py`
