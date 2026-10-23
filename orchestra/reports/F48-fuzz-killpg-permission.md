status: done

summary:
- Timeout cleanup handles process-group signal errors, falls back to the child PID, and bounds pipe draining.
- Already-gone groups are accepted only with a reaped child and drained pipes; unconfirmed cleanup retains an unresolved case row and reason.
- Shrinking preserves the last completed comparison and corpus when cleanup cannot be confirmed.
- Seven focused tests pass; DG seed 105 n300 exits 0 with 300 full result rows, including 50 and 123.
- Framework-only implementation; no plugin, release gate, or ledger edits.

facts:
- Base revision: `d6cd18daa05d1106718faa2594d4fe7a3b089564`, branch `orch/F48-fuzz-killpg-permission`.
- Read S01 saved traces: indices 50 and 123 raised `PermissionError` from `core.command` during shrinking, leaving `worker_error` rows without results.
- Deterministic reproduction loaded `git show HEAD:tools/fuzz/core.py` into a separate module and ran `CleanupTests.test_live_child_pid_fallback` against its command function. Both injected OS errors escaped (2 errors), and the old Popen context manager waited for the two 60-second children (120.076 seconds total). Reproducible equivalent: `python3 orchestra/reports/F48-fuzz-killpg-permission/reproduce.py --baseline`. Log: `F48-fuzz-killpg-permission/reproduction.log`.
- Real race probe: 200 calls of `command(['/usr/bin/true'], timeout=.000001, deadline=time.monotonic()+2)` against the fixed code returned 200 budget results. One encountered genuine `killpg: PermissionError: [Errno 1] Operation not permitted`; cleanup confirmed child reaped, pipes drained, and group absent. Against the original code, a separate 200-call probe did not hit the race. Logs: `race.log`, `baseline-race.log`; rerunnable probe in `reproduce.py` (race frequency is nondeterministic).
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_timeout_cleanup.py'`: 7 tests passed in 0.348s. Tests cover real PID fallback for both signal errors, already-gone groups, live group after child exit, bounded denied cleanup, descendants holding pipes, retained shrink results/corpus, and unchanged successful commands.
- `OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F48-fuzz-killpg-permission" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_framework.py'`: 14 tests ran in 2.726s, OK, 1 skipped.
- The campaign command in verify below exited **0**, completed **300/300** in **1756.1519 seconds**, with **0 framework errors** and **0 unresolved cleanup rows**. Both recovered cases have Classic mismatch / Smart exact, with successful AEX results on both routes.
- Counts: Classic 7 exact / 290 mismatch / 3 budget; Smart 280 exact / 6 refusal / 11 uncompared / 3 budget. Five cases have both routes exact. AEX Classic 300 ok; AEX Smart 285 ok / 12 reject / 3 budget.
- First mismatch: index 1, Classic, first byte/word 0, expected `24`, actual `18`, 316 differing bytes/words out of 460 bytes. It matches S01's first mismatch.
- Audit: **296/298** formerly completed cases have identical classifications; all **1446 shared raw SHA-256 fields** are unchanged. Cases 125 and 245 changed Smart refusal → exact. The sole dependency change since S01 is the existing DG C43 source change, commit `abdc36026c358b8a27242162915bcc462b073e79`; its parent source hash equals S01's, and its source hash equals this run's. F48 leaves classification logic and plugin sources unchanged.
- DG source SHA-256: S01 / C43 parent `93e70987a6f0eabc36bda4f351a6d8d8972e8fe6b61cf81add876119e4eff7a0`; current / C43 `8a13dc9d113ef735f0d11e4f6d9ce6a914621b1d508e67cb442f0eb4ce8cbd63`.
- Worker SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903` (retained F46 worker). AEX SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- Uncompressed campaign JSON SHA-256: `5a9971541397b8664dbbea3d8c98c5852737d9bb64fa940caa6cba8752e8578f`. Full report retained as `F48-fuzz-killpg-permission/campaign.json.gz` with campaign log and audit JSON.
- Post-run process inspection found no remaining campaign workers/candidates and no build directories. Real-process unit tests verified the direct child was reaped and its PID absent; the descendant-pipe test verified no live descendant remained. Scratch stayed below 5 GiB. `git diff --check` passed.

inference:
- INFERENCE: the short-lived real probe supports an exit/process-group race as the explanation for the observed EPERM. Neither S01 nor the probe captures pre-signal group membership, so the precise kernel race is not established.
- INFERENCE: the two S01 refusal-to-exact transitions belong to pre-existing C43, rather than this cleanup change, based on the exact source hash boundary and unchanged shared output hashes. No claim of unchanged source provenance across S01 is made.
- A genuinely denied live PID/group cannot be declared cleaned up. That path returns bounded diagnostics, records the PID and unresolved reason, and preserves comparison data instead of raising or waiting indefinitely. Tests inject this condition; the 300-case campaign did not encounter it.

changed_files:
- `tools/fuzz/core.py`: bounded cleanup, PID fallback, lifecycle diagnostics, shrink preservation.
- `tools/fuzz/run.py`: unresolved row metadata and summary count without replacing completed result classifications.
- `tools/fuzz/test_timeout_cleanup.py`: focused regression tests.
- `tools/fuzz/README.md`: timeout/unresolved reporting contract.
- `orchestra/reports/F48-fuzz-killpg-permission.md`: this report.
- `orchestra/reports/F48-fuzz-killpg-permission/`: compressed full campaign, logs, audit/reproduction scripts, audit JSON, final process check.

verify:
Run from the worktree root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_timeout_cleanup.py'
OLM_FUZZ_TEST_SCRATCH="$PWD/orchestra/state/F48-fuzz-killpg-permission" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools/fuzz -p 'test_framework.py'
python3 orchestra/reports/F48-fuzz-killpg-permission/audit.py
```

Expected: 7 tests pass; 14 framework tests run, OK with 1 skipped; audit exits 0, 300 full indexed results, 1446 shared hashes unchanged, and the two documented pre-existing C43 classification changes.

Campaign rerun (about 30 minutes, one job):

```sh
mkdir -p orchestra/state/F48-fuzz-killpg-permission
PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 105 --jobs 1 --scratch orchestra/state/F48-fuzz-killpg-permission/work --report orchestra/state/F48-fuzz-killpg-permission/campaign.json --corpus orchestra/state/F48-fuzz-killpg-permission/corpus --corpus-max-bytes 64000000 > orchestra/state/F48-fuzz-killpg-permission/campaign.log 2>&1
python3 orchestra/reports/F48-fuzz-killpg-permission/audit.py orchestra/state/F48-fuzz-killpg-permission/campaign.json
```

Expected: campaign exit 0, 300 full result rows, no framework errors. Wall-clock budget/shrink observations can vary under machine load; archived counts above are observations, not forced expected-value classifications.

next:
- No remaining F48 implementation work. Existing DG pixel mismatches remain separate plugin tickets.
