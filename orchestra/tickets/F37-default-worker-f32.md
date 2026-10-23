depends: F31-port-ucrtmath-switch-oracle

# F37: make the F32 worker (F30 + DEEP_PIXELS) the fuzzer default

## Facts
- F31 switches the fuzzer default worker from the old one to F30, which has the UCRT math and the
  SSE NaN fix.
- F32 (merged) built `~/.cache/olm-emu/worker-F32-deep/aex-guest-worker` from F30 plus legacy
  DEEP_PIXELS. All 679 non-Smoother-v1 saved outputs are byte-identical to F30. Smoother v1 seed 1
  goes 62/29/95/114 → 205/0/95/0 under it.

## Do
1. Switch the default to F32 the same way F31 switched to F30. Keep F30 and the old worker
   selectable.
2. Replay every corpus under the new default. Every non-Smoother-v1 corpus must match its saved
   result. For Smoother v1, rebaseline with `tools/fuzz/rebaseline_corpus.py` only where the
   oracle newly renders a PF16 case and the result is exact.
3. Run seed 1 n300 for all 10 plugins under the new default. Report the full E/M/R/U table; it
   becomes the new baseline.
- Do not touch plugin code, the release gate, or the ledger. Use 1-2 processes.
