# R07: release gate — R03 contract failures, F40 stale bindings, doc/perf bindings (R06 groups 2-3)

Read `orchestra/reports/R05-regenerate-stale-bindings.md` and `R06-release-gate-closure.md` (its group 1 is being handled
separately by R08 — do not touch the Radial legacy fixtures 152–181).

## Authorization and rules
Same as R05/R06: regenerate pins/bindings and rewrite superseded assertions only from fresh twice-identical original
executions and current builds; never weaken a check; replace a fixture whose historical package is missing by an equally
strict current one and record it. Real-host items stay labelled "requires real AE/Windows".
**Per-item stop rule (orchestrator override):** the two-refuted-hypotheses rule applies to each ITEM, not the ticket.
When an item is blocked, record why, and move on to the next item. Stop the ticket only when every item is either
resolved, a documented real-host item, a genuine finding, or blocked-with-reason.

## Items
1. The 13 R03 runtime/contract failures (fixture047, 063, 083, 126, 162, 163, 164, 184; generic Directional back-only
   and cleanup, Distance production, Kira UI length, Radial baseline).
2. Remaining F40 stale bindings and missing historical fixture packages.
3. Support-documentation and performance-runner bindings; R03's mixed performance entry.
Commit per item group with a before/after gate table. Genuine Mac-vs-original differences → fuzz-format witness + report.

OLM_TEST_JOBS=2, 1-2 processes. No plugin production changes.
