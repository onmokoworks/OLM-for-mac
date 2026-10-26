# R13: get release gate v2 to 7/7 by fixing the stale harness pieces R12 found

Read `orchestra/reports/R12-release-gate-final.md` first. The gate now runs from a worktree: `--state orchestra/state/<ticket>/... --jobs 1`.

## Remaining failures (all predate the Q refactors; checked at 853db347)
1. Corpus replay: 134 setup failures in 15 groups, because the gate does not pass the saved `--max-size` / `--size-sampler` / `--size-max-height` / `--geometry` / `--color-sampler` flags. Two directories mix sizes.
   Fix: the gate runner reads each witness's saved configuration and groups replays by it, the way `rebaseline_corpus.py` and the nightly do. Keep every comparison predicate.
2. Bundle checks: the F51 differences are 521 ColorKeep rows with `host_error` on both archs (`F47c unsupported/invalid callback: iterate`). F47d classifies all ColorKeep cases as refusals.
   Since P02a (`20c40242`), ColorKeep Smart uses the host `iterate` exactly like the original AEX. The pinned F47c/F47d bundle host does not implement it.
   Fix: implement `iterate` (and any sibling callback ColorKeep now uses) in that native host. Follow the AE SDK semantics, matching the source-host implementation already used by the fresh-seed stage. Then ColorKeep bundles must give real exact comparisons, not refusals.
   Do not loosen the refusal-tolerant predicates. If the F47d predicate accepted all refusals for ColorKeep, report that as a weakness.
3. Selected tests:
   - `tests/test_olmcolorkey_generic_roi_tile.py` does not compile. Its probe keeps a private copy of `OLMColorKeyInfo` without `distance_step_x/y`, which P01c (`1d91b958`) added. Make the probe use the production header or struct instead of a copy.
   - `tests/test_olmkirakira_generic_beta_sanitizers_20260820.py` (first failing case `m1_h7_r0`, PF8 17x11, `ok=0`, callbacks 1/1/1/0) and `tests/test_olmkirakira_native_smoke_tuple_20260820.py` (`m2_highlight_r3`, PF8 1920x1080, `ok=0`) also fail at 853db347. Bisect each to its first bad commit. Then decide, with evidence, whether the production code is wrong or the test is stale, the same way R12 did for ColorKeep.
     - If production is wrong: fix it, and prove it with `tools/refactor/native_diff.py` G1 (3,000 cases, both archs and builds). Every difference must be explained and must match the oracle.
     - If the test is stale: update it to the AEX-grounded contract, with no weakening.
4. Run the complete gate. Required: 7/7 PASS, `local_gate_pass=true`.
5. Rebuild the ZIP with the R12 recipe into `~/.cache/olm-emu/release-R13/` and run the audit. Register it in INDEX.json. Do not publish anything.

## Rules
- Production plugin changes only where step 3 proves they are needed. Harness changes must be general, not per-case.
- Use 1 job. The size rule applies: no new one-off scripts, and fixes go in the existing tools.
