## Goal
KiraKira: establish the host row/stride contract and replace unsafe typed row accesses (ReadPixels etc.) so arbitrary legal layouts are admitted safely.

## Evidence
From `orchestra/reports/T06-triage-kirakira.md` (grep the `KIRA-F01` bullet and the related cluster rows):
254 production layout refusals; gate-off gives 150 UBSan misaligned-read aborts at ReadPixels. Fix the access pattern (byte copies / memcpy per AEX semantics), then re-measure which layout refusals can be lifted with sanitizer clean.

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
