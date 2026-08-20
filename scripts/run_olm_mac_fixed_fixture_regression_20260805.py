#!/usr/bin/env python3
"""Run the bounded Mac-only OLM conformance lanes.

The default suite consumes retained Windows-AEX fixtures and runs local
production/focused adapters.  It does not contact or require a Windows host.
The expensive RadialBlur full Unicorn replay is opt-in.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from olm_installed_identity import verified_binary

LANE_INSTALLED_PLUGIN = {
    "smoother": "OLMSmoother",
    "smoother2": "OLMSmoother2",
    "toondilate": "OLMToonDilate",
}


@dataclass(frozen=True)
class Lane:
    name: str
    commands: tuple[tuple[str, ...], ...]


LANES = (
    Lane(
        "blur",
        (
            (sys.executable, "refs/scripts/smoke_olmblur_worker_orchestration.py"),
            (sys.executable, "refs/scripts/smoke_olmblur_worker32_nonlegacy.py"),
            (sys.executable, "refs/scripts/smoke_olmblur_worker32_legacy.py"),
            (sys.executable, "tools/emulation/smoke_olmblur_worker16_legacy.py"),
            (sys.executable, "refs/scripts/audit_olmblur_pf32_formal_worker_matrix_20260805.py"),
            # Public Smart is deliberately bounded to the retained
            # exported-owner 24x24 exact-source matrix (three depths crossed
            # with Legacy 0/1) plus the independently exported-owner-grounded
            # Eight PF16 exact-source cells: NonLegacy 7x5, 12x12 Repeat1/2,
            # 18x18 Repeat1/3; Legacy 12x12 Repeat2, 18x18 Repeat3/Bias2,
            # 18x12 mixed-alpha, and Legacy 20x16 Smooth62.5. Twelve PF8 and
            # twenty PF32 retained cells are also tuple/source-bound. The three
            # fractional Smoothness cells reproduce the exported owner's
            # signed integer-part boundary only inside their exact predicates. Historical
            # fake-ABI production replays of the
            # broad Amount/Repeat/downsample matrices remain typed/internal
            # oracle artifacts only; the live worker commands above retain
            # the independently valid typed-worker regression coverage.
            # Running the four old fake-ABI adapters as public regressions
            # would both fail against the real SDK ABI and undo exact-source/
            # tuple fail-close admission.
            (sys.executable, "tools/emulation/test_olmblur_exported_effectmain_chain_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmblur_classic_public_real_sdk_20260813.py"),
            (sys.executable, "tests/test_olmblur_classic_public_real_sdk_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_smart_public_admission_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_smart_public_admission_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_current_installed_public_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmblur_current_installed_public_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_7x5_exported_public_owner_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_7x5_exported_public_owner_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_7x5_public_admission_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_7x5_public_admission_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_worker_sources_exported_public_owner_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_retained_tuples_exported_public_owner_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_legacy_retained_exported_public_owner_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_worker_sources_public_admission_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf16_worker_sources_public_admission_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf8_retained_exported_public_owner_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf8_retained_exported_public_owner_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf8_retained_public_admission_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf8_retained_public_admission_20260813.py", "-v"),
            (sys.executable, "tools/emulation/test_olmblur_pf32_retained_public_closure_20260813.py", "--validate-only"),
            (sys.executable, "tests/test_olmblur_pf32_retained_public_closure_20260813.py", "-v"),
            (sys.executable, "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/verify_candidate.py"),
            (sys.executable, "tests/test_olmblur_retained_public_universal_candidate_v4_20260813.py", "-v"),
        ),
    ),
    Lane(
        "colorkeep",
        (
            # The public production route is now deliberately bounded to the
            # six current-AEX 11x7 owner cells plus the separate count9 4x3
            # public closure and their exact palette/source contracts.
            # Historical broad EffectMain probes above exercised
            # tuples that must now reject; treating those rejections as a
            # regression would silently undo the fail-closed admission rule.
            (sys.executable, "-m", "unittest", "tests.test_colorkeep_public_guard_closure_20260812"),
            (sys.executable, "tools/emulation/test_colorkeep_nine_color_public_closure_20260813.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_colorkeep_nine_color_public_closure_20260813"),
            # The old count9-only installed replay points to the pre-union
            # source/install identity.  Current authority is the complete
            # installed 11x7 + count9 bounded union on both Universal slices.
            (sys.executable, "tools/emulation/test_colorkeep_current_installed_complete_union_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_colorkeep_current_installed_complete_union_20260814"),
            (sys.executable, "tools/emulation/test_colorkeep_global_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_params_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_global_setdown_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_installed_entry_worker_writer_20260805.py"),
        ),
    ),
    Lane(
        "colorkey",
        (
            (sys.executable, "tools/emulation/test_olmcolorkey_pf16_full_worker_20260805.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmcolorkey_edge_blur_second_source_20260814"),
            (sys.executable, "tools/emulation/test_olmcolorkey_public_source_bound_closure_20260813.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmcolorkey_public_source_bound_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmcolorkey_current_installed_public_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmcolorkey_current_installed_public_closure_20260813"),
            (sys.executable, "-m", "unittest", "tests.test_olmcolorkey_real_sdk_suite_lifecycle_20260813", "tests.test_olmcolorkey_source_bound_atomic_20260813", "tests.test_olmcolorkey_public_entries_real_sdk_20260813"),
            (sys.executable, "-m", "unittest", "tests.test_olmcolorkey_public_source_bound_docs_20260813"),
        ),
    ),
    Lane(
        "directionalblur",
        (
            (sys.executable, "tools/emulation/test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_type2_natural64_aexcompat_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_type3_public_owner_boundary_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_type3_public_owner_boundary_20260814"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_dual_side_exported_smart_closure_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_dual_side_exported_smart_closure_20260814"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_dual_side_public_owner_boundary_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_dual_side_public_owner_boundary_20260814"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_exported_smart_remaining6_census_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_exported_smart_remaining6_census_20260814"),
            # This is a host-substitute plumbing proof, not native-UCRT or
            # public-EffectMain evidence.  It keeps the exported AEX and the
            # Mac production direct owner on the same keyed expf/pow table so
            # a future native Windows return cannot silently bypass either
            # side of the comparison.
            (sys.executable, "tools/emulation/test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_same_table_dual_owner_plumbing_20260814"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_dual_side_public_source_guard_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_smart_cleanup_atomic_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_type2_natural64_current_install_smoke_20260812"),
            # The pre-Type3 expffloat candidate is retained as rollback history.
            # Current authority is the installed complete bounded union, which
            # replays both Universal slices and the six architecture-gated
            # fail-closed cells against the accepted installed identity.
            (sys.executable, "tools/emulation/test_olmdirectionalblur_current_installed_complete_bounded_union_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdirectionalblur_current_installed_complete_bounded_union_20260814"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_default_noop_host_contract_20260806.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_noise_type3_layer_rowbytes_pf8_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_noise_type3_layer_origin_pf8_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_noise_type3_layer_size_contract_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_minimal_pf16_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf16_noise_type3_production_20260806.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf16_fade_sharp_families_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf16_size_variation_family_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_minimal_pf32_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_size_variation_family_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_front_alpha_fade_family_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_fade_size_combination_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_size_noise_type1_combination_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_fade_noise_type1_combination_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_sharp_back_families_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_mac_smartrender_adapter_20260717.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf8_brightness_half_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf8_size_variation_family_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_size_back_crosses_all_depths_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_noise_types23_size_matrix_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_noise_public_pairwise_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_pf32_size_coeff_geometry_matrix_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_fade_sharp_cross_all_depths_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdirectionalblur_installed_completion_route_20260805.py"),
        ),
    ),
    Lane(
        "distancegradation",
        (
            (sys.executable, "tools/emulation/test_olmdistancegradation_installed_identity_20260806.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_pf32_effectmain_fixture_20260805.py"),
            (sys.executable, "tools/emulation/probe_olmdistancegradation_pf16_smartpre_param_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmdistancegradation_pf16_smart_natural_capture_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf8_outside_power_nobg_rgb_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf8_inside_constant_layer_bg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf8_both_linear_layer_nobg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf32_both_linear_layer_nobg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf16_both_power_layer_nobg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf32_both_power_layer_nobg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf32_inside_constant_blur_nobg_20260805.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf16_background_combos_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf16_blur_background_family_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf32_blur_background_family_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf8_blur_modes45_family_20260810.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_classic_pf8_blur_background_family_20260810.py"),
            (sys.executable, "tools/emulation/audit_olmdistancegradation_exported_render_owner_boundary_20260811.py"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdistancegradation_pf32_mode5_ipp_exact_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_current_installed_mode5_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdistancegradation_current_installed_mode5_20260813"),
            (sys.executable, "tools/emulation/test_olmdistancegradation_public_smart_owner_contract_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdistancegradation_public_smart_owner_contract_20260812"),
            (sys.executable, "tools/emulation/audit_olmdistancegradation_pf32_mode5_universal_codegen_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmdistancegradation_pf32_mode5_universal_codegen_20260812"),
            # The old Distance-only 63-row package is a retained component,
            # not the current collection authority.  The official gate uses
            # the combined 1,344-row request so Directional expf/powf and
            # Distance powf are captured under one exact UCRT identity.
            (sys.executable, "tools/emulation/test_olm_math_ucrt_batch_request_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olm_math_ucrt_batch_request_20260814"),
            # Same-table exported-AEX/Mac-RenderBits plumbing is deliberately
            # host-substitute-only.  The two cross-plugin readiness gates
            # remain fail-closed until the exact native Windows UCRT return is
            # present; their unit suites also exercise the synthetic 14-cell
            # consumer and bounded-table emitter without promoting production.
            (sys.executable, "tools/emulation/test_olmdistancegradation_same_table_dual_owner_plumbing_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmdistancegradation_same_table_dual_owner_plumbing_20260814"),
            (sys.executable, "tools/emulation/test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olm_math_ucrt_native_dual_owner_consumer_readiness_20260814"),
            (sys.executable, "tools/emulation/test_olm_native_ucrt_promotion_table_readiness_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olm_native_ucrt_promotion_table_readiness_20260814"),
            (sys.executable, "-m", "unittest", "tests.test_olm_math_ucrt_fixed_fixture_runner_integration_20260814"),
        ),
    ),
    Lane(
        "kirakira",
        (
            (sys.executable, "tools/emulation/test_olmkirakira_public_smart_bounded_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_public_smart_bounded_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmkirakira_classic_smart_admission_guard_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_classic_smart_admission_guard_20260812"),
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_smart_workspace_dependency_manifest_20260812"),
            # The earlier FP-contract candidate/install chain is a retained historical
            # handoff.  Current authority is the later WorldSuite lifecycle install
            # exercised by the installed public closure below; do not compare the old
            # candidate's source snapshot with the live post-WorldSuite source tree.
            (sys.executable, "tools/emulation/test_olmkirakira_current_installed_public_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_current_installed_public_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmkirakira_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_length9_15x6_exact_boundary_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_9x7_length_family_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_default50_canonical_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py"),
            # Current public 32x18 remains deliberately unpromoted: all three
            # depths must reject before touching the input or destination.
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_mode3_32x18_public_failclose_20260814"),
            (sys.executable, "-m", "unittest", "tests.test_olmkirakira_mode3_32x18_public_closure_20260814"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_nonwhitelist_production_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode2_ramp_production_seam_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode2_ramp_typed_completion_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode4_production_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode4_canonical_angles_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode4_highlight_premultiply_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode4_cropped_typed_installed_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode4_mac_ae_runner_preflight_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_warp_production_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_merge2_mac_production_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_params_setup_contract_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_checkout_dataflow_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_arbitrary_registration_abi_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_default_purecall_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_default_handle_relocation_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_derived_vtable_contract_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_arbitrary_entrypoint_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_mismatched_interpolation_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_compare_signed_zero_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_flat_version_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_flat_relocation_boundary_20260805.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_ramp_event_contract_20260805.py"),
        ),
    ),
    Lane(
        "radialblur",
        (
            (sys.executable, "tools/emulation/test_olmradialblur_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_ui_selectors_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_size_variation_opaque_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_noise_variation_type1_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_size_noise_combo_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_ellipse_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_pf32_ellipse_32x18_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_ellipse_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_unsupported_variation_fail_closed_20260806.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_unproven_geometry_fail_closed_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_production_outer_inputs_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf16_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_intersections_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_strength5_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf16_strength5_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf16_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf16_strength5_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf16_offset_mode3_ui2_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf16_offset_mode2_ui2_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_ui3_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_ui4_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf16_offset_mode3_ui2_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf16_offset_mode3_ui3_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf8_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_type3_host_plumbing_20260811.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_type1_inverse_cell_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_rotation_type1_inverse_cell_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmradialblur_strength290_exported_math_boundary_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_strength290_exported_math_boundary_20260814"),
            (sys.executable, "tools/emulation/test_olmradialblur_strength290_ucrt_math_request_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_strength290_ucrt_math_request_20260814"),
            (sys.executable, "tools/emulation/test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_strength290_native_ucrt_exported_public_boundary_20260815"),
            (sys.executable, "tools/emulation/test_olmradialblur_type3_layer_span_natural_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_type3_layer_span_natural_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmradialblur_type3_all_depth_public_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_type3_all_depth_public_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmradialblur_current_installed_type3_all_depth_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_current_installed_type3_all_depth_closure_20260813"),
            (sys.executable, "-m", "unittest", "tests.test_olmradialblur_smart_cleanup_candidate_20260813"),
            (sys.executable, "tools/emulation/test_olmradialblur_smartrender_fullpath_connection_20260805.py"),
        ),
    ),
    Lane(
        "smoother",
        (
            (sys.executable, "tests/test_olmsmoother_v1_pf16_macos_aexcompat_contract_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_global_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_params_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_ui_noop_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_classifier8_tail_cfg_interpreter_20260805.py"),
            (sys.executable, "tools/emulation/analyze_olmsmoother_v1_classifier8_binary_families_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_edgewalker8_cfg_interpreter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_subhandler8_cfg_interpreter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_subhandler8_generated_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_evaluator8_actual_semantics_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_mainkernel8_cfg_interpreter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_executor8_cfg_interpreter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_mainkernel8_case0001_all_boundaries_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_case0001_pf8_fullframe_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_keymask8_actual_production_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_pf16_colorkey_actual_production_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_pf16_colorkey_effectmain_actual_production_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_multivalue_ramp_boundary_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_colorcompare8_grayscale_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_colorcompare16_colored_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_classifier16_colored_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_colored_fractional_alpha_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_retained_case05_pf8_colorkey_fullframe_actual_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.py"),
            # The old three-cell installed replay is only representative and
            # pins the pre-v3 guard report.  Current authority replays the
            # complete Classic admission union on both installed slices.
            (sys.executable, "tools/emulation/test_olmsmoother_v1_current_installed_admission_union_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother_v1_current_installed_admission_union_20260813"),
        ),
    ),
    Lane(
        "smoother2",
        (
            (sys.executable, "tools/emulation/test_olmsmoother2_pf8_nonuniform_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_pf8_key_gamma_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_pf8_gamma_all_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_public_smoothing_endpoints_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_combined_parameters_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_gamma_all_key_smoothing_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_version_key_gamma_smoothing_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_semtransparent_premul_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_nonuniform_geometry_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_nonuniform_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_key_threshold_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_invert_key_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_all_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_colors_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette2_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette3_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette4_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette_duplicate_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette_tolerance_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_key_gamma_colors_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_invert_key_gamma_colors_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette5_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_gamma_palette_count6_contract_cap_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_palette5_reordered_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_value1_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_gamma_value19328_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_smoothness0_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_smoothrange0_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_extra_smooth100_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_smoothrange255_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_key_white_endpoint_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_invert_key_white_endpoint_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_v2_invert_white_key_gamma_colors_actual_aex_20260806.py"),
            # Smoother2 classic rendering is intentionally fail-closed at all
            # depths.  The historical PF16 classic-positive probe predates the
            # entry-ownership split and must not be used as a regression gate.
            (sys.executable, "tools/emulation/test_olmsmoother2_effectmain_pf32_smart_chain_installed_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_public_admission_guard_closure_20260812.py", "--validate-only"),
            (sys.executable, "tools/emulation/test_olmsmoother_public_admission_guard_closure_unit_20260812.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother_source_contract_20260813"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother_real_sdk_suite_lifecycle_20260813"),
            (sys.executable, "tools/emulation/test_olmsmoother2_case07_unique_direct_oracle_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother2_case07_unique_direct_oracle_20260814"),
            (sys.executable, "tools/emulation/test_olmsmoother2_case07_public_smart_closure_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother2_case07_public_smart_closure_20260814"),
            (sys.executable, "tools/emulation/test_olmsmoother2_case07_pf16_unique_public_closure_20260814.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother2_case07_pf16_unique_public_closure_20260814"),
            (sys.executable, "tools/emulation/test_olmsmoother2_pf8_legacy12_public_closure_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmsmoother2_pf8_legacy12_public_closure_20260814"),
            (sys.executable, "-m", "unittest", "handoffs.olmsmoother2_pf8_pf16_pf32_public_smart_candidate_20260814.test_build_identity"),
        ),
    ),
    Lane(
        "toondilate",
        (
            # Current bounded public route: the additive corner closure and
            # exact12 paired closure perform fresh Windows-AEX/Mac public
            # replays, while the admission closure fresh-runs every exact
            # rejection/control row. The optional checkin artifact is now a
            # lifecycle-only supersession link.
            (sys.executable, "tools/emulation/test_olmtoondilate_corner_seed_public_candidate_20260814.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmtoondilate_corner_seed_public_admission_20260814"),
            (sys.executable, "tools/emulation/test_olmtoondilate_same_source_public_paired_replay_20260813.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_same_source_public_paired_replay_20260813.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmtoondilate_same_source_public_paired_replay_20260813"),
            (sys.executable, "tools/emulation/test_olmtoondilate_public_admission_negative_closure_20260813.py"),
            (sys.executable, "-m", "unittest", "tests.test_olmtoondilate_public_admission_negative_closure_20260813"),
            (sys.executable, "tools/emulation/test_olmtoondilate_optional_checkin_closure_20260812.py", "--validate-only"),
            (sys.executable, "-m", "unittest", "tests.test_olmtoondilate_optional_checkin_closure_20260812"),
            (sys.executable, "tools/emulation/test_olmtoondilate_nonpositive_radius_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/audit_olmtoondilate_actual_aex_smartrender_entrypoint_20260805.py"),
            (sys.executable, "tools/emulation/probe_olmtoondilate_actual_aex_sequence_smartpre_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py"),
        ),
    ),
)


def run(command: tuple[str, ...]) -> float:
    started = time.monotonic()
    subprocess.run(command, cwd=ROOT, check=True)
    return time.monotonic() - started


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plugin",
        action="append",
        choices=tuple(lane.name for lane in LANES),
        help="run only the selected plugin lane; repeatable",
    )
    parser.add_argument(
        "--include-slow-radial-unicorn",
        action="store_true",
        help="also regenerate the approximately 21-minute RadialBlur full AEX replay",
    )
    args = parser.parse_args()

    selected = set(args.plugin or ())
    lanes = tuple(lane for lane in LANES if not selected or lane.name in selected)
    failures: list[tuple[str, tuple[str, ...], int]] = []
    total_started = time.monotonic()

    for lane in lanes:
        print(f"\n== {lane.name} ==", flush=True)
        installed_plugin = LANE_INSTALLED_PLUGIN.get(lane.name)
        if installed_plugin:
            try:
                binary, identity = verified_binary(installed_plugin)
            except RuntimeError as exc:
                command = ("installed-identity-manifest", installed_plugin)
                failures.append((lane.name, command, 126))
                print(f"FAIL {lane.name}: {exc}", file=sys.stderr)
                continue
            print(
                f"PASS {lane.name}: accepted installed identity "
                f"{binary} sha256={identity['sha256']}",
                flush=True,
            )
        for command in lane.commands:
            if command[1] != "-m":
                missing = ROOT / command[1]
                if not missing.is_file():
                    print(f"FAIL missing test: {missing}", file=sys.stderr)
                    failures.append((lane.name, command, 127))
                    continue
            try:
                elapsed = run(command)
            except subprocess.CalledProcessError as exc:
                failures.append((lane.name, command, exc.returncode))
                print(f"FAIL {lane.name}: {' '.join(command)} (rc={exc.returncode})", file=sys.stderr)
            else:
                print(f"PASS {lane.name}: {command[1]} ({elapsed:.2f}s)", flush=True)

    if args.include_slow_radial_unicorn and (not selected or "radialblur" in selected):
        command = (sys.executable, "tools/emulation/test_m4_case0010.py")
        print("\n== radialblur slow full Unicorn replay ==", flush=True)
        try:
            elapsed = run(command)
        except subprocess.CalledProcessError as exc:
            failures.append(("radialblur-slow", command, exc.returncode))
        else:
            print(f"PASS radialblur-slow ({elapsed:.2f}s)", flush=True)

    elapsed = time.monotonic() - total_started
    if failures:
        for lane, command, returncode in failures:
            print(
                "FAILURE "
                + json.dumps(
                    {"lane": lane, "command": list(command), "returncode": returncode},
                    sort_keys=True,
                )
            )
        print(f"\nFAIL_OLM_MAC_FIXED_FIXTURE_REGRESSION failures={len(failures)} elapsed={elapsed:.2f}s")
        return 1
    print(f"\nPASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes={len(lanes)} elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
