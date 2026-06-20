#!/usr/bin/env python3
"""Package debugger/runtime trace requests for a Windows helper machine."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


TRACE_NOTE = Path("notes/WINDOWS_RUNTIME_TRACE_REQUESTS.md")
DEFAULT_REQUESTS = [
    Path("refs/reference_requests/radialblur_inner_20260605.json"),
    Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
    Path("refs/reference_requests/kirakira_strength0_brightness_20260614.json"),
]
SUPPORTING_NOTES = [
    Path("notes/OLMRadialBlur_ASM_FACTS.md"),
    Path("notes/OLMKiraKira_ASM_FACTS.md"),
    Path("notes/PROGRESS_MATRIX.md"),
]
KIRAKIRA_STAGE_SUPPORTING_NOTES = [
    Path("notes/IR_OLMKiraKira.md"),
    Path("notes/OLMKiraKira_ASM_FACTS.md"),
    Path("notes/OLMKiraKira_SCALAR_AGGREGATION_AUDIT.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("refs/reports/runtime_trace_summary.md"),
]
COLORKEY_SUPPORTING_NOTES = [
    Path("notes/OLMColorKey_ASM_FACTS.md"),
    Path("notes/IR_OLMColorKey_Edge.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
]
OLMBLUR_SUPPORTING_NOTES = [
    Path("notes/IR_OLMBlur.md"),
    Path("notes/CONFORMANCE_LEDGER.md"),
    Path("notes/AE_HOST_VALIDATION_20260618.md"),
    Path("notes/PORTING_BOARD.md"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output zip. Defaults to refs/runtime_trace_packages/olm_runtime_trace_requests_YYYYMMDD_HHMMSS.zip.",
    )
    parser.add_argument(
        "--profile",
        choices=[
            "hard-paths",
            "colorkey-edge",
            "olmblur-repeat-threshold",
            "kirakira-stage-values",
            "smoother2-no-key-grid",
            "smoother2-legacy-key-gamma",
            "distancegradation-field-prep",
        ],
        default="hard-paths",
        help="Trace request set to package.",
    )
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def next_actions_snapshot(root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(root / "refs" / "scripts" / "next_reference_actions.py"), "--json"],
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise ValueError("next_reference_actions.py did not return an object")
    return data


def runtime_actions(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    actions = snapshot.get("covered_actions")
    if not isinstance(actions, list):
        return []
    return [
        action
        for action in actions
        if isinstance(action, dict) and str(action.get("mode", "")).endswith("trace")
    ]


def colorkey_edge_action() -> dict[str, Any]:
    return {
        "request_id": "colorkey_edge_runtime_trace_20260619",
        "plugin_area": "OLMColorKey Edge Thin/Edge Blur runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMColorKey case_0005/case_0006 Edge Thin erode witnesses "
            "and case_0008/case_0009 Edge Blur witnesses around FUN_1800094b0/"
            "FUN_180008c90/FUN_180008320/FUN_1800085b0. Record ctx fields plus "
            "local matte/distance/weight/apply samples at the listed coordinates. "
            "Compare against Mac baseline logs in "
            "refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/."
        ),
        "stop_condition": (
            "Return ctx+0x28/+0x2c/+0x40/+0x44/+0x48 and sample values that "
            "distinguish manifest/ctx scaling, border seed ownership, <= vs < "
            "erode/dilate shell, and Edge Blur apply semantics."
        ),
    }


def olmblur_repeat_threshold_action() -> dict[str, Any]:
    return {
        "request_id": "olmblur_repeat_threshold_runtime_trace_20260619",
        "plugin_area": "OLMBlur repeat-10 threshold/runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMBlur normalized Software cases case_0006 and case_0007 at "
            "the listed residual pixels. Record post-blur/pre-writeback float "
            "RGB, final writeback operation, and the Legacy helper border/all_same "
            "state needed to distinguish accumulation/writeback ordering. Compare "
            "against Mac baseline logs in "
            "refs/reports/olmblur_trace_baseline_20260619_030633_mac/."
        ),
        "stop_condition": (
            "Return enough values to decide why case_0006 (498,940) writes 185 "
            "instead of the CLI's 186 and why case_0007 keeps two red pixels at "
            "251 plus the top-left border at 0."
        ),
    }


def kirakira_stage_values_action() -> dict[str, Any]:
    return {
        "request_id": "kirakira_fun_181150790_stage_values_20260620",
        "plugin_area": "OLMKiraKira FUN_181150790 stage-value runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMKiraKira single-ray Software case "
            "kk_vertical_len50_brightness1_strength100 through FUN_181150790. "
            "Record both warpAffine calls' Mat headers, dsize, affine matrix "
            "values, ROI/copy rectangles, selected boxFilter branch, and float "
            "witness values before/after center-copy, forward warp, each of the "
            "three horizontal boxFilter passes, rotate-back, final center-copy, "
            "FUN_18114fd90 aggregation, and merge-mode-1 compose."
        ),
        "stop_condition": (
            "Return enough values to decide whether the remaining KiraKira "
            "residual is caused by Windows AVX2 boxFilter numeric behavior, "
            "warpAffine Mat/ROI placement, final centered copy, ray aggregation, "
            "or merge-mode compose."
        ),
    }


def smoother2_no_key_grid_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_no_key_grid_runtime_trace_20260619",
        "plugin_area": "OLMSmoother2 no-key grid runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 case sm2_no_key_s100_r3 at the listed residual "
            "pixels. Record FUN_18000c280 switch index, cardinal dispatcher "
            "descriptors/keys, the d520/dbd0/d230/d800 scan helper returns that "
            "feed those keys, the FUN_180010550 p1/p2/p3 index inputs plus "
            "idx=7 context values for each "
            "scan helper, every FUN_1800104d0 append src/rgba/weight/count, "
            "FUN_18000ab00 composite inputs/output, FUN_18000b120 output, and "
            "FUN_1800036e0 final sRGB/writeback values. Compare against the Mac "
            "baseline logs in refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/."
        ),
        "stop_condition": (
            "Return enough values to decide whether the Mac port is missing a "
            "0.2 duplicate sample, using the wrong cardinal span formula, or "
            "matching the polygon but differing in final color/writeback. If the "
            "append sequence differs, the scan helper return values should point "
            "to the first mismatching descriptor/key."
        ),
    }


def smoother2_legacy_key_gamma_action() -> dict[str, Any]:
    return {
        "request_id": "olmsmoother2_legacy_key_gamma_runtime_trace_20260620",
        "plugin_area": "OLMSmoother2 legacy key/gamma runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMSmoother2 legacy key/gamma AE-exact failures at the listed "
            "top-edge witness pixels. Focus on case_0001, case_0002, case_0003, "
            "and case_0010. Record parameter struct values, Color Key active/"
            "invert decisions, gamma/sRGB decode/encode decisions, class-plane "
            "bytes, pre/post FUN_1800036e0 writeback values, and final RGBA. "
            "Compare against the AE-host failure report in "
            "refs/reports/ae_host_validation_20260620_1425/"
            "ae_pixel_olmsmoother2_legacy_20260619/reports/."
        ),
        "stop_condition": (
            "Return enough values to decide whether the 0/7 legacy failures are "
            "caused by Color Key mask polarity, premultiply/unpremultiply, gamma "
            "setup, class-plane generation, or final writeback. Do not continue "
            "no-key grid tuning from this package."
        ),
    }


def distancegradation_field_prep_action() -> dict[str, Any]:
    return {
        "request_id": "olmdistancegradation_field_prep_runtime_trace_20260619",
        "plugin_area": "OLMDistanceGradation distance field / Constant interpolation runtime trace",
        "mode": "external-trace",
        "command": (
            "Trace OLMDistanceGradation cases 0020, 0022, and 0029 around the "
            "distance-field construction and FUN_181170870 compose path. Record "
            "the field Mat/AE-world RGBA values consumed by compose, the "
            "Constant-mode binarization point, blur input/output field values, "
            "OpenCV/helper distanceTransform args, min/max normalization facts, "
            "GaussianBlur args for case_0029, and final compose values at the "
            "listed witness pixels."
        ),
        "stop_condition": (
            "Return enough values to decide whether Constant mode binarizes the "
            "field upstream for all non-blur cases, only background cases, or "
            "only blur cases, and which channel(s) carry the normalized distance "
            "field into FUN_181170870."
        ),
    }


def selected_actions(snapshot: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    if profile == "colorkey-edge":
        return [colorkey_edge_action()]
    if profile == "olmblur-repeat-threshold":
        return [olmblur_repeat_threshold_action()]
    if profile == "kirakira-stage-values":
        return [kirakira_stage_values_action()]
    if profile == "smoother2-no-key-grid":
        return [smoother2_no_key_grid_action()]
    if profile == "smoother2-legacy-key-gamma":
        return [smoother2_legacy_key_gamma_action()]
    if profile == "distancegradation-field-prep":
        return [distancegradation_field_prep_action()]
    return runtime_actions(snapshot)


def package_manifest(root: Path, snapshot: dict[str, Any], profile: str) -> dict[str, Any]:
    actions = selected_actions(snapshot, profile)
    return {
        "kind": "olm_runtime_trace_request_package",
        "schema": 1,
        "profile": profile,
        "packaged_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "repo_root_name": root.name,
        "runtime_actions": [
            {
                "request_id": action.get("request_id"),
                "plugin_area": action.get("plugin_area"),
                "mode": action.get("mode"),
                "command": action.get("command"),
                "stop_condition": action.get("stop_condition"),
            }
            for action in actions
        ],
        "entrypoint": str(TRACE_NOTE),
    }


def build_readme(manifest: dict[str, Any]) -> str:
    actions = manifest["runtime_actions"]
    lines = [
        "# OLM Runtime Trace Request Package",
        "",
        "This zip is for the Windows machine / Windows Codex session.",
        "It asks for debugger or exact-library primitive facts, not another PNG render batch.",
        "",
        f"Entrypoint: `{TRACE_NOTE}`",
        "",
        "Priority order:",
        "",
    ]
    for index, action in enumerate(actions, start=1):
        lines.extend(
            [
                f"{index}. `{action['request_id']}`",
                f"   - Area: {action['plugin_area']}",
                f"   - Action: {action['command']}",
                f"   - Stop: {action['stop_condition']}",
                "",
            ]
        )
    lines.extend(
        [
            "Return exactly the trace values / primitive fact requested in the note.",
            "You can fill `RETURN_RUNTIME_TRACE_TEMPLATE.json` and zip it back as the return artifact.",
            "Do not tune implementation code from PNG residuals while answering this package.",
            "",
        ]
    )
    return "\n".join(lines)


def build_return_template(manifest: dict[str, Any]) -> dict[str, Any]:
    result_templates = []
    for action in manifest["runtime_actions"]:
        request_id = action.get("request_id")
        if request_id == "radialblur_inner_runtime_trace_20260618":
            observations: dict[str, Any] = {
                "case_id": "rb_inner_only_strength_small",
                "module_base": "0x...",
                "r8d_at_0x26e5": None,
                "rsp_0x138_dword_at_0x26e5": "0x...",
                "edx_at_0x26e5": None,
                "r9d_at_0x26e5": None,
                "source_alpha_raw_dword_rsp_0x48": "0x...",
                "span_gate_raw_dword_rsp_0x28": "0x...",
                "inner_offset_mode_dword_rcx_0x2c": None,
                "inner_base_span_dword_rcx_0x3a9ec": None,
                "ebp_after_0x1d18": None,
                "r14d_after_0x1d18": None,
                "eax_after_0x1d43_optional": None,
                "xmm7_after_0x1d43_optional": None,
            }
            summary = "Fill with the observed RadialBlur inner helper registers/stack values."
        elif request_id == "kirakira_opencv455_primitive_fact_20260618":
            observations = {
                "fun_181281260_first_boxfilter_branch": "FUN_1812e39d0 | FUN_1812d7c40 | FUN_181280fa0 | other",
                "branch_condition": "feature 0xb | feature 6 | neither | unknown",
                "filter_constructors": "RowSum<float,double>/ColumnSum<double,float> equivalent | SIMD equivalent | other",
                "microprobe_opencv_version": "4.5.5 | not run",
                "microprobe_mean_diff_case_0001_optional": None,
                "microprobe_mean_diff_case_0002_optional": None,
                "microprobe_mean_diff_case_0003_optional": None,
            }
            summary = "Fill with the observed KiraKira OpenCV 4.5.5 primitive branch/fact."
        elif request_id == "colorkey_edge_runtime_trace_20260619":
            observations = {
                "effect": "OLM Color Key",
                "module_base": "0x...",
                "fun_1800094b0_hit": True,
                "ctx_0x28_edge_thin_direction_or_mode": None,
                "ctx_0x2c_edge_blur_direction": None,
                "ctx_0x40_edge_amount_raw_float": "0x...",
                "ctx_0x44_distance_type": None,
                "ctx_0x48_edge_blur_amount_raw_float": "0x...",
                "edge_thin_erode_cases": [
                    {
                        "case_id": "case_0005",
                        "witness": {"x": 34, "y": 0},
                        "reason": "top-edge erode alpha polarity; current C++ transparent, Windows opaque",
                        "initial_matched_or_keep_matte": None,
                        "distance_seed_input": None,
                        "distance_after_transform": None,
                        "ctx_amount_decoded_float": None,
                        "branch_condition_observed": "dist <= amount | dist < amount | dist > adjusted_limit | other",
                        "edge_thin_output_matte_or_alpha": None,
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0006",
                        "witness": {"x": 34, "y": 0},
                        "reason": "paired color-keep polarity; current C++ opaque, Windows transparent",
                        "initial_matched_or_keep_matte": None,
                        "distance_seed_input": None,
                        "distance_after_transform": None,
                        "ctx_amount_decoded_float": None,
                        "branch_condition_observed": "dist <= amount | dist < amount | dist > adjusted_limit | other",
                        "edge_thin_output_matte_or_alpha": None,
                        "final_output_rgba": [None, None, None, None],
                    },
                ],
                "edge_blur_samples": [
                    {
                        "case_id": "case_0008",
                        "x": 1111,
                        "y": 628,
                        "reason": "RGB/alpha contour residual; Python max-diff neighborhood",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0008",
                        "x": 464,
                        "y": 0,
                        "reason": "top-edge alpha residual; C++ max-diff neighborhood",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0009",
                        "x": 1116,
                        "y": 136,
                        "reason": "known high-diff neighborhood from normalized Software case_0009",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_thin_output_value": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                    {
                        "case_id": "case_0009",
                        "x": 1699,
                        "y": 7,
                        "reason": "top-edge/background neighborhood sanity sample",
                        "initial_keep_or_match_value": None,
                        "boundary_seed_after_FUN_180008c90": None,
                        "distance_after_transform": None,
                        "edge_thin_output_value": None,
                        "edge_blur_weight": None,
                        "edge_blur_apply_source_rgba": [None, None, None, None],
                        "final_output_rgba": [None, None, None, None],
                    },
                ],
                "positive_edge_thin_copy_condition_observed": "dist <= amount | dist < amount | other",
                "edge_blur_distance_dispatch_observed": "1->FUN_180006e20,2->FUN_180005d60,3->FUN_180007ec0 | other",
                "edge_blur_apply_formula_summary": "",
            }
            summary = "Fill with ColorKey Edge Thin/Edge Blur ctx and sample trace values."
        elif request_id == "olmblur_repeat_threshold_runtime_trace_20260619":
            observations = {
                "effect": "OLM Blur",
                "module_base": "0x...",
                "cases": [
                    {
                        "case_id": "case_0006",
                        "legacy": 0,
                        "repeat": 10,
                        "bias_direction": 1,
                        "residual_pixels": [
                            {
                                "x": 498,
                                "y": 940,
                                "windows_reference_rgba": [185, 0, 0, 255],
                                "mac_cli_candidate_rgba": [186, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": ["0x1.73p+7", "0x1.44a3c6p-4", "0x1.44a3c6p-4"],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "aex_writeback_operation": "floorf(value + 0.5) | cvt/trunc | other",
                                "aex_final_rgba": [None, None, None, None],
                            }
                        ],
                        "radius_path_fact": "confirm decay is powf but per-iteration radius uses pow(double,double) and float sigma",
                        "accumulation_order_notes": "",
                    },
                    {
                        "case_id": "case_0007",
                        "legacy": 1,
                        "repeat": 10,
                        "bias_direction": 1,
                        "residual_pixels": [
                            {
                                "x": 0,
                                "y": 0,
                                "windows_reference_rgba": [0, 0, 0, 255],
                                "mac_cli_candidate_rgba": [1, 1, 1, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                            {
                                "x": 488,
                                "y": 941,
                                "windows_reference_rgba": [251, 0, 0, 255],
                                "mac_cli_candidate_rgba": [250, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                            {
                                "x": 488,
                                "y": 942,
                                "windows_reference_rgba": [251, 0, 0, 255],
                                "mac_cli_candidate_rgba": [250, 0, 0, 255],
                                "cli_pre_writeback_rgb_hex": [None, None, None],
                                "aex_pre_writeback_rgb_hex": [None, None, None],
                                "legacy_border_sample_included": None,
                                "legacy_all_same_state": None,
                                "aex_final_rgba": [None, None, None, None],
                            },
                        ],
                        "negative_probes_to_avoid": [
                            "initializing all_same from -1 worsened case_0007 to max=16 / 21px",
                            "including border coordinate 0 worsened case_0007 to max=15 / 5412px",
                        ],
                    },
                ],
            }
            summary = "Fill with OLMBlur residual pre-writeback/writeback and Legacy border trace facts."
        elif request_id == "kirakira_fun_181150790_stage_values_20260620":
            observations = {
                "effect": "OLM Kira Kira",
                "module_base": "0x...",
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "reference_case_path_hint": (
                    "refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira/"
                    "kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png"
                ),
                "known_facts_to_keep": {
                    "first_boxfilter_branch": "FUN_1812e39d0 / AVX2",
                    "boxfilter_args": {
                        "ksize": [50, 1],
                        "anchor": [-1, -1],
                        "normalize": True,
                        "border_type": 4,
                    },
                    "warpaffine_flags": "INTER_LINEAR, no WARP_INVERSE_MAP, BORDER_CONSTANT zero",
                    "temp_extent_rule": "truncate after +4.0 then clamp to at least source size + 4",
                },
                "fun_181150790_entry": {
                    "src_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp1_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "tmp2_mat": {"rows": None, "cols": None, "type": None, "step": None, "data": "0x..."},
                    "ray_length": None,
                    "angle_degrees_or_radians": None,
                    "affine_forward_matrix": [None, None, None, None, None, None],
                    "affine_back_matrix": [None, None, None, None, None, None],
                    "forward_dsize": [None, None],
                    "back_dsize": [None, None],
                    "source_roi_rect": [None, None, None, None],
                    "final_copy_rect": [None, None, None, None],
                },
                "witness_pixels": [
                    {
                        "label": "source_seed_center",
                        "xy": [960, 540],
                        "source_xy": [960, 540],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [960, 540],
                        "before_center_copy_float": None,
                        "after_center_copy_tmp1_float": None,
                        "after_forward_warp_tmp2_float": None,
                        "after_box_1_float": None,
                        "after_box_2_float": None,
                        "after_box_3_float": None,
                        "after_rotate_back_tmp1_float": None,
                        "after_final_center_copy_ray_float": None,
                    },
                    {
                        "label": "vertical_ray_peak_or_first_nonzero",
                        "xy": [960, 490],
                        "source_xy": [960, 490],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [960, 490],
                        "before_center_copy_float": None,
                        "after_center_copy_tmp1_float": None,
                        "after_forward_warp_tmp2_float": None,
                        "after_box_1_float": None,
                        "after_box_2_float": None,
                        "after_box_3_float": None,
                        "after_rotate_back_tmp1_float": None,
                        "after_final_center_copy_ray_float": None,
                    },
                    {
                        "label": "current_residual_hotspot_optional",
                        "xy": [None, None],
                        "source_xy": [None, None],
                        "tmp1_xy": [None, None],
                        "tmp2_xy": [None, None],
                        "ray_xy": [None, None],
                        "windows_reference_rgba": [None, None, None, None],
                        "mac_cli_candidate_rgba": [None, None, None, None],
                        "ray_float_before_aggregation": None,
                        "aggregation_output_float_rgba": [None, None, None, None],
                        "final_merge_rgba": [None, None, None, None],
                    },
                ],
                "boxfilter_calls": [
                    {
                        "index": 1,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                    {
                        "index": 2,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                    {
                        "index": 3,
                        "selected_branch": "FUN_1812e39d0 | other",
                        "src_mat_header": {},
                        "dst_mat_header": {},
                        "sample_before_after": [],
                    },
                ],
                "aggregation_and_compose": {
                    "fun_18114fd90_inputs": {
                        "brightness": None,
                        "strength": None,
                        "ray_scalar_or_gain": None,
                    },
                    "fun_18114fd90_sample_outputs": [],
                    "merge_mode_1_sample_inputs_outputs": [],
                },
            }
            summary = "Fill with KiraKira FUN_181150790 stage values and aggregation/compose witnesses."
        elif request_id == "olmsmoother2_no_key_grid_runtime_trace_20260619":
            observations = {
                "effect": "OLM Smoother v2",
                "module_base": "0x...",
                "case_id": "sm2_no_key_s100_r3",
                "reference_case_path_hint": (
                    "refs/win_references/20260605_extra/OLMSmoother2/"
                    "smoother2_no_key_grid_20260606__software__fr24__sm2_no_key_s100_r3.png"
                ),
                "pixels": [
                    {
                        "x": 211,
                        "y": 139,
                        "mac_cli_idx": "0x10",
                        "mac_cli_candidate_rgba": [203, 66, 66, 255],
                        "windows_reference_rgba": [212, 68, 68, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x1e",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [210, 139], "weight": 0.40000001},
                                {"src": [210, 139], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 215,
                        "y": 145,
                        "mac_cli_idx": "0x08",
                        "mac_cli_candidate_rgba": [54, 34, 34, 255],
                        "windows_reference_rgba": [46, 32, 32, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x14",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [216, 145], "weight": 0.32000002},
                                {"src": [216, 145], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 991,
                        "y": 139,
                        "mac_cli_idx": "0x10",
                        "mac_cli_candidate_rgba": [212, 194, 57, 255],
                        "windows_reference_rgba": [221, 202, 59, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x1e",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [990, 139], "weight": 0.40000001},
                                {"src": [990, 139], "weight": 0.2},
                            ],
                        },
                    },
                    {
                        "x": 995,
                        "y": 145,
                        "mac_cli_idx": "0x08",
                        "mac_cli_candidate_rgba": [56, 53, 33, 255],
                        "windows_reference_rgba": [47, 45, 32, 255],
                        "expected_mac_trace": {
                            "cardinal3_key": "0x14",
                            "cardinal12_key": "0x29",
                            "appends": [
                                {"src": [996, 145], "weight": 0.32000002},
                                {"src": [996, 145], "weight": 0.2},
                            ],
                        },
                    },
                ],
                "requested_for_each_pixel": {
                    "fun_18000c280_switch_idx": None,
                    "cardinal3_descriptor_and_key": None,
                    "cardinal12_descriptor_and_key": None,
                    "scan_helpers": {
                        "FUN_180010820": {
                            "d520_return_xy_class": [None, None, None],
                            "d520_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "dbd0_return_xy_class": [None, None, None],
                            "dbd0_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "FUN_1800101e0_key": None,
                        },
                        "FUN_1800105f0": {
                            "d230_return_xy_class": [None, None, None],
                            "d230_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "d800_return_xy_class": [None, None, None],
                            "d800_fun_180010550_inputs_p1_p2_p3_p4_p5": [None, None, None, None, None],
                            "FUN_18000fbf0_key": None,
                        },
                    },
                    "append_sequence": [
                        {
                            "src_xy": [None, None],
                            "sample_rgba_float_hex": [None, None, None, None],
                            "weight_float_hex": None,
                            "count_before": None,
                        }
                    ],
                    "composite": {
                        "center_rgba_float_hex": [None, None, None, None],
                        "total_weight_hex": None,
                        "output_before_b120_hex": [None, None, None, None],
                    },
                    "post_b120_rgba_float_hex": [None, None, None, None],
                    "writeback": {
                        "pre_srgb_rgb_hex": [None, None, None],
                        "post_srgb_rgb_hex": [None, None, None],
                        "final_rgba_8bit": [None, None, None, None],
                    },
                },
            }
            summary = "Fill with OLMSmoother2 no-key grid per-pixel polygon/composite/writeback trace facts."
        elif request_id == "olmsmoother2_legacy_key_gamma_runtime_trace_20260620":
            observations = {
                "effect": "OLM Smoother v2",
                "module_base": "0x...",
                "reference_report_hint": (
                    "refs/reports/ae_host_validation_20260620_1425/"
                    "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
                ),
                "cases": [
                    {
                        "case_id": "case_0001",
                        "reason": (
                            "Color Key disabled; alpha matches at witnesses but RGB is much lower "
                            "in the Mac candidate, so writeback/premultiply/gamma ownership is suspect."
                        ),
                        "expected_params": {
                            "enable_color_key": 0,
                            "invert_color_key": 0,
                            "smoothness": 100,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [25, 25, 25, 75], "windows_reference_rgba": [75, 75, 75, 75]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [44, 44, 44, 106], "windows_reference_rgba": [106, 106, 106, 106]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [25, 25, 25, 75], "windows_reference_rgba": [75, 75, 75, 75]},
                        ],
                    },
                    {
                        "case_id": "case_0002",
                        "reason": (
                            "Color Key enabled + invert; Mac candidate zeros top-edge pixels where "
                            "Windows keeps nonzero RGBA."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 1,
                            "smoothness": 100,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [75, 75, 75, 75]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [106, 106, 106, 106]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [0, 0, 0, 0], "windows_reference_rgba": [75, 75, 75, 75]},
                        ],
                    },
                    {
                        "case_id": "case_0003",
                        "reason": (
                            "Color Key enabled without invert and Smoothness=0; Mac candidate keeps "
                            "nonzero pixels where Windows writes transparent black."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 0,
                            "smoothness": 0,
                            "extra_smooth": 0,
                            "smooth_range": 2,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [106, 106, 106, 106], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                        ],
                    },
                    {
                        "case_id": "case_0010",
                        "reason": (
                            "Color Key + Extra Smooth/Gamma-range stress; Mac candidate keeps top-edge "
                            "pixels where Windows writes transparent black."
                        ),
                        "expected_params": {
                            "enable_color_key": 1,
                            "invert_color_key": 0,
                            "smoothness": 100,
                            "extra_smooth": 40,
                            "smooth_range": 22,
                            "smoother_version": 2,
                        },
                        "witness_pixels": [
                            {"x": 15, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 16, "y": 0, "mac_candidate_rgba": [106, 106, 106, 106], "windows_reference_rgba": [0, 0, 0, 0]},
                            {"x": 438, "y": 0, "mac_candidate_rgba": [75, 75, 75, 75], "windows_reference_rgba": [0, 0, 0, 0]},
                        ],
                    },
                ],
                "requested_for_each_case": {
                    "parameter_struct": {
                        "enable_color_key": None,
                        "color_key_rgba_or_packed": None,
                        "invert_color_key": None,
                        "smoothness": None,
                        "extra_smooth": None,
                        "smooth_range": None,
                        "smoother_version": None,
                        "gamma_correction": None,
                        "num_gamma_colors": None,
                        "observed_flags_and_offsets": {},
                    },
                    "setup_and_keying": {
                        "input_pixel_rgba_before_effect": [None, None, None, None],
                        "after_any_unpremultiply_rgba": [None, None, None, None],
                        "active_palette_filter_hit": None,
                        "active_palette_filter_value": None,
                        "scalar_key_filter_hit": None,
                        "scalar_key_filter_value": None,
                        "invert_branch_taken": None,
                        "class_plane_byte_before_smoothing": None,
                        "class_plane_neighbors": [],
                    },
                    "smoothing_and_writeback": {
                        "fun_18000c280_switch_idx_if_hit": None,
                        "append_count_if_hit": None,
                        "before_FUN_1800036e0_rgba_float_hex": [None, None, None, None],
                        "gamma_or_srgb_decode_encode_steps": [],
                        "premultiply_or_unpremultiply_step": None,
                        "final_writeback_operation": "floorf(value+0.5) | trunc | cvt | other",
                        "final_rgba_8bit": [None, None, None, None],
                    },
                },
            }
            summary = "Fill with OLMSmoother2 legacy key/gamma setup, mask, gamma, and writeback trace facts."
        elif request_id == "olmdistancegradation_field_prep_runtime_trace_20260619":
            observations = {
                "effect": "OLM Distance Gradation",
                "module_base": "0x...",
                "cases": [
                    {
                        "case_id": "case_0020",
                        "reason": "Constant + background + Inside; removing compose-time Constant binarization worsens mean 0.0561 -> 6.9951",
                        "params": {
                            "invert": 0,
                            "in_out": 1,
                            "inside_threshold": 78,
                            "outside_threshold": 204,
                            "render_mode": 1,
                            "use_background_color": 1,
                            "interpolation_mode": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 951,
                                "y": 417,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                            {
                                "x": 952,
                                "y": 417,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                        ],
                    },
                    {
                        "case_id": "case_0022",
                        "reason": "Constant + background + Both with small thresholds; broad residual but old binarization still much closer than pass-through",
                        "params": {
                            "invert": 0,
                            "in_out": 3,
                            "inside_threshold": 36,
                            "outside_threshold": 11,
                            "render_mode": 1,
                            "use_background_color": 1,
                            "interpolation_mode": 1,
                            "blur_mode": 1,
                            "blur_size": 0,
                        },
                        "pixels": [
                            {
                                "x": 4,
                                "y": 0,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                            {
                                "x": 28,
                                "y": 0,
                                "windows_reference_rgba": [28, 0, 238, 255],
                                "mac_cli_candidate_rgba": [255, 0, 0, 255],
                            },
                        ],
                    },
                    {
                        "case_id": "case_0029",
                        "reason": "Constant + Blur; current binary-field-before-blur is guarded but not exact",
                        "params": {
                            "invert": 1,
                            "in_out": 1,
                            "inside_threshold": 158,
                            "outside_threshold": 13,
                            "render_mode": 1,
                            "use_background_color": 0,
                            "interpolation_mode": 1,
                            "blur_mode": 2,
                            "blur_size": 30,
                        },
                        "pixels": [
                            {
                                "x": 524,
                                "y": 783,
                                "windows_reference_rgba": [15, 0, 126, 135],
                                "mac_cli_candidate_rgba": [17, 0, 147, 158],
                            },
                            {
                                "x": 525,
                                "y": 783,
                                "windows_reference_rgba": [15, 0, 129, 138],
                                "mac_cli_candidate_rgba": [18, 0, 150, 161],
                            },
                        ],
                    },
                ],
                "requested_for_each_pixel": {
                    "source_input_rgba_8bit": [None, None, None, None],
                    "distance_field_before_constant_rgba_or_mat_values": [None, None, None, None],
                    "distance_field_after_constant_rgba_or_mat_values": [None, None, None, None],
                    "distance_field_after_blur_if_any": [None, None, None, None],
                    "field_world_pointer_rowbytes_dimensions": {
                        "pointer": None,
                        "rowbytes": None,
                        "width": None,
                        "height": None,
                    },
                    "distance_transform_call": {
                        "input_mat_type_size_channels": None,
                        "dist_type": None,
                        "mask_size": None,
                        "dst_type": None,
                    },
                    "threshold_and_normalization": {
                        "ui_threshold": None,
                        "threshold_clamp_before_minmax": None,
                        "actual_min": None,
                        "actual_max": None,
                        "normalization_denominator": None,
                        "denominator_source": "ui-threshold|actual-max|other",
                    },
                    "gaussian_blur_call_if_case_0029": {
                        "input_mat_type_size_channels": None,
                        "output_mat_type_size_channels": None,
                        "ksize": [None, None],
                        "sigma_x": None,
                        "sigma_y": None,
                        "border_type": None,
                        "anchor": [None, None],
                        "radius_source": "blur-size|scaled|constant-doubled|other",
                    },
                    "fun_181170870_field_pixel_bytes": [None, None, None, None],
                    "fun_181170870_X_before_invert": None,
                    "fun_181170870_X_after_invert": None,
                    "fun_181170870_X_after_interp": None,
                    "fun_181170870_alpha_base": None,
                    "fun_181170870_output_rgba_before_byte_cast": [None, None, None, None],
                    "final_rgba_8bit": [None, None, None, None],
                },
            }
            summary = "Fill with OLMDistanceGradation field-prep/Constant-mode runtime trace facts."
        else:
            observations = {}
            summary = "Fill with the requested runtime trace fact."
        result_templates.append(
            {
                "request_id": request_id,
                "status": "answered",
                "summary": summary,
                "observations": observations,
            }
        )
    return {
        "kind": "olm_runtime_trace_result",
        "schema": 1,
        "results": result_templates,
    }


def checked_files(root: Path, profile: str) -> list[Path]:
    if profile == "colorkey-edge":
        files = [
            TRACE_NOTE,
            *COLORKEY_SUPPORTING_NOTES,
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0005_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0006_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0008_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/case_0009_trace.log"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/diff.json"),
            Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/diff.csv"),
        ]
    elif profile == "olmblur-repeat-threshold":
        files = [
            TRACE_NOTE,
            *OLMBLUR_SUPPORTING_NOTES,
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/case_0006_trace.log"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/case_0007_trace.log"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/diff.json"),
            Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac/diff.csv"),
        ]
    elif profile == "kirakira-stage-values":
        files = [
            TRACE_NOTE,
            *KIRAKIRA_STAGE_SUPPORTING_NOTES,
            Path("refs/reference_requests/kirakira_single_ray_20260606.json"),
            Path("refs/reference_requests/kirakira_strength0_brightness_20260614.json"),
        ]
    elif profile == "smoother2-no-key-grid":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/OLMSmoother2_FORECAST_AUDIT_20260619.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_211_139.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_215_145.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_991_139.log"),
            Path("refs/reports/olmsmoother2_trace_baseline_20260619_025911_mac/mac_trace_995_145.log"),
        ]
    elif profile == "smoother2-legacy-key-gamma":
        files = [
            TRACE_NOTE,
            Path("notes/OLMSmoother2_ASM_FACTS.md"),
            Path("notes/IR_OLMSmoother2.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json"
            ),
            Path(
                "refs/reports/ae_host_validation_20260620_1425/"
                "ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.csv"
            ),
        ]
    elif profile == "distancegradation-field-prep":
        files = [
            TRACE_NOTE,
            Path("notes/IR_OLMDistanceGradation.md"),
            Path("notes/CONFORMANCE_LEDGER.md"),
            Path("notes/PORTING_BOARD.md"),
        ]
    else:
        files = [TRACE_NOTE, *DEFAULT_REQUESTS, *SUPPORTING_NOTES]
    missing = [path for path in files if not (root / path).exists()]
    if missing:
        raise FileNotFoundError("missing package input(s): " + ", ".join(str(path) for path in missing))
    return files


def main() -> int:
    args = parse_args()
    root = repo_root()
    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        output = root / "refs" / "runtime_trace_packages" / f"olm_runtime_trace_requests_{stamp}.zip"
    elif not output.is_absolute():
        output = root / output

    try:
        files = checked_files(root, args.profile)
        snapshot = next_actions_snapshot(root)
        manifest = package_manifest(root, snapshot, args.profile)
        if not manifest["runtime_actions"]:
            return fail("next_reference_actions.py produced no runtime trace actions")

        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README_RUNTIME_TRACE.md", build_readme(manifest))
            archive.writestr(
                "RETURN_RUNTIME_TRACE_TEMPLATE.json",
                json.dumps(build_return_template(manifest), indent=2, sort_keys=True),
            )
            archive.writestr("runtime_trace_package_manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            archive.writestr("next_reference_actions_snapshot.json", json.dumps(snapshot, indent=2, sort_keys=True))
            for path in files:
                archive.write(root / path, path.as_posix())
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc))

    print(f"[OK] runtime trace package: {output}")
    for action in manifest["runtime_actions"]:
        print(f"- {action['request_id']}: {action['plugin_area']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
