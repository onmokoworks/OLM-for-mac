# R07 F40 per-item adjudication

Before is F40; current is a fresh R07 child exit unless explicitly reserved/host-only. Full diagnostics and missing-path checks are in the evidence archive. No blocked result is a pass.

| Fixture | Before | R07 before → after refresh | Disposition / first diagnostic |
|---|---:|---|---|
| fixture-004 | 1 | 0 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-006 | 1 | 1 → 1 | blocked: Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure. |
| fixture-007 | 1 | 1 → 1 | blocked: ERROR: test_live (__main__.ClassicRealSDK.test_live) |
| fixture-008 | 1 | 1 → 1 | blocked: RuntimeError: identity drift |
| fixture-009 | 1 | 1 → 1 | blocked: FAIL: test_exact_live_identities (__main__.ClosureTest.test_exact_live_identities) |
| fixture-010 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/R07-gate-contracts-and-bindings/handoffs/olmblur_retained_public_universal_candidate_v4_20260813/build_identity.json' |
| fixture-011 | 1 | 1 → 1 | blocked: FAIL: test_canonical_artifact_hashes (tests.test_olmblur_current_installed_public_closure_20260813.OLMBlurCurrentInstalledPublicClosureTest.test_canonical_artifact_hashes) |
| fixture-012 | 1 | 1 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-013 | 1 | 1 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-014 | 1 | 1 → 1 | blocked: RuntimeError: identity drift |
| fixture-015 | 1 | 1 → 1 | blocked: ERROR: test_live (__main__.Closure.test_live) |
| fixture-016 | 1 | 0 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-017 | 1 | 0 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-018 | 1 | 1 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-019 | 1 | 1 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-020 | 1 | 1 → 0 | passed: PASS_THREE_LEGACY_RETAINED_EXACT_ONE_PUBLIC_MISMATCH_FAIL_CLOSED |
| fixture-021 | 1 | 1 → 0 | passed: Current strict consumer passes; unchanged numerical assertions. |
| fixture-022 | 1 | 1 → 1 | blocked: RuntimeError: identity drift |
| fixture-023 | 1 | 1 → 1 | blocked: ERROR: test_live (__main__.OLMBlurPF16WorkerSourcesAdmission.test_live) |
| fixture-024 | 1 | 1 → 1 | blocked: RuntimeError: identity drift |
| fixture-025 | 1 | 1 → 1 | blocked: FAIL: test_generator_identity (__main__.TestPF8Owner.test_generator_identity) |
| fixture-026 | 1 | 1 → 1 | blocked: RuntimeError: identity drift {'source': 'b91706aff22b1aae3c2f4c7bfec719a73c27647b4f65f5739deb0f2f502fc08b', 'probe': 'ee0e21390b69d7a766717275b3b6ecd03cce49caae89fccf84f0d7d8b5674b46', 'worker': 'c36db12f84bfd78ba425f4196dcddaedc5c87bc207ac |
| fixture-027 | 1 | 1 → 1 | blocked: FAIL: test_generator_identity (__main__.TestPF8Admission.test_generator_identity) |
| fixture-028 | 1 | 1 → 1 | blocked: RuntimeError: identity drift {'source': 'b91706aff22b1aae3c2f4c7bfec719a73c27647b4f65f5739deb0f2f502fc08b', 'probe': '0d4c9e29c50e7656ba46186dd78ac54af6e086c6f2bc9daaa5940028d8a9f690', 'public_runner': '2b07c6ea1cde0640f954caaab28d5d9294e0b |
| fixture-029 | 1 | 1 → 1 | blocked: FAIL: test_current_docs_and_candidate (__main__.Closure.test_current_docs_and_candidate) |
| fixture-030 | 127 | 2 → 2 | blocked: Missing dependency; existence checked separately at MAIN. A path fix cannot reconstruct absent historical bytes or establish an equally strict replacement. |
| fixture-031 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/R07-gate-contracts-and-bindings/handoffs/olmblur_retained_public_universal_candidate_v4_20260813/verify_candidate.py' |
| fixture-032 | 1 | 1 → 1 | blocked: ERROR: test_actual_exported_and_installed_owner_matrix_is_bound (tests.test_colorkeep_public_guard_closure_20260812.ColorKeepPublicGuardClosureTests.test_actual_exported_and_installed_owner_matrix_is_bound) |
| fixture-033 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: PosixPath('/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue1135-typed-iterate-suites') |
| fixture-034 | 1 | 1 → 1 | blocked: ERROR: test_candidate_arch (tests.test_colorkeep_nine_color_public_closure_20260813.ColorKeepNineClosure.test_candidate_arch) |
| fixture-035 | 1 | 1 → 1 | blocked: RuntimeError: ColorKeep current identity drift: {'source_sha256': '5a8502ad3cd11a78f16cd800736fb53ac43c6c4abf2eacdebb192f3a1924e284', 'installed_binary_sha256': 'ae9643a5a02f111ac48d284d646418cb1f6c4e9b3eaf213a34c17c5698dd1a10', 'accepted_i |
| fixture-036 | 1 | 1 → 1 | blocked: FAIL: test_default_is_read_only (tests.test_colorkeep_current_installed_complete_union_20260814.ColorKeepCurrentInstalledCompleteUnionTest.test_default_is_read_only) |
| fixture-040 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: ColorKeep executable drifted: ae9643a5a02f111ac48d284d646418cb1f6c4e9b3eaf213a34c17c5698dd1a10 != dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d |
| fixture-042 | 1 | 1 → 1 | blocked: RuntimeError: pinned typed-iterate worker missing or drifted |
| fixture-043 | 1 | 1 → 1 | blocked: FAIL_OLMCOLORKEY_PUBLIC_SOURCE_BOUND_CLOSURE |
| fixture-044 | 1 | 1 → 1 | blocked: ERROR: test_canonical_report_and_live_inputs (tests.test_olmcolorkey_public_source_bound_closure_20260813.ColorKeyPublicSourceBoundClosure.test_canonical_report_and_live_inputs) |
| fixture-045 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/R07-gate-contracts-and-bindings/handoffs/olmcolorkey_toggle24_universal_candidate_20260814/build_identity.json' |
| fixture-046 | 1 | 1 → 1 | blocked: FAIL: test_canonical_artifact_hashes (tests.test_olmcolorkey_current_installed_public_closure_20260813.OLMColorKeyCurrentInstalledPublicClosureTest.test_canonical_artifact_hashes) |
| fixture-047 | 1 | — → — | group1 contract finding: See group1 table; no acceptance inferred |
| fixture-048 | 1 | 1 → 1 | blocked: ERROR: test_authoritative_chain (tests.test_olmcolorkey_public_source_bound_docs_20260813.ColorKeyPublicSourceBoundDocs.test_authoritative_chain) |
| fixture-049 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker' |
| fixture-050 | 1 | 1 → 1 | blocked: ERROR: test_checked_in_report_validates (tests.test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.DirectionalBlurNatural64ClosureTest.test_checked_in_report_validates) |
| fixture-051 | 1 | 1 → 1 | blocked: RuntimeError: stored Type-3 owner-boundary report is invalid |
| fixture-052 | 1 | 1 → 1 | blocked: FAIL: test_saved_report_validates (tests.test_olmdirectionalblur_type3_public_owner_boundary_20260814.DirectionalType3PublicOwnerBoundaryTest.test_saved_report_validates) |
| fixture-053 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/R07-gate-contracts-and-bindings/handoffs/olmdirectionalblur_exported_smart_worker_ceil_20260814/bin/aex-guest-worker' |
| fixture-054 | 1 | 1 → 1 | blocked: ERROR: test_arm64_and_x86_fifteen_boundary (tests.test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.DirectionalDualSideExportedSmartClosureTest.test_arm64_and_x86_fifteen_boundary) |
| fixture-059 | 1 | 1 → 1 | blocked: RuntimeError: same-table dual-owner plumbing evidence invalid |
| fixture-060 | 1 | 1 → 1 | blocked: FAIL: test_external_file_pins (tests.test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.SameTableDualOwnerPlumbingTest.test_external_file_pins) |
| fixture-061 | 1 | 1 → 1 | blocked: RuntimeError: stored dual-side source guard report is invalid |
| fixture-062 | 1 | 1 → 1 | blocked: FAIL: test_checked_in_report_validates (tests.test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.DirectionalDualSidePublicSourceGuardClosureTest.test_checked_in_report_validates) |
| fixture-064 | 1 | 1 → 1 | blocked: FAIL: test_current_workspace_supersedes_historical_snapshot (tests.test_olmdirectionalblur_type2_natural64_current_install_smoke_20260812.DirectionalBlurNatural64CurrentInstallSmokeTest.test_current_workspace_supersedes_historical_snapshot) |
| fixture-065 | 1 | 1 → 1 | blocked: RuntimeError: Directional current authority drift: {'source_sha256': '6f3207c4b4fd5ec8b4630c9b2755bc9f692ba6256f47041c10ba9e2e1cb7457b', 'installed_binary_sha256': 'bced525426da29a67c45d5cb3071de06cc417d9732a15108dfa1188cb03a7bcc', 'accepte |
| fixture-066 | 1 | 1 → 1 | blocked: FAIL: test_default_is_read_only (tests.test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.DirectionalInstalledCompleteBoundedUnionTest.test_default_is_read_only) |
| fixture-083 | 1 | — → — | group1 contract finding: See group1 table; no acceptance inferred |
| fixture-091 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: OLMDirectionalBlur executable drifted: bced525426da29a67c45d5cb3071de06cc417d9732a15108dfa1188cb03a7bcc != c64f8ff701008ae0390eb9da1a9e073dcde97a77e9b32701becf6eaa241a2666 |
| fixture-092 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: OLMDistanceGradation executable drifted: ce48b9ebf92bb1b66db9e3da1c0c17f4b176553a4f5097fed0b5f5630d6cb1e5 != 9a97a076c118fd1015f40d922bf7f21be7a041f1f049a0e465cc0bc9cd1cd349 |
| fixture-095 | 1 | 1 → 1 | blocked: AssertionError: {'smart_pf16_dispatch': True, 'smart_pf8_dispatch': True, 'smart_depth_bit': True, 'smart_sequence_entry': True, 'sequence_calls_pre_render_owner': True, 'production_pf16_full_owner_connected': False, 'production_pf8_full_ow |
| fixture-097 | 1 | 1 → 1 | blocked:     require(p.get("schema")=="olmdistancegradation.pf32-mode5-ipp-exact-closure/1"and p.get("status")=="PASS_FIXED17X11_PF32_MODE5_IPP_FIELD_EXACT_6_ADMITTED_2_POWER_FAIL_CLOSED","schema/status");worker=Path(os.environ.get("OLM_AEX_GUEST_WO |
| fixture-098 | 1 | 1 → 1 | blocked: ERROR: test_admission (tests.test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.Closure.test_admission) |
| fixture-099 | 1 | 1 → 1 | blocked: RuntimeError: authority drift: {'probe': 'ef0e7ccbb75d4d9d10c405306c2ee797d0f11e6d2cf3a5cad59e7d45533665f3', 'source': 'e1d5c652e1a716448bf9f79dc1452b6899d58d6114c12bfa509e5ac75a92fa8a', 'strings': '7c8e13d4490e67f9cb918199891d96831b50929d4 |
| fixture-100 | 1 | 1 → 1 | blocked: FAIL: test_hashes (tests.test_olmdistancegradation_current_installed_mode5_20260813.DistanceInstalledMode5Test.test_hashes) |
| fixture-101 | 1 | 1 → 1 | blocked: FileNotFoundError: [Errno 2] No such file or directory: '/Users/onmk/Documents/Projects/Personal/04_Tools/AEXCompat-issue851-smart-primary-checkout/guest/target/release/aex-guest-worker' |
| fixture-102 | 1 | 1 → 1 | blocked: ERROR: test_alpha_bits_tamper (tests.test_olmdistancegradation_public_smart_owner_contract_20260812.DistanceGradationPublicSmartOwnerContract.test_alpha_bits_tamper) |
| fixture-103 | 1 | 1 → 1 | blocked:     assert p["schema"]=="olmdistancegradation.pf32-mode5-universal-codegen/1"and p["status"]=="PASS_UNIVERSAL_MODE5_CODEGEN_6_EXACT_2_POWER_FAIL_CLOSED";assert p["binary_sha256"]==sha(BINARY)and p["project_sha256"]==PROJECT_SHA==sha(PROJECT |
| fixture-104 | 1 | 1 → 1 | blocked: ERROR: test_binary_identity_tamper (tests.test_olmdistancegradation_pf32_mode5_universal_codegen_20260812.DistanceGradationMode5UniversalCodegen.test_binary_identity_tamper) |
| fixture-105 | 1 | 1 → 1 | blocked: FAIL_OLM_MATH_UCRT_BATCH_REQUEST: persisted batch request drift |
| fixture-106 | 1 | 1 → 1 | blocked: ERROR: test_exact_ae_free_batch_contract (tests.test_olm_math_ucrt_batch_request_20260814.OLMUcrtMathBatchRequestTest.test_exact_ae_free_batch_contract) |
| fixture-107 | 1 | 1 → 1 | blocked: RuntimeError: Distance same-table dual-owner plumbing evidence invalid |
| fixture-108 | 1 | 1 → 1 | blocked: FAIL: test_live_report_and_markdown (tests.test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.DistanceSameTableDualOwnerPlumbingTest.test_live_report_and_markdown) |
| fixture-109 | 1 | 1 → 1 | blocked: RuntimeError: native dual-owner consumer readiness invalid |
| fixture-110 | 1 | 1 → 1 | blocked: FAIL: test_external_pins (tests.test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.NativeDualOwnerConsumerReadinessTest.test_external_pins) |
| fixture-111 | 1 | 1 → 1 | blocked: RuntimeError: production source drift: {'core/dblur_gaussian.h': '232f032ba9a3085de0e000742c6696f99446ac21301741c18a012ecf8a377092', 'mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp': '6f3207c4b4fd5ec8b4630c9b2755bc9f692ba6256f47041c10ba9e2e1 |
| fixture-112 | 1 | 1 → 1 | blocked: ERROR: test_current_sources_remain_exactly_fail_closed (tests.test_olm_native_ucrt_promotion_table_readiness_20260814.OLMNativeUcrtPromotionTableReadinessTest.test_current_sources_remain_exactly_fail_closed) |
| fixture-114 | 1 | 1 → 1 | blocked: Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure. |
| fixture-115 | 1 | 1 → 1 | blocked: ERROR: setUpClass (tests.test_olmkirakira_public_smart_bounded_closure_20260812.KiraPublicSmartBoundedClosureTests) |
| fixture-116 | 1 | 1 → 1 | blocked: Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure. |
| fixture-117 | 1 | 1 → 1 | blocked: ERROR: setUpClass (tests.test_olmkirakira_classic_smart_admission_guard_20260812.KiraClassicSmartAdmissionGuardTests) |
| fixture-118 | 1 | 1 → 1 | blocked: FAIL: test_all_dependency_hashes_match_live_workspace (tests.test_olmkirakira_smart_workspace_dependency_manifest_20260812.KiraSmartWorkspaceDependencyManifestTests.test_all_dependency_hashes_match_live_workspace) |
| fixture-119 | 1 | 1 → 1 | blocked: FAIL_OLMKIRAKIRA_CURRENT_INSTALLED_PUBLIC_CLOSURE: authority drift: {'production_source': 'ac0f133785090baf85bca2b2df78979e2a268b7c43f676857822d77ea20be40d', 'installed_binary': '69e87ce32570ebf299d8a3e94b707321b607ac51de42324e6a0444f490714 |
| fixture-120 | 1 | 1 → 1 | blocked: FAIL: test_canonical_artifact_hashes (tests.test_olmkirakira_current_installed_public_closure_20260813.KiraCurrentInstalledPublicClosureTest.test_canonical_artifact_hashes) |
| fixture-126 | 1 | — → — | group1 contract finding: See group1 table; no acceptance inferred |
| fixture-127 | 1 | 1 → 1 | blocked: RuntimeError: Traceback (most recent call last): |
| fixture-128 | 1 | 1 → 1 | blocked: Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure. |
| fixture-134 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: OLMKiraKira executable drifted: 69e87ce32570ebf299d8a3e94b707321b607ac51de42324e6a0444f490714c4d != d4c9b587d41797259de8627e2d3d5bcf7a376f12fa3c8b99dcd820e0b6d80ae3 |
| fixture-135 | 1 | 1 → 1 | blocked: AssertionError: ('', 'Traceback (most recent call last):\n  File "/Users/onmk/Documents/Projects/Personal/OLM as/worktrees/R07-gate-contracts-and-bindings/scripts/run_olmkirakira_mode4_case01_mac_ae_20260805.py", line 21, in <module>\n    f |
| fixture-137 | 1 | 1 → 1 | blocked: AssertionError: {'distinct_outer_mode2_dispatch': True, 'public_inner_is_fd90': True, 'five_layer_order': True, 'gain_before_skip_and_ramp': True, 'scaled_ray_alpha': True, 'fd90_pf32_single_reciprocal': True, 'outer_mode2_helper': True, 'u |
| fixture-162 | 1 | — → — | reserved for R08: See group1 table; no acceptance inferred |
| fixture-163 | 1 | — → — | reserved for R08: See group1 table; no acceptance inferred |
| fixture-164 | 1 | — → — | reserved for R08: See group1 table; no acceptance inferred |
| fixture-183 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: OLMRadialBlur executable drifted: 0ed4a2f573c1e48471309b3a35209bbefda90d977aee8ddca3b216a94f7014c9 != 9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5 |
| fixture-184 | 1 | — → — | group1 contract finding: See group1 table; no acceptance inferred |
| fixture-185 | 1 | 1 → 1 | blocked: RuntimeError: production source identity drift (Type1/Type3 integrated source expected) |
| fixture-186 | 1 | 1 → 1 | blocked: ERROR: test_checked_in_report_validates (tests.test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.ClosureTamper.test_checked_in_report_validates) |
| fixture-187 | 1 | 1 → 1 | blocked: RuntimeError: live identity drift: {'production_source_sha256': '8ea892bcae5882b8d212c1d1494b68dbf8fe39dce212f133ad2491c200ea200e', 'aex_sha256': 'ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb', 'aexcompat_float_math_patc |
| fixture-188 | 1 | 1 → 1 | blocked: FAIL: test_default_and_validate_only_are_read_only (tests.test_olmradialblur_strength290_exported_math_boundary_20260814.Strength290BoundaryTest.test_default_and_validate_only_are_read_only) |
| fixture-189 | 1 | 1 → 1 | blocked: ValueError: provenance drift: production_source_sha256 |
| fixture-190 | 1 | 1 → 1 | blocked: ERROR: test_csharp_symbol_tamper_rejected (tests.test_olmradialblur_strength290_ucrt_math_request_20260814.Strength290UcrtRequestTest.test_csharp_symbol_tamper_rejected) |
| fixture-191 | 1 | 1 → 1 | blocked: RuntimeError: Radial Strength290 native-UCRT boundary evidence invalid |
| fixture-192 | 1 | 1 → 1 | blocked: FAIL: test_frozen_evidence_is_live_valid (tests.test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.RadialNativeUcrtBoundaryTest.test_frozen_evidence_is_live_valid) |
| fixture-193 | 1 | 1 → 1 | blocked: Current consumer rejects its retained binding/contract. No complete twice-original plus current-build replacement for this entire consumer was obtained; retain failure. |
| fixture-194 | 1 | 1 → 1 | blocked: FAIL: test_canonical_report (tests.test_olmradialblur_type3_layer_span_natural_closure_20260812.Type3NaturalClosureTests.test_canonical_report) |
| fixture-195 | 1 | 1 → 1 | blocked: AssertionError: production source identity drift |
| fixture-196 | 1 | 1 → 1 | blocked: AssertionError: production source identity drift |
| fixture-197 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: installed Radial binary drift: 0ed4a2f573c1e48471309b3a35209bbefda90d977aee8ddca3b216a94f7014c9 |
| fixture-198 | 1 | 1 → 1 | requires real AE/Windows: FAIL: test_canonical_artifact_hashes (tests.test_olmradialblur_current_installed_type3_all_depth_closure_20260813.RadialCurrentInstalledType3AllDepthTest.test_canonical_artifact_hashes) |
| fixture-199 | 1 | 1 → 1 | blocked: ERROR: test_external_identities_and_live_validation (tests.test_olmradialblur_smart_cleanup_candidate_20260813.RadialSmartCleanupCandidate.test_external_identities_and_live_validation) |
| fixture-200 | 1 | 1 → 1 | requires real AE/Windows: RuntimeError: FAIL CLOSED: installed identity manifest: OLMRadialBlur executable drifted: 0ed4a2f573c1e48471309b3a35209bbefda90d977aee8ddca3b216a94f7014c9 != 9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5 |
| fixture-201 | 126 | — → — | requires real AE/Windows: Installed identity preflight requires current installation receipts and host evidence; R05 remains historical, not a new R07 host run. |
| fixture-202 | 126 | — → — | requires real AE/Windows: Installed identity preflight requires current installation receipts and host evidence; R05 remains historical, not a new R07 host run. |
| fixture-203 | 126 | — → — | requires real AE/Windows: Installed identity preflight requires current installation receipts and host evidence; R05 remains historical, not a new R07 host run. |
