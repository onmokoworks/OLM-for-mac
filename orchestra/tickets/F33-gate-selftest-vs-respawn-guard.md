# F33: release-gate self-test broken by the F25 self-respawn guard

## Facts (I02, `reports/integration_I02.md` + `orchestra/reports/I02-integration-finish.md`, `orchestra/reports/I02-bisect-gate-self.py`)
- Gate self-test passes at fe69053a. It fails at the F25 merge dd7d8fa1 and at HEAD with `SystemExit(2)`
  under `OLM_SELF_SPAWN_CHILD=1`.
- F25's guard (`OLM_SELF_SPAWN_CHILD=1` → refuse `main()`, exit 2) is meant to stop
  *unmatched* fall-through recursion (the ellipse fork bomb). Legitimate child dispatch must still work.

## Goal
Make the gate self-test pass again and keep the fork-bomb protection.
- Find the exact spawn chain that now hits the guard, for example the gate self-test spawning a script
  that is itself a legitimate child entry point, or the env leaking into a grandchild that is a fresh
  top-level run.
- Fix it in general, for example by clearing `OLM_SELF_SPAWN_CHILD` when launching an independent
  top-level tool, or by keying the guard on the script's own dispatch argument. Do not weaken the
  guard.
- `tests/test_self_respawn_guard.py` and `tests/test_pool_job_cap.py` must still pass. Add a
  regression test that reproduces the I02 failure.
- Do not modify release-gate expectations or the ledger. Fixing the guard/launcher code is in scope.
- Verify with I02's bisect script on HEAD (expected: pass).
