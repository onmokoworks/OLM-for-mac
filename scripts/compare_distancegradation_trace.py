#!/usr/bin/env python3
"""Classify returned OLMDistanceGradation field-prep runtime trace facts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "olmdistancegradation_16bpc_constant_boundary_witness_20260630"
CASE0023_REQUEST_ID = "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630"
FIELD_PREP_REQUEST_ID = "olmdistancegradation_field_prep_runtime_trace_20260619"
CASE0026_REQUEST_ID = "olmdistancegradation_16bpc_case0026_x_witness_20260628"
REQUEST_IDS = {REQUEST_ID, CASE0023_REQUEST_ID, FIELD_PREP_REQUEST_ID, CASE0026_REQUEST_ID}

LOCAL_ASSUMPTIONS = {
    "distance_transform": "scipy/OpenCV-like Euclidean distance_transform_edt for current CLI; Windows AEX embeds OpenCV 4.5.5",
    "normalization": "clamp to UI threshold, then divide by actual max with denominator at least 1.0",
    "constant_no_blur": "current CLI binarizes non-blur Constant after interpolation-prep, but this is inferred upstream behavior",
    "constant_blur": "current CLI binarizes field before blur and doubles blur radius",
    "gaussian_blur": "separable Gaussian with OpenCV default sigma formula and Reflect101/mirror border",
    "compose": "FUN_181170870 reads field green byte, applies invert/interpolation, then writes 8bpc RGBA",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    ordered_ids = [CASE0023_REQUEST_ID, REQUEST_ID, CASE0026_REQUEST_ID, FIELD_PREP_REQUEST_ID]
    for request_id in ordered_ids:
        for row in summary.get("results", []):
            if isinstance(row, dict) and row.get("request_id") == request_id:
                return row
    return None


def concrete_trace_value(value: Any) -> bool:
    """Return true only for values that look like measured Windows runtime facts."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(concrete_trace_value(item) for item in value)
    if isinstance(value, dict):
        return any(concrete_trace_value(item) for item in value.values())
    if isinstance(value, str):
        text = value.strip().lower()
        if not text or text in {
            "0x...",
            "ui-threshold|actual-max|other",
            "blur-size|scaled|constant-doubled|other",
            "none",
            "null",
            "n/a",
            "unknown",
        }:
            return False
        placeholder_needles = (
            "not isolated",
            "not reached",
            "inferred",
            "likely",
            "expected",
            "current implementation",
            "current best",
            "runtime",
            "still needs",
            "untraced",
            "unknown",
            "needs live",
            "was not captured",
            "see witness",
            "exact in current ae return",
        )
        if any(needle in text for needle in placeholder_needles):
            return False
        return False
    return False


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    requested = observations.get("requested_for_each_pixel", {})
    if not isinstance(requested, dict):
        requested = {}
    if row.get("request_id") in {REQUEST_ID, CASE0023_REQUEST_ID}:
        if row.get("request_id") == CASE0023_REQUEST_ID:
            case_meta = observations.get("case", {})
            if not isinstance(case_meta, dict):
                case_meta = {}
            return {
                "present": True,
                "status": row.get("status"),
                "summary": row.get("summary"),
                "source_file": row.get("source_file"),
                "cases": [case_meta] if case_meta else [],
                "field_values": {
                    "source_input_rgba16": requested.get("source_input_rgba16"),
                    "binary_mask_before_distance_transform": requested.get("binary_mask_value_before_distance_transform"),
                    "inside_or_outside_distance_before_threshold": {
                        "inside": requested.get("inside_distance_before_threshold"),
                        "outside": requested.get("outside_distance_before_threshold"),
                    },
                    "field_value_before_compose_or_color_pick": requested.get(
                        "field_value_after_constant_threshold_before_compose"
                    ) or requested.get("field_value_finally_consumed_by_FUN_181170480"),
                },
                "threshold_and_normalization": {
                    "threshold_values_ui_and_internal": requested.get("threshold_values"),
                    "comparison_rule": requested.get("comparison_rule"),
                    "selected_side_inside_outside_or_both": requested.get("selected_side_for_both_mode"),
                    "outside_threshold_zero_special_case": requested.get("outside_threshold_zero_special_case"),
                },
                "compose": {
                    "output_rgba_float_before_cvt": requested.get("fun_181170480_output_rgba_before_word_store"),
                    "final_rgba16": requested.get("final_rgba16"),
                },
                "branch_decision": {
                    "focus": observations.get("focus"),
                    "known_binary_facts_to_preserve": observations.get("known_binary_facts_to_preserve"),
                    "failed_breakpoint_or_watchpoint_reason": observations.get("failed_breakpoint_or_watchpoint_reason"),
                },
            }
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "cases": observations.get("cases", []),
            "field_values": {
                key: requested.get(key)
                for key in (
                    "source_input_rgba16",
                    "binary_mask_before_distance_transform",
                    "inside_or_outside_distance_before_threshold",
                    "field_value_before_compose_or_color_pick",
                    "fun_181170480_X_before_invert",
                    "fun_181170480_X_after_invert",
                )
            },
            "threshold_and_normalization": {
                key: requested.get(key)
                for key in (
                    "threshold_values_ui_and_internal",
                    "comparison_rule",
                    "selected_side_inside_outside_or_both",
                )
            },
            "compose": {
                key: requested.get(key)
                for key in (
                    "output_rgba_float_before_cvt",
                    "final_rgba16",
                )
            },
            "branch_decision": observations.get("case_level_contract", {}),
        }
    if row.get("request_id") == CASE0026_REQUEST_ID:
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": observations.get("case_id"),
            "witness_pixels": observations.get("witness_pixels", []),
            "field_values": {
                key: requested.get(key)
                for key in (
                    "source_input_rgba16",
                    "field_world_pointer_rowbytes_dimensions",
                    "field_pixel_raw_rgba16_or_mat_channels_before_compose",
                )
            },
            "compose": {
                key: requested.get(key)
                for key in (
                    "fun_181170480_X_before_invert",
                    "fun_181170480_X_after_invert",
                    "fun_181170480_X_after_power_interp",
                    "fun_181170480_background_rgba_float_or_16",
                    "fun_181170480_gradation_rgba_float_or_16",
                    "output_rgba_float_before_cvt",
                    "final_rgba16",
                )
            },
            "branch_decision": observations.get("branch_decision", {}),
        }
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": row.get("source_file"),
        "cases": observations.get("cases", []),
        "field_values": {
            key: requested.get(key)
            for key in (
                "distance_field_before_constant_rgba_or_mat_values",
                "distance_field_after_constant_rgba_or_mat_values",
                "distance_field_after_blur_if_any",
                "field_world_pointer_rowbytes_dimensions",
            )
        },
        "opencv_calls": {
            "distance_transform_call": requested.get("distance_transform_call"),
            "gaussian_blur_call_if_case_0029": requested.get("gaussian_blur_call_if_case_0029"),
        },
        "threshold_and_normalization": requested.get("threshold_and_normalization"),
        "compose": {
            key: requested.get(key)
            for key in (
                "fun_181170870_field_pixel_bytes",
                "fun_181170870_X_before_invert",
                "fun_181170870_X_after_invert",
                "fun_181170870_X_after_interp",
                "fun_181170870_alpha_base",
                "fun_181170870_output_rgba_before_byte_cast",
                "final_rgba_8bit",
            )
        },
    }


def classify_next_focus(windows: dict[str, Any]) -> str:
    if not windows.get("present"):
        return "await-windows-trace"
    field_values = windows.get("field_values", {})
    branch_decision = windows.get("branch_decision")
    if isinstance(branch_decision, dict) and concrete_trace_value(branch_decision):
        if branch_decision.get("field_already_ramps_before_compose") is True:
            return "case0026-field-prep-normalization"
        if branch_decision.get("compose_interpolation_creates_ramp_from_saturated_field") is True:
            return "case0026-invert-power-compose"
        if branch_decision.get("parameter_or_color_branch_mismatch") is True:
            return "case0026-parameter-color-branch"
        return "case0026-branch-decision"
    if concrete_trace_value(field_values.get("field_pixel_raw_rgba16_or_mat_channels_before_compose")):
        return "case0026-field-prep-normalization"
    if concrete_trace_value(field_values.get("inside_or_outside_distance_before_threshold")) or concrete_trace_value(
        field_values.get("binary_mask_before_distance_transform")
    ):
        return "constant-boundary-threshold-ownership"
    opencv_calls = windows.get("opencv_calls", {})
    threshold = windows.get("threshold_and_normalization")
    compose = windows.get("compose", {})
    if concrete_trace_value(field_values.get("distance_field_before_constant_rgba_or_mat_values")) or concrete_trace_value(
        field_values.get("distance_field_after_constant_rgba_or_mat_values")
    ):
        return "constant-field-prep"
    if concrete_trace_value(threshold):
        return "threshold-normalization"
    if concrete_trace_value(opencv_calls.get("distance_transform_call")):
        return "distance-transform-args"
    if concrete_trace_value(opencv_calls.get("gaussian_blur_call_if_case_0029")) or concrete_trace_value(
        field_values.get("distance_field_after_blur_if_any")
    ):
        return "gaussian-blur-args"
    if concrete_trace_value(compose):
        return "compose-field-byte"
    return "trace-too-sparse"


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    result = find_result(summary)
    request_id = result.get("request_id") if isinstance(result, dict) else REQUEST_ID
    windows = summarize_windows(result)
    return {
        "kind": "olmdistancegradation_trace_comparison",
        "schema": 1,
        "request_id": request_id,
        "likely_next_focus": classify_next_focus(windows),
        "local_assumptions": LOCAL_ASSUMPTIONS,
        "windows": windows,
    }


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    assumptions = comparison["local_assumptions"]
    lines = [
        "# OLMDistanceGradation Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        "",
        "## Local Assumptions",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in assumptions.items())
    lines.extend(
        [
            "",
            "## Windows Observations",
            "",
            f"- Status: {md_value(windows.get('status'))}",
            f"- Summary: {windows.get('summary') or '-'}",
            f"- Cases: {md_value(windows.get('cases'))}",
            f"- Witness pixels: {md_value(windows.get('witness_pixels'))}",
            f"- Field values: {md_value(windows.get('field_values'))}",
            f"- OpenCV calls: {md_value(windows.get('opencv_calls'))}",
            f"- Threshold/normalization: {md_value(windows.get('threshold_and_normalization'))}",
            f"- Compose: {md_value(windows.get('compose'))}",
            f"- Branch decision: {md_value(windows.get('branch_decision'))}",
            "",
            "## Interpretation",
            "",
            "- `constant-field-prep`: update the field construction/packing IR before touching compose.",
            "- `threshold-normalization`: settle clamp/minmax denominator before Gaussian or compose changes.",
            "- `distance-transform-args`: update OpenCV/helper primitive assumptions first.",
            "- `gaussian-blur-args`: focus `case_0029` blur radius/kernel/border.",
            "- `compose-field-byte`: focus `FUN_181170870` green-byte/invert/interp/writeback.",
            "- `case0026-field-prep-normalization`: Windows already has a ramp before 16bpc compose; fix field prep/normalization.",
            "- `case0026-invert-power-compose`: Windows creates the ramp in `FUN_181170480`; fix invert/power/compose ownership.",
            "- `case0026-parameter-color-branch`: fix AE parameter/color branch ownership before math changes.",
            "- `constant-boundary-threshold-ownership`: Constant-mode boundary values were captured; decide `<` vs `<=`, side ownership, and plateau handling before touching compose.",
            "- `trace-too-sparse`: request missing field/OpenCV/compose values instead of PNG tuning.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    comparison = build_comparison(summary)
    if args.output_json:
        output = resolve(root, args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(comparison, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        print(f"comparison_json={output}")
    if args.output_md:
        output = resolve(root, args.output_md)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_markdown(comparison), encoding="utf-8")
        print(f"comparison_md={output}")
    if not args.output_json and not args.output_md:
        print(render_markdown(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
