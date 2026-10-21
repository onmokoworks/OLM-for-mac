status: done

summary:
- Added an off-by-default compile-time bypass to `mac/OLMRadialBlur/OLMRadialBlur.cpp` and matching adapter switches, so each T03 admission guard (and all six together) can fall through in a scratch build without changing default behavior.
- Ran 500-case seed-1 campaigns for each of the six top gates and for all six. All completed 500/500 with zero candidate crashes, zero new errors and zero input-budget returns.
- Lifting all six gates unblocks 763/764 route rows: 69 exact, 654 mismatch, 40 uncomparable, 1 still refused by the Smart work-budget return. The gates mostly hide missing or unverified code, not a complete working renderer.
- Individually, `unadmitted-zoom-profile` unblocks 240/408 rows (16 exact, 224 mismatch); `generic-world-not-admitted` only 11/216 (4 exact, 7 mismatch); `unadmitted-rotation-profile` 0/60 because every case is caught by `unadmitted-two-stage-profile`; `type3-zero-noise` 6/42 (2 exact, 4 uncompared); `unadmitted-zoom-noise-inner-profile` 24/24 (2 exact, 22 mismatch); `unadmitted-two-stage-profile` 14/14 (12 mismatch, 2 uncompared).
- Sanitizer all-six run: 370 route rows with UBSan reports (367 in the six-gate population), all misaligned-address reference bindings; no ASan or leak reports. A default-build sanitizer control reports the same class on 35 rows, so the UB pre-exists the bypass.
- Default build replay remains 35/35 `matches_saved`; integration tests remain 8/8 OK.

facts:
- Branch `orch/T05-radialblur-gate-off-experiment`, base commit `78f633ee` (T03 merge), ticket commit `5fc88ab8`.
- Read the T05 ticket, T03 report, `tools/fuzz/README.md`, the RadialBlur adapter/core/run/test modules, and the six guard regions in the `.cpp`.
- Bypass: `#ifndef OLM_RADIAL_EXPERIMENT_BYPASS` defaults to `""`; `RadialExperimentBypass(tag)` checks a comma-separated list; each guard condition gained `&& !RadialExperimentBypass("<tag>")`. The guarded code is not skipped by an early success return; execution falls through to the existing implementation.
- Adapter: `OLM_RADIAL_CANDIDATE_BYPASS="tag1,tag2"` prepends the define to a scratch copy of the source; `OLM_RADIAL_CANDIDATE_SANITIZE=1` selects the probe's existing `-O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer` build. Both default off. Sanitizer reports are returned per route, and the adapter now parses only `KEY value` harness metadata lines so UBSan stack traces cannot become harness errors.
- Default replay: `python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 20 --report orchestra/state/T05-radialblur-gate-off-experiment/final_default_replay.json --scratch orchestra/state/T05-radialblur-gate-off-experiment/final_default_scratch` -> `replay_complete`, 35/35, exit 0. `OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py` -> 8 tests OK.
- Campaigns: `--n 500 --seed 1 --jobs 4`, each with its own scratch `--corpus` and `--report`; 25-minute budget. All six gate reports and the all-six report were produced with the final adapter (framework SHA-256 `4c13a3b61cf8c23b2f86c8597c0505fd8d735705579ddb557807e90efea998bc`).
- Per-gate results (route rows; `unblocked` = candidate produced output; `exact`/`mismatch` compare to AEX; `uncompared` = candidate rendered but AEX rejected/budgeted; `UB rows` from the all-six sanitizer report grouped by the baseline guard):

  | gate | rows | unblocked | exact | mismatch | uncompared | still refused | crash | new error | budget | UB rows |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | unadmitted-zoom-profile | 408 | 240 | 16 | 224 | 0 | 168 | 0 | 0 | 0 | 173 |
  | generic-world-not-admitted | 216 | 11 | 4 | 7 | 0 | 205 | 0 | 0 | 0 | 160 |
  | unadmitted-rotation-profile | 60 | 0 | 0 | 0 | 0 | 60 | 0 | 0 | 0 | 20 |
  | type3-zero-noise | 42 | 6 | 2 | 0 | 4 | 36 | 0 | 0 | 0 | 10 |
  | unadmitted-zoom-noise-inner-profile | 24 | 24 | 2 | 22 | 0 | 0 | 0 | 0 | 0 | 2 |
  | unadmitted-two-stage-profile | 14 | 14 | 0 | 12 | 2 | 0 | 0 | 0 | 0 | 2 |
  | ALL SIX | 764 | 763 | 69 | 654 | 40 | 1 | 0 | 0 | 0 | 367 |

- Same populations with all gates lifted: zoom-profile 408/408 unblocked (24 exact, 382 mismatch, 2 uncompared); generic-world 215/216 (31 exact, 184 mismatch, 1 budget refusal); rotation 60/60 (8 exact, 44 mismatch, 8 uncompared); type3-zero-noise 42/42 (4 exact, 8 mismatch, 30 uncompared); zoom-noise-inner 24/24 (2 exact, 22 mismatch); two-stage 14/14 (0 exact, 14 mismatch).
- Downstream guards still refusing in single-gate runs: zoom-profile -> zoom-noise-inner 168; generic-world -> zoom-profile 177, rotation 19, zoom-noise-inner 6, two-stage 2, generic-budget 1; rotation -> two-stage 60; type3-zero-noise -> zoom-profile 28, rotation 8; zoom-noise-inner/two-stage -> none. ALL SIX -> generic-budget 1.
- The all-six `uncompared` 40 rows split into 30 AEX reject and 10 AEX budget. The 30 rejects are mostly `type3-zero-noise` cases the original AEX also refuses, so those rows have no reference by construction.
- Exact rows per gate (baseline guard): zoom-profile 16 (8 cases: 38, 98, 146, 150, 264, 286, 397, 475); generic-world 4 (2 cases: 166, 326); type3-zero-noise 2 (1 case: 312); zoom-noise-inner 2 (1 case: 319); rotation and two-stage 0 alone. With all gates lifted: zoom-profile 24 exact rows (12 cases), generic-world 31 (16 cases), rotation 8 (4 cases: 28, 61, 108, 438), type3-zero-noise 4 (2 cases: 297, 312), zoom-noise-inner 2 (1 case: 319), two-stage 0. All rotation and type3-zero-noise exact cases are 1x1 frames; many generic-world exact cases are also 1x1.
- Mismatch clusters: zoom-profile 50 clusters (top `[inner Offset]@16` 24, `[outer Offset]@16` 22, `[inner Offset]@32` 16, `[outer Offset]@32` 10); generic-world 5 clusters (`[outer Strength, Angle]@32` 2, `[outer Strength]@32` 2); zoom-noise-inner 6 (`[inner Strength, inner Offset Mode]@8` 8, `[outer Offset Mode, inner Strength]@8` 6); two-stage 5 (`[Blur Type, inner Offset]@32` 4). ALL SIX 118 clusters (top `[inner Strength]@32` 54, `[inner Strength]@16` 46, `[outer Strength]@16` 32, `[outer Strength]@32` 32, `[inner Edge Fade]@16` 31, `[inner Edge Fade]@32` 30).
- Sanitizer: all-six run reports 370 route rows with UBSan (217 Classic, 153 Smart); 367 in the six-gate population, 3 on already-admitted rows. Every report is `-fsanitize=alignment` "reference binding to misaligned address" for `PF_Pixel16`/`PF_PixelFloat`; no AddressSanitizer, LeakSanitizer or aborted process. Sites: 1666/2559/2573 (input admission probes), 3034/3432 (Zoom read/write), 4366/5051 (Rotation read/write), 5017-5020 (PF16 pack writes). Source-line numbers are pre-prepended-define.
- Default-build sanitizer control (same 500 cases, no bypass): 35 rows with the same alignment reports (32 refusal, 2 exact, 1 mismatch). Exact row is case 193 (SDR/16bpc, Classic+Smart); mismatch row is case 425 (HDR/32bpc).
- Provenance: source SHA-256 `ba824fe8627eb5f4cc92686e0970bafba0a41c29e98840b3941cc5e66906f750`; all-six candidate source SHA-256 `cad0e11e8de2b1b5b24772804f475d13b0cd3a775900cfe75ad97b1d74a5ce28`; candidate binary SHA-256 `1d8fe761bc40c95d7cc2171bc2c57d32fe6a5662961ef170b69f3bdc3d585eb5`; worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; AEX SHA-256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- Scratch stayed at 40 MB (limit 5 GiB); no `/tmp` writes, no push, no MAIN edits, no history rewrite. `tests/fuzz_corpus/radialblur` was only read for replay.

inference:
- The answer to the ticket question is: lifting the gates does not reveal a broadly working renderer. 85.7% of unblocked route rows mismatch, 9.0% are exact and 5.2% cannot be compared. The admission model is mostly hiding missing or unverified behavior, not complete code.
- `generic-world-not-admitted` is mostly a precondition/catch-all: alone it unblocks 11/216 rows, and 205 fall to another gate. It is not an independent compatibility lift.
- `unadmitted-rotation-profile` must be considered together with `unadmitted-two-stage-profile`. The rotation guard is fully shadowed downstream, not missing a fall-through path. Even with both lifted, 44/60 rotation rows mismatch and all 8 exact rows are degenerate 1x1 frames.
- `type3-zero-noise` is not a large hidden feature: 30/42 rows are also rejected by the original AEX, so the Mac refusal matches the reference refusal for those inputs. Of the 12 renderable rows, 8 mismatch and 4 exact.
- Narrow exact pockets exist under the two broad gates. Non-degenerate exact cases include zoom-profile 38, 98, 146, 475 and generic-world 49, 60, 166, 232, 326, 352, 371, 429. These are candidates for narrowly widening an exact predicate only after checking the fixture/worker contract; the fuzz cases alone are single-case evidence, not a tuple proof. Degenerate 1x1 exact cases should not be used as evidence of working code.
- The sanitizer defect is unaligned `PixelT` dereference in admission probes and render loops, exposed by adversarial odd rowbyte padding. Because the default build reports the same class, this is a general alignment issue rather than a consequence of the bypass. Real AE worlds may be aligned, so the production risk is unknown from this harness; the UB itself is real C++ behavior on a fuzzer-generatable input.
- Run-to-run AEX wall-time budgets can move `uncompared` by a few rows. The all-six totals were stable across the pre-final and final runs; individual-gate rows can shift by one case.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tools/fuzz/adapters/radialblur.py`
- `tools/fuzz/README.md`
- `tools/fuzz/t05_bypass_summary.py` (new)
- `reports/fuzz/radialblur_t05_bypass_zoom_profile_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_generic_world_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_rotation_profile_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_type3_zero_noise_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_zoom_noise_inner_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_two_stage_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_all_20261021.json`
- `reports/fuzz/radialblur_t05_bypass_all_sanitize_20261021.json`
- `reports/fuzz/radialblur_t05_default_sanitize_control_20261021.json`
- `reports/fuzz/radialblur_t05_gate_bypass_20261021.md` (new)
- `orchestra/reports/T05-radialblur-gate-off-experiment.md`

verify:
```sh
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 20 --report orchestra/state/T05-radialblur-gate-off-experiment/verify-replay.json
python3 tools/fuzz/t05_bypass_summary.py
```
Expected: 8 tests pass; replay exits 0 with 35/35 `matches_saved`; the summary prints the ALL SIX line `764 | 763 | 69 | 654 | 40 | 1 | 0 | 0 | 0 | 367`. Do not omit `--corpus` when re-running a campaign unless the intent is to rewrite `tests/fuzz_corpus/radialblur`.

next:
- Do not lift any of the six gates on this evidence. The broad gates admit mostly mismatching output.
- Triage only the non-degenerate exact cases under `unadmitted-zoom-profile` and `generic-world-not-admitted`; if they share an existing exact fixture, consider a narrow predicate widening with its own regression evidence.
- Treat rotation as a gate pair in any follow-up; `unadmitted-rotation-profile` alone cannot be evaluated.
- Fix the fuzzer runner's `os.killpg` race: a shrink subprocess timeout raised `PermissionError` and lost rows in the first ASan pass. This is harness robustness, not RadialBlur policy.
- Open a separate general alignment ticket for unaligned `PixelT` access; do not fold it into gate promotion.
- Re-run the same seed after T01/gate changes; changed exact/mismatch counts are new evidence, not a target.
