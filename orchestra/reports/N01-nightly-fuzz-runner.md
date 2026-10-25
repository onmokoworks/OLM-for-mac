status: partial
summary: Overnight runner and summary implemented; 40-cell real-worker integration passed. The required 15-minute smoke is still running; final evidence will follow.
facts:
- `OLM_NIGHTLY_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: 5 tests passed in 142.388 seconds; all 40 plugin/sampler cells completed one case, E=38/M=0/R=0/U=2.
- `sh -n tools/fuzz/nightly.sh`, Python AST parsing, and `git diff --check`: passed.
- `tools/fuzz/nightly.sh --hours 0.25 --jobs 1` started, log at `orchestra/state/N01-nightly-fuzz-runner/smoke.log`.
- First retained ColorKey/default mismatch: seed 812324792801853187, index 2081, reduced geometry 1x8, PF32, first word 25 / byte 100; expected hex b7b6b63e, actual 4523c17f. No plugin source modified.
inference:
- The real-worker test validates orchestration/routing, not all-input compatibility. The ColorKey difference needs a separate investigation; no cause inferred.
changed_files:
- tools/fuzz/nightly.sh
- tools/fuzz/nightly_summary.py
- tools/fuzz/test_nightly.py
- tools/fuzz/README.md
- orchestra/reports/N01-nightly-fuzz-runner.md
verify:
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: unit tests pass, opt-in integration skipped.
- `OLM_NIGHTLY_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: five tests pass; 40 completed observations, numerical outcomes are measurements.
- `tools/fuzz/nightly.sh --hours 0.25 --jobs 1`: exits at its wall deadline, writes summary under orchestra/state/nightly/YYYYMMDD, deletes campaign scratch.
next: Complete smoke, commit summary and retained witness, then investigate the ColorKey witness in a separate ticket.
