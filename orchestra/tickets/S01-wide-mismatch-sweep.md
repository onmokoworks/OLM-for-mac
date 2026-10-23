# S01: wide-seed mismatch sweep (measurement only)

## Why
Seeds 44, 45 and 46 each exposed rare admitted mismatches (DG, Radial, ColorKey) that seed 1 never
showed. Before freeze we need a broad sweep for wrong outputs. Refusals matter less.

## Do
- Run `tools/fuzz/run.py` for all 10 plugins on seeds 101..105, n300 each, with the default
  worker. That is 15,000 cases. Use `--jobs 1`, keep the default shrinking for mismatches, and
  give each mismatch a scratch corpus.
- Run sequentially; at most 2 processes in total. Check `memory_pressure` between plugins.
- Report a table of plugin × seed with E/M/R/U. For **every Smart mismatch** (and Classic for
  Smoother v1), give the plugin, seed, case, depth, the first differing word with Mac/ref values,
  and the shrunk input path.
- Commit every mismatch witness to `tests/fuzz_corpus/<plugin>/` as a saved mismatch, named
  `seed<N>_case<id>_S01.json`.
- Do not change any code. A follow-up fix ticket per plugin will be issued.
- Do not touch the release gate/ledger.
