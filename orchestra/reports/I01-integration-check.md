status: blocked
summary: Found and bisected a real ColorKey hostless ROI integration regression to merge 58ef618832837adb0f46f016b27a114d7f146df9 (F18).
  Stopped testing under the ticket's class-(a) rule; no numerical/source/gate fixes.
  Recovered 20/20 successful builds and generic gate 47 PASS / 6 FAIL / 0 SKIP.
  Full release gate, independent fast tests, fuzz framework and corpus replay remain incomplete.

facts:
- Checked source HEAD: 3f25fe3754df61caab1fca3624c9ce26f455aac8; branch orch/I01-integration-check.
- Ran `python3 orchestra/reports/I01-integration-check-bisect.py > orchestra/state/I01-integration-check/bisect-run.log 2>&1`: exit 0, 9 revision probes, 48 first-parent merge candidates since d027fd4d.
- Good first parent cbb2d255d89d8d064122a97c92352b684e47e442: ROI row exit 0. F18 merge 58ef618832837adb0f46f016b27a114d7f146df9: exit 1.
- First failure: undeclared identifier PF_OutFlag2_SUPPORTS_THREADED_RENDERING at ColorKey.cpp:169:24 at merge, :200:24 at checked HEAD. Compilation fails before pixels are compared.
- Retained build result commands/logs: all 20 exit 0 and BUILD SUCCEEDED. These were prior-attempt runs, verified on resume, not rerun. Build provenance and deviations from normal wrapper are documented in reports/integration_I01.md.
- Retained generic-resumed.json completed with 47 PASS / 6 FAIL / 0 SKIP; all recorded test/dependency SHA-256 bindings match current files. Two failing rows timed out. One KiraKira row has confirmed stale source binding; remaining failures are explicitly unresolved.
- Release log files were empty; no completed release report recovered. No independent fast/framework/corpus results recovered. Complete run/skip inventory is in the integration report/evidence.
- Deleted regenerable scratch directories/build trees and object files; retained logs, JSON, and prior runner scripts. No launched process remains.

inference:
- F18 exposed a missing SDK flag declaration in the source-included hostless adapter. This is a genuine integration-test regression, not a demonstrated numeric/AE regression and not a stale hash failure.
- Other failures cannot all be forced into (a)/(b) without further evidence. Classification is incomplete because the explicit stop rule takes precedence.

changed_files:
- reports/integration_I01.md
- reports/integration_I01_evidence.json
- orchestra/reports/I01-integration-check.md
- orchestra/reports/I01-integration-check-bisect.py
- orchestra/reports/I01-integration-check-build.py

verify:
- From this worktree: `export TMPDIR="$PWD/orchestra/state/I01-integration-check"; export PYTHONDONTWRITEBYTECODE=1; mkdir -p "$TMPDIR"`.
- `python3 orchestra/reports/I01-integration-check-bisect.py > "$TMPDIR/bisect-run.log" 2>&1` => exit 0, FIRST_BAD_MERGE 58ef618832837adb0f46f016b27a114d7f146df9; good parent cbb2d255d89d8d064122a97c92352b684e47e442.
- `python3 scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_olmcolorkey_generic_roi_tile.py > "$TMPDIR/colorkey-recheck.log" 2>&1` => exit 1, undeclared threaded-rendering flag.
- Build replay and full evidence commands/hashes are in reports/integration_I01.md and reports/integration_I01_evidence.json.

next:
- Follow-up: synchronize the ColorKey hostless adapter with F18 SDK flags; re-run the ROI/generic gates.
- Resume I01 release gate and remaining failure classification, baseline warnings, fast tests, OLM_FUZZ_INTEGRATION=1, and every corpus (jobs 2, specified radial worker and 30s timeout).
- Re-evidence KiraKira source-bound owner report; investigate Length contract/doc drift and performance/package timeouts separately. No bindings were refreshed.
