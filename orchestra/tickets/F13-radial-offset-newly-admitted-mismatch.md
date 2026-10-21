## Goal
RadialBlur: close the 4 routes that T01 changed from refusal to mismatch (newly admitted but wrong). Either fix the cause so they become exact, or narrow admission so they are refused again. Then rebaseline tests/fuzz_corpus/radialblur.

## Evidence
From `orchestra/reports/T01-radial-offset-promote.md` (grep the `refusal→mismatch` bullet and the related cluster rows):
T01 Round 6: all base-exact preserved; 4 refusal->mismatch routes listed in the report. Production policy: admitted outputs must be exact.

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
