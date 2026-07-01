#!/usr/bin/env python3
"""Compare returned OLMKiraKira stage trace facts with the local trace baseline.

This intentionally does not try to prove exactness. Its job is to put the
Windows runtime facts and the Mac/OpenCV baseline next to each other so the
next implementation change can be grounded in trace evidence instead of PNG
tuning.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUEST_IDS = {
    "kirakira_fun_181150790_stage_values_20260620",
    "kirakira_fun_181150790_deep_stage_values_20260621",
    "kirakira_forward_warp_box_input_20260621",
    "kirakira_boxfilter_pass1_microprobe_20260622",
    "kirakira_aggregation_compose_bt709_20260624",
    "kirakira_compose_writeback_witness_20260630",
    "kirakira_hotspot_compose_writeback_witness_20260701",
}
DEFAULT_REQUEST_ID = "kirakira_aggregation_compose_bt709_20260624"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        required=True,
        help="Summary JSON written by scripts/verify_runtime_trace_return.py or scripts/intake_olm_return.py.",
    )
    parser.add_argument(
        "--local-trace-json",
        type=Path,
        default=Path("refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json"),
        help="Local trace JSON written by refs/scripts/write_olmkirakira_trace_baseline.py.",
    )
    parser.add_argument("--output-json", type=Path, default=None, help="Write normalized comparison JSON.")
    parser.add_argument("--output-md", type=Path, default=None, help="Write a human-readable comparison Markdown.")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def result_quality(row: dict[str, Any]) -> tuple[int, int, int]:
    """Prefer real return rows over packaged templates with the same request id."""
    observations = row.get("observations", {})
    source_file = str(row.get("source_file") or "").replace("\\", "/").lower()
    status = str(row.get("status") or "").lower()
    template_penalty = -100 if "/request_package/" in source_file or source_file.endswith("return_runtime_trace_template.json") else 0
    status_score = {"answered": 30, "answered_partial": 25}.get(status, 0)
    concrete_score = 1 if isinstance(observations, dict) and contains_number(observations) else 0
    return (template_penalty, status_score, concrete_score)


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    candidates = [
        row
        for row in summary.get("results", [])
        if isinstance(row, dict) and row.get("request_id") in REQUEST_IDS
    ]
    if not candidates:
        return None
    return max(candidates, key=result_quality)


def local_ray_records(local_trace: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in local_trace.get("rays", []) if isinstance(row, dict) and row.get("ray")]


def local_aggregation_record(local_trace: dict[str, Any]) -> dict[str, Any] | None:
    for row in local_trace.get("rays", []):
        if isinstance(row, dict) and row.get("stage") == "aggregation_and_compose":
            return row
    return None


def first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def is_placeholder(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        text = value.lower()
        return any(
            marker in text
            for marker in (
                "not isolated",
                "not fully decoded",
                "not decoded",
                "not captured",
                "not breakpointed",
                "not traced",
                "missing",
            )
        )
    if isinstance(value, list):
        return not value or all(is_placeholder(item) for item in value)
    if isinstance(value, dict):
        return not value or all(is_placeholder(item) for item in value.values())
    return False


def has_concrete(value: Any) -> bool:
    return not is_placeholder(value)


def contains_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(contains_number(item) for item in value)
    if isinstance(value, dict):
        return any(contains_number(item) for item in value.values())
    return False


def has_concrete_stage_value(value: Any) -> bool:
    if is_placeholder(value):
        return False
    if isinstance(value, list):
        return any(has_concrete_stage_value(item) for item in value)
    if isinstance(value, dict):
        metadata_keys = {
            "index",
            "label",
            "reason",
            "status",
            "selected_branch",
            "register_pointer",
            "raw_header_dump",
            "decoded",
            "xy",
            "source_xy",
            "ray_xy",
            "tmp1_xy",
            "tmp2_xy",
        }
        stage_markers = ("float", "rgba", "sample", "before", "after", "output", "input", "value", "values")
        for key, item in value.items():
            if key in metadata_keys:
                continue
            if is_placeholder(item):
                continue
            if any(marker in key.lower() for marker in stage_markers) and contains_number(item):
                return True
            if has_concrete_stage_value(item):
                return True
        return False
    return False


def get_path(value: Any, path: list[Any]) -> Any:
    current = value
    for part in path:
        if isinstance(part, int):
            if not isinstance(current, list) or part >= len(current):
                return None
            current = current[part]
        else:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        if current is None:
            return None
    return current


def summarize_local(local_trace: dict[str, Any]) -> dict[str, Any]:
    rays = local_ray_records(local_trace)
    ray = rays[0] if rays else {}
    aggregation = local_aggregation_record(local_trace) or {}
    ray_samples = ray.get("sample_points", [])
    agg_samples = aggregation.get("sample_points", [])
    return {
        "ray_count": len(rays),
        "first_ray": {
            "name": ray.get("ray"),
            "length": ray.get("length"),
            "angle": ray.get("angle"),
            "source_size": ray.get("source_size"),
            "temp_size": ray.get("temp_size"),
            "center": ray.get("center"),
            "copy_origin": ray.get("copy_origin"),
            "forward_matrix": ray.get("forward_matrix"),
            "back_matrix": ray.get("back_matrix"),
            "center_sample": get_path(ray_samples, [0, "values"]),
            "second_sample": get_path(ray_samples, [1, "values"]),
        },
        "aggregation": {
            "scale": aggregation.get("scale"),
            "compose_mode": aggregation.get("compose_mode"),
            "center_sample": get_path(agg_samples, [0, "values"]),
        },
    }


DEEP_STAGE_MAP = (
    ("after_box_filter_pass_1_ret_1151174", "after_box_1"),
    ("after_box_filter_pass_2_ret_11511c7", "after_box_2"),
    ("after_box_filter_pass_3_ret_115121a", "after_box_3"),
    ("after_rotate_back_ret_1150ffd", "after_rotate_back"),
    ("after_final_center_copy_ret_115104e", "after_final_center_copy"),
)

DEEP_POINT_MAP = {
    "center_temp_962_962": ("center", "center_source_960_540"),
    "ray_length_up_temp_962_912": ("ray_length_up", "ray_length_up_source_960_490"),
    "ray_length_right_temp_1012_962": ("ray_length_right", "ray_length_right_source_1010_540"),
}


def local_sample_values(local_trace: dict[str, Any]) -> dict[str, dict[str, float]]:
    rays = local_ray_records(local_trace)
    if not rays:
        return {}
    values: dict[str, dict[str, float]] = {}
    for point in rays[0].get("sample_points", []):
        if not isinstance(point, dict):
            continue
        label = point.get("label")
        point_values = point.get("values")
        if isinstance(label, str) and isinstance(point_values, dict):
            values[label] = point_values
    return values


def deep_stage_deltas(observations: dict[str, Any], local_trace: dict[str, Any]) -> list[dict[str, Any]]:
    stage_values = observations.get("stage_values")
    if not isinstance(stage_values, dict):
        return []
    local_values = local_sample_values(local_trace)
    rows: list[dict[str, Any]] = []
    for windows_stage, local_stage in DEEP_STAGE_MAP:
        stage = stage_values.get(windows_stage)
        if not isinstance(stage, dict):
            continue
        for temp_key, (label, source_key) in DEEP_POINT_MAP.items():
            windows_key = source_key if windows_stage == "after_final_center_copy_ret_115104e" else temp_key
            item = stage.get(windows_key)
            local_item = local_values.get(label, {}).get(local_stage)
            if not isinstance(item, dict) or not isinstance(item.get("float"), (int, float)):
                continue
            if not isinstance(local_item, (int, float)):
                continue
            windows_float = float(item["float"])
            local_float = float(local_item)
            rows.append(
                {
                    "windows_stage": windows_stage,
                    "local_stage": local_stage,
                    "label": label,
                    "windows_float": windows_float,
                    "local_float": local_float,
                    "delta": windows_float - local_float,
                    "windows_hex": item.get("hex"),
                }
            )
    return rows


DEEP_STAGE_MATCH_EPSILON = 1.0e-5


def first_divergence(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        delta = row.get("delta")
        if isinstance(delta, (int, float)) and abs(float(delta)) > DEEP_STAGE_MATCH_EPSILON:
            return row
    return None


def deep_stage_values_match(rows: list[dict[str, Any]]) -> bool:
    return bool(rows) and all(
        isinstance(row.get("delta"), (int, float)) and abs(float(row["delta"])) <= DEEP_STAGE_MATCH_EPSILON
        for row in rows
    )


def microprobe_witnesses(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows = observations.get("witnesses")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    rows = observations.get("witness_proofs")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    return []


def microprobe_seed_reconciled(observations: dict[str, Any], local_trace: dict[str, Any]) -> bool:
    upstream = observations.get("upstream_signal")
    if not isinstance(upstream, dict):
        return False
    plateau = upstream.get("source_window_plateau_example")
    if not isinstance(plateau, dict) or not isinstance(plateau.get("windows_observed"), (int, float)):
        return False
    windows_value = float(plateau["windows_observed"])
    local_values = local_sample_values(local_trace)
    candidates = [
        local_values.get("ray_length_up", {}).get("seed"),
        local_values.get("ray_length_up", {}).get("after_center_copy"),
    ]
    return any(isinstance(value, (int, float)) and abs(float(value) - windows_value) <= 1.0e-5 for value in candidates)


def microprobe_classification(observations: dict[str, Any], local_trace: dict[str, Any] | None = None) -> str:
    explicit = observations.get("classification")
    if isinstance(explicit, str):
        lowered = explicit.strip().lower()
        if lowered and "|" not in lowered and "failed" not in lowered and "unknown" not in lowered:
            return lowered
    if local_trace is not None and microprobe_seed_reconciled(observations, local_trace):
        return "seed-luma-reconciled"
    decision = observations.get("witness_decision")
    if isinstance(decision, dict):
        if decision.get("different_contributing_window") is True or decision.get("different_border_reflection") is True:
            return "different-window-or-border-reflect"
        if decision.get("different_accumulator_or_store") is True:
            return "accumulator-precision-or-store"
        if (
            decision.get("different_contributing_window") is False
            and decision.get("different_border_reflection") is False
            and decision.get("different_accumulator_or_store") is False
            and decision.get("different_mat_or_address_stage") is False
        ):
            return "upstream-source-buffer-content"
    witnesses = microprobe_witnesses(observations)
    if not witnesses:
        return "trace-too-sparse"
    concrete_windows = 0
    concrete_stores = 0
    different_windows = 0
    accumulator_or_store = 0
    for witness in witnesses:
        local_window = witness.get("local_input_window")
        local_range = local_window.get("x_range_unbordered") if isinstance(local_window, dict) else None
        resolved_range = witness.get("resolved_source_x_range_after_border")
        if has_concrete(resolved_range):
            concrete_windows += 1
            if local_range and resolved_range != local_range:
                different_windows += 1
        summary = witness.get("sample_summary")
        if isinstance(summary, dict) and has_concrete(summary.get("count")):
            concrete_windows += 1
            if summary.get("count") != 50:
                different_windows += 1
            local_after = witness.get("local_after_box_1")
            total = summary.get("sum")
            count = summary.get("count")
            if isinstance(local_after, (int, float)) and isinstance(total, (int, float)) and isinstance(count, (int, float)) and count:
                if abs((float(total) / float(count)) - float(local_after)) > 1.0e-6:
                    different_windows += 1
        stored = witness.get("stored_float_after_pass_1")
        normalized = witness.get("normalized_sum_before_store")
        windows_after = witness.get("windows_after_box_1")
        source_delta = witness.get("source_window_mean_delta_vs_local")
        output_delta = witness.get("after_pass_1_delta_vs_local")
        if isinstance(source_delta, (int, float)) and isinstance(output_delta, (int, float)):
            concrete_windows += 1
            concrete_stores += 1
            if abs(float(source_delta) - float(output_delta)) <= 1.0e-6:
                continue
            accumulator_or_store += 1
        if has_concrete(stored) or has_concrete(normalized) or has_concrete(windows_after):
            concrete_stores += 1
            local_after = witness.get("local_after_box_1")
            observed = first_non_none(stored, windows_after, normalized)
            if isinstance(local_after, (int, float)) and isinstance(observed, (int, float)):
                if abs(float(observed) - float(local_after)) > 1.0e-7:
                    accumulator_or_store += 1
    if different_windows:
        return "different-window-or-border-reflect"
    if accumulator_or_store:
        return "accumulator-precision-or-store"
    if concrete_windows and concrete_stores:
        return "boxfilter-pass1-window-matches"
    if concrete_windows:
        return "window-values-without-store"
    if concrete_stores:
        return "store-values-without-window"
    return "trace-structure-present-values-missing"


def recommended_next_evidence(focus: str) -> str:
    if focus == "await-windows-trace":
        return "Import the focused Windows runtime trace return before changing KiraKira behavior."
    if focus == "trace-too-sparse" or focus.endswith("trace-too-sparse"):
        return "Do not tune from this return; rerun with concrete witness values or an exact breakpoint failure reason."
    if focus == "ray-length-normalization":
        return "Ground ray length normalization and parameter scaling against the helper entry values."
    if focus == "warp-matrix-or-center":
        return "Ground the affine matrix, temp center, and copy origin before touching blur/compose math."
    if focus == "forward-warp-or-boxfilter-input":
        return "Capture the pass-1 input window or same-Mat/address proof at the first divergent witness."
    if focus == "center-copy-or-boxfilter-input":
        return "Prove whether the divergent witness comes from center-copy/source ROI state or boxFilter input state."
    if focus == "boxfilter-stage-values":
        return "Capture pass-by-pass boxFilter values for the same witnesses, including pass-1 input and stored output."
    if focus == "aggregation-or-compose":
        return "Ground the final scale/screen-over compose inputs before changing ray generation."
    if focus == "hotspot-local-compose-writeback":
        return "Keep the ask hotspot-local: compare post-FUN_18114fd90 glow, merge-mode-1 composed RGBA, and final quantization/writeback only at the residual hotspot."
    if focus == "fd90-aggregation-grounded-compose-scale":
        return "FUN_18114fd90 aggregation is grounded; update the aggregation scale/alpha model, then remeasure before requesting more compose internals."
    if focus == "ray-helper-stages-match-aggregation-or-compose":
        return "Ray helper stages match within float print precision; ground aggregation, compose, or final quantization next."
    if focus.endswith("different-window-or-border-reflect"):
        return "Use the resolved source indices and sample list to update only the boxFilter border/window rule."
    if focus.endswith("accumulator-precision-or-store"):
        return "Ground accumulator precision and store rounding in the AVX2 helper before changing output values."
    if focus.endswith("upstream-source-buffer-content"):
        return "Treat pass-1 boxFilter window/border/store as grounded; trace the pre-boxFilter source fill or center-copy stage next."
    if focus.endswith("seed-luma-reconciled"):
        return "The pass-1 source-buffer delta is explained by the local BT.709 seed update; remeasure later stages before requesting more Windows data."
    if focus.endswith("boxfilter-pass1-window-matches"):
        return "Treat pass-1 window selection as grounded; move downstream to later passes or compose witnesses."
    if focus.endswith("window-values-without-store"):
        return "Add stored pass-1 output or normalized sum before deciding whether the window alone explains the residual."
    if focus.endswith("store-values-without-window"):
        return "Add contributing-window values to distinguish accumulator/store behavior from a different input window."
    if focus.endswith("trace-structure-present-values-missing"):
        return "The trace hit the expected shape but lacks concrete values; request witness floats/sums before tuning."
    return "Record the concrete witness that explains this focus before changing KiraKira implementation."


def safe_source_file(value: Any) -> str | None:
    if not value:
        return None
    return Path(str(value)).name


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    entry = observations.get("fun_181150790_entry", {})
    witnesses = observations.get("witness_pixels", [])
    aggregation = observations.get("aggregation_and_compose", {})
    fd90_aggregation = observations.get("fun_18114fd90_aggregation", {})
    merge_mode_1_compose = observations.get("merge_mode_1_compose", {})
    case = observations.get("case", {})
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": safe_source_file(row.get("source_file")),
        "case_id": observations.get("case_id") or (case.get("case_id") if isinstance(case, dict) else None),
        "known_facts": observations.get("known_facts_to_keep"),
        "entry": {
            "src_mat": entry.get("src_mat") if isinstance(entry, dict) else None,
            "tmp1_mat": entry.get("tmp1_mat") if isinstance(entry, dict) else None,
            "tmp2_mat": entry.get("tmp2_mat") if isinstance(entry, dict) else None,
            "ray_length": entry.get("ray_length") if isinstance(entry, dict) else None,
            "angle": entry.get("angle_degrees_or_radians") if isinstance(entry, dict) else None,
            "forward_matrix": entry.get("affine_forward_matrix") if isinstance(entry, dict) else None,
            "back_matrix": entry.get("affine_back_matrix") if isinstance(entry, dict) else None,
            "forward_dsize": entry.get("forward_dsize") if isinstance(entry, dict) else None,
            "back_dsize": entry.get("back_dsize") if isinstance(entry, dict) else None,
            "source_roi_rect": entry.get("source_roi_rect") if isinstance(entry, dict) else None,
            "final_copy_rect": entry.get("final_copy_rect") if isinstance(entry, dict) else None,
        },
        "witness_pixels": witnesses if isinstance(witnesses, list) else [],
        "boxfilter_calls": observations.get("boxfilter_calls"),
        "forward_warp": observations.get("forward_warp"),
        "boxfilter_pass_1": observations.get("boxfilter_pass_1"),
        "forward_warp_witnesses": observations.get("witnesses"),
        "microprobe_witnesses": observations.get("witnesses") or observations.get("witness_proofs"),
        "microprobe_classification": observations.get("classification"),
        "witness_decision": observations.get("witness_decision"),
        "upstream_signal": observations.get("upstream_signal"),
        "first_divergence_classification": observations.get("first_divergence_classification"),
        "previous_first_concrete_divergence": observations.get("previous_first_concrete_divergence"),
        "aggregation_and_compose": aggregation if isinstance(aggregation, dict) else aggregation,
        "fun_18114fd90_aggregation": fd90_aggregation if isinstance(fd90_aggregation, dict) else fd90_aggregation,
        "merge_mode_1_compose": merge_mode_1_compose if isinstance(merge_mode_1_compose, dict) else merge_mode_1_compose,
        "residual_hotspot": observations.get("residual_hotspots") or observations.get("residual_hotspot_optional"),
        "stage_values": observations.get("stage_values"),
        "not_captured": observations.get("not_captured"),
    }


def build_comparison(summary: dict[str, Any], local_trace: dict[str, Any]) -> dict[str, Any]:
    row = find_result(summary)
    windows = summarize_windows(row)
    local = summarize_local(local_trace)
    observations = row.get("observations", {}) if isinstance(row, dict) else {}
    if not isinstance(observations, dict):
        observations = {}
    deltas = deep_stage_deltas(observations, local_trace)
    first_delta = first_divergence(deltas)
    likely_next_focus = "await-windows-trace"
    if windows.get("present"):
        entry = windows.get("entry", {})
        local_ray = local.get("first_ray", {})
        win_length = entry.get("ray_length")
        win_forward = entry.get("forward_matrix")
        win_witnesses = windows.get("witness_pixels")
        win_box = windows.get("boxfilter_calls")
        win_forward_warp = windows.get("forward_warp")
        win_boxfilter_pass_1 = windows.get("boxfilter_pass_1")
        win_forward_warp_witnesses = windows.get("forward_warp_witnesses")
        win_microprobe_witnesses = windows.get("microprobe_witnesses")
        win_agg = windows.get("aggregation_and_compose")
        win_fd90 = windows.get("fun_18114fd90_aggregation")
        win_merge = windows.get("merge_mode_1_compose")
        win_stage_values = windows.get("stage_values")
        if has_concrete(win_length) and win_length != local_ray.get("length"):
            likely_next_focus = "ray-length-normalization"
        elif row.get("request_id") == "kirakira_boxfilter_pass1_microprobe_20260622":
            likely_next_focus = "boxfilter-pass1-" + microprobe_classification(observations, local_trace)
        elif has_concrete(win_forward) and win_forward != local_ray.get("forward_matrix"):
            likely_next_focus = "warp-matrix-or-center"
        elif deep_stage_values_match(deltas):
            likely_next_focus = "ray-helper-stages-match-aggregation-or-compose"
        elif deltas and all(row.get("windows_stage", "").startswith("after_box_filter_pass") for row in deltas[:3]):
            likely_next_focus = "forward-warp-or-boxfilter-input"
        elif has_concrete_stage_value(win_forward_warp_witnesses) or has_concrete_stage_value(win_forward_warp):
            likely_next_focus = "center-copy-or-boxfilter-input"
        elif has_concrete_stage_value(win_boxfilter_pass_1):
            likely_next_focus = "boxfilter-stage-values"
        elif has_concrete_stage_value(win_microprobe_witnesses):
            likely_next_focus = "boxfilter-pass1-" + microprobe_classification(observations, local_trace)
        elif has_concrete_stage_value(win_stage_values):
            likely_next_focus = "boxfilter-stage-values"
        elif has_concrete_stage_value(win_witnesses) or has_concrete_stage_value(win_box):
            likely_next_focus = "boxfilter-stage-values"
        elif row.get("request_id") == "kirakira_hotspot_compose_writeback_witness_20260701" and (
            has_concrete_stage_value(win_merge) or has_concrete_stage_value(win_fd90)
        ):
            likely_next_focus = "hotspot-local-compose-writeback"
        elif row.get("request_id") in {"kirakira_aggregation_compose_bt709_20260624", "kirakira_compose_writeback_witness_20260630"} and has_concrete_stage_value(win_fd90):
            likely_next_focus = "fd90-aggregation-grounded-compose-scale"
        elif has_concrete_stage_value(win_agg) or has_concrete_stage_value(win_merge):
            likely_next_focus = "aggregation-or-compose"
        else:
            likely_next_focus = "trace-too-sparse"
    return {
        "kind": "olmkirakira_stage_trace_comparison",
        "schema": 1,
        "request_id": row.get("request_id") if isinstance(row, dict) else DEFAULT_REQUEST_ID,
        "likely_next_focus": likely_next_focus,
        "recommended_next_evidence": recommended_next_evidence(likely_next_focus),
        "windows": windows,
        "local": local,
        "deep_stage_deltas": deltas,
        "first_divergence": first_delta,
    }


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    local = comparison["local"]
    local_ray = local.get("first_ray", {})
    win_entry = windows.get("entry", {}) if isinstance(windows, dict) else {}
    lines = [
        "# OLMKiraKira Stage Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Recommended next evidence: {comparison['recommended_next_evidence']}",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        "",
        "## Ray Helper",
        "",
        "| Field | Windows trace | Local OpenCV baseline |",
        "| --- | --- | --- |",
        f"| length | {md_value(win_entry.get('ray_length'))} | {md_value(local_ray.get('length'))} |",
        f"| angle | {md_value(win_entry.get('angle'))} | {md_value(local_ray.get('angle'))} |",
        f"| dsize/temp | {md_value(first_non_none(win_entry.get('forward_dsize'), win_entry.get('back_dsize')))} | {md_value(local_ray.get('temp_size'))} |",
        f"| forward matrix | {md_value(win_entry.get('forward_matrix'))} | {md_value(local_ray.get('forward_matrix'))} |",
        f"| back matrix | {md_value(win_entry.get('back_matrix'))} | {md_value(local_ray.get('back_matrix'))} |",
        f"| source/final copy | {md_value(first_non_none(win_entry.get('source_roi_rect'), win_entry.get('final_copy_rect')))} | {md_value(local_ray.get('copy_origin'))} |",
        "",
        "## Local Samples",
        "",
        f"- Ray center sample: {md_value(local_ray.get('center_sample'))}",
        f"- Ray second sample: {md_value(local_ray.get('second_sample'))}",
        f"- Aggregation center sample: {md_value(local.get('aggregation', {}).get('center_sample'))}",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- Witness pixels: {md_value(windows.get('witness_pixels'))}",
        f"- BoxFilter calls: {md_value(windows.get('boxfilter_calls'))}",
        f"- Forward warp: {md_value(windows.get('forward_warp'))}",
        f"- BoxFilter pass 1: {md_value(windows.get('boxfilter_pass_1'))}",
        f"- Forward-warp witnesses: {md_value(windows.get('forward_warp_witnesses'))}",
        f"- Microprobe witnesses: {md_value(windows.get('microprobe_witnesses'))}",
        f"- Microprobe classification: {md_value(windows.get('microprobe_classification'))}",
        f"- Witness decision: {md_value(windows.get('witness_decision'))}",
        f"- Upstream signal: {md_value(windows.get('upstream_signal'))}",
        f"- First divergence classification: {md_value(windows.get('first_divergence_classification'))}",
        f"- Previous concrete divergence: {md_value(windows.get('previous_first_concrete_divergence'))}",
        f"- Aggregation/compose: {md_value(windows.get('aggregation_and_compose'))}",
        f"- FUN_18114fd90 aggregation: {md_value(windows.get('fun_18114fd90_aggregation'))}",
        f"- Merge mode 1 compose: {md_value(windows.get('merge_mode_1_compose'))}",
        f"- Residual hotspot: {md_value(windows.get('residual_hotspot'))}",
        "",
    ]
    deltas = comparison.get("deep_stage_deltas")
    if isinstance(deltas, list) and deltas:
        first_delta = comparison.get("first_divergence")
        if isinstance(first_delta, dict):
            lines.extend(
                [
                    "## First Divergence",
                    "",
                    f"- Stage: `{first_delta.get('local_stage')}`",
                    f"- Point: `{first_delta.get('label')}`",
                    f"- Windows - local: `{float(first_delta.get('delta')):+.8f}`",
                    "",
                ]
            )
        lines.extend(
            [
                "## Deep Stage Deltas",
                "",
                "| Stage | Point | Windows | Local | Delta | Hex |",
                "| --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for row in deltas:
            lines.append(
                f"| `{row.get('local_stage')}` | `{row.get('label')}` | "
                f"{float(row.get('windows_float')):.8f} | "
                f"{float(row.get('local_float')):.8f} | "
                f"{float(row.get('delta')):+.8f} | `{row.get('windows_hex')}` |"
            )
        lines.append("")
    if windows.get("not_captured"):
        lines.extend(["## Not Captured", "", md_value(windows.get("not_captured")), ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    local_path = resolve(root, args.local_trace_json)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    if not local_path.exists():
        return fail(f"local trace JSON not found: {local_path}")
    summary = load_json(summary_path)
    local_trace = load_json(local_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    if not isinstance(local_trace, dict):
        return fail("local trace JSON must be an object")
    comparison = build_comparison(summary, local_trace)

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
