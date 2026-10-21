## Goal
RadialBlur: remove misaligned-address reference bindings (UBSan) in the DEFAULT production build.

## Evidence
From `orchestra/reports/T05-radialblur-gate-off-experiment.md` (grep the `sanitizer` bullet and the related cluster rows):
Default-build sanitizer control reports misaligned reference bindings on 35 rows; all-gates-off run on 370 rows. Fix with byte-safe loads/stores (memcpy) matching the existing KiraKira/Smoother2 precedent; outputs must stay byte-identical (corpus replay 35/35).

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for radialblur: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmradialblur*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
