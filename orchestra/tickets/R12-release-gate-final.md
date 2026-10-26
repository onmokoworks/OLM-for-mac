# R12: ColorKeep check-out/check-in count failure, then the full release gate

## Findings (orchestrator, 2026-10-26)
- `scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_colorkeep_generic_beta_20260820.py` fails at 853db347 (the R11 tree, before the refactors), at 9c4c496a and at the current head. The failure is the same every time:
  - test `test_exported_effectmain_nonzero_origin_classic_and_smart`, Smart path, all depths;
  - `fail smart=1 depth=8 rc=0 ... co=101 cc=100 ci=101 li=1`.
- So it predates the Q series. However, release gate v2 reported 7/7 PASS on 2026-10-24, so either the test or the code changed since then. Find out which.
- If `co`/`cc` are layer checkout and checkin counts, a checkout without a matching checkin would leak a layer in real AE. That could be a real bug. Treat it as one until proven otherwise.
- `scripts/run_olm_release_gate_v2.py` only accepts `orchestra/state/R09-release-gate-v2` as its state directory and forces `OLM_TEST_JOBS=2`. It cannot run from a worktree.

## Do
1. Read the test and the harness. Find what co/cc/ci/li count and what the expected values are. Bisect the first failing commit: `git bisect` between the last commit where the gate passed (R09 era, 2026-10-24) and 853db347.
2. If production code is wrong (an unbalanced checkout or checkin), fix it in general code. Then prove that ColorKeep's output is unchanged with `tools/refactor/native_diff.py` (G1: 3,000 cases, both archs and both builds; a balanced checkin must not change pixels). If the test expectation is stale, fix the test to reflect the real contract, and say why with evidence. Do not weaken it.
3. Make the release gate runnable from any worktree:
   - accept `--state` anywhere under the worktree's `orchestra/state/`;
   - accept `--jobs` (default 2, worker runs use 1).
   Keep every stage and assertion as it is.
4. Run the complete release gate v2 (all seven stages) on the current head. Then run `scripts/package_mac_plugins.sh --configuration Release` with the R11 recipe (`orchestra/reports/R11-evidence/build.sh`) and `verify.py` on the new ZIP. Keep the ZIP under `~/.cache/olm-emu/release-R12/` and register it in INDEX.json. Do not publish anything.
5. Report: the root cause, the fix, the seven stage results, and the ZIP path and SHA-256.
