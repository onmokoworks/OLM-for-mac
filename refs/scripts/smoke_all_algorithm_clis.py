#!/usr/bin/env python3
"""Run all current AE-free algorithm smoke tests.

Some ports are intentionally still red measurement scaffolds. For those, a
nonzero exit with DIFF output is treated as expected observation, while missing
CLIs/references or command failures without DIFF still fail this aggregate.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Smoke:
    name: str
    command: list[str]
    expected: str = "regression-gate"  # regression-gate | red-measurement | optional-red-measurement


def run(root: Path, smoke: Smoke, timeout: int) -> tuple[bool, str]:
    print(f"\n=== {smoke.name} ({smoke.expected}) ===", flush=True)
    try:
        proc = subprocess.run(
            smoke.command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        print(output, end="" if output.endswith("\n") else "\n")
        return False, f"TIMEOUT after {timeout}s"
    output = proc.stdout or ""
    print(output, end="" if output.endswith("\n") else "\n")

    if smoke.expected in ("green", "regression-gate"):
        if proc.returncode == 0:
            return True, "OK"
        return False, f"FAILED exit={proc.returncode}"

    if smoke.expected == "optional-red-measurement":
        if proc.returncode == 0:
            return True, "OK-now-green"
        if "[DIFF]" in output:
            return True, "DIFF-observed"
        if "missing cv2" in output or "opencv-python" in output:
            return True, "SKIP missing optional cv2"
        return False, f"FAILED exit={proc.returncode} without DIFF"

    if proc.returncode == 0:
        return True, "OK-now-green"
    if "[DIFF]" in output:
        return True, "DIFF-observed"
    return False, f"FAILED exit={proc.returncode} without DIFF"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=("quick", "full", "opencv", "nonhard", "blur-kirakira"),
        default="full",
        help=(
            "quick runs all regression gates; full also runs expected-red diagnostics; "
            "opencv runs optional OpenCV probes; nonhard runs regression gates for the non-hard plug-in set; "
            "blur-kirakira runs the focused OLMBlur/OLMKiraKira handoff gates"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Per-smoke timeout in seconds for the aggregate runner.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    smokes = [
        Smoke("Reference request package", [py, "refs/scripts/package_reference_requests.py", "--only", "kirakira_single_ray_20260606", "--output", "/tmp/olm_reference_requests_smoke.zip"]),
        Smoke("Reference request package handoff", [py, "refs/scripts/smoke_reference_request_package.py"]),
        Smoke("Reference request package verifier", [py, "refs/scripts/verify_reference_request_package.py", "/tmp/olm_reference_requests_smoke.zip"]),
        Smoke("Reference request result verifier", [py, "refs/scripts/smoke_reference_request_result_verifier.py"]),
        Smoke("Reference request importer", [py, "refs/scripts/smoke_import_win_reference.py"]),
        Smoke("Reference import and check runner", [py, "refs/scripts/smoke_import_and_check_win_reference.py"]),
        Smoke("Reference request CLI probe runner", [py, "refs/scripts/smoke_reference_request_cli_probe_runner.py"]),
        Smoke("Reference requests after import runner", [py, "refs/scripts/smoke_reference_requests_after_import_runner.py"]),
        Smoke("Reference requests after import", [py, "refs/scripts/smoke_reference_requests_after_import.py"]),
        Smoke("Reference request status", [py, "refs/scripts/check_reference_request_status.py"]),
        Smoke("Next reference actions", [py, "refs/scripts/smoke_next_reference_actions.py"]),
        Smoke("Runtime trace package", [py, "refs/scripts/smoke_runtime_trace_package.py"]),
        Smoke("Runtime trace return", [py, "refs/scripts/smoke_runtime_trace_return.py"]),
        Smoke("Pending runtime trace package audit", [py, "refs/scripts/smoke_analyze_pending_runtime_trace_packages.py"]),
        Smoke("Runtime trace comparison index", [py, "refs/scripts/smoke_compare_runtime_trace_summary.py"]),
        Smoke("OLMBlur trace comparison", [py, "refs/scripts/smoke_compare_olmblur_trace.py"]),
        Smoke("OLMBlur provenance audit", [py, "refs/scripts/smoke_analyze_olmblur_reference_provenance.py"]),
        Smoke("Software reference canonicalization", [py, "refs/scripts/smoke_analyze_soft_reference_canonicalization.py"]),
        Smoke("KiraKira stage trace comparison", [py, "refs/scripts/smoke_compare_kirakira_stage_trace.py"]),
        Smoke("KiraKira trace box windows", [py, "refs/scripts/smoke_olmkirakira_trace_box_windows.py"]),
        Smoke("KiraKira forward-warp box-input package", [py, "refs/scripts/smoke_package_kirakira_forward_warp_box_input.py"]),
        Smoke("ColorKey Edge trace comparison", [py, "refs/scripts/smoke_compare_colorkey_edge_trace.py"]),
        Smoke("ColorKey Edge provenance audit", [py, "refs/scripts/smoke_analyze_colorkey_edge_reference_provenance.py"]),
        Smoke("OLMDistanceGradation trace comparison", [py, "refs/scripts/smoke_compare_distancegradation_trace.py"]),
        Smoke("OLMDistanceGradation provenance audit", [py, "refs/scripts/smoke_analyze_distancegradation_reference_provenance.py"]),
        Smoke("OLMRadialBlur trace comparison", [py, "refs/scripts/smoke_compare_radialblur_trace.py"]),
        Smoke("OLMRadialBlur reference set audit", [py, "refs/scripts/smoke_audit_radialblur_reference_sets.py"]),
        Smoke("OLMRadialBlur residual clusters", [py, "refs/scripts/smoke_analyze_radialblur_residual_clusters.py"]),
        Smoke("OLMRadialBlur scatter static facts", [py, "refs/scripts/smoke_analyze_radialblur_scatter_static_facts.py"]),
        Smoke("OLMRadialBlur residual witness package", [py, "refs/scripts/smoke_package_radialblur_residual_witness.py"]),
        Smoke("OLMDirectionalBlur trace comparison", [py, "refs/scripts/smoke_compare_directionalblur_trace.py"]),
        Smoke("OLMDirectionalBlur reference set audit", [py, "refs/scripts/smoke_audit_directionalblur_reference_sets.py"]),
        Smoke("OLMDirectionalBlur residual clusters", [py, "refs/scripts/smoke_analyze_directionalblur_residual_clusters.py"]),
        Smoke("OLMDirectionalBlur residual witness package", [py, "refs/scripts/smoke_package_directionalblur_residual_witness.py"]),
        Smoke("Port dashboard", [py, "refs/scripts/smoke_generate_port_dashboard.py"]),
        Smoke("Diff gallery", [py, "refs/scripts/smoke_generate_diff_gallery.py"]),
        Smoke("Current handoff printer", [py, "refs/scripts/smoke_print_current_handoff.py"]),
        Smoke("Next OLM action printer", [py, "refs/scripts/smoke_print_next_olm_action.py"]),
        Smoke("Prepare Windows handoff", [py, "refs/scripts/smoke_prepare_windows_reference_handoff.py"]),
        Smoke("Windows action bundle", [py, "refs/scripts/smoke_windows_action_bundle.py"]),
        Smoke("AE validation result verifier", [py, "refs/scripts/smoke_ae_validation_result_verifier.py"]),
        Smoke("AE pixel validation request", [py, "refs/scripts/smoke_ae_pixel_validation_request.py"]),
        Smoke("AE host return verifier", [py, "refs/scripts/smoke_ae_host_return_verifier.py"]),
        Smoke("OLM return intake", [py, "refs/scripts/smoke_olm_return_intake.py"]),
        Smoke("OLM return candidate lister", [py, "refs/scripts/smoke_list_olm_return_candidates.py"]),
        Smoke("Mac plugin package verifier", [py, "refs/scripts/smoke_mac_plugin_package_verifier.py"]),
        Smoke("Mac plugin MediaCore installer", [py, "refs/scripts/smoke_mac_plugin_installer.py"]),
        Smoke("OLM handoff package verifier", [py, "refs/scripts/smoke_olm_handoff_package_verifier.py"]),
        Smoke("harness", [py, "refs/scripts/smoke_algorithm_harness.py"]),
        Smoke("ColorKeep synthetic", [py, "refs/scripts/smoke_colorkeep_cli.py"]),
        Smoke("OLMBlur build", ["refs/scripts/build_olmblur_cli.sh"]),
        Smoke("OLMBlur", [py, "refs/scripts/smoke_olmblur_cli.py"]),
        Smoke("OLMColorKey RGB", [py, "refs/scripts/smoke_olmcolorkey_cli.py"]),
        Smoke("OLMColorKey Edge Thin", [py, "refs/scripts/smoke_olmcolorkey_extended_cli.py"]),
        Smoke("OLMColorKey Edge Blur", [py, "refs/scripts/smoke_olmcolorkey_edgeblur_cli.py"]),
        Smoke("OLMColorKey C++", [py, "refs/scripts/smoke_olmcolorkey_cpp_cli.py"]),
        Smoke("OLMColorKey C++ Edge Blur", [py, "refs/scripts/smoke_olmcolorkey_cpp_edgeblur_cli.py"]),
        Smoke("OLMColorKey Rust", [py, "refs/scripts/smoke_olmcolorkey_rust_cli.py"]),
        Smoke("OLMColorKey Replace/color-space request", [py, "refs/scripts/smoke_olmcolorkey_replace_colorspace_request_cli.py"]),
        Smoke("OLMToonDilate", [py, "refs/scripts/smoke_olmtoondilate_cli.py"]),
        Smoke("OLMToonDilate C++ build", ["refs/scripts/build_olmtoondilate_cli.sh"]),
        Smoke("OLMToonDilate C++", [py, "refs/scripts/smoke_olmtoondilate_cpp_cli.py"]),
        Smoke("OLMDistanceGradation", [py, "refs/scripts/smoke_olmdistancegradation_cli.py"]),
        Smoke("OLMDistanceGradation extended", [py, "refs/scripts/smoke_olmdistancegradation_extended_cli.py"]),
        Smoke("OLMDistanceGradation Blur", [py, "refs/scripts/smoke_olmdistancegradation_blur_cli.py"]),
        Smoke("OLMSmoother build", ["refs/scripts/build_olmsmoother_cli.sh"]),
        Smoke("OLMSmoother", [py, "refs/scripts/smoke_olmsmoother_cli.py"], "red-measurement"),
        Smoke("OLMSmoother2 build", ["refs/scripts/build_olmsmoother2_cli.sh"]),
        Smoke("OLMSmoother2 v1 compatibility", [py, "refs/scripts/smoke_olmsmoother2_v1_compat_cli.py"]),
        Smoke("OLMSmoother2 key paths", [py, "refs/scripts/smoke_olmsmoother2_keypaths_cli.py"]),
        Smoke("OLMSmoother2 Gamma Colors", [py, "refs/scripts/smoke_olmsmoother2_gamma_cli.py"]),
        Smoke("OLMSmoother2", [py, "refs/scripts/smoke_olmsmoother2_cli.py"], "red-measurement"),
        Smoke("OLMSmoother2 idx0 probe", [py, "refs/scripts/smoke_olmsmoother2_idx0_probe_cli.py"], "red-measurement"),
        Smoke("OLMSmoother2 Plane Split probe", [py, "refs/scripts/smoke_olmsmoother2_plane_split_probe_cli.py"], "red-measurement"),
        Smoke("OLMSmoother2 no-key grid request", [py, "refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py"]),
        Smoke("OLMRadialBlur tiny Rotation", [py, "refs/scripts/smoke_olmradialblur_tiny_rotation_cli.py"]),
        Smoke("OLMRadialBlur C++ tiny Rotation", [py, "refs/scripts/smoke_olmradialblur_cpp_tiny_rotation_cli.py"]),
        Smoke("OLMRadialBlur Rotation", [py, "refs/scripts/smoke_olmradialblur_rotation_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Rotation", [py, "refs/scripts/smoke_olmradialblur_cpp_rotation_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur Zoom", [py, "refs/scripts/smoke_olmradialblur_zoom_cli.py"]),
        Smoke("OLMRadialBlur Zoom Offset", [py, "refs/scripts/smoke_olmradialblur_zoom_offset_cli.py"]),
        Smoke("OLMRadialBlur C++ Zoom Offset", [py, "refs/scripts/smoke_olmradialblur_cpp_cli.py"]),
        Smoke("OLMRadialBlur C++ Zoom", [py, "refs/scripts/smoke_olmradialblur_cpp_zoom_cli.py"]),
        Smoke("OLMRadialBlur Inner", [py, "refs/scripts/smoke_olmradialblur_inner_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Scatter Stats", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_scatter_stats_cli.py"]),
        Smoke("OLMRadialBlur C++ Inner Small Scatter Stats", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_small_scatter_stats_cli.py"]),
        Smoke("OLMRadialBlur C++ Inner Alpha Mode probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_alpha_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Source Scatter Prepass probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_source_scatter_prepass_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Prepass Mode probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_prepass_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Prepass Overwrite probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_prepass_overwrite_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Prepass Factor probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_prepass_factor_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Edge Fade Factor probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_edgefade_factor_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Edge Fade Wrap probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_edgefade_wrap_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Edge Fade Seed probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_edgefade_seed_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner AEX Split probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_aex_split_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Polar Sample probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_polar_sample_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Scatter RGB probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_scatter_rgb_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Source Scale probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_source_scale_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Dynamic Offset probe", [py, "refs/scripts/smoke_olmradialblur_cpp_dynamic_offset_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Prepass Dynamic Offset probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_prepass_dynamic_offset_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Final Norm probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_final_norm_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Seed Alpha probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_seed_alpha_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Span Scale probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_span_scale_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Param10 Plane probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_param10_plane_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Conditional Seed probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_conditional_seed_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Wrap probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_wrap_probe_cli.py"], "red-measurement"),
        Smoke("OLMRadialBlur C++ Inner Polar Valid probe", [py, "refs/scripts/smoke_olmradialblur_cpp_inner_polar_valid_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur", [py, "refs/scripts/smoke_olmdirectionalblur_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur Back probe", [py, "refs/scripts/smoke_olmdirectionalblur_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Back probe", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Direct Map", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_direct_map_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Rotateback Denom Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_rotateback_denom_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Exact Scatter", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_exact_scatter_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Exact Rowdriver", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_exact_rowdriver_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Pad Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Prepass Full Choreo", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_prepass_full_choreo_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Half-height", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_halfheight_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Float Center", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_float_center_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Component Tail", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_component_tail_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Global Tail", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_global_tail_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX No Tail", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_no_tail_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Preserve Invalid Input", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_preserve_invalid_input_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Binary Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_binary_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Straight Source RGB", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_straight_source_rgb_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Float Math", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_float_math_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Trunc Output", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_trunc_output_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Truncated Span", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_truncated_span_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Row Init probe", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_row_init_probe_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated AEX Pad", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_aex_pad_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Alpha Sum", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_alpha_sum_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Front Strength Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_front_strength_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Rowdriver Prepass", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_rowdriver_prepass_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Gather", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_gather_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map Alpha Coeff", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_alpha_coeff_cli.py"], "red-measurement"),
        Smoke("OLMDirectionalBlur C++ Rotated Map Preserve Alpha", [py, "refs/scripts/smoke_olmdirectionalblur_cpp_rotated_map_preserve_alpha_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira", [py, "refs/scripts/smoke_olmkirakira_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++", [py, "refs/scripts/smoke_olmkirakira_cpp_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ remapBilinear f32 diagnostic", [py, "refs/scripts/smoke_olmkirakira_cpp_remap_bilinear_f32_diag.py"]),
        Smoke("OLMKiraKira C++ WarpAffine map f32 diagnostic", [py, "refs/scripts/smoke_olmkirakira_cpp_warpaffine_map_f32_diag.py"]),
        Smoke("OLMKiraKira C++ WarpAffine remap f32 diagnostic", [py, "refs/scripts/smoke_olmkirakira_cpp_warpaffine_remap_f32_diag.py"]),
        Smoke("OLMKiraKira trace-json", [py, "refs/scripts/smoke_olmkirakira_trace_json.py"]),
        Smoke("OLMKiraKira OpenCV two-temp probe", [py, "refs/scripts/smoke_olmkirakira_opencv_two_temp_probe_cli.py"], "optional-red-measurement"),
        Smoke("OLMKiraKira OpenCV two-temp alias probe", [py, "refs/scripts/smoke_olmkirakira_opencv_two_temp_alias_probe_cli.py"], "optional-red-measurement"),
        Smoke("OLMKiraKira Brightness probe", [py, "refs/scripts/smoke_olmkirakira_brightness_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira Rotate probe", [py, "refs/scripts/smoke_olmkirakira_rotate_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Filter probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_filter_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Border probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_border_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Rotate Size probe", [py, "refs/scripts/smoke_olmkirakira_cpp_rotate_size_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Warp Mode probe", [py, "refs/scripts/smoke_olmkirakira_cpp_warp_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ AEX getRotationMatrix2D probe", [py, "refs/scripts/smoke_olmkirakira_cpp_aex_getrot_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Direct Rotate-Back probe", [py, "refs/scripts/smoke_olmkirakira_cpp_direct_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Two-Temp No Fastpath probe", [py, "refs/scripts/smoke_olmkirakira_cpp_two_temp_no_fastpath_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Two-Temp Direct Back probe", [py, "refs/scripts/smoke_olmkirakira_cpp_two_temp_direct_back_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Strength Fastpath probe", [py, "refs/scripts/smoke_olmkirakira_cpp_strength_fastpath_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Crop Mode probe", [py, "refs/scripts/smoke_olmkirakira_cpp_crop_mode_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Glow Normalize probe", [py, "refs/scripts/smoke_olmkirakira_cpp_glow_normalize_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Aggregation probe", [py, "refs/scripts/smoke_olmkirakira_cpp_aggregation_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Anchor probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_anchor_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Normalize probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_normalize_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Output Depth probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_output_depth_probe_cli.py"], "red-measurement"),
        Smoke("OLMKiraKira C++ Box Size probe", [py, "refs/scripts/smoke_olmkirakira_cpp_box_size_probe_cli.py"], "red-measurement"),
    ]
    if args.profile == "quick":
        smokes = [smoke for smoke in smokes if smoke.expected in ("green", "regression-gate")]
    elif args.profile == "nonhard":
        nonhard_names = (
            "ColorKeep",
            "OLMBlur",
            "OLMColorKey",
            "OLMToonDilate",
            "OLMDistanceGradation",
            "OLMSmoother2",
            "AE pixel validation request",
            "Software reference canonicalization",
            "Pending runtime trace package audit",
        )
        smokes = [
            smoke
            for smoke in smokes
            if smoke.expected in ("green", "regression-gate") and any(name in smoke.name for name in nonhard_names)
        ]
    elif args.profile == "opencv":
        smokes = [smoke for smoke in smokes if smoke.expected == "optional-red-measurement"]
    elif args.profile == "blur-kirakira":
        focus_names = {
            "Runtime trace package",
            "Runtime trace comparison index",
            "OLMBlur trace comparison",
            "KiraKira stage trace comparison",
            "Next OLM action printer",
            "Windows action bundle",
            "OLMBlur build",
            "OLMBlur",
            "OLMKiraKira C++ remapBilinear f32 diagnostic",
            "OLMKiraKira C++ WarpAffine map f32 diagnostic",
            "OLMKiraKira C++ WarpAffine remap f32 diagnostic",
            "OLMKiraKira trace-json",
        }
        smokes = [smoke for smoke in smokes if smoke.name in focus_names]

    results: list[tuple[str, bool, str]] = []
    print(f"running smoke profile: {args.profile} ({len(smokes)} checks)", flush=True)
    for smoke in smokes:
        ok, status = run(root, smoke, args.timeout)
        results.append((smoke.name, ok, status))

    print("\n=== summary ===")
    for name, ok, status in results:
        mark = "OK" if ok else "FAIL"
        print(f"{mark:4} {name}: {status}")

    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
