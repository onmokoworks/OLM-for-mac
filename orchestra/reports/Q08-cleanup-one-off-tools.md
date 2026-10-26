status: blocked

summary:
- Removed 157 unreachable investigation scripts: 142 from scripts/ and 15 from tools/fuzz/, in separate directory commits.
- Removed 41,777 source lines; preserved all plugin code, corpora, reference data, emulation/AE-smoke tools, tests and release-gate files.
- Framework tests and ten before/after corpus witnesses pass; all ten Release bundles build and packaging succeeds.
- The required all-pass release gate is blocked by an unchanged ColorKeep Smart ROI test failure present before deletion.

facts:
- Base: `b9c61119754387f399f4c9c19daf0ed2ae4370fd` (full SHA in the evidence JSON); Q07 is merged. Deletion commits: `bcd70b36` (scripts: 41,242 lines) and `52851fe3` (tools/fuzz: 535 lines).
- Read AGENT_GUIDE.md, orchestra/BRIEF.md, orchestra/REFACTOR_SPEC.md and emulation GOTCHAS. No plugin behavior was edited; no worker was rebuilt, no MAIN file modified, and nothing pushed.
- The conservative closure examined 756 source/script candidates. It preserves 2,687 tool/script paths; all 2,687 still exist. Most fuzz probes remain because documentation, retained emulation tools, or their dependencies reference them. Examples: verify_F53.py is linked from emulation/aexcompat_patches/README-F53.md; sweep_T15b.py is imported by nightly_summary.py and linked by fuzz/README.md.
- Roots include every requested entry point/directory, all tests, all READMEs, docs, the shared guide/brief/spec, Mac build sources, release-gate variants, and retained non-source tool assets. Full-path, basename and Python-module tokens are followed transitively, including subprocess/path strings and comments. Ambiguous names preserve every match. Binary/unreadable files and text above 8 MiB are not scanned. This over-approximates literal references; it is not a general proof about arbitrary dynamically constructed strings.
- Dynamic adapter imports in run.py/ref_vs_fast.py are covered by retaining the complete adapters directory. run.py also hashes all remaining fuzz Python files for provenance; that inventory necessarily shrinks but does not execute the removed scripts. The fixture-source directory and its builder are explicitly retained as part of reference-fixture generation.
- `git diff --check b9c61119`: exit 0. Before adding this report/evidence, the only changed paths were the 157 deletions and notes/REMOVED_TOOLS.md.

Validation (commands run with TMPDIR/TMP/TEMP inside this ticket and OLM_TEST_JOBS=1):

| Check | Before | After |
| --- | --- | --- |
| `python -B -m unittest discover -s tools/fuzz -p 'test_*.py' -v` | exit 0; 50 tests, 3 skipped | exit 0; 50 tests, 3 skipped |
| One recorded corpus witness per plugin, `tools/fuzz/run.py --jobs 1 --replay ...` | 10/10 complete, exit 0 | 10/10 complete, exit 0; entire replay result objects identical |
| `python -B tests/test_release_gate_v2.py` | not run | exit 0; 5 tests passed |
| ColorKeep generic-beta file through the release gate's stdlib test runner | exit 1 | exit 1; same Smart ROI callback-accounting failure |
| Release packaging | not run | ten universal builds verified; archive with ten plugins verified, exit 0 |

- Corpus comparisons: zero changed result objects, zero new refusals, zero execution errors; first before/after mismatch: none. All ten witnesses match their saved results. Existing Classic mismatches for ColorKey, DirectionalBlur and DistanceGradation remain mismatches; successful replay is not a new claim that these routes are exact. Detailed commands, selected paths, route hashes and results are in the evidence JSON.
- Initial replay setup attempts lacked the recorded max-size on some nested corpora; those returned setup_error and were corrected by passing the saved max-size/geometry/size/color flags. These setup attempts are not counted as successful comparisons.
- Initial ColorKeep compilation failed because SDK links were absent. `scripts/setup_ae_sdk_links.sh` created worktree links to the installed SDK, after which both before/after runs reproduce the existing failure: `co=101 cc=100 ci=101 li=1`, all three depths, `test_generic_admission_is_not_fixture_bound` calling `test_exported_effectmain_nonzero_origin_classic_and_smart`. Q07 reports the same failure. The runner executes function tests after its zero-test unittest discovery; the displayed `Ran 0 tests` is not a pass claim for the function suite.
- Pytest invocation with MAIN's emulation venv returned `No module named pytest`; system Python also lacks pytest. The entire repository pytest suite was not run. No dependency installation or test weakening was performed.
- The complete release-v2 orchestration was not run and is not claimed PASS: its selected ColorKeep test already fails at base/head. Its CLI additionally fixes scratch to the R09 ticket and OLM_TEST_JOBS=2; those release-gate files were left unchanged. Other local stages (full corpus inventory, fresh-seeds and bundle-differential checks) remain for the orchestrator.
- Packaging command: `bash scripts/package_mac_plugins.sh --configuration Release --output "$S/olm-mac.zip"`. A scratch PATH shim adds `-jobs 1` to xcodebuild; each Mac/build path was temporarily linked into this ticket's package-builds directory. All ten builds succeeded with arm64+x86_64 and signing checks. The first packaging attempt then lacked worktree-only reference manifests. With `OLM_REFERENCE_ROOT="$MAIN"`, rerunning with `--skip-build` reused those already verified products and packaged ten plugins successfully. The archive SHA-256 is in the evidence JSON. Host-validation entries remain incomplete as expected; this is not AE-host authorization.
- Nightly command: `PYTHON="$PY" bash tools/fuzz/nightly.sh --hours 0.05 --jobs 1`. Sessions: [{"actual_jobs": 1, "elapsed_seconds": 180.003, "hours": 0.05, "jobs_limit": 1, "retained_bytes": 8142, "start": "20261026T145420352629", "status": "deadline"}]; campaign summary: [{"plugin": "olmcolorkey", "sampler": "default", "seed": 105539603739615074, "status": "budget_exhausted", "counts": {"E": 6030}, "elapsed_seconds": 179.997, "error": null}].

inference:
- Literal-reference closure, unchanged retained source, equal before/after corpus results and successful builds support the deletion's safety within measured coverage. They do not prove that untracked external callers or arbitrary dynamically assembled filenames cannot reference a removed tool.
- The known ColorKeep failure prevents satisfying the ticket's all-pass gate without out-of-scope changes. Stop here and let the orchestrator resolve/assign that failure; do not weaken the gate or alter plugin code in this cleanup ticket.

changed_files:
- notes/REMOVED_TOOLS.md (restoration index).
- orchestra/reports/Q08-cleanup-one-off-tools.md (this report).
- orchestra/reports/Q08-cleanup-one-off-tools-evidence.json (keep map, replay commands/results, test logs, nightly summary, archive identity).
- The deleted paths and their last-containing branch commits are listed below, one per line; these duplicate the restoration index.

```text
scripts/ae_debug_colorkey_case.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ae_dump_colorkey_props.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ae_probe_distancegradation_case0027_variants.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ae_probe_distancegradation_extended_focus_original.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ae_probe_distancegradation_field_cases.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ae_render_32bpc_template_probe.jsx b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_16bpc_mac_ae_residuals.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_colorkey_16bpc_case_0009.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_directionalblur_algorithm_presets.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_directionalblur_scatter_ownership.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_0010_0011_field_pack_read.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_0010_0011_normalization_denominator.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_0010_0011_opencv_field_prep.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_16bpc_constant_variants.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_16bpc_focus_cases.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_bg_compose_variants_return.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_case0023_plateau_transition.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_case0027_probe_x.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_constant_both_outside_zero_variants.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_constant_case_correlations.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_constant_threshold_bias.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_constant_two_stage_variants.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_debug_points.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_field_cases_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_distancegradation_layer_source_true16.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_kirakira_compose_debug_neighborhood.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_kirakira_compose_model_audit.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_kirakira_hotspot_local_compose_diagnostic.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmblur_16bpc_proof_plan.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmblur_32bpc_float_focus_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmdirectionalblur_witness_logging_prep.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmkirakira_aggregation_quantization_invariant_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmkirakira_live_hotspot_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmkirakira_reference_provenance.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmkirakira_witness_path_split.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmradialblur_tiny_rotation_row_coupling_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmradialblur_tiny_rotation_source_polar_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmradialblur_tiny_rotation_support_envelope.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_olmradialblur_zoom_final_plane_index_variants.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_radialblur_inner_candidate_matrix.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_radialblur_outer_propagated_validity_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_radialblur_outer_validity_rejection.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_radialblur_tiny_rotation_same_row_audit.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/analyze_smoother2_current_aex_diff_clusters.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/attest_olmsmoother_v1_mac_process_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_colorkey_16bpc_current_aex_followup.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_colorkey_bitdepth_evidence_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olm_crosshost_corrected_returns_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olm_crosshost_linear_input_returns_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmblur_current_binary_exact_subset_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmblur_mac_host_phase_ready_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmcolorkey_current_binary_exact_identity_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmcolorkey_mac_ae_host_phase_package_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmcolorkey_mac_ae_host_phase_result_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmdirectionalblur_32bpc_float_evidence_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmdistancegradation_16bpc_layer_residual_20260717.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmradialblur_rotation_producer_contract_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_olmsmoother_v1_32bpc_host_conversion_boundary_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/audit_request_param_pinning.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/classify_olmdistancegradation_exact_fixed_failure_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/extract_mac_plugin_param_schema.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/generate_all_32bpc_exr_reference_bundle.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/generate_olm_crosshost_linear_fixture_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/ghidra_export_all_2025.sh b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/guard_olmkirakira_saved_project_abi_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_dual_side64_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_expffloat_arm15_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_exported_smart5_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_exported_smart9_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_internal_owner_failclose_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_testseam_compat_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_type3_layer_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/install_olmdirectionalblur_worldsuite_lifecycle_20260814.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/materialize_directionalblur_lane_state.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/materialize_distancegradation_0010_0011_aex_fieldgen_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/materialize_distancegradation_case0023_lane_state.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/materialize_radialblur_tiny_rotation_lane_state.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olm_crosshost_linear_input_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmblur_32bpc_case0001_hash_bound_recapture_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmblur_32bpc_case0001_repeat1_provenance_request_20260718.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmblur_8bpc_windows_canonical_recapture_20260711.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmblur_windows_canonical_recapture_20260711.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmcolorkey_saved_project_abi_validation_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdirectionalblur_8bpc_mac_validation_20260718.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_0010_compose_single_site_followup_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_16bpc_livefield_source_witness_20260713.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_8bpc_coordinate_liveness_census_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_8bpc_current_aex_typed_boundary_20260712.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_8bpc_current_aex_typed_witness_20260716.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_8bpc_depth_control_20260713.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmdistancegradation_8bpc_hook_liveness_20260713.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmradialblur_zoom_case0009_final_plane_typed.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmradialblur_zoom_case0009_final_plane_typed_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmradialblur_zoom_case0009_hook_liveness_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmradialblur_zoom_case0009_sample_target_gate_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmradialblur_zoom_case0009_sampler_args_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmsmoother2_case0012_live_config_binding_20260713.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_olmsmoother2_no_key_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_32bpc_second_generation_parity_20260713.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_ae26_3_32bpc_recap_20260710.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_all_plugins_reference_campaign_20260731.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_olmdirectionalblur_target_writer_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_olmdistancegradation_pf16_boundary_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_olmdistancegradation_pf16_boundary_r2_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_olmdistancegradation_pf16_boundary_r3_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_olmradialblur_case0010_20260728.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_codex_owner_retry_v2_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_witness_olmsmoother2_case0004_writer_frame_20260718.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_witness_olmsmoother2_inprocess_collector_20260716.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/package_windows_witness_olmsmoother2_legacy_key_producer_20260716.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/preflight_olmradialblur_mac_ae_supported_targets_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/preflight_olmsmoother2_current_ae_host_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/prepare_kirakira_hotspot_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/prepare_olmcolorkey_32bpc_windows_aepx_20260727.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/prepare_radialblur_single_case_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/refresh_curated_runtime_trace_comparisons.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olm_public_beta_rc_native_ae_20260822.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olmdirectionalblur_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olmkirakira_mode2_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olmradialblur_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olmsmoother2_16bpc_case01_10_ae_exact_20260727.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/report_olmsmoother_v1_32bpc_mac_validation_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_ae_32bpc_template_probe.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_colorkeep_pf16_extended_mac_validation_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_colorkeep_pf16_upstream_chain_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_headless.sh b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olm_all10_batch5_current_identity_direct_r_v5_20260816.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olm_all10_batch5_current_identity_direct_r_v6_20260816.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olm_crosshost_linear_input_mac_ae_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olm_windows_ae_release_boundary_20260806.ps1 b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmblur_16bpc_candidates_mac_validation_20260716.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmcolorkey_32bpc_windows_aerender_20260727.ps1 b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmcolorkey_case0001_pf16_current_binary_mac_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmdirectionalblur_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmkirakira_crosshost_normalized_mac_ae_20260806.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmkirakira_mode2_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmradialblur_32bpc_mac_validation_20260715.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmsmoother_v1_32bpc_after_pf16_fix_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmsmoother_v1_32bpc_mac_validation_20260730.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_olmsmoother_v1_pf8_current_mac_ae_20260805.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/run_overnight.sh b9c61119754387f399f4c9c19daf0ed2ae4370fd
scripts/verify_olm_windows_all_plugins_reference_return_20260731.py b9c61119754387f399f4c9c19daf0ed2ae4370fd
tools/fuzz/build_F31.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/build_F44.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/recheck_blur_C21.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/recheck_blur_C24.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/recheck_blur_C32.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/retry_V01_budgets.py bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/run_C23_fresh.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/s02_float_campaign.py bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/summarize_V01.py bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_C23_stages.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_colorkey_C20.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_colorkey_C42.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_colorkey_F20.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_colorkey_downsample_P01c.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
tools/fuzz/verify_colors_T12.sh bcd70b36ff0ca45866322d4c24479fdb4255d162
```

verify:
Run from this worktree with the read-only MAIN venv; set scratch variables first:

```sh
S="$PWD/orchestra/state/Q08-cleanup-one-off-tools"
MAIN='/Users/onmk/Documents/Projects/Personal/OLM as'
PY="$MAIN/tools/emulation/.venv/bin/python3"
mkdir -p "$S/tests"
export TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export OLM_FUZZ_TEST_SCRATCH="$S/tests"
# The legacy F53/N01/F20 tests and nightly hardcode these scratch names.
for d in F53-oracle-cropped-checkout N01-nightly-fuzz-runner F20-colorkey-zero-color-and-byte-safe nightly; do
  mkdir -p "$S/$d"
  test -e "orchestra/state/$d" || ln -s "$S/$d" "orchestra/state/$d"
done
"$PY" -B -m unittest discover -s tools/fuzz -p 'test_*.py' -v
"$PY" -B tests/test_release_gate_v2.py
"$PY" -B scripts/run_olm_generic_beta_gate.py --run-test-file "$PWD/tests/test_colorkeep_generic_beta_20260820.py"
PYTHON="$PY" bash tools/fuzz/nightly.sh --hours 0.05 --jobs 1
git diff --check b9c61119
```

Expected: framework 50 tests / 3 skipped, gate self-tests 5/5; ColorKeep exits 1 with the callback counts above. Nightly must exit 0 at its budget deadline; random-seed case counts vary. The full release-v2 gate remains unverified/failing, not accepted.

The evidence JSON stores the exact ten replay commands. Execute each `head_replays[].command` with its old worktree prefix replaced by the current `$PWD`, and compare its report's `replays` field with the stored one; expected ten exit-0 replays and zero changed results. All report/corpus/scratch paths are under this ticket. For package recheck, use the command above with OLM_REFERENCE_ROOT="$MAIN", the scratch xcodebuild -jobs 1 shim and scratch build links; omit --skip-build for a fresh build. Expected ten verified bundles and a verified ten-plugin archive. Package bytes can vary with build metadata. Exact fresh packaging setup (the script creates no oracle):

```sh
export OLM_REFERENCE_ROOT="$MAIN"
mkdir -p "$S/bin"
printf '%s\n' '#!/bin/sh' 'exec /usr/bin/xcodebuild -jobs 1 "$@"' > "$S/bin/xcodebuild"
chmod +x "$S/bin/xcodebuild"
export PATH="$S/bin:$MAIN/tools/emulation/.venv/bin:$PATH"
for plugin in ColorKeep OLMBlur OLMColorKey OLMDirectionalBlur OLMRadialBlur OLMKiraKira OLMToonDilate OLMDistanceGradation OLMSmoother OLMSmoother2; do
  mkdir -p "$S/package-builds/$plugin"
  test -e "mac/$plugin/Mac/build" || ln -s "$S/package-builds/$plugin" "mac/$plugin/Mac/build"
done
bash scripts/package_mac_plugins.sh --configuration Release --output "$S/olm-mac.zip"
```


Reachability reproduction: run the following Python command on a checkout of the recorded base (not on MAIN). It writes only a scratch inventory and does not delete files. The kept map and selected deletions should match the committed evidence. No reusable verification tool was added.

```sh
python3 - <<'PY_REACH'
import collections,json,pathlib,re,subprocess
root=pathlib.Path.cwd(); state=root/'orchestra/state/Q08-cleanup-one-off-tools'
files=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')[:-1]
# Only executable/source tools are deletion candidates; retain data and fixtures.
exts={'.py','.sh','.cpp','.c','.h','.hpp','.jsx','.js','.ps1','.bat','.cmd'}
candidates={p for p in files if p.startswith(('tools/','scripts/')) and pathlib.Path(p).suffix in exts and not p.startswith(('tools/emulation/','tools/ae_smoke/','tools/refactor/','tools/fuzz/fixtures/','tools/fuzz/declarations/','tools/fuzz/adapters/','tools/fuzz/harnesses/','tools/ae_pf16_fixture_source/')) and not pathlib.Path(p).name.startswith('test_')}
# Index full paths, basenames and Python module names; ambiguous matches keep all targets.
index=collections.defaultdict(set)
for p in files:
    path=pathlib.Path(p)
    index[p].add(p); index[path.name].add(p)
    if path.suffix=='.py':
        index[path.stem].add(p); index[p[:-3].replace('/','.')].add(p)
roots={p for p in files if p.startswith(('tests/','docs/','mac/','tools/emulation/','tools/ae_smoke/','tools/refactor/','tools/fuzz/adapters/','tools/fuzz/harnesses/','tools/fuzz/declarations/')) or pathlib.Path(p).name.lower().startswith('readme') or pathlib.Path(p).name.startswith('test_')}
roots.update(p for p in files if p in {'AGENT_GUIDE.md','orchestra/BRIEF.md','orchestra/REFACTOR_SPEC.md','tools/fuzz/run.py','tools/fuzz/core.py','tools/fuzz/geometry.py','tools/fuzz/sizes.py','tools/fuzz/nightly.sh','tools/fuzz/rebaseline_corpus.py','tools/perf/ref_vs_fast.py','scripts/package_mac_plugins.sh','scripts/run_olm_release_gate_v2.py'} or 'release_gate' in p and p.startswith('scripts/'))
roots.update(p for p in files if p.startswith(('tools/', 'scripts/')) and p not in candidates)
roots.add('scripts/build_ae_pf16_fixture_source_20260806.py')
seen=set(roots); queue=collections.deque(sorted(roots)); reason={p:'root' for p in roots}
while queue:
    p=queue.popleft(); path=root/p
    if not path.is_file() or path.stat().st_size>8*1024*1024: continue
    try: content=path.read_text()
    except (UnicodeError,OSError): continue
    tokens=set(re.findall(r'[A-Za-z0-9_./-]+',content))
    tokens|={t.rsplit('/',1)[-1] for t in tokens}
    tokens|=set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*',content))
    for t in tokens:
        for q in index.get(t,()):
            if q not in seen: seen.add(q); reason[q]=p; queue.append(q)
deleted=sorted(candidates-seen)
result=dict(base=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),candidate_count=len(candidates),reachable_count=len(seen),deleted=deleted,kept={p:reason[p] for p in sorted(seen) if p.startswith(('tools/','scripts/'))})
(state/'reachability.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(candidates=len(candidates),deleted=len(deleted),directories=dict(collections.Counter(str(pathlib.Path(p).parent) for p in deleted)),deleted_lines=sum(len((root/p).read_bytes().splitlines()) for p in deleted)),indent=2))
print('\n'.join(deleted[:35]))
PY_REACH
```

next:
- Orchestrator: review the conservative keep map and directory commits; resolve the pre-existing ColorKeep ROI gate failure in its own ticket, provision pytest if required, then run the complete release-v2/pytest suites. No gate-pass exception is inferred here.
- Scratch build trees, package archive and temporary Mac/build links are removed after recording results; logs and summaries remain in this ticket's scratch. No durable oracle bundle was produced.
