status: done
summary:
- SmartPreRender preserves the requested/checked-out rectangles.
- Smart rendering retains input-sized work planes but only ingests the output-local extent; negotiated rows are published after successful cleanup.
- Realistic seed 1 and fresh 20261026: 100/100 exact each, no Mac-only refusal, mismatch, or unavailable oracle.
- Default 300 output hashes/errors unchanged on both routes; 83 old corpus cases and 200 realistic cases replay, and the T15 rectangle witness improves to exact.
- Unit file outcomes unchanged (7 pass / 32 historical failures); ASan/UBSan 200/200 exact. Classic and numerical kernels unchanged.

facts:

Starting commit: `ad12dc148133d5551e7b14cf32d465d3db2fb000`, branch `orch/P02j-directionalblur-geometry`.
Read AGENT_GUIDE, GOTCHAS, compatibility plan, DirectionalBlur ledger row, T15 evidence, P02h and P02d reports.

Original evidence, from read-only MAIN `decomp/OLMDirectionalBlur.aex.c.txt`, retained in [original-geometry-excerpts.txt](P02j-evidence/original-geometry-excerpts.txt):
- `entryPointFunc` case 0x17 copies the incoming render request to checkout and unions checkout result/max rectangles; it does not replace the request with full bounds.
- PF8 worker `FUN_180004a20` calls the world-copy callback before the scaled-zero test. Working-plane sizes derive from INPUT width/height.
- BOTH input-unpack callback `0x180006980` and final writer `0x180006b30` are invoked through Iterate with OUTPUT extent at world+0x2c. `FUN_180006700` forwards this area to PF Iterate8 Suite.
- This is a local-coordinate ingestion boundary, not merely a final-output crop. No aspect correction or extent_hint filtering was added.

Reference identities:
- F52c worker SHA256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`, reused from cache; no rebuild.
- Original AEX SHA256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Final production cpp SHA256 `cf77bd659c85c025d2c179be8fff0b789c97ec2f0a1bdfe6680a696098d66bb6`.
- Per-build binary/dependency hashes are in final-*-provenance.json and sanitized.json.

Commands and real results (all campaigns --jobs 1):
- `python3 orchestra/reports/P02j-evidence/check.py baseline`: realistic seed 1/n100 Smart 61 exact / 39 mismatch / 0 refusal. Default seed 1/n300 Smart 298 exact / 2 unavailable (indices 274,289); Classic 4 exact / 296 mismatch.
- `.../check.py candidate`: first implementation, preserving request and copying full rendered local rows, reached 78 exact / 22 mismatch. First remaining case index 0: PF8 input 11x7, output [5,4,6,5], first word expected 00 / actual 99, one differing byte. Original SHA256 `df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119`; candidate `eef0ac911772395190d6e5ea52cb4f6aaecf2e22fe5ef73b0bff0a1b8c28370d`. The rejected full-input hypothesis is retained in initial-full-input.patch. This new pixel boundary led to inspection of BOTH Iterate calls, not another rectangle-only retry.
- `.../check.py masked`: restricting ingestion to the output-local extent closes all 22 residuals: 100 exact. Default 300: all output hashes and errors unchanged on both routes, zero exact-to-nonexact, same two unavailable Smart oracles. See default-regression.json. Later changes only reuse staging memory and validate input stride before the ROI copy; default geometry does not enter that branch.
- `python3 orchestra/reports/P02j-evidence/measure.py --label final-seed1 --seed 1 --save` and `... --label final-fresh --seed 20261026 --save`: FINAL source, each 100 exact / 0 mismatch / 0 refusal / 0 unavailable. Case-level results, geometry, raw hashes and provenance committed. The fresh run was repeated after the stride check so both provenance files bind final source. First mismatch: none.
- `python3 orchestra/reports/P02j-evidence/replay.py`: existing root corpus 83/83 saved results match. T15 nested rectangle witness changes from its saved Smart mismatch to exact (Classic exact retained); output [1,0,5,1], hash `374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb`. The underlying runner returns 1 for this intentional saved-result change. New labelled realistic corpus 200/200 saved Smart results match. No old corpus edited.
- `python3 orchestra/reports/P02j-evidence/unit_tests.py --label before` / `--label final`: 39 files, 7 pass / 32 fail on each, zero per-file exit changes. Before run temporarily loaded the starting commit cpp with git show and restored the final bytes in a finally block; no concurrent build during that swap. Tests include unittest and no-argument test functions. Historical failures include missing MAIN-only fixture/SDK utility paths and stale source/installed-identity assertions. Full failing-file list below and diagnostics in units-before.json/units-final.json. An earlier unittest-only check attempted 23 files (4 pass/19 fail), superseded by this full 39-file comparison.
- `python3 orchestra/reports/P02j-evidence/verify_sanitized.py`: FINAL source, 200/200 saved exact output hashes and rectangles under ASan/UBSan, including odd byte strides and ROI. No sanitizer error.
- `git diff --check`: pass. Scratch stayed far below 5 GiB; regenerable builds removed at completion. No oracle rebuild, MAIN modification, push, release-gate/ledger edit, or background process left running.

Historical failing files (unchanged):
- `tests/test_directionalblur_dual_independent_20261001.py`
- `tests/test_directionalblur_general_features_20261001.py`
- `tests/test_directionalblur_general_features_effectmain_20261001.py`
- `tests/test_directionalblur_general_input_owner_20261001.py`
- `tests/test_directionalblur_hdr_effectmain_20261001.py`
- `tests/test_directionalblur_hdr_layer_effectmain_20261001.py`
- `tests/test_directionalblur_independent_layer_20261001.py`
- `tests/test_directionalblur_layer_general_effectmain_20261001.py`
- `tests/test_directionalblur_layer_geometry_effectmain_20261001.py`
- `tests/test_directionalblur_layer_span_budget_20261001.py`
- `tests/test_directionalblur_native_noise_bounds_20261001.py`
- `tests/test_directionalblur_pf16_neutral_20261001.py`
- `tests/test_directionalblur_pf16_range_20261001.py`
- `tests/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py`
- `tests/test_olmdirectionalblur_current_installed_dual_side_20260813.py`
- `tests/test_olmdirectionalblur_current_installed_internal_owner_boundary_20260814.py`
- `tests/test_olmdirectionalblur_current_installed_source_bound_union_20260813.py`
- `tests/test_olmdirectionalblur_current_installed_type3_layer_20260814.py`
- `tests/test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.py`
- `tests/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py`
- `tests/test_olmdirectionalblur_remaining6_ucrt_expf_request_20260814.py`
- `tests/test_olmdirectionalblur_remaining6_ucrt_powf_census_20260814.py`
- `tests/test_olmdirectionalblur_remaining6_ucrt_powf_request_20260814.py`
- `tests/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py`
- `tests/test_olmdirectionalblur_smart_cleanup_candidate_20260813.py`
- `tests/test_olmdirectionalblur_testseam_install_closure_20260814.py`
- `tests/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py`
- `tests/test_olmdirectionalblur_type2_natural64_current_install_smoke_20260812.py`
- `tests/test_olmdirectionalblur_type3_layer_source_guard_closure_20260813.py`
- `tests/test_olmdirectionalblur_type3_public_owner_boundary_20260814.py`
- `tests/test_olmdirectionalblur_worldsuite_candidate_20260814.py`
- `tests/test_olmdirectionalblur_worldsuite_lifecycle_closure_20260814.py`

inference:
- The rectangular refusal was an ownership/layout mismatch: a negotiated smaller destination was fed to same-size render helpers. A separate full-size work world preserves their storage contract, while the AEX Iterate area determines which source samples enter the working plane. Zero-initializing samples outside that area reproduces the original initialized plane without per-case corrections.
- The two rectangle-only T15 hypotheses were not retried as fixes. This ticket's first full-input staging hypothesis was refuted at a new pixel boundary; output-local ingestion then passed both campaigns.
- This establishes sampled local CPU-AEX Smart behavior, not native AE or arbitrary host allocations. Expanded incoming requests use checkout's returned bounds; realistic-v1 clips them to input bounds. Outputs physically larger than the checked-out input retain an explicit guard and require a separate original-host witness. Independent selected Noise Layer/ROI intersections and nonzero input origins are not covered by these campaigns.

changed_files:
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp`
- `tests/fuzz_corpus/olmdirectionalblur_realistic_P02j/*.json` (200 separate labelled Smart witnesses)
- `orchestra/reports/P02j-evidence/*` (drivers, results, hashes, historical diagnostics, initial hypothesis patch, original excerpts)
- `orchestra/reports/P02j-directionalblur-geometry.md`

verify:

From this worktree, run serially:
```sh
export TMPDIR="$PWD/orchestra/state/P02j-directionalblur-geometry"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P02j-evidence/measure.py --label verify-seed1 --seed 1
python3 orchestra/reports/P02j-evidence/measure.py --label verify-fresh --seed 20261026
python3 orchestra/reports/P02j-evidence/check.py verify
python3 orchestra/reports/P02j-evidence/replay.py
python3 orchestra/reports/P02j-evidence/unit_tests.py --label verify
python3 orchestra/reports/P02j-evidence/verify_sanitized.py
git diff --check
```
Expected: realistic 100 exact each; default 298 exact/2 unavailable with hashes/errors matching baseline-default-1.json (oracle timeout availability can vary); root corpus 83/83; T15 witness exact despite saved-result mismatch; realistic corpus 200/200; unit files 7 pass/32 historical fails; sanitizer 200/200 exact. check.py uses standard run.py with --geometry realistic n100 and default n300, seed 1, --jobs 1, --shrink-attempts 0. measure.py uses the same realistic-v1 sampler and qualified adapter as measure_F52c.py.

next:
- Orchestrator review/merge, then native AE 26.3 preview/ROI validation.
- Follow up separately on larger-than-input output allocations, nonzero input origins, independent Noise Layer geometry, and historical fixture maintenance. No broader AE-exact claim.
