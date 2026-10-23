status: done
summary:
- Fixed gate child marker lifetime and distinguished explicit in-process main(argv) calls from CLI fall-through.
- Valid --run-test-file dispatch consumes the marker while running tests and restores it on return/error.
- Unmatched CLI children still exit 2; malformed ellipse child protection is unchanged.
- Added I02 and real child-dispatch regressions; no release expectations or ledger changes.

facts:
- Exact chain: execute_entry -> run_captured_process_group -> gate --run-test-file tests/test_run_olm_generic_beta_gate.py with OLM_SELF_SPAWN_CHILD=1 -> run_test_file imports tests -> GATE.main(["--report", ...]) raised SystemExit(2). Test-launched independent optimized gate processes also inherited the marker.
- Before fix: `python3 -B tests/test_self_respawn_guard.py` with the initial regressions ran 7 tests, 2 failures; the direct I02 case raised SystemExit(2). Log: orchestra/state/F33-gate-selftest-vs-respawn-guard/before.log.
- After fix: same command, 7 tests OK (exit 0). Includes malformed gate CLI and existing malformed ellipse children, the I02 explicit invocation, and real --run-test-file dispatch invoking existing report-publication and independent optimized-process tests.
- `python3 -B tests/test_pool_job_cap.py`: 2 tests OK, exit 0.
- `OLM_SELF_SPAWN_CHILD=1 python3 -B scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_run_olm_generic_beta_gate.py`: 20 tests OK, exit 0.
- Full self-test initially exposed missing Util SDK dependencies; created ignored read-only symlink Util -> /Users/onmk/Documents/Projects/Personal/OLM as/Util. No MAIN writes or copied assets. Focused new regressions do not require these SDK files.
- I02 bisect script with --expect-head-pass --scratch-dir orchestra/state/F33-gate-selftest-vs-respawn-guard: exit 0. fe69053af992fae06864d75de83faadcb18d6cc3 PASS, dd7d8fa1f9c457628d2837aed81cce4016399d81 FAIL (SystemExit(2)), dc68ec0acad975030355e34626c02fc553237cfb PASS. Each revision ran the original single I02 test.
- Bisect script retains historical default expectations; optional --expect-head-pass verifies repaired HEAD and --scratch-dir keeps evidence in this ticket's scratch directory.
- `git diff --check`: exit 0. No emulator/build campaigns or build trees created; no background processes remain.

inference:
- The marker describes an unmatched process entry, not all future calls or descendants. Consuming it after recognized dispatch and applying the fall-through guard only to CLI argument parsing preserves the recursion boundary while allowing explicit in-process calls.
- This is a harness repair; no numerical compatibility claims follow from it.

changed_files:
- scripts/run_olm_generic_beta_gate.py
- tests/test_self_respawn_guard.py
- orchestra/reports/I02-bisect-gate-self.py
- orchestra/reports/F33-gate-selftest-vs-respawn-guard.md

verify:
Run from the worktree root:
```sh
mkdir -p orchestra/state/F33-gate-selftest-vs-respawn-guard
export TMPDIR="$PWD/orchestra/state/F33-gate-selftest-vs-respawn-guard"
export TMP="$TMPDIR" TEMP="$TMPDIR" PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
python3 -B tests/test_self_respawn_guard.py > "$TMPDIR/guard.log" 2>&1
python3 -B tests/test_pool_job_cap.py > "$TMPDIR/pool.log" 2>&1
# Full gate-self requires the existing SDK Util files. For a fresh worktree:
if [ ! -e Util ]; then ln -s '/Users/onmk/Documents/Projects/Personal/OLM as/Util' Util; fi
OLM_SELF_SPAWN_CHILD=1 python3 -B scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_run_olm_generic_beta_gate.py > "$TMPDIR/gate-self.log" 2>&1
python3 -B orchestra/reports/I02-bisect-gate-self.py --expect-head-pass --scratch-dir "$TMPDIR" > "$TMPDIR/bisect.log" 2>&1
git diff --check
```
Expected: every command exits 0; 7 guard tests, 2 pool tests, 20 gate self-tests OK; bisect success vector [true, false, true]. The historical F25 failure printed in bisect.log is intentional.

next:
- Orchestrator review/merge. Other I02 release and numerical failures remain outside this ticket.
