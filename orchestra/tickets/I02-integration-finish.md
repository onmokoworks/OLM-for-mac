## Goal
Finish the integration check I01 left incomplete, safely, and identify the test that exploded processes.

## Background
During I01 the Mac reached ~2,000 processes (~1,500 runnable Python), 15.6 GB swap, 90% system CPU, while
`scripts/run_olm_mac_fixed_fixture_regression_20260805.py` (via the release gate) was running alongside other
workers. The runners now kill whole process groups on timeout (commit "Guard against process explosions"),
and `orchestra/procguard.py` kills the largest worker group if Python processes > 150 or swap > 8 GiB.

## Steps
1. Never run two gates at once. Run, strictly one after another, each in background with a log:
   release gate, generic beta gate, fuzz framework tests, all corpus replays (`--jobs 2`).
2. While the fixed-fixture regression runs, sample every 5 s the descendant count of the runner process
   (`pgrep -g <pgid> | wc -l`, Python count, RSS sum) and record, per regression command (the runner prints
   lanes/commands), the max descendants and max RSS. Report the top 10 commands by descendants.
   If one command exceeds 100 descendants, stop it, report its source and the spawning code path.
3. Classify each gate FAIL as (a) regression (bisect merge) or (b) stale evidence binding. Known pre-existing
   (b): tests.test_olm_release_documentation_20260806, test_olmcolorkey_public_source_bound_docs_20260813,
   test_olmkirakira_smart_workspace_dependency_manifest_20260812 fail identically before and after the runner fix.
4. Report `reports/integration_I02.md`.

## Retry note (orchestrator)
F26 capped every test pool via OLM_TEST_JOBS (default 2) and closed the remaining ellipse fallbacks. The queue now
runs this ticket ALONE (no other worker). Export OLM_TEST_JOBS=2 for all gate runs. procguard still active.
Proceed with the gates; the two-process rule is satisfied by OLM_TEST_JOBS=2 plus exclusivity.
