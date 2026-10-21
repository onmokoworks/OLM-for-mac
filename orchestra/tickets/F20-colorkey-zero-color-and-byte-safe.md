## Goal
ColorKey: (1) admit legal zero-color-count inputs per the original semantics, (2) byte-safe padded pixel access, (3) then the signaling-NaN / signed-zero alpha first divergences if time permits.

## Evidence
From `orchestra/reports/T12-triage-colorkeep-colorkey.md` (grep the `ColorKey zero-color public admission` bullet and the related cluster rows):
Original renders all 41 zero-count cases; existing fall-through gives 40 exact / 1 sNaN alpha mismatch. 88 default + 16 newly reachable UB cases from misaligned typed access. Keep nonfinite coverage; never final-bit corrections.

## Rules for a fix ticket
- Find the cause with the original AEX as oracle (emulation worker + decomp/disasm +
  intermediate traces). Fix it in general code. No per-case expected values, no tolerance.
- Acceptance, all required:
  1. Target clusters: the shrunk cases named above become exact (or the cause is proven
     to be outside the port: Windows dependency / host / comparator — then document and stop).
  2. `tools/fuzz/run.py --plugin olmcolorkey --n 300 --seed 1 --jobs 2` with scratch `--corpus`:
     exact count must not decrease on either route; report before/after per route.
  3. Corpus replay for olmcolorkey: cases that changed must change only toward exact.
     Update the corpus only with the orchestrator-visible before/after table in your report.
  4. Existing plugin tests (`tests/test_olmcolorkey*` relevant subset — pick the fast ones,
     list what you ran) still pass.
- If the fix needs relaxing an admission guard, allowed only when the gate-off experiment
  for the unblocked cases shows exact, and sanitizer is clean.
