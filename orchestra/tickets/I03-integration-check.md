# I03: integration check after S01 follow-ups (C47–C56, F48–F51)

## Goal
Many plugin changes merged since I02. Confirm the integrated branch is consistent: every gate, every corpus, unit tests,
and the shipped bundles. Read-only verification: do not change production code; report and classify.

## Steps (strictly sequential, background with logs, OLM_TEST_JOBS=2; this ticket runs alone)
1. Release gate, generic beta gate, fuzz framework tests (`tools/fuzz/test_*.py`), every plugin's unit tests.
2. All corpus replays (`run.py --replay tests/fuzz_corpus/<plugin>` for all ten). A replay difference whose only cause
   is an original-side stop ("execution stopped before the guest returned") is an oracle-budget event: retry that case
   alone with `--case-timeout 120` before classifying.
3. Fresh seed 777 n300 Smart for all ten plugins (Smoother v1 Classic), report E/M/R/U. Any mismatch is a finding: save
   the witness and report it (do not fix here).
4. Universal bundles: `build_F47_bundles.py`, then `verify_F47d.py` (arm64 bundle vs AEX, n100 each) and
   `verify_F51.py --n 100` (x86_64 vs arm64 slices) for all ten.
5. Classify each gate FAIL: (a) regression → bisect to the merge; (b) stale evidence binding (F40 list) → list only.

## Output
`orchestra/reports/I03-integration-check.md` with a per-plugin table and the classified failures.
Worktree-aware asset resolution: original assets in MAIN by absolute path, never copied.
