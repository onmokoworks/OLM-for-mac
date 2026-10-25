status: done
summary:
- DistanceGradation Smart final-row shading uses the shared GCD helper at 65536+ output pixels; reference builds retain sequential row calls.
- Debug capture, Classic and overlapping worlds retain sequential ordering. Field generation and pixel arithmetic are unchanged.
- Native comparisons: 669 images exact, six matching refusals; AEX campaigns: 825 exact, 25 oracle rejects/budgets, no Smart mismatches or Mac-only refusals.
- All 454 corpus records replay true; TSan50 and 90 concurrent/threshold runs pass. Historical unit failures are unchanged.

facts:
- `dg_before_bench.py`: 12 OK matrix rows; `sample PID 1 1` exit0 and host exit0. The short 4K PF16 capture contains 19 top-of-stack shade_scanline samples; it sampled the later portion of this short render. P00b uses opaque alpha, and source inspection shows the existing degenerate-mask path. This motivated optimizing the observed final-row stage.
- P00b retained corpus02 has the largest corpus timing cell (4K PF32 0.249849791s in the historical matrix). Its current selected file identity matches the retained manifest. Native driver registry uses heavy index2 and the existing DistanceGradation adapter/build hook.
- `ref_vs_fast.py --plugin olmdistancegradation --jobs 1`: before/after each 669 exact image comparisons, six matching refusals, zero mismatches, with caps1/2/8. Two small input cases refuse in both builds. Includes 200 small, 20 HD, five UHD inputs and heavy cases. First mismatch: none.
- `verify.py olmdistancegradation dg`: default seed1 n300=290 exact/8 AEX rejects/2 budgets; realistic-v1 seed1=96/3/1, seed2026102507=98/1/1; odd-even seed2026 n150=146/4/0; realistic-v2 seed1=96/3/1, seed2026102507=99/1/0. Total 825 Smart exact, 20 original rejects, five original budgets; no mismatches or Mac-only refusals. Classic historical mismatches are separately retained in the raw reports.
- `compare_dg_prior.py`: all 300 default input hashes and 600 candidate route hash/error pairs match retained P04a. No exact-to-non-exact candidate regression.
- Standard replay with stored size/geometry flags and workers: root147, T15b9, P04a72, P02b226: 454/454 `replay_matches_saved=true`.
- `dg_threads.py`: 50 generated cases at caps1/2/8, plus the same 50 under TSan cap8; all 200 executions produce successful images with matching per-case hashes, no sanitizer reports. Half the cases use 257x259 to exercise dispatch.
- Units before/after: 20 class modules, identical statuses (4 exit0, 14 exit1, 2 exit5); the 74 failure/error labels are identical. Two module-level function suites fail identically. These historical suites are not green.
- `dg_concurrent.py` and `dg_bench.py`: 90 exact threshold/concurrent runs. Four simultaneous PF8 Smart RenderBits calls: 1080p median seconds cap1 0.045542667, cap2 0.041480000, cap8 0.038068500, no deadlock. Each cap has three trials.
- Measured cutoff: at 256x256, single-render median cap1 0.000991959 versus cap8 0.000862833; four-render cap1 0.001528666 versus cap8 0.001466833. Below 65536 pixels the same sequential path runs. Values are small and subject to scheduling noise.
- A setup-only script substitution accidentally wrote the first candidate build under the sibling scratch name `orchestra/state/P07d-distancegradation-blur-colordg-threading`. Its build log was retained, the generated directory was deleted, and the script was corrected. The first baseline measurement attempt failed because the expected cache was absent; it produced no measurements. The baseline was rebuilt in the required ticket scratch before the successful measurements. No MAIN or oracle source was modified.
- Memory free checks remained above 30% (55% at DistanceGradation validation). Builds/fuzz use one job and at most two worker/build processes.
- Registered bundles: `~/.cache/olm-emu/P07d-dg-before` SHA256 `a193ac89f4d1585228e9d450a88e011cde357d8bbae9af71aa3e9f78e44a4ee6`; candidate `~/.cache/olm-emu/P07d-dg` SHA256 `15ef510df502b3fb9e801ab30d2acdef8f0c2d803a0eeaa3c738f6538a28a0be`. Both reuse the registered P00b host, and neither is an AEX oracle.

Timing: `dg_before_bench.py` and `dg_bench.py` hold `lockf -k ~/.cache/olm-emu/bench.lock` around `ae_realism_audit.py --phase matrix --plugins olmdistancegradation --cases default corpus02 --situations full 4k --jobs 1` and profiling/concurrent runs. Before/after each 12 OK, no refusal. Render-selector seconds in an SDK host, not native AE. These are single matrix measurements on a shared machine; load may affect them.

| Case | Size | Depth | Before seconds | After seconds |
|---|---|---:|---:|---:|
| default | full | 8 | 0.024490 | 0.018009 |
| default | full | 16 | 0.026670 | 0.021970 |
| default | full | 32 | 0.033296 | 0.030513 |
| default | 4k | 8 | 0.098700 | 0.073378 |
| default | 4k | 16 | 0.114060 | 0.088375 |
| default | 4k | 32 | 0.200510 | 0.152645 |
| corpus02 | full | 8 | 0.029422 | 0.018784 |
| corpus02 | full | 16 | 0.031609 | 0.021214 |
| corpus02 | full | 32 | 0.036605 | 0.029642 |
| corpus02 | 4k | 8 | 0.109648 | 0.083821 |
| corpus02 | 4k | 16 | 0.122424 | 0.089689 |
| corpus02 | 4k | 32 | 0.138315 | 0.127162 |

inference:
- Independent shading rows improve the measured preview workload without changing field construction, reductions, pixel conversion or operand order. Mixed-alpha field generation may remain a useful separate profiling target; this result does not establish an EDT speedup.

changed_files:
- mac/OLMDistanceGradation/OLMDistanceGradation.cpp
- tools/perf/ref_vs_fast.py (registry/heavy preset/default caps)
- orchestra/reports/P07d-evidence/ DistanceGradation scripts, compressed evidence and this report
- orchestra/reports/P07d-distancegradation-blur-colorkey-threading.md

verify:
Run from this worktree, serially, with `OLM_TEST_JOBS=1`:
```
python3 tools/perf/ref_vs_fast.py --plugin olmdistancegradation --jobs 1 --scratch orchestra/state/P07d-distancegradation-blur-colorkey-threading/dg-recheck
python3 orchestra/reports/P07d-evidence/verify.py olmdistancegradation dg
python3 orchestra/reports/P07d-evidence/compare_dg_prior.py
python3 orchestra/reports/P07d-evidence/dg_threads.py
python3 orchestra/reports/P07d-evidence/units.py olmdistancegradation dg-units-recheck
python3 orchestra/reports/P07d-evidence/functions.py olmdistancegradation dg-functions-recheck
python3 orchestra/reports/P07d-evidence/build_dg.py --before
python3 orchestra/reports/P07d-evidence/build_dg.py
python3 orchestra/reports/P07d-evidence/dg_before_bench.py
python3 orchestra/reports/P07d-evidence/dg_concurrent.py
python3 orchestra/reports/P07d-evidence/dg_bench.py
```
Expected counts above; `dg_concurrent.py` builds only, and `dg_bench.py` executes it under the shared lock. Before-source extraction is pinned to commit12b78241; other plugin dependencies are unchanged in this ticket. `retain_dg.py` registers both bundles and preserves evidence. No oracle rebuild is used.

next:
- No required work remains for this ticket. Separate follow-ups may restore historical unit evidence/assets or profile mixed-alpha EDT/field generation.
