## Goal
DirectionalBlur: recover PF16/PF32 semantics with Front=Back=0 and render instead of refusing.

## Evidence
From `orchestra/reports/T10-triage-directionalblur.md` (grep the `DBLUR zero-strength deep dispatch` bullet and the related cluster rows):
115 refusals with 114 completed AEX renders; gate-off reaches only the final refusal, so code must be implemented from the AEX branch, not unblocked.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmdirectionalblur --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmdirectionalblur: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmdirectionalblur*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
