status: blocked
summary: Safety preflight prevented launching a release gate that violates the two-process limit.
  Found 18 over-limit pool sites in 10 directly enumerated tests.
  Verified the known 32x18 ellipse recursive-dispatch fix using inert dispatch experiments.
  Found the equivalent unguarded fallback in two other gate-listed ellipse tests.
  Full integration and runtime process rankings remain unperformed.

facts:
- Checked fe69053af992fae06864d75de83faadcb18d6cc3 on orch/I02-integration-finish.
- `python3 -B orchestra/reports/I02-integration-finish-preflight.py > orchestra/state/I02-integration-finish/preflight.json 2> orchestra/state/I02-integration-finish/preflight.log` exited 0: 302 commands, 18 literal max_workers > 2 sites, 10 files.
- Two malformed production dispatches before 317e3ae9 reached inert main once each; current fixed dispatches exit 2 with zero main calls.
- Current separate Rotation and Zoom PF32 ellipse scripts both reach inert main on malformed --production invocation. No recursive subprocess was run.
- Full hashes, source locations, causal path, execution inventory and limitations are in reports/integration_I02.md and reports/integration_I02_preflight.json.
- No gate FAIL or pixel mismatch was measured; no descendant/RSS top-10 can be reported. Known stale-evidence failures were not reverified.

inference:
- The old dispatch explains the process-explosion mechanism documented in commit 317e3ae9; the isolated experiment validates that boundary only.
- Unguarded sibling dispatch and literal 3–6-worker pools make launching the unmodified gate unsafe under the worker brief. The guard fix is not a complete suite safety guarantee.

changed_files:
- reports/integration_I02.md
- reports/integration_I02_preflight.json
- orchestra/reports/I02-integration-finish.md
- orchestra/reports/I02-integration-finish-preflight.py

verify:
- Run the preflight command above from this worktree; expect exit 0 and the stated counts/dispatch outcomes. No emulator modules are imported.
- `git diff --check` should pass.

next:
- Feed the two unguarded sibling scripts to F25. Make all gate-listed process pools honor the two-process budget; audit scratch paths.
- Resume release gate, generic beta gate, framework integration, then all corpus replays sequentially, with cross-process-group monitoring and jobs 2. Complete failure classification/bisection and measured top-10 ranking.
