# R06: close the remaining release-gate items (continue R05)

## Facts (read `orchestra/reports/R05-regenerate-stale-bindings.md` and `R05-results.json`)
Generic gate 45 PASS / 8 FAIL. Release aggregate still invalid. Open items:
1. 18 Radial legacy fixtures: final outputs == F46 (drift confirmed), intermediate-plane pins unresolved because R05
   believed no configurable Radial tracer exists. ONE EXISTS: `~/.cache/olm-emu/worker-C53b-trace/aex-guest-worker`
   (INDEX entry, recipe `tools/emulation/aexcompat_patches/build_C53b.py`, configurable resident watches, F46-identical
   arithmetic; C53b used it for Radial planes). Use it with typed raw input (not the RGBA8 PNG transport).
2. 13 R03 runtime/contract failures (list in R05 report: fixture047, 063, 083, 126, 162, 163, 164, 184 and generic
   Directional back-only/cleanup, Distance production, Kira UI length, Radial baseline).
3. Remaining F40 stale bindings and missing historical fixture packages; support-doc and performance-runner bindings.

## Authorization
Same as R05: you may regenerate pins/bindings and rewrite superseded assertions, only from fresh twice-identical original
executions and current builds, never weakening a check. Where a historical package is missing, replace the fixture by an
equally strict current one (original AEX vs Mac, same parameters/sizes), and record the replacement. Items that truly need
native AE or Windows stay labelled "requires real AE/Windows" (do not try to fake them).

## Do
Work through 1 → 2 → 3, committing per group with a before/after gate table. Any genuine Mac-vs-original difference is a
finding: save a fuzz-format witness and report it. Target: generic gate all PASS except documented real-host items, and the
release aggregate reporting only real-host items.

## Rules
OLM_TEST_JOBS=2, 1-2 processes. No plugin production changes (report findings instead). Never edit `04_Tools/AEXCompat*`.
