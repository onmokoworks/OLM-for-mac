## Goal
DirectionalBlur: replace the silent PF8 input-copy path with binary-grounded handling (confirmed port bug).

## Evidence
From `orchestra/reports/T10-triage-directionalblur.md` (grep the `DBLUR PF8 feature dispatch` bullet and the related cluster rows):
Clusters C04/C05/C06/C07/C16/C17 have actual branch traces plus AEX differences of 1-3 bytes on 1x1 inputs.

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
