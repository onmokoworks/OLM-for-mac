# I01 integration check

status: blocked

Checked HEAD: `3f25fe3754df61caab1fca3624c9ce26f455aac8` on `orch/I01-integration-check`.

Stopped under the ticket rule: “For class (a): stop and report the bisect result.” This is an incomplete integration audit, not release approval. No production code, gate, ledger, evidence binding, installed plugin, or numerical output was changed.

## Confirmed regression (FACT)

`tests/test_olmcolorkey_generic_roi_tile.py` passes at base `d027fd4db459` and at first parent `cbb2d255d89d8d064122a97c92352b684e47e442`, then fails at merge **`58ef618832837adb0f46f016b27a114d7f146df9`**: “Merge F18: route targets (9 Smart, Smoother v1 Classic); Mac flags now match originals 10/10”.

First failure: `error: use of undeclared identifier 'PF_OutFlag2_SUPPORTS_THREADED_RENDERING'`, `mac/OLMColorKey/OLMColorKey.cpp:169:24` at the merge (line 200 at checked HEAD). The merge changes GlobalSetup to reference that flag without updating the source-included hostless adapter. No pixel comparison is reached. The real-SDK Xcode build succeeds.

Read-only archive bisection examined 9 revisions across 48 first-parent merge candidates since d027fd4d. Exact commands, source hashes, log hashes, and full boundary logs are in [integration_I01_evidence.json](integration_I01_evidence.json). No checkout/history changes were used.

**INFERENCE:** This is a production-source/test-adapter integration regression, not evidence of a numeric or installed-AE regression. Repair the adapter’s SDK flag declarations in a follow-up ticket, then rerun the gate.

## Build evidence recovered from the prior attempt

FACT: all 10 plugins have successful O2 and sanitizer build logs (20/20, exit 0 and BUILD SUCCEEDED marker). The resumed session checked those markers and retained command/result records; it did not rebuild. The prior runner uses the normal Xcode projects and universal arm64+x86_64 settings, with explicit O2, or O1 + AddressSanitizer/UndefinedBehaviorSanitizer. It is an equivalent direct xcodebuild driver, not a literal invocation of build_all_mac_plugins.sh (that script offers O0/O3 and hardcodes O2 only for DistanceGradation). No post-build lipo/minimum-OS/codesign validation from that script was recovered. Sanitizer compilation is not sanitizer runtime validation.

Build source closure was not separately hashed when the prior attempt ran. The current tracked tree is unchanged, but this limits provenance. Warning novelty against d027fd4d was not established before the stop. Counts below are warning-containing log lines, not unique diagnostics. Common categories include SDK pragma-pack, legacy headermap/Carbon phase warnings, unused functions, C++17 extensions, and conversion warnings.

| Plugin | O2 | sanitizer | warning lines O2 / sanitizer |
|---|---|---|---|
| ColorKeep | PASS | PASS | 330 / 330 |
| OLMBlur | PASS | PASS | 344 / 344 |
| OLMColorKey | PASS | PASS | 332 / 332 |
| OLMDirectionalBlur | PASS | PASS | 354 / 354 |
| OLMRadialBlur | PASS | PASS | 374 / 374 |
| OLMKiraKira | PASS | PASS | 342 / 342 |
| OLMToonDilate | PASS | PASS | 346 / 346 |
| OLMDistanceGradation | PASS | PASS | 354 / 354 |
| OLMSmoother | PASS | PASS | 410 / 410 |
| OLMSmoother2 | PASS | PASS | 350 / 350 |

## Gate rows

FACT: recovered generic gate completed with **47 PASS, 6 FAIL, 0 SKIP**. Every recorded test/dependency SHA-256 was rechecked against this checkout and matched. Gate outputs are retained as reported, not converted to new passes. Eighteen rows print NO TESTS RAN during unittest collection; the runner subsequently executes standalone test functions, so this message alone is not zero coverage.

The release gate was started in the interrupted attempt (release*.log exist, all empty); no completed JSON or row results survived. Its outcome is **UNKNOWN / interrupted**, not PASS or FAIL. It was not restarted after the class-(a) stop.

| Gate/test | Result | Class / detail |
|---|---|---|
| release gate (all rows) | UNKNOWN | Interrupted; no recoverable completed row evidence |
| `tests/test_colorkeep_generic_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_colorkeep_roi_tile_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmblur_generic_beta_lane_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmblur_generic_beta_sanitizers_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmblur_generic_classic_beta_20260822.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmblur_roi_halo_contract_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmcolorkey_generic_pixel_local_beta.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmcolorkey_generic_pixel_local_pairwise.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmcolorkey_generic_roi_tile.py` | FAIL | a: confirmed: Hostless adapter compilation fails; F18 merge 58ef61883283. |
| `tools/emulation/test_dblur_generic_pf8_geometry_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_dblur_generic_deep_geometry_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_dblur_generic_backonly_beta_20260821.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_dblur_generic_backonly_effectmain_20260821.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_dblur_generic_admission_budget_20260821.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py` | PASS | pass: No failure reported in this run. |
| `tools/emulation/test_dblur_generic_roi_policy_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmdistancegradation_generic_production_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmdistancegradation_pf32_smart_unblurred_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmdistancegradation_smart_transactional_20260822.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmkirakira_generic_beta_lane_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmkirakira_generic_beta_sanitizers_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmkirakira_native_smoke_tuple_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmkirakira_mode3_ui_length_beta_20260821.py` | FAIL | unresolved contract drift: 3 unittest failures; length=301 accepted at all three depths. Not a hash-only failure. |
| `tests/test_olmkirakira_mode3_ui_windows_owner_20260821.py` | FAIL | b: stale source binding: 4 unittest failures; repository_source identity[4] is current OLMKiraKira.cpp. |
| `tests/test_olmradialblur_generic_baseline_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmradialblur_generic_baseline_sanitizers_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmradialblur_generic_type3_sanitizers_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmradialblur_generic_budget_20260821.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmradialblur_size_noise_effectmain_20260821.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmradialblur_global_polar_smart_contract_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmsmoother_v1_generic_classic_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmsmoother_v1_smart_beta_20260822.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmsmoother2_default_beta_lane_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmsmoother2_gamma_colors_beta_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmsmoother2_roi_fullframe_contract_20260820.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmtoondilate_generic_beta.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olmtoondilate_roi_safety.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_world_safety.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_checked_allocation.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_checked_rect.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_roi_contract.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_property_cases.py` | PASS | pass: No failure reported in this run. |
| `tests/test_olm_roi_tile_property.py` | PASS | pass: No failure reported in this run. |
| `tests/test_generate_aexcompat_oracle_campaign.py` | PASS | pass: No failure reported in this run. |
| `tests/test_run_aexcompat_reference_20260725.py` | PASS | pass: No failure reported in this run. |
| `tests/test_generic_beta_windows_oracle_handoff.py` | PASS | pass: No failure reported in this run. |
| `tests/test_ae_generalization_smoke.py` | PASS | pass: No failure reported in this run. |
| `tests/test_ae_png_completion.py` | PASS | pass: No failure reported in this run. |
| `tests/test_ae_batch_png_integrity.py` | PASS | pass: No failure reported in this run. |
| `tests/test_run_olm_generic_beta_gate.py` | PASS | pass: No failure reported in this run. |
| `tests/test_beta_support_documentation.py` | FAIL | unresolved documentation/evidence: 4 unittest failures; retained output is truncated. No a/b conclusion. |
| `tests/test_generic_beta_perf_smoke_runner.py` | FAIL | unresolved environment/evidence + timeout: Executable-prefix binding mismatch, followed by 300s timeout; not established as production-source drift. |
| `tests/test_verify_mac_plugin_package_hash.py` | FAIL | unresolved timeout: 300s timeout, terminated -9; output drain incomplete. No a/b conclusion. |

## Stale bindings and unresolved failures

- Confirmed class (b): KiraKira Mode3 Windows-owner report binds an older production source. Re-evidence is required; do not just rewrite expected hashes. Its owner script exposes `--capture` with AEX/worker/source identity inputs. No refresh was performed because the regression stop takes precedence.
- Performance report verification fails with `invocation executable prefix mismatch` and times out. `tools/perf/run_generic_beta_smoke.py` exposes `--bind-existing` and `--verify-only`; applicability to this report has not been established. This is not classified as a production-source regression or a safe hash-only refresh.
- KiraKira Length rejection expectations and support documentation failures remain unclassified. The available tails are insufficient to assign every assertion. Do not infer all are stale hashes.
- Package hash timeout remains unclassified; do not report it as a numerical regression.

## Tests and corpus coverage

The 53 generic rows above are the recovered executed test-file list. No separate fast-test pass or framework integration result was recovered. Bisection reran the ColorKey ROI test nine times. `tools/fuzz/test_framework.py` with OLM_FUZZ_INTEGRATION=1 and all corpus replay remain NOT RUN due to the explicit regression stop.

| Corpus directory | JSON cases | Replay |
|---|---:|---|
| `tests/fuzz_corpus/colorkeep` | 0 | NOT RUN |
| `tests/fuzz_corpus/olmblur` | 39 | NOT RUN |
| `tests/fuzz_corpus/olmcolorkey` | 3 | NOT RUN |
| `tests/fuzz_corpus/olmdirectionalblur` | 56 | NOT RUN |
| `tests/fuzz_corpus/olmdistancegradation` | 145 | NOT RUN |
| `tests/fuzz_corpus/olmkirakira` | 8 | NOT RUN |
| `tests/fuzz_corpus/olmkirakira_gate_off_T06` | 62 | NOT RUN |
| `tests/fuzz_corpus/olmsmoother` | 29 | NOT RUN |
| `tests/fuzz_corpus/olmsmoother2` | 8 | NOT RUN |
| `tests/fuzz_corpus/olmtoondilate` | 300 | NOT RUN |
| `tests/fuzz_corpus/olmtoondilate_T13` | 23 | NOT RUN |
| `tests/fuzz_corpus/radialblur` | 35 | NOT RUN |

Tests under tests/ outside the recovered generic run (not run separately; stopped before runtime selection):

- `tests/test_ae263_preferences_recovery_20260816.py`
- `tests/test_ae_host_minimal_validation_fresh_outputs_20260806.py`
- `tests/test_ae_mac_validation_contract_20260728.py`
- `tests/test_colorkeep_count9_incremental_install_identity_20260813.py`
- `tests/test_colorkeep_current_installed_complete_union_20260814.py`
- `tests/test_colorkeep_current_installed_count9_20260813.py`
- `tests/test_colorkeep_legacy_source_admission_20260813.py`
- `tests/test_colorkeep_nine_color_public_closure_20260813.py`
- `tests/test_colorkeep_pf8_mac_runner_contract_20260806.py`
- `tests/test_colorkeep_public_guard_closure_20260812.py`
- `tests/test_colorkeep_source_bound_complete_union_candidate_20260813.py`
- `tests/test_colorkeep_source_bound_complete_union_install_20260813.py`
- `tests/test_colorkeep_windows_callback_contract_20260731.py`
- `tests/test_colorkeep_windows_mac_boundary_20260806.py`
- `tests/test_colorkey_toondilate_mac_typed_tinyworld_matrix_20260728.py`
- `tests/test_directional_radial_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_directionalblur_dual_independent_20261001.py`
- `tests/test_directionalblur_fixed_getter_20261001.py`
- `tests/test_directionalblur_general_feature_budget_20261001.py`
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
- `tests/test_directionalblur_sse_conversion_20261001.py`
- `tests/test_discriminate_olmsmoother_v1_vs_smoother2_forced_v1_20260728.py`
- `tests/test_kirakira_smoother2_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_native_ae_declared_matrix_20260823.py`
- `tests/test_olm_actual_aex_native_ucrt_table_replay_readiness_20260814.py`
- `tests/test_olm_all10_batch5_current_identity_deferred_v1_20260815.py`
- `tests/test_olm_all10_batch5_current_identity_deferred_v2_20260815.py`
- `tests/test_olm_all10_batch5_current_identity_direct_r_v4_20260816.py`
- `tests/test_olm_all10_batch5_current_identity_live_v3_20260815.py`
- `tests/test_olm_all10_batch5_v3_one_shot_failure_20260815.py`
- `tests/test_olm_all10_current_identity_deferred_v3_20260814.py`
- `tests/test_olm_all10_current_install_fresh_ae_smoke_20260812.py`
- `tests/test_olm_all10_current_installed_public_replay_runner_20260813.py`
- `tests/test_olm_all10_current_installed_public_routes_20260813.py`
- `tests/test_olm_all10_current_source_installed_authority_20260813.py`
- `tests/test_olm_all10_hostless_fixed_fixture_batch_20260814.py`
- `tests/test_olm_all10_post_batch4_fresh_ae_smoke_20260813.py`
- `tests/test_olm_all10_post_radial_type1_smoke_relation_20260812.py`
- `tests/test_olm_all10_post_toondilate_ded9_corrected_20260813.py`
- `tests/test_olm_all10_post_toondilate_ded9_corrected_v2_20260813.py`
- `tests/test_olm_crosshost_corrected_relation_20260806.py`
- `tests/test_olm_crosshost_linear_input_20260806.py`
- `tests/test_olm_deferred_batched_ae_readiness_20260813.py`
- `tests/test_olm_direction_distance_installed_identity_manifest_20260806.py`
- `tests/test_olm_fixed_regression_identity_binding_20260806.py`
- `tests/test_olm_hostless_batch4_install_readiness_20260813.py`
- `tests/test_olm_hostless_batch4_prepared_install_20260813.py`
- `tests/test_olm_hostless_batch4_transaction_readiness_20260813.py`
- `tests/test_olm_hostless_batch4_transactional_installer_20260813.py`
- `tests/test_olm_hostless_batch5_incremental_install_20260813.py`
- `tests/test_olm_hostless_batch5_transaction_20260815.py`
- `tests/test_olm_hostless_batch5_transactional_installer_20260813.py`
- `tests/test_olm_installed_identity_manifest_20260806.py`
- `tests/test_olm_math_ucrt_batch_request_20260814.py`
- `tests/test_olm_math_ucrt_batch_return_20260814.py`
- `tests/test_olm_math_ucrt_downstream_replay_20260814.py`
- `tests/test_olm_math_ucrt_fixed_fixture_runner_integration_20260814.py`
- `tests/test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.py`
- `tests/test_olm_native_ucrt_promotion_table_readiness_20260814.py`
- `tests/test_olm_parameter_ui_gate_20260806.py`
- `tests/test_olm_release_documentation_20260806.py`
- `tests/test_olm_release_gate_20260806.py`
- `tests/test_olmblur_16bpc_typed_exact_contract_20260805.py`
- `tests/test_olmblur_8_16bpc_max1_residual_family_20260718.py`
- `tests/test_olmblur_case0001_reference_conflict_20260805.py`
- `tests/test_olmblur_classic_current_install_smoke_20260812.py`
- `tests/test_olmblur_classic_public_entry_closure_20260812.py`
- `tests/test_olmblur_classic_public_real_sdk_20260813.py`
- `tests/test_olmblur_colorkey_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_olmblur_colorkey_declared_exact_contract_20260805.py`
- `tests/test_olmblur_current_installed_complete_admission_union_20260813.py`
- `tests/test_olmblur_current_installed_public_closure_20260813.py`
- `tests/test_olmblur_pf16_7x5_exported_public_owner_20260813.py`
- `tests/test_olmblur_pf16_7x5_public_admission_20260813.py`
- `tests/test_olmblur_pf16_7x5_universal_candidate_20260813.py`
- `tests/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py`
- `tests/test_olmblur_pf16_legacy_retained_universal_candidate_20260813.py`
- `tests/test_olmblur_pf16_retained_repeat2_universal_candidate_20260813.py`
- `tests/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py`
- `tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py`
- `tests/test_olmblur_pf16_worker_sources_public_admission_20260813.py`
- `tests/test_olmblur_pf16_worker_sources_universal_candidate_20260813.py`
- `tests/test_olmblur_pf32_retained_public_closure_20260813.py`
- `tests/test_olmblur_pf32_retained_universal_candidate_20260813.py`
- `tests/test_olmblur_pf32_retained_universal_candidate_v2_20260813.py`
- `tests/test_olmblur_pf8_retained_exported_public_owner_20260813.py`
- `tests/test_olmblur_pf8_retained_public_admission_20260813.py`
- `tests/test_olmblur_pf8_retained_universal_candidate_20260813.py`
- `tests/test_olmblur_retained_public_universal_candidate_v3_20260813.py`
- `tests/test_olmblur_retained_public_universal_candidate_v4_20260813.py`
- `tests/test_olmblur_smart_public_admission_20260813.py`
- `tests/test_olmblur_smart_public_admission_build_20260813.py`
- `tests/test_olmcolorkey_16bpc_all9_hash_bound_contract_20260805.py`
- `tests/test_olmcolorkey_around_composition_owner_20261001.py`
- `tests/test_olmcolorkey_around_range_20261001.py`
- `tests/test_olmcolorkey_case0005_case0006_provenance_review_20260718.py`
- `tests/test_olmcolorkey_color_hdr_palette_20261001.py`
- `tests/test_olmcolorkey_current_install_smoke_20260812.py`
- `tests/test_olmcolorkey_current_installed_public_closure_20260813.py`
- `tests/test_olmcolorkey_edge_blur_apply_differential_20260716.py`
- `tests/test_olmcolorkey_edge_blur_complete_family_20260806.py`
- `tests/test_olmcolorkey_edge_blur_second_source_20260814.py`
- `tests/test_olmcolorkey_inside_outside_owner_20261001.py`
- `tests/test_olmcolorkey_lab76_multikey_order_closure_20260812.py`
- `tests/test_olmcolorkey_lab94_controlled_20261001.py`
- `tests/test_olmcolorkey_lab_edge_transfer_20261001.py`
- `tests/test_olmcolorkey_lab_state_boundary_20261001.py`
- `tests/test_olmcolorkey_mac_binary_harness_20260716.py`
- `tests/test_olmcolorkey_parameter_order_static_20260728.py`
- `tests/test_olmcolorkey_parameter_ui_parity_20260806.py`
- `tests/test_olmcolorkey_public_entries_real_sdk_20260813.py`
- `tests/test_olmcolorkey_public_source_bound_closure_20260813.py`
- `tests/test_olmcolorkey_public_source_bound_docs_20260813.py`
- `tests/test_olmcolorkey_real_sdk_suite_lifecycle_20260813.py`
- `tests/test_olmcolorkey_source_bound_atomic_20260813.py`
- `tests/test_olmcolorkey_thin_public_owner_20261001.py`
- `tests/test_olmcolorkey_toggle24_transactional_install_20260814.py`
- `tests/test_olmcolorkey_typed_controls_20261001.py`
- `tests/test_olmcolorkey_yuv_limits_20261001.py`
- `tests/test_olmdg_toondilate_classic_render_bitdepth_dispatch_20260716.py`
- `tests/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py`
- `tests/test_olmdirectionalblur_current_installed_dual_side_20260813.py`
- `tests/test_olmdirectionalblur_current_installed_internal_owner_boundary_20260814.py`
- `tests/test_olmdirectionalblur_current_installed_source_bound_union_20260813.py`
- `tests/test_olmdirectionalblur_current_installed_type3_layer_20260814.py`
- `tests/test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.py`
- `tests/test_olmdirectionalblur_dual_side_public_owner_boundary_20260814.py`
- `tests/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py`
- `tests/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py`
- `tests/test_olmdirectionalblur_remaining6_native_ucrt_replay_20260815.py`
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
- `tests/test_olmdirectionalblur_update_params_ui_20260810.py`
- `tests/test_olmdirectionalblur_worldsuite_candidate_20260814.py`
- `tests/test_olmdirectionalblur_worldsuite_lifecycle_closure_20260814.py`
- `tests/test_olmdistancegradation_16bpc_case0012_case0014_preflight_20260716.py`
- `tests/test_olmdistancegradation_actual_aex_powf_xmm_closure_20260814.py`
- `tests/test_olmdistancegradation_current_installed_mode5_20260813.py`
- `tests/test_olmdistancegradation_mode5_incremental_install_identity_20260812.py`
- `tests/test_olmdistancegradation_nonidentity_host_adapter_probe_20260728.py`
- `tests/test_olmdistancegradation_pf16_boundary_capture_integration_20260728.py`
- `tests/test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.py`
- `tests/test_olmdistancegradation_pf32_mode5_universal_codegen_20260812.py`
- `tests/test_olmdistancegradation_pf32_power_native_ucrt_public_closure_20260815.py`
- `tests/test_olmdistancegradation_pf32_power_native_ucrt_universal_candidate_20260815.py`
- `tests/test_olmdistancegradation_pf32_power_native_ucrt_universal_candidate_macos11_20260815.py`
- `tests/test_olmdistancegradation_pf32_power_ucrt_request_20260813.py`
- `tests/test_olmdistancegradation_power_failclose_incremental_install_identity_20260812.py`
- `tests/test_olmdistancegradation_public_smart_owner_contract_20260812.py`
- `tests/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py`
- `tests/test_olmdistancegradation_static_dispatch_contract_20260730.py`
- `tests/test_olmdistancegradation_update_params_ui_20260810.py`
- `tests/test_olmkirakira_approximated_input_resize_contract_20260718.py`
- `tests/test_olmkirakira_classic_smart_admission_guard_20260812.py`
- `tests/test_olmkirakira_current_installed_public_closure_20260813.py`
- `tests/test_olmkirakira_fp_contract_candidate_20260813.py`
- `tests/test_olmkirakira_fp_contract_incremental_install_20260813.py`
- `tests/test_olmkirakira_fp_contract_installed_seam_20260813.py`
- `tests/test_olmkirakira_generic_perf_runner_20260820.py`
- `tests/test_olmkirakira_hotspot_outer_stage_reconciliation_20260730.py`
- `tests/test_olmkirakira_mac_outer_compose_compatibility_20260730.py`
- `tests/test_olmkirakira_merge2_float_oracle_20260728.py`
- `tests/test_olmkirakira_merge2_outer_compose_static_20260728.py`
- `tests/test_olmkirakira_mode1_exported_effectmain_all_depths_20260812.py`
- `tests/test_olmkirakira_mode2_ramp_merge2_exported_effectmain_all_depths_20260812.py`
- `tests/test_olmkirakira_mode2_rotation22_closure_20260812.py`
- `tests/test_olmkirakira_mode2_rotation22_pf32_seam_20260812.py`
- `tests/test_olmkirakira_mode2_rotation22_ramp_helper_exact_20260812.py`
- `tests/test_olmkirakira_mode3_32x18_public_closure_20260814.py`
- `tests/test_olmkirakira_mode3_32x18_public_failclose_20260814.py`
- `tests/test_olmkirakira_mode3_32x18_universal_candidate_20260815.py`
- `tests/test_olmkirakira_mode3_exported_effectmain_all_depths_20260812.py`
- `tests/test_olmkirakira_mode4_compose_matrix_actual_aex_20260811.py`
- `tests/test_olmkirakira_mode4_diagonal2_owner_angle_closure_20260812.py`
- `tests/test_olmkirakira_mode4_fullcaller_hostless_exact_20260807.py`
- `tests/test_olmkirakira_mode4_fullcaller_multiline_fixture_20260811.py`
- `tests/test_olmkirakira_mode4_highlight_gain_boundary_20260806.py`
- `tests/test_olmkirakira_mode4_highlight_gradient_closure_20260812.py`
- `tests/test_olmkirakira_mode4_highlight_gradient_install_smoke_20260812.py`
- `tests/test_olmkirakira_mode4_highlight_gradient_pf32_seam_20260812.py`
- `tests/test_olmkirakira_mode4_highlight_hostless_actual_aex_20260807.py`
- `tests/test_olmkirakira_mode4_multiray_exported_effectmain_all_depths_20260812.py`
- `tests/test_olmkirakira_mode4_natural_families_exact_20260811.py`
- `tests/test_olmkirakira_mode4_natural_fullframe_exact_20260811.py`
- `tests/test_olmkirakira_modes123_rotation_exported_effectmain_all_depths_20260812.py`
- `tests/test_olmkirakira_outer_compose_oracle_20260728.py`
- `tests/test_olmkirakira_parameter_surface_contract_20260717.py`
- `tests/test_olmkirakira_pf8_current_install_smoke_20260812.py`
- `tests/test_olmkirakira_pf8_source_decode_closure_20260812.py`
- `tests/test_olmkirakira_public_smart_bounded_closure_20260812.py`
- `tests/test_olmkirakira_smart_incremental_install_identity_20260812.py`
- `tests/test_olmkirakira_smart_workspace_dependency_manifest_20260812.py`
- `tests/test_olmkirakira_windows_boundary_mac_ae_20260806.py`
- `tests/test_olmkirakira_worldsuite_incremental_install_20260814.py`
- `tests/test_olmkirakira_worldsuite_lifecycle_candidate_20260814.py`
- `tests/test_olmkirakira_worldsuite_lifecycle_closure_20260814.py`
- `tests/test_olmradialblur_current_incremental_install_20260813.py`
- `tests/test_olmradialblur_current_installed_complete_public_union_20260814.py`
- `tests/test_olmradialblur_current_installed_type1_complete_union_20260814.py`
- `tests/test_olmradialblur_current_installed_type3_all_depth_closure_20260813.py`
- `tests/test_olmradialblur_parameter_ui_parity_20260806.py`
- `tests/test_olmradialblur_pf8_writer_oracle_20260728.py`
- `tests/test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.py`
- `tests/test_olmradialblur_smart_cleanup_candidate_20260813.py`
- `tests/test_olmradialblur_strength290_exported_math_boundary_20260814.py`
- `tests/test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.py`
- `tests/test_olmradialblur_strength290_ucrt_math_request_20260814.py`
- `tests/test_olmradialblur_strength290_ucrt_math_return_20260814.py`
- `tests/test_olmradialblur_type1_any_size_edge_noise_source_guard_20260813.py`
- `tests/test_olmradialblur_type1_closure_dependency_manifest_20260812.py`
- `tests/test_olmradialblur_type1_dual_strength_source_guard_20260813.py`
- `tests/test_olmradialblur_type1_edge_noise_source_guard_20260813.py`
- `tests/test_olmradialblur_type1_incremental_install_identity_20260812.py`
- `tests/test_olmradialblur_type1_pairwise_source_guard_readiness_20260813.py`
- `tests/test_olmradialblur_type1_size_noise_source_guard_20260813.py`
- `tests/test_olmradialblur_type1_source_guard_batch4_install_20260813.py`
- `tests/test_olmradialblur_type1_source_guard_batch4_transaction_20260813.py`
- `tests/test_olmradialblur_type3_35_pair_install_20260813.py`
- `tests/test_olmradialblur_type3_35_pair_transaction_20260813.py`
- `tests/test_olmradialblur_type3_45_pair_install_20260813.py`
- `tests/test_olmradialblur_type3_45_pair_transaction_20260813.py`
- `tests/test_olmradialblur_type3_all_depth_public_closure_20260813.py`
- `tests/test_olmradialblur_type3_all_depth_universal_candidate_20260813.py`
- `tests/test_olmradialblur_type3_complete_pair_install_20260813.py`
- `tests/test_olmradialblur_type3_complete_pair_transaction_20260813.py`
- `tests/test_olmradialblur_type3_current_install_smoke_20260812.py`
- `tests/test_olmradialblur_type3_exported_upstream_boundary_20260814.py`
- `tests/test_olmradialblur_type3_layer_span_actual_aex_20260811.py`
- `tests/test_olmradialblur_type3_layer_span_natural_closure_20260812.py`
- `tests/test_olmradialblur_type3_layer_span_production_20260811.py`
- `tests/test_olmradialblur_type3_windows_ae_pilot_20260811.py`
- `tests/test_olmradialblur_typed_inner_geometry_guard_20260807.py`
- `tests/test_olmradialblur_worldsuite_lifecycle_candidate_20260814.py`
- `tests/test_olmradialblur_worldsuite_lifecycle_closure_20260814.py`
- `tests/test_olmradialblur_worldsuite_lifecycle_install_20260814.py`
- `tests/test_olmradialblur_worldsuite_lifecycle_installer_20260814.py`
- `tests/test_olmsmoother2_ada0_input_differential_20260718.py`
- `tests/test_olmsmoother2_case0012_c280_cce0_mac_helper_boundary_20260718.py`
- `tests/test_olmsmoother2_case07_pf16_unique_public_closure_20260814.py`
- `tests/test_olmsmoother2_case07_public_smart_closure_20260814.py`
- `tests/test_olmsmoother2_case07_unique_direct_oracle_20260814.py`
- `tests/test_olmsmoother2_color_weight_20261001.py`
- `tests/test_olmsmoother2_current_installed_public_20260813.py`
- `tests/test_olmsmoother2_gamma18_keyendpoint_exported_owner_closure_20260812.py`
- `tests/test_olmsmoother2_gamma_composition_20261001.py`
- `tests/test_olmsmoother2_key_gamma_hdr_20261001.py`
- `tests/test_olmsmoother2_mac_process_attestation_20260728.py`
- `tests/test_olmsmoother2_mac_report_fail_closed_20260728.py`
- `tests/test_olmsmoother2_pf8_legacy12_public_closure_20260814.py`
- `tests/test_olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.py`
- `tests/test_olmsmoother2_switch_reachability_20261001.py`
- `tests/test_olmsmoother_real_sdk_suite_lifecycle_20260813.py`
- `tests/test_olmsmoother_source_bound_universal_candidates_20260813.py`
- `tests/test_olmsmoother_source_contract_20260813.py`
- `tests/test_olmsmoother_v1_current_installed_admission_union_20260813.py`
- `tests/test_olmsmoother_v1_current_installed_public_20260813.py`
- `tests/test_olmsmoother_v1_pf16_classifier_direction_pair_20260806.py`
- `tests/test_olmsmoother_v1_pf16_interp_codegen_20260806.py`
- `tests/test_olmsmoother_v1_pf16_macos_aexcompat_contract_20260805.py`
- `tests/test_olmsmoother_v1_synthetic_stack.py`
- `tests/test_olmsmoother_v1_windows_boundary_mac_ae_20260806.py`
- `tests/test_olmtoondilate_32bpc_capture_gate_20260718.py`
- `tests/test_olmtoondilate_actual_aex_differential_20260716.py`
- `tests/test_olmtoondilate_actual_aex_differential_20260716_followup.py`
- `tests/test_olmtoondilate_corner_seed_public_admission_20260814.py`
- `tests/test_olmtoondilate_current_installed_exact12_20260813.py`
- `tests/test_olmtoondilate_ded9_incremental_install_identity_20260813.py`
- `tests/test_olmtoondilate_ded9_transactional_installer_20260813.py`
- `tests/test_olmtoondilate_optional_checkin_closure_20260812.py`
- `tests/test_olmtoondilate_public_admission_negative_closure_20260813.py`
- `tests/test_olmtoondilate_same_source_public_paired_replay_20260813.py`
- `tests/test_olmtoondilate_typed_core.py`
- `tests/test_prepare_olmradialblur_type3_windows_witness_20260811.py`
- `tests/test_public_beta_rc_native_ae_20260822.py`
- `tests/test_public_beta_three_gates_20260822.py`
- `tests/test_radialblur_axis_reference_20261001.py`
- `tests/test_radialblur_doublecast_reference_20261001.py`
- `tests/test_radialblur_gain_20261002.py`
- `tests/test_radialblur_noise_offset_20261001.py`
- `tests/test_radialblur_noise_range_20261002.py`
- `tests/test_radialblur_noop_20261002.py`
- `tests/test_radialblur_pf8_writer_20261001.py`
- `tests/test_radialblur_public_parameters_20261001.py`
- `tests/test_radialblur_quality_20261002.py`
- `tests/test_radialblur_rotation_fade_20261001.py`
- `tests/test_radialblur_rotation_fields_20261001.py`
- `tests/test_radialblur_rotation_neutral_alpha_20261001.py`
- `tests/test_radialblur_rotation_restoration_20261001.py`
- `tests/test_radialblur_rotation_size_noise_20261001.py`
- `tests/test_radialblur_seed_thickness_20261002.py`
- `tests/test_radialblur_size_enabled_20261002.py`
- `tests/test_radialblur_size_range_20261002.py`
- `tests/test_radialblur_size_topology_20261002.py`
- `tests/test_radialblur_strength_20261002.py`
- `tests/test_radialblur_typed_angle_20261001.py`
- `tests/test_radialblur_zoom_alpha_20261002.py`
- `tests/test_radialblur_zoom_fade_20261002.py`
- `tests/test_radialblur_zoom_fade_outer_20261002.py`
- `tests/test_release_claim_consistency.py`
- `tests/test_strict_float_exr.py`
- `tests/test_windows_ae_release_boundary_minimal_20260806.py`

## Reproduction and follow-up

From this worktree (all temporary files/logs stay in ticket scratch):

```sh
export TMPDIR="$PWD/orchestra/state/I01-integration-check"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/I01-integration-check-bisect.py > "$TMPDIR/bisect-run.log" 2>&1
# Expected runner exit 0; FIRST_BAD_MERGE 58ef618832837adb0f46f016b27a114d7f146df9.
python3 scripts/run_olm_generic_beta_gate.py --run-test-file tests/test_olmcolorkey_generic_roi_tile.py > "$TMPDIR/colorkey-recheck.log" 2>&1
# Expected exit 1 with undeclared PF_OutFlag2_SUPPORTS_THREADED_RENDERING.
python3 orchestra/reports/I01-integration-check-build.py > "$TMPDIR/build-run.log" 2>&1
# Expected 20 exit-zero build entries; artifacts removed after each build.
```

After the F18 adapter fix, resume the full gates with explicit scratch --report paths, baseline warning comparison, independent fast tests, framework integration, and every corpus. Fuzz runs must use --jobs 2 and the indexed workers; radialblur requires ~/.cache/olm-emu/radial_offset_reference_20261002/target/release/aex-guest-worker with --case-timeout 30. The exact pending tests/corpus inventory and raw recovered gate commands are committed in the evidence JSON. No full-gate PASS is predicted.
