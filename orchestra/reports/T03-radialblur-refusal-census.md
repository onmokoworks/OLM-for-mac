status: done

summary:
- Added optional `OLM_REFUSAL_TRACE` instrumentation to `mac/OLMRadialBlur/OLMRadialBlur.cpp`: 50 guarded returns now append `function:tag@line` and return the original error unchanged.
- Taught the RadialBlur fuzz adapter to capture one trace per route and the framework to store `refusal_guards` outside the compared result; replay equality is untouched.
- Final 500-case seed-1 campaign attributes 784/803 refusals (97.63%) to a named guard and 783/783 error-516 refusals (100%). The remaining 19 are adapter noise-layer checkout refusals (error 710), not production guards.
- Ranked all 8 guards that fired. The two broad exact-fixture gates (`unadmitted-zoom-profile` and `generic-world-not-admitted`) account for 624/803 refusals (77.7%).
- Replay remains 35/35 `matches_saved`; integration tests remain 8/8 OK. No guard was removed or relaxed.

facts:
- Branch `orch/T03-radialblur-refusal-census`, base commit `b899ca88cd43` (T02 merge); ticket commit `0b823df5`.
- Read `orchestra/tickets/T03-radialblur-refusal-census.md`, `tools/fuzz/README.md`, the T02 report, and the RadialBlur adapter/core/run/test modules, plus the `.cpp` guard regions. The campaign report was only queried with small Python summaries.
- Instrumentation: `RadialRefusal(function, tag, line, err)` appends one line to `$OLM_REFUSAL_TRACE` with `O_APPEND` and returns `err` unchanged; `OLM_RADIAL_REFUSAL(tag)` and `OLM_RADIAL_ERROR(tag, code)` wrap it. The path is read only when the environment variable is set. No trace is written when unset.
- Tagged production-reachable guard and error sites (50): Zoom/Rotation profile gates, generic-topology gates, noise-world validation, no-op/compose span checks, pixel-format checks, `Render` argument checks, `SmartPreRender`/`SmartRender` checks, and the OOM/budget returns. Test-seam and diagnostic-only 516 sites were left untagged on purpose.
- Adapter: each route gets `refusal_trace_{route}.txt` in the disposable case directory, is unlinked before the run, read after the route returns, then unlinked. The route result dict is unchanged; the guard list is returned as the third tuple element.
- Framework: `evaluate(..., attribution=None)` accepts a 2- or 3-tuple candidate return and fills per-route attribution. `run_one` writes `row['refusal_guards']` only when non-empty. `refusal_census.py` parses `function:tag@line`, counts per route, and computes non-default parameter slots, depth and profile distributions.
- Final campaign: `python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 --budget-minutes 30 --corpus orchestra/state/T03-radialblur-refusal-census/campaign_corpus` (output in `campaign4.log`). Result: `complete`, 500 cases, 67.14 s, 19 clusters, 35 pixel-mismatch cases.
- Route summary: Classic 62 exact / 24 mismatch / 413 refusal / 1 uncompared. Smart 74 exact / 35 mismatch / 390 refusal / 1 uncompared. Both routes exact: 62. AEX: 461 ok / 32 reject / 7 budget.
- Attribution: 784/803 named (97.63%); 783/783 error 516 (100%); one error-4 work-budget return attributed separately; 19 Smart error-710 refusals unattributed.
- Ranking (Classic/Smart refusals): `RenderZoomTyped:unadmitted-zoom-profile` 204/204; `RenderWorld:generic-world-not-admitted` 120/96; `RenderRotationTyped:unadmitted-rotation-profile` 30/30; `RenderWorld:type3-zero-noise` 21/21; `RenderZoomTyped:unadmitted-zoom-noise-inner-profile` 12/12; `ValidateNoiseLayerWorld:noise-world-invalid` 19/0; `RenderRotationTyped:unadmitted-two-stage-profile` 7/7; `SmartRender:smartrender-generic-budget` 0/1.
- The 19 unattributed Smart 710s all have `noise_type=3` and `noise_variation>0`. The adapter's `pre()` returns 710 for a non-zero Layer slot without constructing an independent noise world, so production code never runs; the Classic route reaches `ValidateNoiseLayerWorld` and returns 516. This is a harness limitation, not an unnamed guard.
- The one error-4 case is seed 1 index 104 (134x253, depth 8, inner strength 1169); it is `SmartRender`'s generic-budget return, so it is not an admission guard and is excluded from 516 coverage.
- Top triggers in the table are descriptive: the most frequent non-default control slots among that guard's cases, plus the full depth and profile distribution. For broad gates no single slot dominates (e.g. `unadmitted-zoom-profile`: slot 12 68/204, depth 32 74 / 16 73 / 8 57, SDR 177).
- Replay: `python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 20 --report orchestra/state/T03-radialblur-refusal-census/replay_final.json` -> 35/35 `matches_saved` (`replay_final.log`).
- Integration: `OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py` -> 8 tests, OK (`integration3.log`).
- Provenance: source SHA-256 `14f1b2a94b8a20eec9742f97ec62e9d168a6c942c05c731a23929ea1d5f97520`; candidate SHA-256 `8b7308839c53a123bf4be677a080edf969314c5e2607e24a18dd3022bb7fb3b0`; worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`; AEX SHA-256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- The committed campaign report's `framework_sha256` entries match the committed `tools/fuzz/*.py` files. Report SHA-256 `98d5f1eb122851041191d205af82446bee51c47640fc966fd15d6c681bdcfc02`; table SHA-256 `94332ab0e4c28382b91663128af5cfbd2d074b8f6d9f90b0a13aa228590265d5`.
- Campaign re-runs rewrite `tests/fuzz_corpus/radialblur` by design when `--corpus` is omitted. Early runs did so; those rewrites were reverted with `git checkout -- tests/fuzz_corpus/radialblur`. The final campaign used a scratch `--corpus`, and the final replay above was run against the committed T02 corpus. The staged diff contains no corpus changes.
- Scratch stayed under 5 GiB; no `/tmp` writes, no push, no MAIN edits, no release-gate/ledger changes.

inference:
- The largest compatibility gap is not a single validation failure but the fail-closed exact-fixture admission model: two catch-all gates reject 624 of 803 refusals (77.7%), and the Zoom catch-all alone rejects half of all refusals (408/803, 50.8%).
- `generic-world-not-admitted` is asymmetric (Classic 120, Smart 96). Smart already diverts some noise-layer cases at checkout (the 19 error-710 cases), so it reaches this gate less often; the gate itself is shared code.
- `ValidateNoiseLayerWorld:noise-world-invalid` appears only on the Classic side for the same reason: Smart's `pre()` stops those cases first. Its 19 cases are exactly the cases the harness cannot route with a real noise world.
- All production-reached refusals are attributed (784/784); the only unattributed refusals are pre-production harness checkout returns. Closing that harness gap is adapter work, not a plugin guard change.
- Counts and top triggers are descriptive for this seed, distribution and worker. They do not prove that the named slot is the sole cause of a guard, and they do not rank legal-input importance. Wall-time AEX budgets and the mismatch count (34 or 35) can move by one under load; the 413/390 refusal counts were stable across runs.
- Tracing is safe for these runs: replay equality, integration tests and refusal counts are unchanged with tracing enabled. This does not prove anything about untested code paths or native AE.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`
- `tools/fuzz/adapters/radialblur.py`
- `tools/fuzz/core.py`
- `tools/fuzz/run.py`
- `tools/fuzz/refusal_census.py` (new)
- `reports/fuzz/radialblur_20261021.json`
- `reports/fuzz/radialblur_refusals_20261021.md` (new)
- `orchestra/reports/T03-radialblur-refusal-census.md`

verify:
```sh
OLM_FUZZ_INTEGRATION=1 python3 tools/fuzz/test_framework.py
python3 tools/fuzz/run.py --plugin radialblur --replay tests/fuzz_corpus/radialblur --budget-minutes 20 --report orchestra/state/T03-radialblur-refusal-census/verify-replay.json
python3 tools/fuzz/run.py --plugin radialblur --n 500 --seed 1 --jobs 4 --budget-minutes 30 --report orchestra/state/T03-radialblur-refusal-census/verify-500.json --corpus orchestra/state/T03-radialblur-refusal-census/verify-corpus
python3 tools/fuzz/refusal_census.py reports/fuzz/radialblur_20261021.json
```
Expected: 8 tests pass; replay exits 0 with 35/35 `matches_saved`; campaign completes 500 with 413 Classic / 390 Smart refusals and 19 signatures; census reports 784/803 total and 783/783 error-516 attribution. Wall-time budget/uncompared counts may vary by one. Keep the corpus destination outside `tests/fuzz_corpus` if the intent is to preserve the T02 fixtures.

next:
- Promote the legal controls behind `unadmitted-zoom-profile` and `unadmitted-rotation-profile` first; they dominate the refusal gap and are already backed by worker families in part.
- Then extend the generic world/layout admission contract, which is the second-largest bucket (216 refusals).
- Add an independent noise-layer world to the adapter so the 19 Smart 710 cases reach production and can be attributed; do not count them as guard evidence until then.
- Re-run the same seed after T01 or any guard promotion; changed refusal counts should be reviewed as new evidence, not patched to hit a target.
