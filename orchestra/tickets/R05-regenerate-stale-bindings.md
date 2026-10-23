depends: R03-harness-ucrt-link
depends: R04-assertion-drift-and-corpus

# R05: regenerate stale evidence bindings and make the release aggregate worktree-aware

## Facts
I03: 68 fixture records are F40 class-(b) stale bindings, 31 more are F40 unresolved inputs/contracts (incl. installed
identity and skipped commands), 1 Windows-owner binding (Kira), 1 doc/source/perf binding, 1 mixed. The release aggregate
aborts in a worktree because the Windows AE boundary return archive is resolved relative to the worktree (MAIN has it,
SHA-256 `e582b0f3…`). Installed-identity and host-smoke audits: all ten bindings invalid (bundles changed since).
Read `F40-stale-bindings-adjudication.md` and `I03-integration-check.md`.

## Authorization (orchestrator)
This ticket MAY regenerate evidence bindings and expected-hash pins, and edit the release gate's path resolution — only
from fresh, reproducible original-AEX executions (run twice, identical) and current builds. Never weaken a check: a binding
is replaced only by an equally strict current one. Do not install into AE.

## Do
1. Make asset resolution worktree-aware (resolve MAIN original assets by absolute path, as the fuzz framework does).
2. For each stale binding: regenerate from current sources + original AEX, verify twice, update the pin. Commands that
   need unavailable assets (installed AE identity, Windows host runs): mark them explicitly as "requires real AE/Windows",
   not pass.
3. Run the release gate and generic gate to completion. Target: every remaining FAIL is either a documented
   requires-real-host item or a genuine finding (reported, not hidden).

## Rules
OLM_TEST_JOBS=2. No plugin production changes. Report a before/after gate table.

## Added by orchestrator after R03 (read `orchestra/reports/R03-harness-ucrt-link.md`)
- 18 RadialBlur fixtures now compile and fail numerically. F39 showed earlier Radial fixture failures were oracle drift
  (references made before UCRT-exact math / SSE NaN fixes). For each: re-render the reference with the current F46 worker
  from the original AEX (twice, identical); if current Mac == new reference, it is drift → repin with provenance. If Mac
  differs from the F46 reference, it is a genuine finding: save a fuzz-format witness and report it (do not hide it).
- 13 runtime/contract failures and 3 stale installed bindings from R03: adjudicate each (current contract vs superseded
  expectation), same strictness rule as above.
