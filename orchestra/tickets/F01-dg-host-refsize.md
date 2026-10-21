## Goal
Populate checkout reference dimensions in the fuzz host for DistanceGradation Smart, then re-baseline the Smart route.

## Evidence
From `orchestra/reports/T07-triage-distancegradation.md` (grep the `DG-HOST-REFSIZE` bullet and the related cluster rows):
All 300 Smart refusals share a missing checkout reference-size field in the fake host; host-fixed build matched gate-off 300/300 and unblocked 249 outputs. This is a harness fix (tools/fuzz / emulation host), not a plugin change.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmdistancegradation: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmdistancegradation*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
