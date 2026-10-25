status: done
summary:
- Added the one-command overnight runner, per-plugin/sampler E/M/R/U summary, and bounded M/R witness reduction.
- Ten-minute round-robin slots use Smart (Classic for Smoother v1), fresh date-derived seeds, and all four samplers with T15b size ceilings.
- Memory admission, date-directory locking, deadline/SIGINT cleanup, disk admission and serial execution are implemented. `--jobs` is a ceiling; actual concurrency is one.
- Completed the requested 15-minute smoke and committed its reports, summary and one reduced ColorKey witness.

facts:
- `tools/fuzz/nightly.sh --hours 0.25 --jobs 1`: exit 0, session status `deadline`, 900.016 seconds. ColorKey/default: E=18368/M=3/R=0/U=6 in 600.003 seconds. DirectionalBlur/default: E=3059/M=0/R=0/U=12 in 300.001 seconds. Total 21448 observations: E=21427/M=3/R=0/U=18.
- First retained ColorKey/default mismatch: seed 812324792801853187, index 2081, reduced geometry 1x8, PF32; first word 25 / byte 100, expected hex `b7b6b63e`, actual `4523c17f`; 3 differing words / 12 bytes. Reduction attempted 32 proposals and accepted 6. Saved at `orchestra/reports/N01-evidence/witnesses/c2d799e6b17314d055e78508.json`.
- After shutdown: `scratch` absent, date directory 51332 bytes including final summary, and `ps -axo pid,ppid,command` showed no aex-guest-worker with this nightly scratch path. No reference workers rebuilt and no plugin sources, ledger or release gate changed.
- `OLM_NIGHTLY_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: 5 tests passed in 142.388 seconds. All 40 plugin/sampler cells completed one observation: E=38/M=0/R=0/U=2. This includes checking each report's same-route oracle binding.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: 4 unit tests passed, 1 opt-in integration test skipped; 0.436 seconds. Includes real child-process-group SIGINT cleanup, refusal reduction, classification and low-memory deadline behavior.
- `python3 tools/fuzz/nightly_summary.py orchestra/reports/N01-evidence` followed by `cmp .../summary.md .../smoke-summary.md`: identical. The extra regenerated summary was removed.
- Shell syntax, Python AST parsing and `git diff --check` passed. Final tool SHA-256 bindings are in `N01-evidence/framework-sha256.json`; adapter/source/oracle bindings are in the two campaign reports and witness.
- Timing provenance: the long smoke started before final hardening of atomic witness writes, repeated-signal handling, setup-deadline classification and the optional test case limit. Those final code changes were present for the 40-cell integration and final unit tests; they do not change sampled cases or numerical code.

inference:
- The runner's orchestration/routing is exercised across all 40 cells; the 15-minute smoke itself covers only the first two cells. Zero rows in its summary mean untested.
- Three ColorKey mismatches share the retained failure signature, not a proven root cause. Investigate the witness separately. These are emulator/fake-host observations, not native AE or all-input compatibility claims.
- Disk admission reserves 200 MB below the 2 GB limit for the current bounded case/final reports. This run demonstrates small retention, not a measured seven-hour disk maximum.

changed_files:
- tools/fuzz/nightly.sh
- tools/fuzz/nightly_summary.py
- tools/fuzz/test_nightly.py
- tools/fuzz/README.md
- orchestra/reports/N01-nightly-fuzz-runner.md
- orchestra/reports/N01-evidence/ (smoke summary, two campaign reports, session report, witness, test logs, final tool hashes)

verify:
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: four tests pass, one skipped.
- `OLM_NIGHTLY_INTEGRATION=1 PYTHONDONTWRITEBYTECODE=1 python3 tools/fuzz/test_nightly.py`: five tests pass; 40 completed observations. Numerical categories are measurements, not an acceptance gate.
- `python3 tools/fuzz/nightly_summary.py orchestra/reports/N01-evidence`: writes `summary.md`, prints the committed counts and first difference; `cmp orchestra/reports/N01-evidence/summary.md orchestra/reports/N01-evidence/smoke-summary.md` returns 0.
- `tools/fuzz/nightly.sh --hours 0.25 --jobs 1`: exits at the deadline, writes reports/summary under orchestra/state/nightly/YYYYMMDD, removes scratch. Fresh seeds and same-date scheduling continuation mean counts need not reproduce the example.
- `tools/fuzz/nightly.sh --hours 7 --jobs 2`: overnight command; serial execution remains within the supplied concurrency ceiling.

next:
- Separate ticket: triage the retained ColorKey PF32 mismatch, beginning with the saved seed/index and reduced witness.
- A full seven-hour run is user-started; it was not performed for this 15-minute-smoke ticket.
