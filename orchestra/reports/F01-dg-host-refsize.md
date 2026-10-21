status: done

summary:
- The fuzz scratch host now fills `PF_CheckoutResult.ref_width/ref_height` from the layer geometry, matching the public owner contract; the shared conformance harness stays byte-identical because its hash is frozen in an existing conformance report.
- Smart exact rose 0 -> 166 of 300 (refusal 300 -> 51); Classic exact held at 145/300; both-routes-exact 0 -> 139.
- Corpus re-baseline: 145/145 cases changed only on Smart refusal -> exact (85) or refusal -> mismatch (60); Classic results and every case input/reduction are byte-identical. Replay is again 145/145 `matches_saved`.
- Seven fast plugin/framework tests pass.

facts:

Fix and provenance:
- Branch `orch/F01-dg-host-refsize`; worktree HEAD `dda5660c`.
- `tools/fuzz/adapters/olmdistancegradation.py` transforms the scratch host it already generates: the `pre_checkout` callback now sets `result->max_result_rect` and then `result->ref_width = W; result->ref_height = H;`. `W/H` are the host's runtime input geometry (`int W,H;`), so this is the layer storage size, not a per-case value.
- Deliberately did **not** modify `tools/emulation/dg_public_smart_owner_contract_harness_20260812.cpp`: `refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.json` and `tools/emulation/test_olmdistancegradation_public_smart_owner_contract_20260812.py` bind its SHA-256 (`6d113e40...`). Changing it would invalidate frozen conformance evidence. The fuzz adapter patches its own generated host instead (same pattern as the existing OLMBlur/KiraKira adapters).
- The adapter reports `host_checkout_reference` in `scope()` so the transformation is visible in campaign provenance.
- Smoke check: 5-case run before/after this refactor produced byte-identical per-case results and Smart raw SHA-256 values.

Campaign before/after (`--n 300 --seed 1 --jobs 2 --shrink-attempts 0 --budget-minutes 15`, scratch corpora; shrink disabled so both runs measure the same cases):
- Before (HEAD host, no adapter transform): AEX 290 ok / 8 reject / 2 budget. Classic 145 exact / 145 mismatch / 10 uncompared. Smart 0 exact / 0 mismatch / 300 refusal / 0 uncompared. `both_routes_exact` 0.
- After: AEX 290 ok / 8 reject / 2 budget. Classic 145 exact / 145 mismatch / 10 uncompared. Smart 166 exact / 76 mismatch / 51 refusal / 7 uncompared. `both_routes_exact` 139.
- Case-level diff: Classic status and raw SHA-256 identical for 300/300. Smart transitions were refusal -> exact 166, refusal -> mismatch 76, refusal -> refusal 51, refusal -> uncompared 7. No exact result regressed on either route.
- These after counts equal the T07 gate-off/host-fix experiment (166 exact / 76 mismatch / 51 refusal / 7 uncompared), which is the expected equivalence for this contract-only fix.

Target clusters (same corpus indices as T07): C01 `case000186`, C02 `case000084`, C11 `case000002` now Smart exact. C03/C04/C05/C06/C07/C08/C09/C10/C12 remain Smart mismatch. T07 already showed host-fix and gate-off agree 300/300, so those nine are not caused by the missing reference-size field and remain under the separate compose/comparator tickets. C08/C09 are the cross-route comparator singletons.

Corpus re-baseline (`tools/fuzz/rebaseline_corpus.py`, new):
- Input replay before update: 0/145 `matches_saved`; every one of the 145 saved rows was Classic mismatch + Smart refusal, and now observed Classic mismatch + Smart exact/mismatch.
- Transition table (all 145 files): Classic mismatch -> mismatch 145; Smart refusal -> exact 85; Smart refusal -> mismatch 60.
- The tool refuses to replace an exact result with a non-exact one (and mismatch -> refusal), so this update cannot mask a regression. It changes only `result` and `provenance`; verified `case`, `operations`, `input_sha256`, `seed`, `index`, `max_size`, `generator_version`, `reduction`, and `pixels_zlib_base64` are byte-identical to HEAD for all 145 files.
- Post-update replay: 145 completed, 145 `matches_saved`, exit 0.

Tests run:
- `python3 tests/test_olmdistancegradation_smart_transactional_20260822.py` -> 2 tests OK.
- `python3 tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py` -> 7 tests OK.
- `python3 tests/test_olmdistancegradation_generic_production_beta_20260820.py` -> 2 tests OK (20.5 s).
- `python3 tools/fuzz/test_adapters.py` -> 5 tests OK, 1 skipped (integration test requires `OLM_FUZZ_INTEGRATION=1`).
- Frozen `tests/test_olmdistancegradation_public_smart_owner_contract_20260812.py` is not runnable in this worktree independently of this change: it resolves `aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex`, and the AEX assets exist only in MAIN. It was not modified.

inference:
- The 300 baseline Smart refusals were a fake-host contract defect: real AE's checkout result carries the layer's reference dimensions, and the scratch host left them zero. Filling them is a host fix, not a plugin admission change; the plugin's reference-size guard is unchanged.
- The remaining Smart mismatches/refusals are downstream of the old top guard and are untouched by this ticket; the exact match with T07's gate-off counts is evidence that the host now reproduces the host-corrected experiment.
- No sanitizer rerun was needed: no production guard was relaxed, and T07 already reported gate-off/host-fix ASan+UBSan agreement (249 outputs, zero sanitizer errors) for this same contract change. This report does not claim native AE/Windows UCRT equivalence.

changed_files:
- `tools/fuzz/adapters/olmdistancegradation.py` (scratch-host reference dimensions + scope note)
- `tools/fuzz/rebaseline_corpus.py` (new, generic guarded corpus result refresh from a replay report)
- `tests/fuzz_corpus/olmdistancegradation/*.json` (145 files: Smart/Classic result and provenance only)
- `orchestra/reports/F01-dg-host-refsize.md` (this report)

verify:
```sh
mkdir -p orchestra/state/F01-dg-host-refsize/verify
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --budget-minutes 10 --scratch orchestra/state/F01-dg-host-refsize/verify --report orchestra/state/F01-dg-host-refsize/verify/replay.json > orchestra/state/F01-dg-host-refsize/verify/replay.log 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --budget-minutes 15 --scratch orchestra/state/F01-dg-host-refsize/verify --report orchestra/state/F01-dg-host-refsize/verify/census.json --corpus orchestra/state/F01-dg-host-refsize/verify/corpus > orchestra/state/F01-dg-host-refsize/verify/census.log 2>&1
python3 tests/test_olmdistancegradation_smart_transactional_20260822.py
python3 tests/test_olmdistancegradation_generic_production_beta_20260820.py
git diff --check
```
Expected: replay exit 0 with 145/145 `matches_saved`; census reports Smart 166 exact / 76 mismatch / 51 refusal / 7 uncompared and Classic 145 exact / 145 mismatch / 10 uncompared (AEX 290 ok / 8 reject / 2 budget; wall-time budget counts can vary under load); transactional 2 OK; generic beta 2 OK; `git diff --check` clean.

next:
- Re-shrink the 60 Smart mismatch corpus cases against the now-reachable Smart path and refresh cluster signatures (the current reductions were accepted under the old all-refusal Smart condition).
- Keep DG-SMART-PF32-ADMISSION, DG-PF32-EXTENDED-DOMAIN, DG-DEFAULT-OWNER-COMPOSE, DG-BLURRED-OWNER-COMPOSE, DG-LAYER-RENDER-MODE, DG-INOUT-BACKGROUND, and DG-COMPARATOR-OWNERS as the owners of the remaining nine representative clusters.
- Optionally wire `rebaseline_corpus.py` into the fuzz README workflow; it is independent of this plugin and only acts on a replay report.
