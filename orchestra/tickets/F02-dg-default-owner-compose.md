## Goal
Fix DistanceGradation default-owner compose mismatch (clusters C10/C11/C12, 122 baseline cases).

## Evidence
From `orchestra/reports/T07-triage-distancegradation.md` (grep the `DG-DEFAULT-OWNER-COMPOSE` bullet and the related cluster rows):
Representatives first differ only in R; C11 is Smart exact but Classic mismatched against both AEX owners. Trace the first differing field/compose stage.

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
