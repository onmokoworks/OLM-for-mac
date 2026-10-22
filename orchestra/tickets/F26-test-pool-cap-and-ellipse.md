## Goal
Make gate-listed tests safe to run on the 16 GB Mac before the integration gate (I02) is retried.

## Facts
`orchestra/reports/I02-integration-finish.md` (blocked): 18 over-limit pool sites (ThreadPoolExecutor max_workers 3-6)
in 10 gate-listed tests, and an unguarded recursive-dispatch fallback in two more gate-listed ellipse tests
(same bug class as the 32x18 ellipse fork bomb fixed in F25; F25's grep pattern missed them).

## Steps
1. Guard the two remaining ellipse fallbacks exactly like the F25 reference (child env OLM_SELF_SPAWN_CHILD=1,
   no fallthrough to main(), timeout). Extend `tests/test_self_respawn_guard.py` so its static scan catches
   this variant too (search more broadly than the F25 regex) and covers them.
2. Every ThreadPoolExecutor/Pool in tests/ and tools/emulation/ test or probe scripts: cap with
   `max_workers=min(<current>, int(os.environ.get("OLM_TEST_JOBS", "2")))`. Do not change measurement logic.
3. Add a static test that no pool in those dirs is uncapped.
4. No campaigns or gates; run only the new tests and 2-3 fast affected tests.
