## Goal
Extend `tools/fuzz/` (built in T02, see `tools/fuzz/README.md` and
`orchestra/reports/T02-fuzz-framework-radialblur.md`) with adapters for the other
nine plugins, and produce a first measured residual for each.

Order (stop and report if the deadline below hits): OLMDirectionalBlur, OLMColorKey,
OLMSmoother2, OLMKiraKira, OLMBlur, ColorKeep, OLMDistanceGradation, OLMSmoother,
OLMToonDilate.

## Requirements
- Same contract as the RadialBlur adapter: legal parameter generator from the
  recovered builder ranges already in the repo, original AEX via the emulation
  worker (record its hash), Mac production public path Classic + Smart, raw-bit
  compare, bounded shrink, refusal/budget classes kept separate from mismatches.
- Reuse existing per-plugin public replay helpers in `tools/emulation/`; do not
  re-derive parameter semantics. If a plugin lacks a usable public oracle path,
  record that as the finding instead of building a new emulator.
- For each plugin: `--n 300 --seed 1` campaign, report at
  `reports/fuzz/<plugin>_<date>.json`, small shrunk corpus under
  `tests/fuzz_corpus/<plugin>/` (cap 2 MB per plugin).
- One summary table in your report: plugin, AEX ok/reject/budget, Mac
  exact/mismatch/refusal per route, cluster count, worker hash.

## Constraints
No production plugin changes. Time budget: about 3 hours of wall time; commit after
each plugin so partial progress is usable.
