## Goal
KiraKira: turn proven internal exactness into production admission. Lift guards only for general rules (profiles/tuples/layouts) whose gate-off fuzz cases are all exact and sanitizer-clean; keep refusing the rest.

## Evidence
From `orchestra/reports/F09-kira-numeric-first-divergence.md` (grep the `KIRA-F10` bullet and the related cluster rows):
Production is still 0 exact / 300 refused per route, while diagnostic gate-off gives Classic 198 / Smart 98 exact after F03+F09. T06 KIRA-F10 warned wholesale removal is unsupported (mismatches exist), so the deliverable is a precise admission predicate derived from the AEX branch structure, validated by: seed 1 n 300 plus a fresh seed 2 n 300 (to avoid overfitting seed 1), zero admitted mismatches, sanitizer clean. Report production exact before/after.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmkirakira: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmkirakira*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
