## Goal
KiraKira: recover the embedded float sine/cosine routine at 0x18132b2e0 and the float32 extent operation order, then fix C60/C62.

## Evidence
From `orchestra/reports/F09-kira-numeric-first-divergence.md` (grep the `18132b2e0` bullet and the related cluster rows):
F09 traced C60/C62 first divergence to geometry using the AEX-embedded float sin/cos. Use Ghidra decomp (decomp/OLMKiraKira.aex.c.txt) and emulator leaf calls to bit-match the routine across a dense angle sweep before wiring it into production.

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
