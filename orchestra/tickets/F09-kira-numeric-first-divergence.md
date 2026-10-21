## Goal
KiraKira: localize and fix the first divergent internal stage for the numeric mismatch clusters (start with KIRA-F03 Mode-2 C60-C62, then KIRA-F04 Channel C23/C24, KIRA-F05 Mode-3 C30-C32, and C28 from F03).

## Evidence
From `orchestra/reports/T06-triage-kirakira.md` (grep the `KIRA-F03` bullet and the related cluster rows):
After F03 (byte-safe IO, merged) and F04 (geometry measured, blocked), numeric mismatches are the remaining blocker: tuple-bypass gives 99 exact / 51 mismatch on tiny Smart; all-gates-off Classic 184 exact / 103 mismatch. See orchestra/reports/F03-kira-typed-row-io.md and F04-kira-tiny-smart-owner.md. Build a paired AEX/Mac intermediate trace (seed, rays, aggregation, compose) if none exists; that transport is itself a valid deliverable (KIRA-F08).

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
