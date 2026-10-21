## Goal
OLMBlur: replace the Smart generic-small-fixture gate with a precise general admission rule, and fix the confirmed Classic copy-path port bugs.

## Evidence
From `orchestra/reports/T09-triage-olmblur.md` (grep the `generic-small-fixture` bullet and the related cluster rows):
Smart generic-small-fixture refuses 198/300; removing it gives 148 exact / 50 mismatch. Classic nondefault-tuple gate-off gives 13 exact / 179 mismatch (Classic copy path is largely unimplemented). 2 clusters are confirmed Classic copy-path port bugs. Follow the F10/F12 KiraKira method: promote only rules proven exact on seed 1 and a fresh seed, sanitizer clean, zero admitted mismatches.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmblur --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmblur: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmblur*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
