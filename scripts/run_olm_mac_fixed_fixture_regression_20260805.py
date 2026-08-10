#!/usr/bin/env python3
"""Run the bounded Mac-only OLM conformance lanes.

The default suite consumes retained Windows-AEX fixtures and runs local
production/focused adapters.  It does not contact or require a Windows host.
The expensive RadialBlur full Unicorn replay is opt-in.
"""

from __future__ import annotations

import argparse
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
            (sys.executable, "refs/scripts/smoke_olmblur_effectmain_completion_matrix_20260805.py"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_legacy_source_aex_adapter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmblur_pf8_legacy_source_aex_adapter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmblur_pf16_nonlegacy_source_aex_adapter_20260805.py"),
            (sys.executable, "tools/emulation/test_olmblur_effectmain_smart_chain_20260805.py"),
            (sys.executable, "tools/emulation/test_olmblur_nondefault_smoothness_effectmain_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmblur_amount_repeat_legacy_matrix_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmblur_downsample_amount_matrix_actual_aex_20260811.py"),
        ),
    ),
    Lane(
        "colorkeep",
        (
            (sys.executable, "tools/emulation/test_colorkeep_disabled_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_fixed_tolerance_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_max100_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_count_late_boundary_combo_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_colorkeep_invalid_counts_checkout_effectmain_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_duplicate_colors_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_pf32_nan_inf_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_pf32_snan_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_pf32_signed_zero_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_pf32_subnormal_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_pf16_extended_range_effectmain_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_update_params_ui_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_user_changed_param_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_global_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_params_setup_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_global_setdown_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_installed_entry_worker_writer_20260805.py"),
            (sys.executable, "tools/emulation/test_colorkeep_installed_public_pf16_render_20260805.py"),
        ),
    ),
    Lane(
        "colorkey",
        (
            (sys.executable, "tools/emulation/test_olmcolorkey_pf16_full_worker_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_pf16_edge_blur_internal_plane_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_pf32_edge_blur_full_worker_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_pf8_edge_blur_full_worker_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_2_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_1_5_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_0_5_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_2_5_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_3_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_3_5_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_4_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_direction_1_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_direction_3_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_direction_4_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_direction_0_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_direction_1_amount_1_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_edge_blur_center_geometry_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/test_olmcolorkey_practical_multi_geometry_all_depths_20260810.py"),
            (sys.executable, "tools/emulation/test_olmcolorkey_practical_distance_types_all_depths_20260810.py"),
            (sys.executable, "tools/emulation/test_olmcolorkey_edge_thin_family_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmcolorkey_colorspace_2_5_matrix_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmcolorkey_replace_edge_composition_actual_aex_20260811.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_entry_writer_installed_connection_20260805.py"),
            (sys.executable, "tools/emulation/audit_olmcolorkey_effectmain_fallback_typed_writer_connection_20260805.py"),
        ),
    ),
    Lane(
        "directionalblur",
        (
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
        ),
    ),
    Lane(
        "kirakira",
        (
            (sys.executable, "tools/emulation/test_olmkirakira_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_length9_15x6_exact_boundary_20260806.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_9x7_length_family_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_default50_canonical_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmkirakira_mode3_geometry_generalization_actual_aex_20260810.py"),
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
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_strength5_noise_type1_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_offset_mode3_noise_type1_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_noise_inner_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_zoom_pf32_noise_32x18_actual_aex_20260810.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_unsupported_variation_fail_closed_20260806.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_case0009_pf32_ae_control_replay_20260806.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_case0010_rotation_mac_production_planes_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_production_outer_inputs_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf16_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_small_actual_aex_20260805.py"),
            (sys.executable, "tools/emulation/test_olmradialblur_rotation_pf32_edge_fade_actual_aex_20260811.py"),
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
            (sys.executable, "tools/emulation/test_olmsmoother_v1_retained_case05_pf8_colorkey_fullframe_actual_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother_v1_retained_case01_pf8_owner_and_host_boundary_20260806.py"),
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
            (sys.executable, "tools/emulation/test_olmsmoother2_effectmain_pf16_chain_installed_20260805.py"),
            (sys.executable, "tools/emulation/test_olmsmoother2_effectmain_pf32_smart_chain_installed_20260805.py"),
        ),
    ),
    Lane(
        "toondilate",
        (
            (sys.executable, "tools/emulation/test_olmtoondilate_nonpositive_radius_all_depths_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_ui_setup_actual_aex_20260806.py"),
            (sys.executable, "tools/emulation/audit_olmtoondilate_actual_aex_smartrender_entrypoint_20260805.py"),
            (sys.executable, "tools/emulation/probe_olmtoondilate_actual_aex_sequence_smartpre_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_installed_completion_route_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_installed_dynamic_entry_20260805.py"),
            (sys.executable, "tools/emulation/test_olmtoondilate_installed_dynamic_all_depths_20260806.py"),
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
        print(f"\nFAIL_OLM_MAC_FIXED_FIXTURE_REGRESSION failures={len(failures)} elapsed={elapsed:.2f}s")
        return 1
    print(f"\nPASS_OLM_MAC_FIXED_FIXTURE_REGRESSION lanes={len(lanes)} elapsed={elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
