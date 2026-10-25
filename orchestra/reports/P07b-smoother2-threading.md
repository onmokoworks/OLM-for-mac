status: partial
summary:
- Parallelized Smoother2's independent per-pixel stage using the shared GCD row helper.
- Preserved ordered diagnostics and the OLM_REFERENCE_BUILD sequential path.
- 850 generated AEX cases: 701 Smart exact, 149 matched refusals, zero pixel mismatches or Smart Mac-only refusals.
- All 15 retained corpus cases replay true; forced-cap and TSan checks pass.
- Large-frame differential and locked performance/concurrency measurements are still in progress.

facts:
- `memory_pressure`: initially 61% free; subsequent checks >=58%.
- Locked P00b baseline: 18/18 rows return successfully. See `P07b-evidence/baseline-matrix.jsonl`.
- Locked `sample`: exit 0; the sampled 4K PF32 window identifies `win_FUN_18000cce0_orchestrate` as the main hot path. See `before.sample.txt`.
- `python3 orchestra/reports/P07b-evidence/campaigns.py`: default seed 1 n300; realistic-v1 and v2 seeds 1/20261025 n100 each; odd-even-v1 seed 2026 n150 at 623x623 maximum. All six generation campaigns exit 0.
- Initial mixed-size replay failed setup (`Replay requires the corpus --max-size`); grouped standard replay (`replay.py`) then passes 12/12 at max-size 256 and 3/3 at max-size 623.
- `python3 orchestra/reports/P07b-evidence/threads.py`: 50 cases match hashes at caps 1/2/8; all 50 TSan cases match and have no reports. Half the cases are resized to 257x259 to exercise threading.
- `unit_comparison.py`: 100 tests before and after, both with 17 failures and 7 errors (same named failures/errors and module exit codes). These are existing red tests, not claimed as a passing suite. Full logs are retained.
- Universal candidate and reference bundles build successfully, installed under `~/.cache/olm-emu/P07b-smoother2{,-before}` and registered in INDEX.json. The initial candidate build failed for absent SDK links; `scripts/setup_ae_sdk_links.sh` resolved that build prerequisite.

inference:
- The completed source/class planes are read-only during the pixel stage. Each task owns complete output rows; polygon traversal and all sums retain their original order.
- The current-switch diagnostic variable and input-premultiply flag needed thread-local storage: the former was written per pixel and the latter per render even in normal operation.
- Performance acceptance is not yet claimed.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`
- `tools/perf/ref_vs_fast.py` (Smoother2 registration, heavy preset and default-parameter mode)
- `orchestra/reports/P07b-evidence/*`
- This report.

verify:
- `python3 orchestra/reports/P07b-evidence/campaigns.py` — six completed generation campaigns, zero Smart mismatches/Mac-only refusals.
- `python3 orchestra/reports/P07b-evidence/replay.py` — 15 saved results replay true.
- `python3 orchestra/reports/P07b-evidence/threads.py` — 50 forced-cap and 50 TSan cases pass.
- `python3 orchestra/reports/P07b-evidence/unit_comparison.py` — requires no concurrent source builds; preserves candidate source and compares against pinned pre-ticket source. Same 100-test baseline failures expected.
- `python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 20 --hd 3 --uhd 3 --parallel 1 2 8 --jobs 1 --scratch orchestra/state/P07b-smoother2-threading/diff`
- `python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 0 --hd 3 --uhd 3 --no-large-corpus --default-params --parallel 1 2 8 --jobs 1 --scratch orchestra/state/P07b-smoother2-threading/diff-default`
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07b-evidence/benchmarks.py` — pending.

next:
- Finish large-frame differentials and locked before/after, threshold and four-render concurrency measurements; update this report with final evidence and remove scratch build products.
