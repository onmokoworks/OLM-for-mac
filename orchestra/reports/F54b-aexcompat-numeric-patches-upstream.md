status: partial
summary:
- Checkpoint: F29/F30/F32/F44/F45/F46/F49/F50 are ported as separate commits on olm/F54b-numeric.
- All eight math unit tests pass; integer portability test passes 100512 cases.
- Full worker test run found one stale DEEP_PIXELS expectation (fixed), then one newly added import test missing its return stub (fixed; rerun pending).
- Full corpus equivalence, final build registration and 4K measurements are pending.
- No claim, push, PR, default-oracle switch, MAIN edit or release-gate edit.

facts:
- AEXCompat dedicated worktree: sibling AEXCompat-olm-F54b, stacked on 5a9bd8f7; checkpoint HEAD 4cf8426a.
- Read shared AGENT_GUIDE, GOTCHAS, compatibility plan, ledger decision matrix and upstream AGENTS/CLAUDE execution floor.
- Fetched origin and read current open issues (34) and PRs (0); no matching numeric issue selected or claim posted, per ticket.
- F29 focused cargo test: 1 passed, 0 failed.
- F30 retained raw UCRT fixtures: 134 rows across 3 passing tests.
- F44/F45/F46 crate suites: respectively 6/7/8 tests passed.
- Wide-integer clang oracle: 512 boundary + 100000 deterministic random combinations passed.
- First full worker run: 705 passed, 1 failed, 3 ignored; stale unsupported DEEP_PIXELS assertion.
- Second full worker run: 707 passed, 1 failed, 3 ignored; added import test omitted loader-provided RET byte. Fix committed; rerun pending.
- Corpus inventory: 2976 saved cases in 23 sets; new verifier includes all sets and both original routes (Smoother Classic only).
- Independent review accepted portability fixes at eba86350; final documentation/test-stub changes await review.

inference:
- Ported dependencies address the known F54 difference categories, but actual corpus equivalence is not yet demonstrated.

changed_files:
- AEXCompat guest numeric/math implementation, behavioral tests, vendored math provenance and documentation.
- tools/emulation/aexcompat_patches/verify_F54b.py
- tools/emulation/aexcompat_patches/install_F54b.py
- This report.

verify:
- With TMPDIR in this ticket scratch, CARGO_TARGET_DIR=$HOME/.cache/olm-emu/build-F54b and memory_pressure >=30% free:
  cargo test --manifest-path <AEXCompat-olm-F54b>/guest/Cargo.toml --release -p aex-guest-worker -p olm-ucrtmath -j 1
- Expected after return-stub fix: no test failures (not yet measured at this checkpoint).
- python3 tools/emulation/aexcompat_patches/verify_F54b.py --worker <built-worker> --plugin <plugin> --jobs 1
- Actual equivalence results pending; no expected success claim.

next:
- Finish reviewed build/tests, replay all corpus sets, measure 4K, exercise F49 capture and register durable worker.
