#!/usr/bin/env python3
"""Summarize runtime trace packages, answer status, and next intake commands."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Any

RUNTIME_RESULT_FILENAMES = {
    "RETURN_RUNTIME_TRACE_RESULT.json",
    "RETURN_RUNTIME_TRACE.json",
    "AE_RUNTIME_TRACE_RESULT.json",
}

PRIORITY_PROFILES = {
    "olmdirectionalblur-2025-front-alpha-host-boundary": 1,
    "olmdirectionalblur-2025-alpha-fade-fullrender-row755-pre-normalization": 3,
    "olmdirectionalblur-row755-common-core": 3,
    "olmdirectionalblur-front-alpha-writer-entry": 2,
    "distancegradation-8bpc-current-aex-same-run-typed-boundary": 1,
    "distancegradation-8bpc-coordinate-liveness-census": 1,
    "radialblur-tiny-rotation-anchor-context-watch-followup": 3,
    "radialblur-tiny-rotation-anchor-pointer-watch-followup": 4,
    "radialblur-tiny-rotation-anchor-watch-followup": 5,
    "radialblur-tiny-rotation-backstep-followup": 6,
    "radialblur-tiny-rotation-followup": 7,
    "radialblur-residual-witness": 10,
    "radialblur-caller-collapse-witness": 9,
    "radialblur-caller-collapse-followup": 8,
    "distancegradation-0010-compose-source-901-394-tile-retry": 8,
    "distancegradation-0010-compose-visited-tile-source-0-45": 8,
    "distancegradation-0010-compose-single-site-break-ignore-retry": 9,
    "distancegradation-0010-compose-single-site-followup": 10,
    "distancegradation-0010-0011-compose-exact-address-witness": 11,
    "distancegradation-case0023-final-source-ownership": 16,
    "distancegradation-0010-0011-compose-input-pointer-witness": 12,
    "distancegradation-0010-0011-rdx-producer-packsite-witness": 13,
    "distancegradation-0010-0011-writeback-pointer-map-witness": 14,
    "distancegradation-0010-0011-writeback-follow-witness": 15,
    "distancegradation-0010-0011-field-store-prewarm-witness": 16,
    "distancegradation-0010-0011-field-store-witness": 16,
    "distancegradation-depthgate-quantization-witness": 17,
    "distancegradation-depthgate-907-store-export-witness": 17,
    "distancegradation-case0012-case0014-store-export-rounding": 17,
    "distancegradation-case0014-layer-source-witness": 18,
    "radialblur-case0010-final-writeback": 18,
    "radialblur-zoom-case0009-final-plane-cells": 18,
    "radialblur-zoom-case0009-final-plane-typed": 18,
    "radialblur-case0009-fullframe-postnorm-typed-common-core": 18,
    "distancegradation-case0023-refcon-stack-wordmap-followup": 17,
    "distancegradation-case0023-refcon-wordmap-followup": 18,
    "distancegradation-case0023-output-word-triplet-followup": 19,
    "distancegradation-case0023-triplet-xy-compose-followup": 20,
    "distancegradation-case0023-threshold-followup": 21,
    "kirakira-hotspot-compose-writeback-witness": 43,
    "olmkirakira-mode2-compose-writeback": 42,
    "olmblur-case0006-helper-prestore": 18,
    "distancegradation-constant-case0023-witness": 22,
    "olmblur-final-word-witness": 19,
    "kirakira-boxfilter-pass1-microprobe": 20,
    "kirakira-compose-writeback-witness": 44,
    "directionalblur-helper-coverage-witness": 29,
    "directionalblur-residual-witness": 30,
    "directionalblur-angle0-single-shot-witness": 31,
    "kirakira-forward-warp-box-input": 40,
    "kirakira-aggregation-compose-bt709": 45,
    "kirakira-stage-values-deep": 50,
    "olmblur-repeat-threshold": 60,
    "colorkey-edge": 70,
    "distancegradation-field-prep": 80,
    "directionalblur-angle0-helper-gate-retry": 110,
    "directionalblur-angle0-load-prewarm-retry": 111,
    "directionalblur-witness-logging-prep": 112,
    "smoother2-current-aex-0004-load-prewarm-retry": 210,
    "smoother2-current-aex-0004-writer-gate-retry": 211,
    "smoother2-current-aex-producer-path-diff": 212,
    "smoother2-current-aex-producer-bytes-20260708": 213,
    "smoother2-current-aex-0012-bind-then-read-20260708": 214,
    "olmsmoother2-case0012-current-aex-common-core": 214,
    "olmsmoother2-legacy-key-producer-common-core": 214,
    "windows-ae-addproperty-stall-diagnostics": 900,
    "windows-ae-runner-startup-diagnostics": 901,
}

PARTIAL_STILL_PENDING_REQUEST_IDS = {
    # A one-pixel or downstream-missing single-shot answer is useful evidence,
    # but it is not enough to retire the angle-0 witness request.
    "olmdirectionalblur_angle0_single_shot_witness_20260708",
    # The prewarm retry must prove the Windows module loaded before binding
    # target pixels. A module-only or coordinate-miss partial is useful
    # diagnostics, but cannot retire the 0010/0011 field/store witness.
    "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709",
    "olmdistancegradation_0010_0011_writeback_follow_witness_20260709",
    "olmdistancegradation_case0014_layer_source_witness_20260708",
}

PARTIAL_VISIBLE_OPEN_REQUEST_IDS = {
    # This return is already imported and useful, but the comparison classifies
    # the lane as still open. Keep it visible as answered_partial without
    # allowing it to displace the currently staged RadialBlur request.
    "olmdistancegradation_depthgate_907_store_export_witness_20260708",
    # Pointer map and same-run PF16 target words returned successfully, but the
    # package missed same-run true16 TIFF/EXR export samples. Keep it visible as
    # partial success; do not keep staging the same debugger package unchanged.
    "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709",
}

# These returns contain numeric fields that were not captured by the claimed
# Windows runtime target. Keep them visible as invalid evidence rather than
# allowing a hand-edited result status to close the request.
INVALID_UNGROUNDED_REQUEST_IDS = {
    "olmblur_case0006_helper_prestore_witness_20260630",
}

COMPARISON_COMMANDS = [
    (
        "kirakira_hotspot_compose_writeback_witness_20260701",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.md",
    ),
    (
        "kirakira_compose_writeback_witness_20260630",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_compose_writeback_witness.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_compose_writeback_witness.md",
    ),
    (
        "kirakira_aggregation_compose_bt709_20260624",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md",
    ),
    (
        "olmradialblur_zoom_case0009_final_plane_cells_20260709",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_zoom_case0009_final_plane_cells_20260709.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_zoom_case0009_final_plane_cells_20260709.md",
    ),
    (
        "olmradialblur_case0010_final_writeback_20260708",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_case0010_final_writeback_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_case0010_final_writeback_20260708.md",
    ),
    (
        "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702.md",
    ),
    (
        "olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702.md",
    ),
    (
        "olmradialblur_tiny_rotation_anchor_watch_followup_20260701",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_watch_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_watch_followup_20260701.md",
    ),
    (
        "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_backstep_followup_20260701.md",
    ),
    (
        "olmradialblur_tiny_rotation_substitute_path_followup_20260701",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_followup_20260701.md",
    ),
    (
        "olmradialblur_caller_collapse_followup_20260701",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_caller_collapse_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_caller_collapse_followup_20260701.md",
    ),
    (
        "olmradialblur_caller_collapse_witness_20260630",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_caller_collapse_witness.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_caller_collapse_witness.md",
    ),
    (
        "olmradialblur_zoom_tiny_rotation_residual_witness_20260622",
        "python3 scripts/compare_radialblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.json --output-md refs/reports/runtime_trace_comparisons/olmradialblur_residual_witness.md",
    ),
    (
        "kirakira_boxfilter_pass1_microprobe_20260622",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260622_box_windows_mac/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_boxfilter_pass1_microprobe.md",
    ),
    (
        "olmdirectionalblur_helper_coverage_witness_20260630",
        "python3 scripts/compare_directionalblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdirectionalblur_helper_coverage_witness.json --output-md refs/reports/runtime_trace_comparisons/olmdirectionalblur_helper_coverage_witness.md",
    ),
    (
        "olmdirectionalblur_angle0_single_shot_witness_20260708",
        "python3 scripts/compare_directionalblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdirectionalblur_angle0_single_shot_witness_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmdirectionalblur_angle0_single_shot_witness_20260708.md",
    ),
    (
        "olmdirectionalblur_angle0_diagonal_residual_witness_20260622",
        "python3 scripts/compare_directionalblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.json --output-md refs/reports/runtime_trace_comparisons/olmdirectionalblur_residual_witness.md",
    ),
    (
        "kirakira_forward_warp_box_input_20260621",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --local-trace-json refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan/trace.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_forward_warp_box_input.md",
    ),
    (
        "kirakira_fun_181150790",
        "python3 scripts/compare_kirakira_stage_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmkirakira_stage_values.json --output-md refs/reports/runtime_trace_comparisons/olmkirakira_stage_values.md",
    ),
    (
        "olmblur_case0006_helper_prestore_witness_20260630",
        "python3 scripts/compare_olmblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_witness.json --output-md refs/reports/runtime_trace_comparisons/olmblur_case0006_helper_prestore_witness.md",
    ),
    (
        "olmblur_final_word_witness_20260630",
        "python3 scripts/compare_olmblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmblur_final_word_witness.json --output-md refs/reports/runtime_trace_comparisons/olmblur_final_word_witness.md",
    ),
    (
        "olmblur_repeat_threshold",
        "python3 scripts/compare_olmblur_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold.json --output-md refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold.md",
    ),
    (
        "colorkey_edge",
        "python3 scripts/compare_colorkey_edge_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmcolorkey_edge.json --output-md refs/reports/runtime_trace_comparisons/olmcolorkey_edge.md",
    ),
    (
        "olmdistancegradation_0010_0011_field_store_witness_20260709",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_witness_20260709.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_witness_20260709.md",
    ),
    (
        "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709",
        "python3 scripts/compare_distancegradation_trace.py --request-id olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709 --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709.md",
    ),
    (
        "olmdistancegradation_0010_0011_writeback_follow_witness_20260709",
        "python3 scripts/compare_distancegradation_trace.py --request-id olmdistancegradation_0010_0011_writeback_follow_witness_20260709 --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_follow_witness_20260709.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_follow_witness_20260709.md",
    ),
    (
        "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709",
        "python3 scripts/compare_distancegradation_trace.py --request-id olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709 --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709.md",
    ),
    (
        "olmdistancegradation_case0023_final_source_ownership_20260707",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_final_source_ownership_20260707.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_final_source_ownership_20260707.md",
    ),
    (
        "olmdistancegradation_depthgate_907_store_export_witness_20260708",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.md",
    ),
    (
        "olmdistancegradation_depthgate_quantization_witness_20260708",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_quantization_witness_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_quantization_witness_20260708.md",
    ),
    (
        "olmdistancegradation_case0014_layer_source_witness_20260708",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0014_layer_source_witness_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0014_layer_source_witness_20260708.md",
    ),
    (
        "olmdistancegradation_16bpc_case0026_x_witness_20260628",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_case0026_x_witness_20260628.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_case0026_x_witness_20260628.md",
    ),
    (
        "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629.md",
    ),
    (
        "olmdistancegradation_16bpc_constant_boundary_witness_20260630",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_boundary_witness.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_boundary_witness.md",
    ),
    (
        "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.md",
    ),
    (
        "olmdistancegradation_case0023_refcon_wordmap_followup_20260702",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_wordmap_followup_20260702.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_wordmap_followup_20260702.md",
    ),
    (
        "olmdistancegradation_case0023_output_word_triplet_followup_20260701",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_output_word_triplet_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_output_word_triplet_followup_20260701.md",
    ),
    (
        "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701.md",
    ),
    (
        "olmdistancegradation_case0023_threshold_family_followup_20260701",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_threshold_family_followup_20260701.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_threshold_family_followup_20260701.md",
    ),
    (
        "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_case0023_outside0_witness.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_constant_case0023_outside0_witness.md",
    ),
    (
        "olmdistancegradation",
        "python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_field_prep.md",
    ),
]

ACCEPTANCE_NOTES = {
    "olmdirectionalblur_alpha_fade_fullrender_row755_20260712": "refs/runtime_trace_packages/olmdirectionalblur_alpha_fade_fullrender_row755_20260712/README.md",
    "olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712": "refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_current_aex_same_run_typed_boundary_20260712/README_RUNTIME_TRACE.md",
    "olmdirectionalblur_front_alpha_host_boundary_2025_20260711": "refs/conformance/dblur_alpha_host_boundary_20260711.md",
    "olmdistancegradation_0010_compose_source_901_394_tile_retry_20260710": "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
    "olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710": "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
    "olmdistancegradation_0010_compose_single_site_followup_20260710": "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
    "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710": "refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md",
    "olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_compose_input_pointer_contract_20260709.md",
    "olmdistancegradation_0010_0011_rdx_producer_packsite_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_rdx_producer_packsite_contract_20260709.md",
    "olmdistancegradation_0010_0011_field_world_pack_read_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_field_world_pack_read_contract_20260709.md",
    "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md",
    "olmdistancegradation_0010_0011_writeback_follow_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_contract_20260709.md",
    "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_contract_20260709.md",
    "olmdistancegradation_0010_0011_field_store_witness_20260709": "refs/conformance/olmdistancegradation_0010_0011_field_store_witness_contract_20260709.md",
    "olmradialblur_zoom_case0009_final_plane_cells_20260709": "refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md",
    "olmradialblur_zoom_case0009_final_plane_typed_20260710": "refs/conformance/olmradialblur_zoom_case0009_final_plane_typed_contract_20260710.md",
    "olmradialblur_case0010_final_writeback_20260708": "refs/conformance/olmradialblur_case0010_final_writeback_contract_20260708.md",
    "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702": "refs/conformance/olmradialblur_tiny_rotation_anchor_context_watch_return_acceptance_20260702.md",
    "olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702": "refs/conformance/olmradialblur_tiny_rotation_anchor_pointer_watch_return_acceptance_20260702.md",
    "olmradialblur_tiny_rotation_anchor_watch_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_anchor_watch_return_acceptance_20260701.md",
    "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_backstep_return_acceptance_20260701.md",
    "olmradialblur_tiny_rotation_substitute_path_followup_20260701": "refs/conformance/olmradialblur_tiny_rotation_return_acceptance_20260701.md",
    "olmradialblur_caller_collapse_followup_20260701": "refs/conformance/olmradialblur_outer_return_acceptance_20260701.md",
    "olmdirectionalblur_angle0_single_shot_witness_20260708": "refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md",
    "olmdistancegradation_case0023_final_source_ownership_20260707": "refs/conformance/olmdistancegradation_case0023_final_source_ownership_contract_20260707.md",
    "olmdistancegradation_depthgate_quantization_witness_20260708": "refs/conformance/olmdistancegradation_depthgate_quantization_witness_contract_20260708.md",
    "olmdistancegradation_depthgate_907_store_export_witness_20260708": "refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md",
    "olmdistancegradation_case0012_case0014_store_export_rounding_20260708": "refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_contract_20260708.md",
    "olmdistancegradation_case0014_layer_source_witness_20260708": "refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md",
    "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702": "refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md",
    "olmdistancegradation_case0023_refcon_wordmap_followup_20260702": "refs/conformance/olmdistancegradation_case0023_refcon_wordmap_return_acceptance_20260702.md",
    "olmdistancegradation_case0023_output_word_triplet_followup_20260701": "refs/conformance/olmdistancegradation_case0023_output_word_triplet_return_acceptance_20260701.md",
    "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701": "refs/conformance/olmdistancegradation_case0023_triplet_xy_compose_return_acceptance_20260701.md",
    "olmdistancegradation_case0023_threshold_family_followup_20260701": "refs/conformance/olmdistancegradation_case0023_threshold_return_acceptance_20260701.md",
    "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630": "refs/conformance/olmdistancegradation_case0023_return_acceptance_20260701.md",
    "olmblur_case0006_helper_prestore_witness_20260630": "refs/conformance/olmblur_case0006_reference_provenance_20260701.md",
    "olmsmoother2_current_aex_producer_bytes_20260708": "refs/conformance/olmsmoother2_current_aex_producer_bytes_contract_20260708.md",
    "olmsmoother2_current_aex_0012_bind_then_read_20260708": "refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_contract_20260708.md",
}

HARD_LANE_CONTEXTS = {
    "olmdirectionalblur_front_alpha_host_boundary_2025_20260711": {
        "note": "refs/conformance/dblur_alpha_host_boundary_20260711.md",
        "summary": "The front-alpha kernel is binary-grounded, but the retained June19 reference omitted loaded-AEX identity and the exact PF input world. This one hash-gated invocation-bound capture decides host input, AEX generation, and output/export ownership without PNG tuning.",
    },
    "olmdistancegradation_0010_compose_source_901_394_tile_retry_20260710": {
        "note": "refs/conformance/olmdistancegradation_0010_compose_break_ignore_return_intake_20260710.md",
        "summary": "Tile-aware successor: the break-ignore source run hit entry at (0,90), while target (6,40) never reached the downstream site. Run source only for the grounded residual (901,394).",
    },
    "olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710": {
        "note": "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
        "summary": "Direct debugger-control retry: prior field/source runs reached entry, then ended on first-chance 0x80000003. Ignore that exception and retain the same one-target/one-site gates.",
    },
    "olmdistancegradation_0010_compose_single_site_followup_20260710": {
        "note": "refs/conformance/olmdistancegradation_0010_compose_single_site_followup_contract_20260710.md",
        "summary": "Direct successor to the partial exact-address return. Run one case, one target, and one downstream site per debugger process; first bind field/source words for case_0010 (6,40).",
    },
    "olmradialblur_case0010_final_writeback_20260708": {
        "note": "refs/conformance/olmradialblur_static_witness_plan_20260708.md",
        "summary": "Tiny Rotation case_0010 needs same-run final-writeback/provenance proof to split CPU-rule gap from final output/export or stale-reference drift.",
    },
    "olmradialblur_zoom_case0009_final_plane_cells_20260709": {
        "note": "refs/conformance/olmradialblur_zoom_case0009_final_plane_cells_contract_20260709.md",
        "summary": "Zoom case_0009 is narrowed to final polar-plane cell identity: prove why Windows top-row alpha=254 occurs only at x=6,7,12 without the local candidate's false positives.",
    },
    "olmradialblur_zoom_case0009_final_plane_typed_20260710": {
        "note": "refs/conformance/olmradialblur_zoom_remaining_polar_sampler_audit_20260710.md",
        "summary": "Exact AEX trig leaves top-row alpha targets unresolved; capture final polar cell IDs, +0xe RGBA, +0xf252 validity, weights, and pre-byte alpha for (7,0) with controls.",
    },
    "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702": {
        "note": "refs/conformance/olmradialblur_tiny_rotation_lane_state_20260703.md",
        "summary": "Same-row direct-source cells stay black; only missing proof is which upstream promoted branch creates the one-row-up bright lobe.",
    },
    "olmdistancegradation_case0023_final_source_ownership_20260707": {
        "note": "refs/conformance/olmdistancegradation_case0023_neighborhood_probe_result_20260707.md",
        "summary": "Mac-only source/field/shade/store probes bound the 16bpc case_0023 residual to two sampled pixels; return must prove Windows final/source ownership, not reopen broad field or compose tuning.",
    },
    "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709": {
        "note": "refs/conformance/olmdistancegradation_0010_0011_field_store_prewarm_contract_20260709.md",
        "summary": "Sparse 16bpc case_0010/0011 R/A abs-2 residual: local Meijster and OpenCV-compatible EDT agree. Latest failed_partial proves module-load reliability but not typed target values; next proof should continue past DistanceGradation+0x117051c into PF interleave/writeback.",
    },
    "olmdistancegradation_0010_0011_writeback_follow_witness_20260709": {
        "note": "refs/conformance/olmdistancegradation_0010_0011_writeback_follow_contract_20260709.md",
        "summary": "Narrow successor to the 0010/0011 field-store lane: module load is reliable; follow the stable hardware-entry path past DistanceGradation+0x117051c into PF interleave/writeback and bind the two sign-flipped case_0010 pixels.",
    },
    "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709": {
        "note": "refs/conformance/olmdistancegradation_0010_0011_writeback_pointer_map_return_intake_20260709.md",
        "summary": "Pointer map returned partial_success_missing_true16_export: output base formula, rowbytes, pixel size, and same-run PF16 words are bound for case_0010 (6,40)/(901,394). Local Mac-side classification is next; only ask for true16 TIFF/EXR export if export binding remains mandatory.",
    },
    "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710": {
        "note": "refs/conformance/olmdistancegradation_0010_0011_compose_exact_address_contract_20260710.md",
        "summary": "Compose-input roles are known, but exact pixels were not bound because rbp is not y. Derive field/source/output address formulas and gate +0x117057d/+0x11705f1/final writer by address.",
    },
    "olmdistancegradation_depthgate_quantization_witness_20260708": {
        "note": "refs/conformance/olmdistancegradation_depthgate_nearmiss_witness_20260708.md",
        "summary": "Depth-gated build closes case_0023; remaining 0024..0027 max=1 family needs compose/store/export-stage proof, not source-mask or field retuning.",
    },
    "olmdistancegradation_depthgate_907_store_export_witness_20260708": {
        "note": "refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md",
        "summary": "One-pixel closeout for depthgate case_0026 `(907,222)`: prove whether Windows stores B=0 before export or stores a small positive B that export quantizes to byte zero.",
    },
    "olmdistancegradation_case0012_case0014_store_export_rounding_20260708": {
        "note": "refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_contract_20260708.md",
        "summary": "Layer/no-bg source ownership is narrowed to max 2/4; this request must bind same-run pre-store float, PF16 store words, and exported true16/TIFF/EXR values for case_0012 and case_0014.",
    },
    "olmdistancegradation_case0014_layer_source_witness_20260708": {
        "note": "refs/conformance/olmdistancegradation_case0014_layer_source_witness_contract_20260708.md",
        "summary": "16bpc Layer-source family proof for case_0014; alpha matches at the primary witness, so this isolates source RGB/pre-store ownership.",
    },
    "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702": {
        "note": "refs/conformance/olmdistancegradation_case0023_lane_state_20260707.md",
        "summary": "Residual is split into edge 65px plus threshold 8px; this request is superseded by local AEX CPU simu evidence and remains only a historical refcon/output-word ownership lane.",
    },
    "olmdirectionalblur_angle0_helper_gate_retry_20260702": {
        "note": "refs/conformance/olmdirectionalblur_lane_state_20260703.md",
        "summary": "Keep angle-0 helper validity separate from diagonal rotate validity; broad prepass or scatter tuning remains forbidden.",
    },
    "olmdirectionalblur_angle0_single_shot_witness_20260708": {
        "note": "refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md",
        "summary": "Angle-0 only single-shot witness for `(494,169)` / `(579,169)`; capture typed helper/writeback facts without broad hit-storm replay or diagonal tuning.",
    },
    "olmdirectionalblur_angle0_load_prewarm_retry_20260703": {
        "note": "refs/conformance/olmdirectionalblur_lane_state_20260703.md",
        "summary": "This retry exists only to get a stable module-loaded witness for the angle-0 helper lane before any diagonal replay.",
    },
    "olmdirectionalblur_witness_logging_prep_20260702": {
        "note": "refs/conformance/olmdirectionalblur_lane_state_20260703.md",
        "summary": "Witness prep should surface denominator and validity facts, not reopen PNG-only angle or front-strength tuning.",
    },
    "olmsmoother2_current_aex_0004_load_prewarm_retry_20260703": {
        "note": "refs/conformance/olmsmoother2_legacy_lane_state_20260703.md",
        "summary": "Writer bytes are already grounded; unresolved lane is the first producer divergence feeding c280/cce0 for legacy case_0004.",
    },
    "olmsmoother2_current_aex_0004_writer_gate_retry_20260702": {
        "note": "refs/conformance/olmsmoother2_legacy_lane_state_20260703.md",
        "summary": "Need a gated witness that distinguishes c280 polygon append from cce0 fallback without changing global fallback behavior.",
    },
    "olmsmoother2_current_aex_producer_path_diff_20260702": {
        "note": "refs/conformance/olmsmoother2_legacy_lane_state_20260703.md",
        "summary": "Track the producer path diff from the writer anchor back into the first diverging emit chain; do not tune curves globally.",
    },
    "olmsmoother2_current_aex_producer_bytes_20260708": {
        "note": "refs/conformance/olmsmoother2_current_aex_producer_bytes_contract_20260708.md",
        "summary": "Final writer bytes are already grounded; read the 0012 e170 producer bytes/c value and the 0004 scanner-span/class-prev byte3 producer state.",
    },
    "olmsmoother2_current_aex_0012_bind_then_read_20260708": {
        "note": "refs/conformance/olmsmoother2_current_aex_0012_bind_then_read_contract_20260708.md",
        "summary": "Narrow the next Windows request to one same-run `0012 (91,841)` bind-then-read witness: first bind the live producer/class buffer, then read `center_b0`, `prev_b0`, `left_b1`, and observed `e170 c`.",
    },
    "olmsmoother2_legacy_key_producer_common_core_20260716": {
        "note": "refs/conformance/olmsmoother2_legacy_key_producer_request_contract_20260716.md",
        "summary": "Run the real AE case0012 and bind the exact f270 callsite before reading class bytes and producer return values; entry-register guesses and final-writer recapture are forbidden.",
    },
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_request_id(request_id: str) -> str:
    return re.sub(r"_retry_\d{8}$", "", request_id)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=root / "refs/runtime_trace_packages")
    parser.add_argument("--output-json", type=Path, default=root / "refs/reports/pending_runtime_trace_packages.json")
    parser.add_argument("--output-md", type=Path, default=root / "refs/reports/pending_runtime_trace_packages.md")
    return parser.parse_args()


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def package_manifest(path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            name = next(
                (member for member in archive.namelist() if member.replace("\\", "/").endswith("runtime_trace_package_manifest.json")),
                None,
            )
            if name is None:
                name = next(
                    (member for member in archive.namelist() if member.replace("\\", "/").endswith("package-manifest.json")),
                    None,
                )
            if name is None:
                return None
            data = json.loads(archive.read(name).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if data.get("kind") == "olm_runtime_trace_request_package":
        return data
    if data.get("kind") != "windows_witness_generated_package":
        return None
    queue = data.get("queue")
    request_id = data.get("request_id")
    if not isinstance(queue, dict) or not isinstance(request_id, str):
        return None
    return {
        "kind": "olm_runtime_trace_request_package",
        "profile": queue.get("profile") or "",
        "supersedes": queue.get("supersedes") or [],
        "runtime_actions": [
            {
                "request_id": request_id,
                "plugin_area": queue.get("plugin_area") or "",
                "command": queue.get("command") or "",
                "stop_condition": queue.get("stop_condition") or "",
            }
        ],
    }


def answered_request_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((root / "refs/reports").glob("**/runtime_trace_summary*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        for row in data.get("results", []):
            if not isinstance(row, dict) or not isinstance(row.get("request_id"), str):
                continue
            request_id = normalize_request_id(row["request_id"])
            if request_id in INVALID_UNGROUNDED_REQUEST_IDS:
                continue
            status = str(row.get("status") or "").lower()
            if (
                status.startswith("answered_partial")
                and request_id not in PARTIAL_STILL_PENDING_REQUEST_IDS
                and request_id not in PARTIAL_VISIBLE_OPEN_REQUEST_IDS
            ):
                ids.add(request_id)
                continue
            if status in {"answered", "ok", "complete"}:
                ids.add(request_id)
    for path in sorted((root / "refs/reports/runtime_trace_comparisons").glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("request_id"), str):
            continue
        windows = data.get("windows")
        if not isinstance(windows, dict):
            continue
        request_id = normalize_request_id(str(data["request_id"]))
        if request_id in INVALID_UNGROUNDED_REQUEST_IDS:
            continue
        status = str(windows.get("status") or "").lower()
        if (
            status.startswith("answered_partial")
            and request_id not in PARTIAL_STILL_PENDING_REQUEST_IDS
            and request_id not in PARTIAL_VISIBLE_OPEN_REQUEST_IDS
        ):
            ids.add(request_id)
            continue
        if status in {"answered", "ok", "complete"}:
            ids.add(request_id)
    return ids


def latest_result_rows(root: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[int, float, dict[str, Any]]] = {}
    reports_root = root / "refs/reports"
    candidates = sorted(reports_root.glob("**/runtime_trace_summary*.json"))
    candidates.extend(
        path
        for path in sorted(reports_root.glob("**/summary.json"))
        if "runtime_trace_returns" in path.parts
    )
    seen: set[Path] = set()
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        data = read_json(path)
        if not isinstance(data, dict) or data.get("kind") != "olm_runtime_trace_return_summary":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        for row in data.get("results", []):
            if not isinstance(row, dict) or not isinstance(row.get("request_id"), str):
                continue
            request_id = normalize_request_id(str(row["request_id"]))
            source_file = str(row.get("source_file") or "")
            status = str(row.get("status") or "").lower()
            priority = 0
            if Path(source_file).name in RUNTIME_RESULT_FILENAMES:
                priority += 4
            if status in {"failed_partial", "answered_partial", "answered", "ok", "complete"}:
                priority += 2
            if status == "diagnostic":
                priority -= 2
            current = latest.get(request_id)
            if current is None or (priority, mtime) >= (current[0], current[1]):
                latest[request_id] = (priority, mtime, row)
    return {request_id: row for request_id, (_, _, row) in latest.items()}


def latest_comparison_paths(root: Path) -> dict[str, str]:
    latest: dict[str, tuple[float, str]] = {}
    for path in sorted((root / "refs/reports/runtime_trace_comparisons").glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("request_id"), str):
            continue
        request_id = normalize_request_id(str(data["request_id"]))
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        md_path = path.with_suffix(".md")
        display = display_path(root, md_path if md_path.exists() else path)
        current = latest.get(request_id)
        if current is None or mtime >= current[0]:
            latest[request_id] = (mtime, display)
    return {request_id: display for request_id, (_, display) in latest.items()}


def latest_comparison_statuses(root: Path) -> dict[str, str]:
    latest: dict[str, tuple[float, str]] = {}
    for path in sorted((root / "refs/reports/runtime_trace_comparisons").glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or not isinstance(data.get("request_id"), str):
            continue
        windows = data.get("windows")
        if not isinstance(windows, dict):
            continue
        status = str(windows.get("status") or "").lower()
        if not status:
            continue
        request_id = normalize_request_id(str(data["request_id"]))
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        current = latest.get(request_id)
        if current is None or mtime >= current[0]:
            latest[request_id] = (mtime, status)
    return {request_id: status for request_id, (_, status) in latest.items()}


def latest_return_archives(root: Path) -> dict[str, str]:
    latest: dict[str, tuple[float, str]] = {}
    for path in sorted((root / "refs/returns/windows").glob("**/*.zip")):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        request_ids: list[str] = []
        try:
            with zipfile.ZipFile(path) as archive:
                result_name = next(
                    (
                        member
                        for member in archive.namelist()
                        if Path(member.replace("\\", "/")).name
                        in RUNTIME_RESULT_FILENAMES
                    ),
                    None,
                )
                if result_name is not None:
                    data = json.loads(archive.read(result_name).decode("utf-8-sig"))
                    if isinstance(data, dict):
                        if isinstance(data.get("request_id"), str):
                            request_ids.append(normalize_request_id(str(data["request_id"])))
                        for row in data.get("results", []):
                            if isinstance(row, dict) and isinstance(row.get("request_id"), str):
                                request_ids.append(normalize_request_id(str(row["request_id"])))
        except Exception:
            request_ids = []
        if not request_ids:
            name = path.name
            if "_return_windows" not in name:
                continue
            fallback = name.split("__", 1)[-1].rsplit("_return_windows.zip", 1)[0]
            request_ids = [fallback]
        display = display_path(root, path)
        for request_id in request_ids:
            current = latest.get(request_id)
            if current is None or mtime >= current[0]:
                latest[request_id] = (mtime, display)
    return {request_id: display for request_id, (_, display) in latest.items()}


def superseded_request_ids(root: Path) -> set[str]:
    data = read_json(root / "refs/reports/runtime_trace_superseded.json")
    if not isinstance(data, dict):
        return set()
    ids = set()
    for row in data.get("superseded", []):
        if isinstance(row, dict) and isinstance(row.get("request_id"), str):
            ids.add(normalize_request_id(row["request_id"]))
    return ids


def comparison_command(request_id: str) -> str:
    for needle, command in COMPARISON_COMMANDS:
        if needle in request_id:
            return command
    return "python3 scripts/intake_olm_return.py path/to/return.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons"


def acceptance_note(request_id: str) -> str:
    return ACCEPTANCE_NOTES.get(request_id, "")


def hard_lane_context(request_id: str) -> dict[str, str]:
    return dict(HARD_LANE_CONTEXTS.get(request_id, {}))


def profile_priority(profile: str) -> int:
    if profile in PRIORITY_PROFILES:
        return PRIORITY_PROFILES[profile]
    versionless = re.sub(r"-v[0-9]+$", "", profile)
    return PRIORITY_PROFILES.get(versionless, 500)


def row_status(request_id: str, answered: set[str], superseded: set[str], latest_status: str = "") -> str:
    if request_id in INVALID_UNGROUNDED_REQUEST_IDS:
        return "invalid_unverified_values"
    if request_id in superseded:
        return "superseded"
    if request_id in PARTIAL_VISIBLE_OPEN_REQUEST_IDS and (
        latest_status.startswith("answered_partial") or latest_status.startswith("partial_success")
    ):
        return latest_status
    if request_id in answered:
        return "answered"
    if request_id.startswith("windows_ae_"):
        return "diagnostic-pending"
    if latest_status.startswith("failed"):
        return latest_status
    return "pending"


def collect(root: Path, package_dir: Path) -> list[dict[str, Any]]:
    answered = answered_request_ids(root)
    superseded = superseded_request_ids(root)
    latest_rows = latest_result_rows(root)
    latest_comparisons = latest_comparison_paths(root)
    latest_comparison_status = latest_comparison_statuses(root)
    latest_archives = latest_return_archives(root)
    rows: list[dict[str, Any]] = []
    packages = [
        (package, manifest)
        for package in sorted(package_dir.glob("*.zip"))
        if (manifest := package_manifest(package)) is not None
    ]
    for _, manifest in packages:
        for request_id in manifest.get("supersedes", []):
            if isinstance(request_id, str):
                superseded.add(normalize_request_id(request_id))
    for package, manifest in packages:
        profile = str(manifest.get("profile") or "")
        for action in manifest.get("runtime_actions", []):
            if not isinstance(action, dict):
                continue
            request_id = str(action.get("request_id") or "")
            if not request_id:
                continue
            normalized_request_id = normalize_request_id(request_id)
            latest_row = latest_rows.get(request_id) or latest_rows.get(normalized_request_id) or {}
            latest_status = str(latest_row.get("status") or "").lower()
            if not latest_status:
                latest_status = latest_comparison_status.get(request_id) or latest_comparison_status.get(
                    normalized_request_id, ""
                )
            status = row_status(normalized_request_id, answered, superseded, latest_status)
            rows.append(
                {
                    "request_id": request_id,
                    "status": status,
                    "profile": profile,
                    "priority": profile_priority(profile),
                    "package": display_path(root, package),
                    "plugin_area": action.get("plugin_area") or "",
                    "command": action.get("command") or "",
                    "stop_condition": action.get("stop_condition") or "",
                    "intake_command": "python3 scripts/intake_olm_return.py path/to/return.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons",
                    "comparison_command": comparison_command(request_id),
                    "acceptance_note": acceptance_note(request_id),
                    "hard_lane_context": hard_lane_context(request_id),
                    "latest_known_result_status": str(latest_row.get("status") or latest_status or ""),
                    "latest_known_result_summary": str(latest_row.get("summary") or ""),
                    "latest_comparison": latest_comparisons.get(request_id, ""),
                    "latest_return_archive": latest_archives.get(request_id)
                    or latest_archives.get(normalized_request_id, ""),
                }
            )
    newest_by_request: dict[str, dict[str, Any]] = {}
    for row in rows:
        current = newest_by_request.get(row["request_id"])
        if current is None or row["package"] > current["package"]:
            newest_by_request[row["request_id"]] = row
    return sorted(newest_by_request.values(), key=lambda row: (row["status"] != "pending", row["priority"], row["request_id"]))


def short(text: str, limit: int = 180) -> str:
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def render_markdown(report: dict[str, Any]) -> str:
    rows = report["requests"]
    pending = [row for row in rows if row["status"] == "pending"]
    lines = [
        "# Pending Runtime Trace Packages",
        "",
        "This report lists project-local Windows debugger/runtime trace packages and whether each request still needs a return.",
        "",
        f"- Pending: `{len(pending)}`",
        f"- Answered/superseded: `{len(rows) - len(pending)}`",
        "",
        "| Status | Priority | Request | Package | Why needed | Hard lane context | Acceptance note | Latest known result | Latest evidence |",
        "| --- | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        latest = row.get("latest_known_result_status") or "-"
        if row.get("latest_known_result_summary"):
            latest = f"{latest}: {row['latest_known_result_summary']}"
        acceptance = row.get("acceptance_note") or "-"
        hard_lane = row.get("hard_lane_context") or {}
        hard_lane_summary = "-"
        if hard_lane:
            summary = short(hard_lane.get("summary") or "-", 100)
            note = hard_lane.get("note") or ""
            hard_lane_summary = f"{summary} (`{note}`)" if note else summary
        evidence_bits = []
        if row.get("latest_comparison"):
            evidence_bits.append(f"cmp={row['latest_comparison']}")
        if row.get("latest_return_archive"):
            evidence_bits.append(f"zip={row['latest_return_archive']}")
        evidence = " ; ".join(evidence_bits) if evidence_bits else "-"
        lines.append(
            f"| `{row['status']}` | {row['priority']} | `{row['request_id']}` | "
            f"`{row['package']}` | {short(row['plugin_area'] or row['command'])} | "
            f"{hard_lane_summary} | `{acceptance}` | {short(latest, 120)} | {short(evidence, 120)} |"
        )
    if pending:
        lines.extend(["", "## Send First", ""])
        first = pending[0]
        commands = [first["intake_command"]]
        if first["comparison_command"] != first["intake_command"]:
            commands.append(first["comparison_command"])
        hard_lane = first.get("hard_lane_context") or {}
        lines.extend(
            [
                f"- Package: `{first['package']}`",
                f"- Request: `{first['request_id']}`",
                f"- Why: {first['plugin_area']}",
                f"- Hard lane context: {hard_lane.get('summary') or '-'}",
                f"- Hard lane note: `{hard_lane.get('note') or '-'}`",
                f"- Stop condition: {first['stop_condition']}",
                f"- Acceptance note: `{first['acceptance_note'] or '-'}`",
                "",
                "After the Windows return is imported:",
                "",
                "```bash",
                *commands,
                "```",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = repo_root()
    rows = collect(root, args.package_dir)
    report = {
        "kind": "pending_runtime_trace_packages",
        "schema": 1,
        "requests": rows,
    }
    for output in (args.output_json, args.output_md):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"report_json={display_path(root, args.output_json)}")
    print(f"report_md={display_path(root, args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
