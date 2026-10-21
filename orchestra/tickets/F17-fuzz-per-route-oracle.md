## Goal
Make every fuzz adapter compare each Mac route against the matching original-AEX route
(Mac Classic vs AEX Classic, Mac Smart vs AEX Smart) wherever the original exposes both, then
re-baseline the measured residuals. Afterwards, finish the OLMBlur Smart admission promotion.

## Evidence
- `orchestra/reports/F15-olmblur-small-fixture-promotion.md`: the OLMBlur adapter compared Mac
  Classic against AEX Smart. All 13 shrunk "Classic port bug" members are exact against AEX Classic.
- `orchestra/reports/T07-triage-distancegradation.md` (DG-COMPARATOR-OWNERS): C08/C09 were
  cross-route comparator differences.
- Plugins where the original Classic is a no-op (Smoother2, ToonDilate per T08/T04): keep that
  semantics explicit; do not compare against a different route silently.

## Steps
1. Audit all adapters in `tools/fuzz/adapters/` for route pairing. Fix in the framework if possible
   (oracle result keyed by route). Record which original routes exist per plugin.
2. Re-run seed 1 n 300 for every plugin whose pairing changed (--jobs 2); rebaseline those corpora
   only with a before/after table. Report the new per-plugin residual table.
3. Then: OLMBlur Smart `generic-small-fixture` promotion by the F10/F12 method (promote only rules
   exact on seed 1 and a fresh seed, sanitizer clean, zero admitted mismatches).
