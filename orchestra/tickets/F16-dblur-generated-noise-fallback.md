## Goal
DirectionalBlur: ground the generated-Noise fallback in the AEX so the 25 newly refused PF8 inputs (and index 145, 1x1 Noise, formerly exact by a copy exception) render exact.

## Evidence
From `orchestra/reports/F06-dblur-pf8-feature-dispatch.md` (grep the `index145` bullet and the related cluster rows):
F06 replaced the legacy PF8 copy fallback with binary-grounded dispatch or explicit refusal: +7 exact, but 1 formerly-exact and 25 formerly-mismatching inputs now refuse. Do not restore a special copy exception.

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
