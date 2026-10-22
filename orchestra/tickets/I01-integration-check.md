## Goal
Integration check of the current `codex/public-beta-roi` after ~25 merged fix branches. Find any
interaction regression between merged changes. Do not fix numerics here; report.

## Steps
1. Build all 10 Mac plugins from the current branch with the project's normal build scripts
   (O2 and the sanitizer variant used by the release gate). Report build failures/warnings that are new.
2. Run the release gate `scripts/run_olm_release_gate_20260806.py` and the generic beta gate
   `scripts/run_olm_generic_beta_gate.py`. For every FAIL, determine whether it is (a) a real
   regression introduced by a merged branch (bisect over merge commits since d027fd4d), or
   (b) an expected evidence/hash-binding change because production source changed (stale binding).
3. Run the fast unit tests under `tests/` (pick by runtime; list what you ran and skipped) and
   `tools/fuzz/test_framework.py` with OLM_FUZZ_INTEGRATION=1.
4. Replay every fuzz corpus `tests/fuzz_corpus/*` (radialblur needs
   `--worker ~/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker --case-timeout 30`).
5. Produce `reports/integration_I01.md`: table of gate rows (PASS/FAIL + class), regressions with the
   bisected merge commit, stale bindings needing re-evidence.
For class (b) only: you MAY refresh the binding/evidence via the gate's own documented refresh path
if one exists; otherwise list them. For class (a): stop and report the bisect result.

## Resume note (orchestrator)
A previous run was cut off (network) before writing a report. Its uncommitted work in this worktree
includes `scripts/check_integration_I01.py`; inspect it, reuse what is sound, and finish the ticket.
The branch has not moved since (base is still 4800f406).
