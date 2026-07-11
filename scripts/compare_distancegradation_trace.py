#!/usr/bin/env python3
"""Classify returned OLMDistanceGradation field-prep runtime trace facts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUEST_ID = "olmdistancegradation_16bpc_constant_boundary_witness_20260630"
CASE0023_REQUEST_ID = "olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630"
CASE0023_THRESHOLD_REQUEST_ID = "olmdistancegradation_case0023_threshold_family_followup_20260701"
CASE0023_TRIPLET_XY_REQUEST_ID = "olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701"
CASE0023_OUTPUT_WORD_REQUEST_ID = "olmdistancegradation_case0023_output_word_triplet_followup_20260701"
CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID = "olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702"
CASE0023_REFCON_WORDMAP_REQUEST_ID = "olmdistancegradation_case0023_refcon_wordmap_followup_20260702"
CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID = "olmdistancegradation_case0023_final_source_ownership_20260707"
DEPTHGATE_QUANTIZATION_REQUEST_ID = "olmdistancegradation_depthgate_quantization_witness_20260708"
DEPTHGATE_907_STORE_EXPORT_REQUEST_ID = "olmdistancegradation_depthgate_907_store_export_witness_20260708"
CASE0014_LAYER_SOURCE_WITNESS_REQUEST_ID = "olmdistancegradation_case0014_layer_source_witness_20260708"
CASE0010_0011_FIELD_STORE_REQUEST_ID = "olmdistancegradation_0010_0011_field_store_witness_20260709"
CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID = (
    "olmdistancegradation_0010_0011_field_store_prewarm_witness_20260709"
)
CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID = (
    "olmdistancegradation_0010_0011_writeback_follow_witness_20260709"
)
CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID = (
    "olmdistancegradation_0010_0011_writeback_pointer_map_witness_20260709"
)
CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID = (
    "olmdistancegradation_0010_0011_compose_exact_address_witness_20260710"
)
SINGLE_SITE_FOLLOWUP_REQUEST_ID = "olmdistancegradation_0010_compose_single_site_followup_20260710"
SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID = (
    "olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710"
)
SINGLE_SITE_901_394_TILE_RETRY_REQUEST_ID = (
    "olmdistancegradation_0010_compose_source_901_394_tile_retry_20260710"
)
SINGLE_SITE_VISITED_TILE_SOURCE_REQUEST_ID = (
    "olmdistancegradation_0010_compose_visited_tile_source_0_45_20260710"
)
LAYER_NO_BG_SOURCE_OWNERSHIP_REQUEST_ID = "olmdistancegradation_16bpc_layer_no_bg_source_ownership_20260629"
FIELD_PREP_REQUEST_ID = "olmdistancegradation_field_prep_runtime_trace_20260619"
CASE0026_REQUEST_ID = "olmdistancegradation_16bpc_case0026_x_witness_20260628"
REQUEST_IDS = {
    REQUEST_ID,
    CASE0023_REQUEST_ID,
    CASE0023_THRESHOLD_REQUEST_ID,
    CASE0023_TRIPLET_XY_REQUEST_ID,
    CASE0023_OUTPUT_WORD_REQUEST_ID,
    CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
    CASE0023_REFCON_WORDMAP_REQUEST_ID,
    CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
    DEPTHGATE_QUANTIZATION_REQUEST_ID,
    DEPTHGATE_907_STORE_EXPORT_REQUEST_ID,
    CASE0014_LAYER_SOURCE_WITNESS_REQUEST_ID,
    CASE0010_0011_FIELD_STORE_REQUEST_ID,
    CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID,
    CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID,
    CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID,
    CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID,
    SINGLE_SITE_FOLLOWUP_REQUEST_ID,
    SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID,
    SINGLE_SITE_901_394_TILE_RETRY_REQUEST_ID,
    SINGLE_SITE_VISITED_TILE_SOURCE_REQUEST_ID,
    LAYER_NO_BG_SOURCE_OWNERSHIP_REQUEST_ID,
    FIELD_PREP_REQUEST_ID,
    CASE0026_REQUEST_ID,
}
CASE0023_THRESHOLD_AUDIT = (
    ROOT
    / "refs"
    / "conformance"
    / "olmdistancegradation_case0023_threshold_family_audit_20260701.json"
)
CASE0023_LANE_STATE = (
    ROOT
    / "refs"
    / "conformance"
    / "olmdistancegradation_case0023_lane_state_20260703.json"
)
CASE0023_AEX_CPU_SIMU_FULLFRAME = (
    ROOT
    / "refs"
    / "conformance"
    / "olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json"
)
CASE0023_FINAL_SOURCE_EXPECTED_PIXELS = [
    {"x": 1699, "y": 7, "role": "mismatch_representative"},
    {"x": 415, "y": 393, "role": "mismatch_representative"},
    {"x": 1698, "y": 7, "role": "matching_control"},
    {"x": 1700, "y": 7, "role": "matching_control"},
    {"x": 414, "y": 393, "role": "matching_control"},
    {"x": 415, "y": 394, "role": "matching_control"},
    {"x": 416, "y": 393, "role": "matching_control"},
]

LOCAL_ASSUMPTIONS = {
    "distance_transform": "scipy/OpenCV-like Euclidean distance_transform_edt for current CLI; Windows AEX embeds OpenCV 4.5.5",
    "normalization": "clamp to UI threshold, then divide by actual max with denominator at least 1.0",
    "constant_no_blur": "current CLI binarizes non-blur Constant after interpolation-prep, but this is inferred upstream behavior",
    "constant_blur": "current CLI binarizes field before blur and doubles blur radius",
    "gaussian_blur": "separable Gaussian with OpenCV default sigma formula and Reflect101/mirror border",
    "compose": "FUN_181170870 reads field green byte, applies invert/interpolation, then writes 8bpc RGBA",
}


def repo_root() -> Path:
    return ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument(
        "--request-id",
        choices=sorted(REQUEST_IDS),
        default=None,
        help="Select one request from a merged runtime summary instead of using the default priority order.",
    )
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


def find_result(summary: dict[str, Any], requested_id: str | None = None) -> dict[str, Any] | None:
    if requested_id:
        for row in summary.get("results", []):
            if isinstance(row, dict) and row.get("request_id") == requested_id:
                return row
        return None

    ordered_ids = [
        SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID,
        SINGLE_SITE_VISITED_TILE_SOURCE_REQUEST_ID,
        SINGLE_SITE_FOLLOWUP_REQUEST_ID,
        CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID,
        CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID,
        CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID,
        CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID,
        CASE0010_0011_FIELD_STORE_REQUEST_ID,
        CASE0014_LAYER_SOURCE_WITNESS_REQUEST_ID,
        DEPTHGATE_907_STORE_EXPORT_REQUEST_ID,
        DEPTHGATE_QUANTIZATION_REQUEST_ID,
        CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
        CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
        CASE0023_REFCON_WORDMAP_REQUEST_ID,
        CASE0023_OUTPUT_WORD_REQUEST_ID,
        CASE0023_TRIPLET_XY_REQUEST_ID,
        CASE0023_THRESHOLD_REQUEST_ID,
        CASE0023_REQUEST_ID,
        REQUEST_ID,
        CASE0026_REQUEST_ID,
        LAYER_NO_BG_SOURCE_OWNERSHIP_REQUEST_ID,
        FIELD_PREP_REQUEST_ID,
    ]
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


def xy_key(item: Any) -> tuple[int, int] | None:
    if not isinstance(item, dict):
        return None
    x = item.get("x")
    y = item.get("y")
    if isinstance(x, int) and isinstance(y, int):
        return (x, y)
    xy = item.get("xy")
    if (
        isinstance(xy, list)
        and len(xy) == 2
        and isinstance(xy[0], int)
        and isinstance(xy[1], int)
    ):
        return (xy[0], xy[1])
    return None


def keys_from_trace_value(value: Any) -> set[tuple[int, int]]:
    keys: set[tuple[int, int]] = set()
    if isinstance(value, list):
        for item in value:
            key = xy_key(item)
            if key is not None:
                keys.add(key)
            elif isinstance(item, dict):
                keys.update(keys_from_trace_value(list(item.values())))
    elif isinstance(value, dict):
        key = xy_key(value)
        if key is not None:
            keys.add(key)
        for item in value.values():
            keys.update(keys_from_trace_value(item))
    return keys


def final_source_pixel_coverage(*values: Any) -> dict[str, Any]:
    measured_keys: set[tuple[int, int]] = set()
    for value in values:
        measured_keys.update(keys_from_trace_value(value))
    expected = {(item["x"], item["y"]) for item in CASE0023_FINAL_SOURCE_EXPECTED_PIXELS}
    missing = sorted(expected - measured_keys)
    present = sorted(expected & measured_keys)
    return {
        "expected": CASE0023_FINAL_SOURCE_EXPECTED_PIXELS,
        "present_xy": [{"x": x, "y": y} for x, y in present],
        "missing_xy": [{"x": x, "y": y} for x, y in missing],
        "all_expected_pixels_present": not missing,
    }


def answer_text(answer: Any) -> str:
    if answer is None:
        return ""
    if isinstance(answer, str):
        return answer.lower()
    return json.dumps(answer, ensure_ascii=False, sort_keys=True).lower()


def normalize_trace_status(status: Any, observations: Any) -> str:
    normalized = str(status or "answered").lower()
    if normalized == "answered" and isinstance(observations, dict):
        classification = observations.get("classification")
        if isinstance(classification, str) and classification.lower() == "answered_partial":
            return "answered_partial"
    return normalized


def first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def summarize_single_site_runs(observations: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_site_runs = observations.get("site_runs")
    site_runs: list[dict[str, Any]] = []
    if isinstance(raw_site_runs, dict):
        for site_name, value in raw_site_runs.items():
            item = dict(value) if isinstance(value, dict) else {"raw": value}
            item.setdefault("site", site_name)
            site_runs.append(item)
    elif isinstance(raw_site_runs, list):
        for value in raw_site_runs:
            if isinstance(value, dict):
                site_runs.append(dict(value))

    summarized_runs: list[dict[str, Any]] = []
    progress = {
        "site_count": len(site_runs),
        "exact_site_hit_count": 0,
        "field_word_site_count": 0,
        "source_word_site_count": 0,
        "input_word_site_count": 0,
        "writer_word_site_count": 0,
        "console_artifact_count": 0,
        "failed_reason_count": 0,
    }
    for site_run in site_runs:
        status = site_run.get("status")
        exact_site_hit = first_present(site_run, "exact_rdi_gate_hit", "rdi_equals_target_output")
        if not isinstance(exact_site_hit, bool) and isinstance(status, str):
            normalized_status = status.strip().lower()
            if normalized_status == "hit":
                exact_site_hit = True
            elif normalized_status in {"missed", "not_run"}:
                exact_site_hit = False
        field_words = first_present(site_run, "rcx_field_words", "rcx_field_words_u16")
        source_words = first_present(site_run, "rdx_source_words", "rdx_source_words_u16")
        final_words = first_present(site_run, "final_pf16_words", "final_pf16_words_at_rdi")
        console_artifact = first_present(site_run, "console_artifact", "console_log")
        failed_reason = first_present(site_run, "failed_reason", "failed_gate_or_breakpoint_reason")
        has_field_words = concrete_trace_value(field_words) or concrete_hex_blob(field_words)
        has_source_words = concrete_trace_value(source_words) or concrete_hex_blob(source_words)
        has_final_words = concrete_trace_value(final_words) or concrete_hex_blob(final_words)
        if exact_site_hit is True:
            progress["exact_site_hit_count"] += 1
        if has_field_words:
            progress["field_word_site_count"] += 1
        if has_source_words:
            progress["source_word_site_count"] += 1
        if has_field_words or has_source_words:
            progress["input_word_site_count"] += 1
        if has_final_words:
            progress["writer_word_site_count"] += 1
        if concrete_trace_value(console_artifact) or concrete_hex_blob(console_artifact):
            progress["console_artifact_count"] += 1
        if concrete_trace_value(failed_reason):
            progress["failed_reason_count"] += 1
        summarized_runs.append(
            {
                "site": site_run.get("site"),
                "site_address": first_present(site_run, "site_address", "downstream_address"),
                "status": status,
                "exact_rdi_gate_hit": exact_site_hit,
                "rdi": site_run.get("rdi"),
                "target_output": site_run.get("target_output"),
                "field_typed_words": field_words,
                "source_typed_words": source_words,
                "final_typed_words": final_words,
                "console_artifact": console_artifact,
                "failed_reason": failed_reason,
                "typed_capture": {
                    "has_field_words": has_field_words,
                    "has_source_words": has_source_words,
                    "has_final_words": has_final_words,
                },
            }
        )
    return summarized_runs, progress


def final_source_answer_class(
    row: dict[str, Any],
    requested: dict[str, Any],
    answer: dict[str, Any],
    witness_pixels: Any,
) -> dict[str, Any]:
    classification_values = [
        value
        for key, value in answer.items()
        if key != "recommended_next_mac_action"
    ]
    text = answer_text(classification_values)
    classes: list[str] = []
    if "source" in text or "mask" in text:
        classes.append("windows-source-mask")
    if "compose" in text or "writeback" in text or "pre-store" in text or "prestore" in text:
        classes.append("final-compose/writeback")
    if "export" in text or "png" in text or "path split" in text or "path-split" in text:
        classes.append("export-path-split")
    if not classes and concrete_trace_value(requested):
        classes.append("typed-values-returned-unclassified")
    if not classes:
        classes.append("unresolved")
    coverage = final_source_pixel_coverage(requested, witness_pixels)
    has_core_values = any(
        concrete_trace_value(requested.get(key))
        for key in (
            "source_input_rgba16",
            "source_alpha_or_mask_used_for_ownership",
            "field_value_consumed_by_final_compose_or_store",
            "fun_181170480_or_final_writeback_output_rgba_before_word_store",
            "final_stored_rgba16",
            "exported_rgba16",
        )
    )
    status = row.get("status")
    if "unresolved" in classes and not has_core_values:
        acceptance_read = "failed_or_too_sparse"
    elif status == "answered" and coverage["all_expected_pixels_present"]:
        acceptance_read = "answered_candidate"
    elif has_core_values:
        acceptance_read = "answered_partial_candidate"
    else:
        acceptance_read = "failed_partial_candidate"
    return {
        "classes": classes,
        "acceptance_read": acceptance_read,
        "pixel_coverage": coverage,
    }


def concrete_hex_blob(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, list):
        return any(concrete_hex_blob(item) for item in value)
    if isinstance(value, dict):
        return any(concrete_hex_blob(item) for item in value.values())
    if isinstance(value, str):
        text = value.strip().lower().replace("_", "").replace("`", "")
        if not text or text in {"0x...", "none", "null", "n/a", "unknown"} or "..." in text:
            return False
        compact = text.replace(" ", "")
        if compact.startswith("0x"):
            compact = compact[2:]
        return len(compact) >= 4 and all(ch in "0123456789abcdef" for ch in compact)
    return False


def concrete_address_or_numeric(value: Any) -> bool:
    return concrete_trace_value(value) or concrete_hex_blob(value)


def summarize_exact_address_target(target: dict[str, Any]) -> dict[str, Any]:
    final_writer_scalars = target.get("final_writer_scalars")
    if not isinstance(final_writer_scalars, dict):
        final_writer_scalars = {}
    has_field_addr = concrete_hex_blob(target.get("field_addr"))
    has_source_addr = concrete_hex_blob(target.get("source_addr"))
    has_output_addr = concrete_hex_blob(target.get("output_addr"))
    has_field_read = (
        concrete_hex_blob(target.get("rcx_field_words_at_0x117057d"))
        or concrete_address_or_numeric(target.get("xmm1_after_field_read"))
        or concrete_address_or_numeric(target.get("xmm2_after_field_transform"))
    )
    has_source_read = concrete_hex_blob(target.get("rdx_source_words_at_0x11705f1"))
    has_final_writer = concrete_address_or_numeric(final_writer_scalars)
    has_final_store = concrete_hex_blob(target.get("final_pf16_words")) or concrete_trace_value(
        target.get("final_pf16_words")
    )
    return {
        "case_id": target.get("case_id"),
        "xy": target.get("xy"),
        "field_addr": target.get("field_addr"),
        "source_addr": target.get("source_addr"),
        "output_addr": target.get("output_addr"),
        "rcx_field_words_at_0x117057d": target.get("rcx_field_words_at_0x117057d"),
        "rdx_source_words_at_0x11705f1": target.get("rdx_source_words_at_0x11705f1"),
        "xmm1_after_field_read": target.get("xmm1_after_field_read"),
        "xmm2_after_field_transform": target.get("xmm2_after_field_transform"),
        "final_writer_scalars": final_writer_scalars,
        "final_pf16_words": target.get("final_pf16_words"),
        "failed_hook_or_watchpoint_reason": target.get("failed_hook_or_watchpoint_reason"),
        "binding_state": {
            "has_field_addr": has_field_addr,
            "has_source_addr": has_source_addr,
            "has_output_addr": has_output_addr,
            "has_full_address_binding": has_field_addr and has_source_addr and has_output_addr,
            "has_field_read": has_field_read,
            "has_source_read": has_source_read,
            "has_final_writer": has_final_writer,
            "has_final_store": has_final_store,
            "has_full_typed_capture": (
                has_field_addr
                and has_source_addr
                and has_output_addr
                and has_field_read
                and has_source_read
                and (has_final_writer or has_final_store)
            ),
        },
    }


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    requested = observations.get("requested_for_each_pixel", {})
    if not isinstance(requested, dict):
        requested = {}
    status = normalize_trace_status(row.get("status"), observations)
    row = {**row, "status": status}
    if row.get("request_id") in {REQUEST_ID, CASE0023_REQUEST_ID, CASE0023_THRESHOLD_REQUEST_ID, CASE0023_TRIPLET_XY_REQUEST_ID, CASE0023_OUTPUT_WORD_REQUEST_ID}:
        if row.get("request_id") in {CASE0023_REQUEST_ID, CASE0023_THRESHOLD_REQUEST_ID, CASE0023_TRIPLET_XY_REQUEST_ID, CASE0023_OUTPUT_WORD_REQUEST_ID}:
            case_meta = observations.get("case", {})
            if not isinstance(case_meta, dict):
                case_meta = {}
            threshold_triplet = observations.get("threshold_triplet")
            if threshold_triplet is None:
                threshold_triplet = case_meta.get("threshold_triplet")
            if threshold_triplet is None:
                threshold_triplet = requested.get("threshold_triplet")
            return {
                "present": True,
                "status": row.get("status"),
                "summary": row.get("summary"),
                "source_file": row.get("source_file"),
                "cases": [case_meta] if case_meta else [],
                "threshold_triplet": threshold_triplet,
                "field_values": {
                    "source_input_rgba16": requested.get("source_input_rgba16"),
                    "binary_mask_before_distance_transform": requested.get("binary_mask_value_before_distance_transform"),
                    "inside_or_outside_distance_before_threshold": {
                        "inside": (
                            requested.get("inside_distance_before_threshold")
                            or requested.get("raw_inside_distance_before_threshold")
                        ),
                        "outside": (
                            requested.get("outside_distance_before_threshold")
                            or requested.get("raw_outside_distance_before_threshold")
                        ),
                    },
                    "field_value_before_compose_or_color_pick": requested.get(
                        "helper_stage_field_value_before_compose"
                    ) or requested.get(
                        "field_value_after_constant_threshold_before_compose"
                    ) or requested.get("field_value_finally_consumed_by_FUN_181170480"),
                },
                "threshold_and_normalization": {
                    "threshold_values_ui_and_internal": requested.get("threshold_values")
                    or requested.get("threshold_values_ui_and_internal"),
                    "comparison_rule": requested.get("comparison_rule")
                    or requested.get("threshold_equality_or_plateau_decision"),
                    "selected_side_inside_outside_or_both": requested.get("selected_side_for_both_mode")
                    or requested.get("selected_side_inside_outside_or_both"),
                    "outside_threshold_zero_special_case": requested.get("outside_threshold_zero_special_case"),
                    "constant_binary_fork_order": requested.get("constant_binary_fork_order"),
                },
                "compose": {
                    "field_value_consumed_by_compose": requested.get("field_value_finally_consumed_by_FUN_181170480"),
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
    if row.get("request_id") == CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID:
        case_meta = observations.get("case", {})
        if not isinstance(case_meta, dict):
            case_meta = {}
        answer = observations.get("answer_classification", {})
        if not isinstance(answer, dict):
            answer = {}
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": case_meta.get("case_id"),
            "witness_pixels": case_meta.get("representative_pixels", []),
            "field_values": {
                "source_input_rgba16": requested.get("source_input_rgba16"),
                "source_alpha_or_mask_used_for_ownership": requested.get("source_alpha_or_mask_used_for_ownership"),
                "binary_mask_before_distance_transform": requested.get("binary_mask_value_before_distance_transform"),
                "inside_or_outside_distance_before_threshold": {
                    "inside": requested.get("inside_distance_before_threshold"),
                    "outside": requested.get("outside_distance_before_threshold"),
                },
                "field_value_before_compose_or_color_pick": requested.get(
                    "field_value_after_constant_threshold_before_compose"
                ),
                "field_value_consumed_by_final_path": requested.get("field_value_consumed_by_final_compose_or_store"),
            },
            "compose": {
                "output_rgba_before_word_store": requested.get(
                    "fun_181170480_or_final_writeback_output_rgba_before_word_store"
                ),
                "final_stored_rgba16": requested.get("final_stored_rgba16"),
                "exported_rgba16": requested.get("exported_rgba16"),
                "directly_observed_vs_inferred": requested.get("directly_observed_vs_inferred"),
            },
            "branch_decision": {
                "known_facts_to_preserve": observations.get("known_facts_to_preserve"),
                "answer_classification": answer,
            },
            "final_source_ownership": final_source_answer_class(
                row,
                requested,
                answer,
                case_meta.get("representative_pixels", []),
            ),
        }
    if row.get("request_id") == DEPTHGATE_QUANTIZATION_REQUEST_ID:
        primary_case = observations.get("primary_case", {})
        if not isinstance(primary_case, dict):
            primary_case = {}
        witness_pixels = primary_case.get("witness_pixels", [])
        if not isinstance(witness_pixels, list):
            witness_pixels = []
        classes: dict[str, int] = {}
        for pixel in witness_pixels:
            if not isinstance(pixel, dict):
                continue
            classification = str(pixel.get("classification") or "unclassified")
            classes[classification] = classes.get(classification, 0) + 1
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": primary_case.get("case_id"),
            "params": primary_case.get("params"),
            "witness_pixels": witness_pixels,
            "classification_counts": classes,
            "control_case_optional": observations.get("control_case_optional"),
            "requested_for_each_pixel": observations.get("requested_for_each_pixel"),
        }
    if row.get("request_id") == DEPTHGATE_907_STORE_EXPORT_REQUEST_ID:
        witness_pixels = observations.get("witness_pixels", [])
        primary_case: dict[str, Any] = {}
        cases = observations.get("cases")
        if isinstance(cases, list):
            for case in cases:
                if isinstance(case, dict):
                    primary_case = case
                    nested_pixels = case.get("witness_pixels")
                    if isinstance(nested_pixels, list):
                        witness_pixels = nested_pixels
                    break
        if not isinstance(witness_pixels, list):
            witness_pixels = observations.get("pixels", [])
        if not isinstance(witness_pixels, list):
            witness_pixels = []
        witness_pixel = witness_pixels[0] if witness_pixels and isinstance(witness_pixels[0], dict) else {}
        intermediate = witness_pixel.get("intermediate_values") if isinstance(witness_pixel, dict) else {}
        if not isinstance(intermediate, dict):
            intermediate = {}
        classes: dict[str, int] = {}
        for pixel in witness_pixels:
            if not isinstance(pixel, dict):
                continue
            classification = str(pixel.get("classification") or "unclassified")
            classes[classification] = classes.get(classification, 0) + 1
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": observations.get("case_id") or observations.get("case") or primary_case.get("case_id"),
            "witness_xy": observations.get("witness_xy")
            or observations.get("xy")
            or [witness_pixel.get("x"), witness_pixel.get("y")]
            if witness_pixel
            else [907, 222],
            "witness_pixels": witness_pixels,
            "classification_counts": classes,
            "requested_values": {
                "output_world_address": observations.get("output_world_address"),
                "field_value_consumed_by_compose": observations.get("field_value_consumed_by_compose"),
                "field_value_consumed_by_FUN_181170480": intermediate.get("field_value_consumed_by_FUN_181170480"),
                "output_rgba_float_before_pf16": observations.get("output_rgba_float_before_pf16")
                or observations.get("output_rgba_float_before_conversion")
                or witness_pixel.get("pre_writeback_rgba_float_hex"),
                "pf_pixel16_words_after_store": observations.get("pf_pixel16_words_after_store")
                or observations.get("final_stored_rgba16")
                or intermediate.get("pf_pixel16_words_after_store_carried_from_prior_witness"),
                "exported_rgba16_or_png": observations.get("exported_rgba16_or_png")
                or observations.get("exported_rgba16")
                or observations.get("exported_png_rgba8")
                or witness_pixel.get("final_rgba")
                or intermediate.get("same_run_exported_rgba8_carried_from_prior_witness"),
                "failed_hook_or_watchpoint_reason": observations.get("failed_hook_or_watchpoint_reason"),
                "directly_observed_vs_inferred": observations.get("directly_observed_vs_inferred"),
            },
            "raw_observations": observations,
        }
    if row.get("request_id") == CASE0014_LAYER_SOURCE_WITNESS_REQUEST_ID:
        witness_pixels = observations.get("witness_pixels")
        if not isinstance(witness_pixels, list):
            witness_pixels = observations.get("pixels", [])
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": observations.get("case_id") or observations.get("case"),
            "witness_pixels": witness_pixels,
            "requested_values": {
                "source_layer_rgba16": requested.get("source_layer_rgba16")
                or requested.get("consumed_source_layer_rgba16"),
                "source_rgb_before_unpremultiply": requested.get("source_rgb_before_unpremultiply"),
                "source_rgb_after_unpremultiply": requested.get("source_rgb_after_unpremultiply"),
                "source_alpha_or_mask": requested.get("source_alpha_or_mask")
                or requested.get("source_alpha_used_for_ownership_or_mask"),
                "field_pixel_or_channels": requested.get("field_pixel_or_channels")
                or requested.get("field_channels_presented_to_compose"),
                "x_dalpha_outa": {
                    "x": requested.get("x") or requested.get("X"),
                    "d_alpha": requested.get("d_alpha"),
                    "out_a": requested.get("out_a"),
                },
                "output_rgba_float_before_cvt": requested.get("output_rgba_float_before_cvt")
                or requested.get("output_rgba_float_immediately_before_cvttss2si"),
                "final_stored_rgba16": requested.get("final_stored_rgba16"),
                "exported_rgba16_or_png": requested.get("exported_rgba16")
                or requested.get("exported_rgba16_or_png_bytes"),
            },
            "raw_observations": observations,
        }
    if row.get("request_id") in {
        SINGLE_SITE_FOLLOWUP_REQUEST_ID,
        SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID,
        SINGLE_SITE_901_394_TILE_RETRY_REQUEST_ID,
        SINGLE_SITE_VISITED_TILE_SOURCE_REQUEST_ID,
    }:
        site_runs, progress = summarize_single_site_runs(observations)
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "case_id": observations.get("case_id"),
            "target_xy": observations.get("target_xy") or observations.get("xy"),
            "gating_relation": observations.get("gating_relation"),
            "address_model": observations.get("address_model") or observations.get("entry"),
            "site_runs": site_runs,
            "single_site_progress": progress,
            "field_values": {
                "typed_field_words": [
                    {
                        "site": site_run.get("site"),
                        "site_address": site_run.get("site_address"),
                        "words": site_run.get("field_typed_words"),
                    }
                    for site_run in site_runs
                    if site_run.get("typed_capture", {}).get("has_field_words")
                ],
                "typed_source_words": [
                    {
                        "site": site_run.get("site"),
                        "site_address": site_run.get("site_address"),
                        "words": site_run.get("source_typed_words"),
                    }
                    for site_run in site_runs
                    if site_run.get("typed_capture", {}).get("has_source_words")
                ],
            },
            "compose": {
                "typed_final_words": [
                    {
                        "site": site_run.get("site"),
                        "site_address": site_run.get("site_address"),
                        "words": site_run.get("final_typed_words"),
                    }
                    for site_run in site_runs
                    if site_run.get("typed_capture", {}).get("has_final_words")
                ]
            },
            "branch_decision": {
                "ignored_first_chance_80000003": observations.get("ignored_first_chance_80000003"),
                "breakpoint_instability_observed": observations.get("breakpoint_instability_observed"),
                "artifacts_returned": observations.get("artifacts_returned"),
            },
            "raw_observations": observations,
        }
    if row.get("request_id") == CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID:
        address_model = observations.get("address_model")
        if not isinstance(address_model, dict):
            address_model = {}
        targets = observations.get("targets")
        if not isinstance(targets, list):
            targets = []
        summarized_targets = [
            summarize_exact_address_target(target)
            for target in targets
            if isinstance(target, dict)
        ]
        progress = {
            "any_address_model": any(concrete_address_or_numeric(value) for value in address_model.values()),
            "target_count": len(summarized_targets),
            "derived_target_count": 0,
            "fully_address_bound_target_count": 0,
            "field_read_target_count": 0,
            "source_read_target_count": 0,
            "final_writer_target_count": 0,
            "final_store_target_count": 0,
            "fully_typed_target_count": 0,
        }
        case_ids: list[str] = []
        failed_conditions: list[str] = []
        for target in summarized_targets:
            state = target.get("binding_state", {})
            if state.get("has_field_addr") or state.get("has_source_addr") or state.get("has_output_addr"):
                progress["derived_target_count"] += 1
            if state.get("has_full_address_binding"):
                progress["fully_address_bound_target_count"] += 1
            if state.get("has_field_read"):
                progress["field_read_target_count"] += 1
            if state.get("has_source_read"):
                progress["source_read_target_count"] += 1
            if state.get("has_final_writer"):
                progress["final_writer_target_count"] += 1
            if state.get("has_final_store"):
                progress["final_store_target_count"] += 1
            if state.get("has_full_typed_capture"):
                progress["fully_typed_target_count"] += 1
            case_id = target.get("case_id")
            if isinstance(case_id, str) and case_id and case_id not in case_ids:
                case_ids.append(case_id)
            failed_condition = target.get("failed_hook_or_watchpoint_reason")
            if isinstance(failed_condition, str) and failed_condition:
                failed_conditions.append(failed_condition)
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "cases": [{"case_id": case_id} for case_id in case_ids],
            "address_model": address_model,
            "exact_address_targets": summarized_targets,
            "address_binding": {
                "classification": observations.get("classification"),
                "known_previous_return": observations.get("known_previous_return"),
                "progress": progress,
            },
            "branch_decision": {
                "focus": observations.get("focus"),
                "module_base": observations.get("module_base"),
                "failed_hook_or_watchpoint_reasons": failed_conditions,
            },
            "raw_observations": observations,
        }
    if row.get("request_id") in {
        CASE0010_0011_FIELD_STORE_REQUEST_ID,
        CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID,
        CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID,
        CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID,
    }:
        cases = observations.get("cases")
        if not isinstance(cases, list):
            cases = []
        witness_pixels: list[dict[str, Any]] = []
        for case in cases:
            if not isinstance(case, dict):
                continue
            case_id = str(case.get("case_id") or "")
            for pixel in case.get("witness_pixels", []):
                if not isinstance(pixel, dict):
                    continue
                item = dict(pixel)
                item["case_id"] = case_id
                witness_pixels.append(item)
        missing = observations.get("directly_observed_vs_inferred")
        typed_pixels: list[dict[str, Any]] = []
        classification_counts: dict[str, int] = {}
        for pixel in witness_pixels:
            intermediate = pixel.get("intermediate_values")
            if not isinstance(intermediate, dict):
                intermediate = {}
            typed = {
                "case_id": pixel.get("case_id"),
                "x": pixel.get("x"),
                "y": pixel.get("y"),
                "classification": pixel.get("classification") or intermediate.get("classification"),
                "source_rgba16": first_present(pixel, "source_rgba16", "source_input_rgba16", "consumed_source_rgba16")
                or first_present(intermediate, "source_rgba16", "source_input_rgba16", "consumed_source_rgba16"),
                "raw_distance": first_present(
                    pixel,
                    "raw_distance",
                    "raw_distances",
                    "inside_outside_raw_distance",
                    "inside_outside_raw_distances",
                )
                or first_present(
                    intermediate,
                    "raw_distance",
                    "raw_distances",
                    "inside_outside_raw_distance",
                    "inside_outside_raw_distances",
                ),
                "normalized_field": first_present(
                    pixel,
                    "normalized_field",
                    "normalized_field_value",
                    "field_value_consumed_by_final_compose",
                    "field_value",
                )
                or first_present(
                    intermediate,
                    "normalized_field",
                    "normalized_field_value",
                    "field_value_consumed_by_final_compose",
                    "field_value",
                ),
                "field_word": first_present(pixel, "field_word", "field_world_word", "field_store_word")
                or first_present(intermediate, "field_word", "field_world_word", "field_store_word"),
                "compose_out_a": first_present(pixel, "compose_out_a", "out_a", "final_compose_out_a")
                or first_present(intermediate, "compose_out_a", "out_a", "final_compose_out_a"),
                "pre_store_rgba_float": first_present(
                    pixel,
                    "pre_store_rgba_float",
                    "prestore_rgba_float",
                    "pre_writeback_rgba_float",
                    "pre_writeback_rgba_float_hex",
                )
                or first_present(
                    intermediate,
                    "pre_store_rgba_float",
                    "prestore_rgba_float",
                    "pre_writeback_rgba_float",
                    "pre_writeback_rgba_float_hex",
                ),
                "pf16_store_words": first_present(
                    pixel,
                    "pf16_store_words",
                    "pf_pixel16_words_after_store",
                    "final_stored_rgba16",
                    "store_rgba16",
                )
                or first_present(
                    intermediate,
                    "pf16_store_words",
                    "pf_pixel16_words_after_store",
                    "final_stored_rgba16",
                    "store_rgba16",
                ),
                "exported_sample": first_present(
                    pixel,
                    "exported_sample",
                    "exported_rgba16",
                    "exported_true16",
                    "exported_rgba16_or_png",
                    "final_rgba",
                )
                or first_present(
                    intermediate,
                    "exported_sample",
                    "exported_rgba16",
                    "exported_true16",
                    "exported_rgba16_or_png",
                    "final_rgba",
                ),
                "local_store_a": intermediate.get("local_store_a"),
                "windows_implied_store_a": intermediate.get("windows_implied_store_a"),
            }
            classification = typed.get("classification")
            if isinstance(classification, str) and classification:
                classification_counts[classification] = classification_counts.get(classification, 0) + 1
            typed_pixels.append(typed)
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "cases": cases,
            "witness_pixels": witness_pixels,
            "typed_witness_pixels": typed_pixels,
            "classification_counts": classification_counts,
            "field_values": {
                "local_and_implied_store_values": [
                    {
                        "case_id": pixel.get("case_id"),
                        "x": pixel.get("x"),
                        "y": pixel.get("y"),
                        **(
                            pixel.get("intermediate_values")
                            if isinstance(pixel.get("intermediate_values"), dict)
                            else {}
                        ),
                    }
                    for pixel in witness_pixels
                ],
                "directly_observed_vs_inferred": missing,
            },
            "compose": {
                "pre_writeback_rgba_float_hex": [
                    {
                        "case_id": pixel.get("case_id"),
                        "x": pixel.get("x"),
                        "y": pixel.get("y"),
                        "pre_writeback_rgba_float_hex": pixel.get("pre_writeback_rgba_float_hex"),
                    }
                    for pixel in witness_pixels
                ],
                "final_rgba": [
                    {
                        "case_id": pixel.get("case_id"),
                        "x": pixel.get("x"),
                        "y": pixel.get("y"),
                        "final_rgba": pixel.get("final_rgba"),
                    }
                    for pixel in witness_pixels
                ],
            },
            "branch_decision": {
                "directly_observed_vs_inferred": missing,
                "fresh_windows_runtime_witness_present": False,
            },
            "raw_observations": observations,
        }
    if row.get("request_id") == LAYER_NO_BG_SOURCE_OWNERSHIP_REQUEST_ID:
        return {
            "present": True,
            "status": row.get("status"),
            "summary": row.get("summary"),
            "source_file": row.get("source_file"),
            "cases": observations.get("cases", []),
            "field_values": {
                "source_input_rgba16": requested.get("source_input_rgba16"),
                "field_world_pointer_rowbytes_dimensions": requested.get(
                    "field_world_pointer_rowbytes_dimensions"
                ),
                "field_pixel_raw_rgba16_or_mat_channels_before_compose": requested.get(
                    "field_pixel_raw_rgba16_or_mat_channels_before_compose"
                ),
            },
            "compose": {
                "fun_181170480_X_before_invert": requested.get("fun_181170480_X_before_invert"),
                "fun_181170480_X_after_invert": requested.get("fun_181170480_X_after_invert"),
                "fun_181170480_X_after_interp": requested.get("fun_181170480_X_after_interp"),
                "fun_181170480_alpha_base": requested.get("fun_181170480_alpha_base"),
                "source_rgba_before_any_unpremultiply": requested.get(
                    "fun_181170480_source_rgba_float_or_16_before_any_unpremultiply"
                ),
                "source_rgba_after_any_unpremultiply": requested.get(
                    "fun_181170480_source_rgba_after_any_unpremultiply"
                ),
                "output_rgba_float_before_cvt": requested.get("fun_181170480_output_rgba_float_before_cvt"),
                "final_rgba16": requested.get("final_rgba16"),
            },
            "branch_decision": observations.get("branch_decision", {}),
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


def classify_next_focus(request_id: str, windows: dict[str, Any]) -> str:
    if not windows.get("present"):
        return "await-windows-trace"
    if request_id == CASE0023_THRESHOLD_REQUEST_ID:
        return "case0023-threshold-family-provenance-split"
    if request_id == DEPTHGATE_QUANTIZATION_REQUEST_ID:
        classes = windows.get("classification_counts") or {}
        unresolved = int(classes.get("unresolved", 0) or 0) if isinstance(classes, dict) else 0
        if unresolved:
            return "depthgate-export-quantization-one-pixel-open"
        return "depthgate-export-quantization-closeout"
    if request_id == DEPTHGATE_907_STORE_EXPORT_REQUEST_ID:
        if windows.get("status") == "answered_partial":
            return "depthgate-907-store-export-still-open"
        classes = windows.get("classification_counts") or {}
        if isinstance(classes, dict) and classes:
            if classes.get("store-zero-before-export"):
                return "depthgate-907-store-zero-closeout"
            if classes.get("export-quantization"):
                return "depthgate-907-export-quantization-closeout"
        requested_values = windows.get("requested_values") or {}
        if concrete_trace_value(requested_values.get("pf_pixel16_words_after_store")):
            return "depthgate-907-store-captured-export-open"
        return "depthgate-907-store-export-proof"
    if request_id == CASE0014_LAYER_SOURCE_WITNESS_REQUEST_ID:
        return "layer-source-case0014-source-rgb-prestore-proof"
    if request_id in {
        SINGLE_SITE_FOLLOWUP_REQUEST_ID,
        SINGLE_SITE_BREAK_IGNORE_RETRY_REQUEST_ID,
        SINGLE_SITE_901_394_TILE_RETRY_REQUEST_ID,
        SINGLE_SITE_VISITED_TILE_SOURCE_REQUEST_ID,
    }:
        progress = windows.get("single_site_progress") or {}
        if int(progress.get("writer_word_site_count") or 0) > 0:
            return "single-site-writeback-bound"
        if int(progress.get("input_word_site_count") or 0) > 0:
            return "single-site-input-bound"
        if int(progress.get("exact_site_hit_count") or 0) == 0:
            return "single-site-witness-missing"
        return "single-site-witness-missing"
    if request_id == CASE0010_0011_COMPOSE_EXACT_ADDRESS_REQUEST_ID:
        binding = windows.get("address_binding") or {}
        progress = binding.get("progress") or {}
        fully_typed = int(progress.get("fully_typed_target_count") or 0)
        has_partial_binding = bool(progress.get("any_address_model")) or any(
            int(progress.get(key) or 0) > 0
            for key in (
                "derived_target_count",
                "fully_address_bound_target_count",
                "field_read_target_count",
                "source_read_target_count",
                "final_writer_target_count",
                "final_store_target_count",
            )
        )
        if fully_typed >= 2:
            return "case0010-0011-compose-exact-address-proof"
        if has_partial_binding or windows.get("status") == "answered_partial":
            return "case0010-0011-compose-exact-address-partial-address-binding"
        if windows.get("status") == "failed_partial":
            return "case0010-0011-compose-exact-address-witness-missing"
        return "case0010-0011-compose-exact-address-await-typed-targets"
    if request_id in {
        CASE0010_0011_FIELD_STORE_REQUEST_ID,
        CASE0010_0011_FIELD_STORE_PREWARM_REQUEST_ID,
        CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID,
        CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID,
    }:
        if request_id == CASE0010_0011_WRITEBACK_POINTER_MAP_REQUEST_ID:
            if windows.get("status") == "failed_partial":
                return "case0010-0011-writeback-pointer-map-witness-missing"
            return "case0010-0011-writeback-pointer-map-classify"
        if request_id == CASE0010_0011_WRITEBACK_FOLLOW_REQUEST_ID:
            if windows.get("status") == "failed_partial":
                return "case0010-0011-writeback-follow-witness-missing"
            return "case0010-0011-writeback-follow-classify"
        if windows.get("status") == "failed_partial":
            return "case0010-0011-field-store-witness-missing"
        classes = windows.get("classification_counts") or {}
        if isinstance(classes, dict) and classes:
            if classes.get("field-normalization"):
                return "case0010-0011-field-normalization-proof"
            if classes.get("pf16-conversion"):
                return "case0010-0011-pf16-conversion-proof"
            if classes.get("export-split"):
                return "case0010-0011-export-split-proof"
            return "case0010-0011-field-store-classify"
        typed_pixels = windows.get("typed_witness_pixels") or []
        if isinstance(typed_pixels, list):
            complete_pixels = []
            partial_pixels = []
            for pixel in typed_pixels:
                if not isinstance(pixel, dict):
                    continue
                has_field = concrete_trace_value(pixel.get("raw_distance")) or concrete_trace_value(
                    pixel.get("normalized_field")
                )
                has_prestore = concrete_trace_value(pixel.get("compose_out_a")) or concrete_trace_value(
                    pixel.get("pre_store_rgba_float")
                )
                has_store = concrete_trace_value(pixel.get("pf16_store_words"))
                has_export = concrete_trace_value(pixel.get("exported_sample"))
                if has_field and has_prestore and has_store and has_export:
                    complete_pixels.append(pixel)
                elif has_field or has_prestore or has_store or has_export:
                    partial_pixels.append(pixel)
            if complete_pixels:
                return "case0010-0011-field-store-proof"
            if partial_pixels:
                return "case0010-0011-field-store-partial"
        requested = windows.get("field_values") or {}
        if concrete_trace_value(requested.get("local_and_implied_store_values")):
            return "case0010-0011-field-store-classify"
        return "case0010-0011-field-store-proof"
    if request_id in {
        CASE0023_TRIPLET_XY_REQUEST_ID,
        CASE0023_OUTPUT_WORD_REQUEST_ID,
        CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
        CASE0023_REFCON_WORDMAP_REQUEST_ID,
        CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
    }:
        return "case0023-edge-family-output-binding"
    if request_id == LAYER_NO_BG_SOURCE_OWNERSHIP_REQUEST_ID:
        return "layer-no-bg-source-ownership"
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


def build_comparison(summary: dict[str, Any], requested_id: str | None = None) -> dict[str, Any]:
    result = find_result(summary, requested_id)
    request_id = result.get("request_id") if isinstance(result, dict) else (requested_id or REQUEST_ID)
    windows = summarize_windows(result)
    comparison = {
        "kind": "olmdistancegradation_trace_comparison",
        "schema": 4,
        "request_id": request_id,
        "likely_next_focus": classify_next_focus(request_id, windows),
        "local_assumptions": LOCAL_ASSUMPTIONS,
        "windows": windows,
    }
    if request_id in {
        CASE0023_REQUEST_ID,
        CASE0023_THRESHOLD_REQUEST_ID,
        CASE0023_TRIPLET_XY_REQUEST_ID,
        CASE0023_OUTPUT_WORD_REQUEST_ID,
        CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
        CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
    } and CASE0023_THRESHOLD_AUDIT.exists():
        audit = load_json(CASE0023_THRESHOLD_AUDIT)
        comparison["local_case0023_threshold_context"] = {
            "decision": audit.get("decision"),
            "threshold_triplet_roles": audit.get("threshold_triplet_roles"),
            "live_mac_triplet": audit.get("live_mac_triplet"),
            "live_mac_edge_family": audit.get("live_mac_edge_family"),
        }
    if request_id in {
        CASE0023_REQUEST_ID,
        CASE0023_THRESHOLD_REQUEST_ID,
        CASE0023_TRIPLET_XY_REQUEST_ID,
        CASE0023_OUTPUT_WORD_REQUEST_ID,
        CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
        CASE0023_REFCON_WORDMAP_REQUEST_ID,
        CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
    } and CASE0023_LANE_STATE.exists():
        state = load_json(CASE0023_LANE_STATE)
        comparison["local_case0023_lane_state"] = {
            "safe_claim": state.get("safe_claim"),
            "residual": state.get("residual"),
            "threshold_family": state.get("threshold_family"),
            "edge_family": state.get("edge_family"),
            "forbidden_actions": state.get("forbidden_actions"),
        }
    if request_id in {
        CASE0023_REQUEST_ID,
        CASE0023_THRESHOLD_REQUEST_ID,
        CASE0023_TRIPLET_XY_REQUEST_ID,
        CASE0023_OUTPUT_WORD_REQUEST_ID,
        CASE0023_REFCON_STACK_WORDMAP_REQUEST_ID,
        CASE0023_REFCON_WORDMAP_REQUEST_ID,
        CASE0023_FINAL_SOURCE_OWNERSHIP_REQUEST_ID,
    } and CASE0023_AEX_CPU_SIMU_FULLFRAME.exists():
        simu = load_json(CASE0023_AEX_CPU_SIMU_FULLFRAME)
        comparison["local_case0023_aex_cpu_simu_fullframe"] = {
            "status": simu.get("status"),
            "kind": simu.get("kind"),
            "source_png": simu.get("source_png"),
            "combine": simu.get("combine"),
            "reading": simu.get("reading"),
            "samples": simu.get("samples"),
        }
    return comparison


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    assumptions = comparison["local_assumptions"]
    local_case0023 = comparison.get("local_case0023_threshold_context")
    local_case0023_lane_state = comparison.get("local_case0023_lane_state")
    local_case0023_aex_cpu_simu = comparison.get("local_case0023_aex_cpu_simu_fullframe")
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
            f"- Threshold triplet: {md_value(windows.get('threshold_triplet'))}",
            f"- Target XY: {md_value(windows.get('target_xy'))}",
            f"- Gating relation: {md_value(windows.get('gating_relation'))}",
            f"- Address model: {md_value(windows.get('address_model'))}",
            f"- Site runs: {md_value(windows.get('site_runs'))}",
            f"- Single-site progress: {md_value(windows.get('single_site_progress'))}",
            f"- Exact-address targets: {md_value(windows.get('exact_address_targets'))}",
            f"- Address binding: {md_value(windows.get('address_binding'))}",
            f"- Field values: {md_value(windows.get('field_values'))}",
            f"- OpenCV calls: {md_value(windows.get('opencv_calls'))}",
            f"- Threshold/normalization: {md_value(windows.get('threshold_and_normalization'))}",
            f"- Compose: {md_value(windows.get('compose'))}",
            f"- Branch decision: {md_value(windows.get('branch_decision'))}",
            f"- Final/source ownership: {md_value(windows.get('final_source_ownership'))}",
            "",
        ]
    )
    if local_case0023:
        lines.extend(
            [
                "## Local case_0023 Context",
                "",
                f"- Decision: {md_value(local_case0023.get('decision'))}",
                f"- Threshold triplet roles: {md_value(local_case0023.get('threshold_triplet_roles'))}",
                f"- Live Mac triplet: {md_value(local_case0023.get('live_mac_triplet'))}",
                f"- Live Mac edge family: {md_value(local_case0023.get('live_mac_edge_family'))}",
                "",
            ]
        )
    if local_case0023_lane_state:
        lines.extend(
            [
                "## Local case_0023 Lane State",
                "",
                f"- Safe claim: {local_case0023_lane_state.get('safe_claim') or '-'}",
                f"- Residual split: {md_value(local_case0023_lane_state.get('residual'))}",
                f"- Threshold family: {md_value(local_case0023_lane_state.get('threshold_family'))}",
                f"- Edge family: {md_value(local_case0023_lane_state.get('edge_family'))}",
                f"- Forbidden actions: {md_value(local_case0023_lane_state.get('forbidden_actions'))}",
                "",
            ]
        )
    if local_case0023_aex_cpu_simu:
        lines.extend(
            [
                "## Local case_0023 AEX CPU Simu",
                "",
                f"- Status: {md_value(local_case0023_aex_cpu_simu.get('status'))}",
                f"- Kind: {md_value(local_case0023_aex_cpu_simu.get('kind'))}",
                f"- Source PNG: {md_value(local_case0023_aex_cpu_simu.get('source_png'))}",
                f"- Combine: {local_case0023_aex_cpu_simu.get('combine') or '-'}",
                f"- Reading: {md_value(local_case0023_aex_cpu_simu.get('reading'))}",
                f"- Samples: {md_value(local_case0023_aex_cpu_simu.get('samples'))}",
                "",
                "This is binary-grounded helper evidence, not a whole-plugin AE exact claim.",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- `depthgate-export-quantization-one-pixel-open`: keep `case_0024..0027` out of field/source/compose tuning; only `(907,222)` remains open for a direct PF16 store/export stop.",
            "- `depthgate-export-quantization-closeout`: treat the near-miss family as an export-quantization boundary, not an algorithm mismatch.",
            "- `case0023-threshold-family-provenance-split`: do not tune implementation from the packaged threshold triplet; this lane needs current Windows Software export/provenance evidence.",
            "- `case0023-edge-family-output-binding`: keep the live implementation lane on source/mask/final-store ownership around the remaining case_0023 edge pixels, not broad threshold tuning.",
            "- `layer-no-bg-source-ownership`: keep Layer/no-bg 16bpc differences scoped to straight-vs-premultiplied source ownership in `FUN_181170480`.",
            "- `single-site-witness-missing`: no exact site-gated typed capture was retained; treat the return as debugger/gate evidence only, not AE exact.",
            "- `single-site-input-bound`: exact-gated field/source words were captured; keep the lane on compose input ownership and do not promote this to AE exact.",
            "- `single-site-writeback-bound`: exact-gated writer PF16 words were captured; keep the lane on final writeback/export ownership and do not promote this to AE exact.",
            "- `case0010-0011-compose-exact-address-partial-address-binding`: treat the return as address-model progress only; do not claim exact pixel field/source/store proof until same-run `RCX`/`RDX` reads and final PF16 words are bound.",
            "- `case0010-0011-compose-exact-address-proof`: both residual pixels are exact-address bound through field/source/final-store sites in one run.",
            "- `case0010-0011-compose-exact-address-witness-missing`: the narrowed exact-address gate still missed; retry the same request shape with the failed condition preserved.",
            "- `case0010-0011-field-store-witness-missing`: the returned package has only local/implied store directions; keep waiting for same-run Windows field/prestore/PF16/export facts before changing code.",
            "- `case0010-0011-field-store-classify`: classify whether the sparse R/A-only residual comes from field normalization, pre-store float, PF16 conversion, or export.",
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
    comparison = build_comparison(summary, args.request_id)
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
