## Goal
RadialBlur: find and fix the first divergent stage in the general Zoom path behind unadmitted-zoom-profile.

## Evidence
From `orchestra/reports/T05-radialblur-gate-off-experiment.md` (grep the `unadmitted-zoom-profile` bullet and the related cluster rows):
Bypassing this gate alone unblocks 240/408 rows: 16 exact, 224 mismatch. Use the T05 bypass build to pick the smallest mismatching cases, cluster them, and trace AEX vs Mac intermediates (field/sampler/fade/writer). Fix general code; only lift the gate for profiles that then fuzz exact with sanitizer clean.

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
