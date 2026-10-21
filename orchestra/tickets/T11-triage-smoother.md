## Goal
Triage the fuzz residual of **olmsmoother** so it can be turned into fix tickets.
Model it on the RadialBlur work: `orchestra/reports/T03-radialblur-refusal-census.md`
and `orchestra/reports/T05-radialblur-gate-off-experiment.md` (if present).

## Facts
- Fuzz baseline: `reports/fuzz/olmsmoother_*.json`, adapter `tools/fuzz/adapters/`, summary in
  `orchestra/reports/T04-fuzz-adapters-all-plugins.md` (grep the olmsmoother row/section).
- Baseline row: AEX 91/209/0; Classic 62/29/95; Smart 62/29/95; 2 clusters (AEX itself rejects 209: check whether generator ranges are wrong first)

## Steps
1. Refusals: add behavior-neutral refusal tracing to the Mac source (same pattern as
   `OLM_RADIAL_REFUSAL` in `mac/OLMRadialBlur/OLMRadialBlur.cpp`, env `OLM_REFUSAL_TRACE`),
   wire it into the adapter, and rank guards by refused legal cases.
   Prove neutrality by corpus replay (`--replay tests/fuzz_corpus/olmsmoother` must keep all
   `matches_saved`).
2. Gate-off experiment (scratch build only, compile-time-off switch): for the top guards,
   how many unblocked cases are exact / mismatch / crash / sanitizer error.
   "No fall-through path" is a valid finding.
3. Mismatches: for each cluster, take the smallest shrunk case and locate the FIRST
   differing stage if any intermediate trace exists; otherwise give byte-diff stats
   (count, max abs diff, which channels, spatial pattern). Classify per the plan's table
   (docs/COMPATIBILITY_ANALYSIS_PLAN_JA.md): unexplained / port bug / Windows dependency /
   host / comparator / unverified.
4. Use `--jobs 2` for every fuzz run (the machine is shared by several workers). After F17 the fuzz adapters pair routes correctly; read orchestra/reports/F17-fuzz-per-route-oracle.md and F18-route-target-per-plugin.md first, and focus on the route AE actually uses.

## Done when
Report contains: ranked guard table, gate-off table, cluster classification table, and
a list of proposed fix tickets (one line each, with the evidence that motivates it).
No production behavior changes.
