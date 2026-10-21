## Goal
Smoother v1: repair the synthetic-stack address translation UB (stack+a-kStack) and audit related read/write helpers. Bytes must stay identical.

## Evidence
From `orchestra/reports/T11-triage-smoother.md` (grep the `SM1-CLASSIFIER-STACK-UB` bullet and the related cluster rows):
Both minimal PF8 cases trigger UBSan at stack+a-kStack. Require sanitizer-clean replay of tests/fuzz_corpus/olmsmoother with matches_saved unchanged.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmsmoother --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmsmoother: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmsmoother*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
