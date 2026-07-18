# OLMKiraKira Mode4 edge and forward/backward passes (2026-07-18)

Status: **PASS_MODE4_EDGE_FORWARD_BACKWARD_PASSES**
AE exact: **false**
Production edit: **none**

## Bounded result

On the checked `CV_32FC1` path, each of 7 rows seeds the forward accumulator
from destination element zero, executes 8 forward recurrence steps, resets the
backward accumulator to zero, and executes 8 backward recurrence steps. The
9-wide witness takes the reverse body in two four-lane vector iterations per
row, so the observed equivalent count is 56 backward steps.

## Evidence

- Decomp `FUN_181150790`: `fVar16 = *pfVar15` seeds the forward edge;
  `fVar16 = 0.0` resets the backward state; the pointer/index updates form
  increasing and decreasing row passes.
- Assembly: `0x181150a17` is the forward edge load, `0x181150a20` loops the
  forward recurrence, `0x181150b1c` sets up the reverse edge, and
  `0x181150b23` loops the backward recurrence. `0x1811509e0..0x181150b5a`
  encloses the row loop.
- Actual AEX: the instrumented helper reaches 7 row starts, 7 forward edge
  initializations, 7 backward setups, 56 forward steps, and 56 backward steps.

This is an edge/pass-shape proof only. Final normalization, final pixel
writeback, Windows/AE-host behavior, and exact equivalence remain unproven.

Verification: `python3 tools/emulation/test_olmkirakira_mode4_edge_passes_20260718.py`
