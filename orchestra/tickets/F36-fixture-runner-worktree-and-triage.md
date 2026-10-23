# F36: make the fixed-fixture regression runner worktree-aware; triage its failures

## Facts
- I02 (`reports/integration_I02.md`): the SDK-provisioned fixture runner gives 19 PASS, 194 command FAIL,
  3 installed-identity failures, and 89 skipped.
- F35: the DG part gives 2 pass and 20 fail. Its first failure is the installed executable hash
  `ce48b9eb…`, which differs from the pinned `9a97a076…`.
- Workers run in git worktrees. Untracked assets exist only in MAIN
  (`/Users/onmk/Documents/Projects/Personal/OLM as`): `refs/` originals, `plugins_2025/`,
  `tools/emulation/.venv`, `.venv-cv455`, SDK links, and the built CLIs under `cli/`.

## Do
1. Add a single asset-resolution helper and use it in `scripts/run_olm_mac_fixed_fixture_regression_20260805.py`
   and the helpers it calls.
   - Resolution order: the worktree path first; then `OLM_MAIN_ASSETS`, which defaults to the
     git common-dir parent of the main worktree.
   - Read-only use only. Never copy or write into MAIN.
2. Run the full runner in this worktree with `OLM_TEST_JOBS=1`. Classify **every** failing
   command into one of the following and write a table to the report:
   - (a) environment / missing asset, now fixed by step 1
   - (b) stale pinned identity: an installed/built binary hash, or an evidence binding that no
     longer matches HEAD's legitimately changed code. Name the commit that changed it.
   - (c) real numerical regression: bytes differ from original-AEX-derived expectations
   - (d) other
3. For (c), bisect to the merge that introduced each one, like I02 did.
4. Do **not** repin identities, edit expected files, or weaken assertions. List the (b) items with
   their proposed new values and the evidence; the orchestrator decides.
- Do not touch the release gate/ledger. Use 1-2 processes. Do not use `timeout(1)` (not on macOS).
