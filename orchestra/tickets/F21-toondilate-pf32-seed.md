## Goal
ToonDilate: restore the original PF32 seed predicate (finite alpha exactly 1; unordered NaN eligible).

## Evidence
From `orchestra/reports/T13-triage-toondilate.md` (grep the `TD-PF32-SEED` bullet and the related cluster rows):
All 23 Smart mismatches first differ at seed initialization; original accepts alpha==1 or NaN, Mac accepts alpha>=1. Scratch predicate makes 300/300 Smart exact, sanitizer clean. Add neighbouring float, +-inf, quiet/signaling NaN witnesses and a fresh seed 2 n300.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmtoondilate --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmtoondilate: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmtoondilate*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
