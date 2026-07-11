#!/usr/bin/env python3
"""Classify returned OLMRadialBlur dense sampler/scatter runtime trace facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DENSE_REQUEST_ID = "olmradialblur_dense_sampler_trace_20260620"
CALLER_COLLAPSE_REQUEST_ID = "olmradialblur_caller_collapse_witness_20260630"
FOLLOWUP_CALLER_COLLAPSE_REQUEST_ID = "olmradialblur_caller_collapse_followup_20260701"
TINY_ROTATION_FOLLOWUP_REQUEST_ID = "olmradialblur_tiny_rotation_substitute_path_followup_20260701"
TINY_ROTATION_BACKSTEP_REQUEST_ID = "olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701"
TINY_ROTATION_ANCHOR_WATCH_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_watch_followup_20260701"
TINY_ROTATION_ANCHOR_CONTEXT_WATCH_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702"
TINY_ROTATION_ANCHOR_CONTEXT_WATCH_RETRY_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702_retry_20260704"
TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_context_watch_followup_direct_postreturn_20260705"
TINY_ROTATION_ANCHOR_POINTER_WATCH_REQUEST_ID = "olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702"
CASE0010_FINAL_WRITEBACK_REQUEST_ID = "olmradialblur_case0010_final_writeback_20260708"
ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID = (
    "olmradialblur_zoom_case0009_final_plane_cells_20260709"
)
ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID = (
    "olmradialblur_zoom_case0009_final_plane_typed_20260710"
)
LEGACY_RESIDUAL_WITNESS_REQUEST_ID = "olmradialblur_zoom_tiny_rotation_residual_witness_20260622"
TINY_ROTATION_LANE_AUDIT = (
    Path(__file__).resolve().parents[1]
    / "refs"
    / "conformance"
    / "olmradialblur_tiny_rotation_lane_audit_20260701.json"
)
TINY_ROTATION_LANE_STATE = (
    Path(__file__).resolve().parents[1]
    / "refs"
    / "conformance"
    / "olmradialblur_tiny_rotation_lane_state_20260703.json"
)


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


def find_result(summary: dict[str, Any], request_id: str) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == request_id:
            return row
    return None


def find_first_result(summary: dict[str, Any], request_ids: list[str]) -> tuple[str, dict[str, Any] | None]:
    for request_id in request_ids:
        row = find_result(summary, request_id)
        if row is not None:
            return request_id, row
    return request_ids[0], None


def concrete_trace_value(value: Any) -> bool:
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
        if not text or text in {"0x...", "none", "null", "n/a", "unknown"}:
            return False
        if re.fullmatch(r"[-+]?0x[0-9a-f]+(?:\.[0-9a-f]*)?p[-+]?\d+", text):
            return True
        placeholder_needles = (
            "not traced",
            "not isolated",
            "not reached",
            "inferred",
            "likely",
            "expected",
            "still needs",
            "untraced",
            "was not captured",
            "see dense_merge_note",
            "see included ir",
        )
        if any(needle in text for needle in placeholder_needles):
            return False
        return False
    return False


def observations_for(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {}
    observations = row.get("observations", {})
    return observations if isinstance(observations, dict) else {"raw": observations}


def safe_source_file(value: Any) -> str | None:
    if not value:
        return None
    return Path(str(value)).name


def case_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows = observations.get("cases", [])
    if isinstance(rows, list):
        parsed = [row for row in rows if isinstance(row, dict)]
        if parsed:
            return parsed
    if isinstance(rows, dict):
        return [rows]
    if observations.get("request_id") == CASE0010_FINAL_WRITEBACK_REQUEST_ID:
        return [case0010_final_writeback_case(observations)]
    if observations.get("case_id") == "case_0010" and isinstance(observations.get("same_run_values"), dict):
        return [case0010_final_writeback_case(observations)]
    return []


def first_polar_cell_value(cells: Any, key: str) -> Any:
    if not isinstance(cells, list):
        return None
    values = []
    for cell in cells:
        if isinstance(cell, dict):
            values.append(cell.get(key))
    return values or None


def case0010_final_writeback_case(observations: dict[str, Any]) -> dict[str, Any]:
    same_run = observations.get("same_run_values")
    if not isinstance(same_run, dict):
        same_run = observations
    cells = same_run.get("polar_cells")
    witness = observations.get("witness") if isinstance(observations.get("witness"), dict) else {}
    return {
        "case_id": "case_0010",
        "classification": observations.get("classification"),
        "inverse_sampler_input_xy": same_run.get("final_inverse_sampler_xy")
        or same_run.get("inverse_sampler_input_xy")
        or witness.get("local_inverse_sampler_xy"),
        "contributing_polar_cells": [cell.get("cell_xy") for cell in cells if isinstance(cell, dict)]
        if isinstance(cells, list)
        else None,
        "accumulated_f250_rgba": same_run.get("accumulated_f250_rgba")
        or same_run.get("+0xf250_rgba")
        or first_polar_cell_value(cells, "f250_rgba_float"),
        "preserved_validity_f252": same_run.get("preserved_validity_f252")
        or same_run.get("+0xf252")
        or first_polar_cell_value(cells, "f252_validity_or_alpha"),
        "collapsed_e_rgba": same_run.get("collapsed_e_rgba")
        or same_run.get("normalized_e_rgba")
        or same_run.get("+0xe_rgba")
        or first_polar_cell_value(cells, "collapsed_e_rgba_float"),
        "direct_inverse_sampler_result_from_e": same_run.get("direct_inverse_sampler_result_from_e")
        or same_run.get("direct_inverse_sampler_result_rgba_float")
        or same_run.get("direct_inverse_sampler_e_rgba")
        or witness.get("local_direct_e_rgba_float"),
        "output_buffer_rgba_after_writeback": same_run.get("output_buffer_rgba_after_writeback")
        or same_run.get("output_buffer_rgba")
        or witness.get("local_output_world_rgba8"),
        "exported_rgba8_or_png_byte": same_run.get("exported_rgba8_or_png_byte")
        or same_run.get("exported_rgba8")
        or same_run.get("exported_byte")
        or same_run.get("final_exported_rgba8")
        or witness.get("current_windows_software_rgba8"),
        "alternate_final_output_path": same_run.get("alternate_final_output_path_if_any")
        or same_run.get("alternate_final_output_path"),
    }


def case_by_id(observations: dict[str, Any], case_id: str) -> dict[str, Any] | None:
    for row in case_rows(observations):
        if row.get("case_id") == case_id:
            return row
    return None


def witness_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows(observations):
        witnesses = case.get("witness_pixels", [])
        if isinstance(witnesses, dict):
            witnesses = [witnesses]
        if isinstance(witnesses, list):
            rows.extend(row for row in witnesses if isinstance(row, dict))
    return rows


def xy_tuple(row: dict[str, Any]) -> tuple[int, int] | None:
    value = (
        row.get("xy")
        or row.get("output_xy")
        or row.get("final_output_xy")
        or row.get("pixel_xy")
        or row.get("target_xy")
    )
    if isinstance(value, list | tuple) and len(value) >= 2:
        try:
            return int(value[0]), int(value[1])
        except (TypeError, ValueError):
            return None
    if "x" in row and "y" in row:
        try:
            return int(row["x"]), int(row["y"])
        except (TypeError, ValueError):
            return None
    return None


def final_plane_pixel_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows(observations):
        for key in (
            "final_plane_pixels",
            "witness_pixels",
            "pixels",
            "final_plane_cell_witnesses",
            "case0009_final_plane_cells",
        ):
            value = case.get(key)
            if isinstance(value, dict):
                rows.append(value)
            elif isinstance(value, list):
                rows.extend(item for item in value if isinstance(item, dict))
    for key in (
        "final_plane_pixels",
        "witness_pixels",
        "pixels",
        "final_plane_cell_witnesses",
        "case0009_final_plane_cells",
    ):
        value = observations.get(key)
        if isinstance(value, dict):
            rows.append(value)
        elif isinstance(value, list):
            rows.extend(item for item in value if isinstance(item, dict))
    return rows


def has_final_plane_cell_facts(row: dict[str, Any]) -> bool:
    final_byte = (
        row.get("windows_final_rgba8")
        or row.get("final_rgba8")
        or row.get("final_rgba")
        or row.get("exported_rgba8_or_png_byte")
    )
    sampler_xy = (
        row.get("final_inverse_sampler_xy")
        or row.get("inverse_sampler_input_xy")
        or row.get("sampler_xy")
    )
    cells = (
        row.get("four_bilinear_source_cells")
        or row.get("bilinear_source_cells")
        or row.get("final_plane_cells")
        or row.get("source_cells")
    )
    weights = row.get("bilinear_weights") or row.get("weights")
    alpha_sum = (
        row.get("final_sample_alpha_sum")
        or row.get("final_sample_alpha")
        or row.get("pre_byte_alpha")
        or row.get("pre_byte_rgba_float")
        or row.get("pre_byte_rgba")
        or row.get("pre_writeback_rgba_float")
    )
    if not all(concrete_trace_value(value) for value in (final_byte, sampler_xy, cells, weights, alpha_sum)):
        return False
    return isinstance(cells, list) and len(cells) >= 4


TYPED_CASE0009_POINTS = ((7, 0), (8, 0), (24, 0))


def typed_witness_value(value: Any) -> bool:
    """Accept complete typed values while rejecting template/placeholders."""
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        lowered = value.strip().lower()
        if not lowered or lowered in {"null", "none", "n/a", "unknown", "0x..."}:
            return False
        return not any(
            needle in lowered
            for needle in (
                "not traced",
                "not isolated",
                "not reached",
                "inferred",
                "expected",
                "untraced",
                "was not captured",
            )
        )
    if isinstance(value, list):
        return bool(value) and all(typed_witness_value(item) for item in value)
    if isinstance(value, dict):
        return bool(value) and all(typed_witness_value(item) for item in value.values())
    return False


def typed_case0009_point_complete(point: Any) -> bool:
    if not isinstance(point, dict) or xy_tuple(point) not in TYPED_CASE0009_POINTS:
        return False
    if not all(
        typed_witness_value(point.get(key))
        for key in ("observed_rgba8", "inverse_sample_xy", "final_alpha_sum", "pre_byte_alpha")
    ):
        return False
    cells = point.get("cells")
    if not isinstance(cells, list) or len(cells) != 4:
        return False
    required_cell_fields = ("cell_id", "plus_0xe_rgba_float", "plus_0xf252", "bilinear_weight")
    return all(
        isinstance(cell, dict)
        and all(typed_witness_value(cell.get(key)) for key in required_cell_fields)
        for cell in cells
    )


def classify_zoom_case0009_final_plane_typed(
    row: dict[str, Any] | None, observations: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    if row is None:
        return "missing", {"reason": "await-windows-trace", "points": []}
    points = observations.get("points", [])
    points = points if isinstance(points, list) else []
    by_xy = {xy_tuple(point): point for point in points if isinstance(point, dict) and xy_tuple(point)}
    binding = all(
        typed_witness_value(observations.get(key))
        for key in ("run_id", "hook_or_watchpoint", "console_artifact")
    )
    complete_points = [xy for xy in TYPED_CASE0009_POINTS if typed_case0009_point_complete(by_xy.get(xy))]
    primary_complete = (7, 0) in complete_points
    failure_reason = observations.get("failed_reason") or row.get("failed_reason")
    if primary_complete and len(complete_points) == len(TYPED_CASE0009_POINTS) and binding:
        classification = "complete"
    elif primary_complete and isinstance(failure_reason, str) and bool(failure_reason.strip()):
        classification = "partial"
    else:
        classification = "missing"
    surfaced_points = []
    for xy in TYPED_CASE0009_POINTS:
        point = by_xy.get(xy)
        surfaced_points.append(
            {
                "xy": list(xy),
                "complete": xy in complete_points,
                "observed_rgba8": point.get("observed_rgba8") if point else None,
                "inverse_sample_xy": point.get("inverse_sample_xy") if point else None,
                "cells": point.get("cells") if point else None,
                "final_alpha_sum": point.get("final_alpha_sum") if point else None,
                "pre_byte_alpha": point.get("pre_byte_alpha") if point else None,
                "failed_reason": point.get("failed_reason") if point else None,
            }
        )
    return classification, {
        "run_id": observations.get("run_id"),
        "hook_or_watchpoint": observations.get("hook_or_watchpoint"),
        "console_artifact": observations.get("console_artifact"),
        "points": surfaced_points,
        "complete_points": [list(xy) for xy in complete_points],
        "failed_reason": failure_reason,
    }


def classify_zoom_case0009_final_plane(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    rows = final_plane_pixel_rows(observations)
    primary = {(6, 0), (7, 0), (12, 0)}
    controls = {(3, 0), (4, 0), (8, 0), (10, 0), (11, 0), (13, 0), (24, 0), (25, 0), (26, 0), (27, 0), (28, 0)}
    complete_primary = {
        xy_tuple(pixel)
        for pixel in rows
        if xy_tuple(pixel) in primary and has_final_plane_cell_facts(pixel)
    }
    complete_controls = {
        xy_tuple(pixel)
        for pixel in rows
        if xy_tuple(pixel) in controls and has_final_plane_cell_facts(pixel)
    }
    if len(complete_primary) >= 3 and len(complete_controls) >= 4:
        return "zoom_case0009:final-plane-cells-answered"
    if complete_primary:
        return "zoom_case0009:final-plane-cells-partial"
    row_text = json.dumps(
        {"status": row.get("status"), "summary": row.get("summary"), "observations": observations},
        ensure_ascii=False,
        sort_keys=True,
    ).lower()
    if rows or any(needle in row_text for needle in ("final rgba", "png byte", "wrapper", "hit count")):
        return "zoom_case0009:final-plane-witness-missing"
    return "trace-structure-present-values-missing"


def summary_has_inner_span_registers(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    required = ("olmradialblur+0x26e5", "+0x1d18", "r14d=0x1f")
    return all(part in lowered for part in required)


def classify_dense(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    for witness in witness_rows(observations):
        if concrete_trace_value(witness.get("pre_writeback_rgba_float_hex")) or concrete_trace_value(
            witness.get("final_rgba")
        ):
            return "sampler-scatter-or-writeback-values"
        if concrete_trace_value(witness.get("intermediate_values")) or concrete_trace_value(
            witness.get("loop_bounds_or_sample_count")
        ):
            return "sampler-scatter-or-normalization-values"
        if concrete_trace_value(witness.get("sample_order")) or concrete_trace_value(
            witness.get("branch_or_dispatch")
        ):
            return "sampler-branch-or-order"
    if summary_has_inner_span_registers(row.get("summary")):
        return "inner-span-31-registers-only"
    if case_rows(observations):
        return "trace-structure-present-values-missing"
    if observations:
        return "trace-too-sparse"
    return "trace-too-sparse"


def classify_residual_case(case: dict[str, Any] | None, *, zoom: bool) -> str:
    if case is None:
        return "await-windows-trace"
    explicit = case.get("classification")
    if isinstance(explicit, str):
        lowered = explicit.strip().lower()
        if lowered and "unresolved" not in lowered and "|" not in lowered:
            return lowered
    final_rgba = case.get("aex_final_rgba_u8")
    pre_writeback = case.get("aex_pre_writeback_rgba_float_or_hex")
    denominator = case.get("aex_normalization_denominator")
    writeback = case.get("aex_writeback_operation")
    source_rgba = case.get("aex_source_or_polar_rgba_float")
    validity = case.get("aex_validity_or_border_decision")
    substitute = case.get("aex_fallback_or_substitute_path")
    preserved_validity = case.get("aex_preserved_validity_f252")
    accumulated = case.get("aex_accumulated_f250_rgba_float")
    normalized_final = case.get("aex_normalized_final_e_rgba_float")
    sampler_xy = case.get("aex_sampler_or_polar_xy") if zoom else case.get("aex_polar_or_source_xy")
    inverse_sampler_xy = case.get("aex_inverse_sampler_input_xy")
    if not concrete_trace_value(final_rgba):
        if any(
            concrete_trace_value(value)
            for value in (
                pre_writeback,
                denominator,
                source_rgba,
                validity,
                sampler_xy,
                inverse_sampler_xy,
                substitute,
                preserved_validity,
                accumulated,
                normalized_final,
            )
        ):
            return "pre-writeback-values-without-final"
        return "trace-structure-present-values-missing"
    if not zoom and (
        concrete_trace_value(substitute)
        or concrete_trace_value(accumulated)
        or concrete_trace_value(normalized_final)
        or concrete_trace_value(source_rgba)
        or concrete_trace_value(inverse_sampler_xy)
    ):
        return "substitute-or-upstream-rgb"
    if not concrete_trace_value(pre_writeback):
        return "final-writeback-only"
    if zoom:
        if concrete_trace_value(writeback):
            return "writeback-or-alpha-normalization"
        if concrete_trace_value(denominator):
            return "alpha-normalization-or-writeback"
        return "zoom-final-values-need-denominator"
    if concrete_trace_value(substitute) or concrete_trace_value(accumulated) or concrete_trace_value(normalized_final):
        return "substitute-or-upstream-rgb"
    if concrete_trace_value(validity) or concrete_trace_value(sampler_xy) or concrete_trace_value(inverse_sampler_xy):
        return "sampler-or-validity"
    if concrete_trace_value(denominator):
        return "normalization-or-writeback"
    return "tiny-rotation-final-values-need-sampler"


def classify_residual(row: dict[str, Any] | None, observations: dict[str, Any], request_id: str) -> str:
    if row is None:
        return "await-windows-trace"
    if request_id == CASE0010_FINAL_WRITEBACK_REQUEST_ID:
        case = case_by_id(observations, "case_0010") or observations.get("case_0010") or observations
        if not isinstance(case, dict):
            case = {}
        row_text = json.dumps(
            {"status": row.get("status"), "summary": row.get("summary"), "observations": observations},
            ensure_ascii=False,
            sort_keys=True,
        ).lower()
        if row.get("status") == "answered_partial" and (
            "no fresh same-run" in row_text or "not freshly re-hooked" in row_text
        ):
            return "tiny_rotation:case0010-final-writeback-partial-missing-same-run-debugger-stop"
        final_byte = (
            case.get("exported_rgba8_or_png_byte")
            or case.get("exported_rgba8")
            or case.get("exported_byte")
            or case.get("final_exported_rgba8")
        )
        output_buffer = case.get("output_buffer_rgba_after_writeback") or case.get("output_buffer_rgba")
        collapsed_e = case.get("collapsed_e_rgba") or case.get("normalized_e_rgba") or case.get("+0xe_rgba")
        direct_e_sample = (
            case.get("direct_inverse_sampler_result_from_e")
            or case.get("direct_inverse_sampler_e_rgba")
            or case.get("direct_e_sampler_rgba")
            or case.get("+0xe_direct_inverse_sampler_rgba")
        )
        validity = case.get("preserved_validity_f252") or case.get("+0xf252")
        accumulated = case.get("accumulated_f250_rgba") or case.get("+0xf250_rgba")
        if all(
            concrete_trace_value(value)
            for value in (final_byte, output_buffer, collapsed_e, direct_e_sample, validity, accumulated)
        ):
            return "tiny_rotation:case0010-final-writeback-provenance"
        fields = {
            "export": final_byte,
            "output-buffer": output_buffer,
            "+0xe": collapsed_e,
            "direct-+0xe-sampler": direct_e_sample,
            "+0xf252": validity,
            "+0xf250": accumulated,
        }
        missing = [name for name, value in fields.items() if not concrete_trace_value(value)]
        if len(missing) < len(fields):
            if len(missing) == 1:
                return f"tiny_rotation:case0010-final-writeback-partial-missing-{missing[0]}"
            return "tiny_rotation:case0010-final-writeback-partial"
        return "trace-structure-present-values-missing"
    if request_id == TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID:
        status = row.get("status")
        if status == "partial_with_direct_postreturn_registers":
            return "tiny_rotation:direct-postreturn-captured-upstream-branch-still-missing"
    zoom = classify_residual_case(case_by_id(observations, "case_0009"), zoom=True)
    tiny = classify_residual_case(case_by_id(observations, "case_0010"), zoom=False)
    if request_id in {
        TINY_ROTATION_ANCHOR_CONTEXT_WATCH_REQUEST_ID,
        TINY_ROTATION_ANCHOR_CONTEXT_WATCH_RETRY_REQUEST_ID,
        TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID,
    } and tiny == "substitute-or-upstream-rgb":
        return "tiny_rotation:anchor-context-upstream-branch"
    if request_id in {
        TINY_ROTATION_ANCHOR_POINTER_WATCH_REQUEST_ID,
        TINY_ROTATION_ANCHOR_WATCH_REQUEST_ID,
        TINY_ROTATION_BACKSTEP_REQUEST_ID,
        TINY_ROTATION_FOLLOWUP_REQUEST_ID,
    } and tiny == "substitute-or-upstream-rgb":
        return "tiny_rotation:upstream-branch-not-isolated"
    if request_id in {TINY_ROTATION_FOLLOWUP_REQUEST_ID, TINY_ROTATION_BACKSTEP_REQUEST_ID}:
        return f"tiny_rotation:{tiny}"
    if zoom == "trace-structure-present-values-missing" and tiny == "trace-structure-present-values-missing":
        return "trace-structure-present-values-missing"
    return f"zoom:{zoom}; tiny_rotation:{tiny}"


def recommended_next_evidence(focus: str) -> str:
    if focus == "await-windows-trace":
        return "Import the focused Windows runtime trace return before changing RadialBlur behavior."
    if focus == "trace-too-sparse":
        return "Do not tune from this return; rerun with concrete witness values or an exact breakpoint/watchpoint failure reason."
    if focus == "trace-structure-present-values-missing" or focus.endswith("trace-structure-present-values-missing"):
        return "Repeat with typed numeric witness values for pre-writeback, final byte, sampler, denominator, or validity."
    if focus == "sampler-scatter-or-writeback-values":
        return "Compare concrete sampler/scatter/pre-writeback/final values before changing the implementation."
    if focus == "sampler-scatter-or-normalization-values":
        return "Ground span/count/denominator and scatter normalization before changing output writeback."
    if focus == "sampler-branch-or-order":
        return "Update sampler branch/order IR before tuning pixels."
    if focus == "inner-span-31-registers-only":
        return "Keep the span-31 fact, but request typed sampler/scatter/writeback witnesses before changing Inner behavior."
    if focus == "zoom_case0009:final-plane-cells-answered":
        return "Use the same-run final-plane cell ids/alphas/weights to update the Zoom case_0009 IR and only then decide whether the C++ cell-set or coordinate rule changes."
    if focus == "zoom_case0009:final-plane-cells-partial":
        return "Preserve the captured primary final-plane facts, but request the missing primary/control cells before promoting this to proof or changing broad RadialBlur behavior."
    if focus == "zoom_case0009:final-plane-witness-missing":
        return "Do not tune from this return; rerun the final-plane cell witness with typed same-run cells/weights/alpha sums for primary pixels and controls."
    if focus == "zoom_case0009:final-plane-typed-complete":
        return "Use the same-run `(7,0)`, `(8,0)`, and `(24,0)` cell ids, `+0xe`, `+0xf252`, weights, and pre-byte alpha to update the Zoom case_0009 IR."
    if focus == "zoom_case0009:final-plane-typed-partial":
        return "Preserve the complete `(7,0)` typed witness and exact isolation failure; do not promote controls or change broad RadialBlur behavior."
    if focus == "zoom_case0009:final-plane-typed-missing":
        return "Do not tune from this return; rerun one same-run Windows witness with all typed fields and the exact hook/watchpoint artifact."
    parts = {}
    for segment in focus.split(";"):
        if ":" not in segment:
            continue
        key, value = segment.split(":", 1)
        parts[key.strip()] = value.strip()
    zoom = parts.get("zoom")
    tiny = parts.get("tiny_rotation")
    messages: list[str] = []
    if zoom in {"writeback-or-alpha-normalization", "alpha-normalization-or-writeback"}:
        messages.append("Zoom: compare denominator, pre-writeback alpha/RGBA, and byte conversion at `case_0009`.")
    elif zoom == "final-writeback-only":
        messages.append("Zoom: add pre-writeback float and denominator values; final bytes alone cannot choose the rule.")
    elif zoom == "pre-writeback-values-without-final":
        messages.append("Zoom: add final byte/writeback operation to connect pre-writeback values to the PNG residual.")
    elif zoom == "zoom-final-values-need-denominator":
        messages.append("Zoom: add normalization denominator and writeback operation before changing the path.")
    elif zoom and zoom.startswith("trace"):
        messages.append("Zoom: rerun with typed numeric witness values, not placeholders.")
    if tiny == "sampler-or-validity":
        messages.append("tiny Rotation: compare inverse sampler/polar coordinates and border validity at `case_0010`.")
    elif tiny == "case0010-final-writeback-provenance":
        messages.append("tiny Rotation: classify the returned `+0xf250/+0xf252/+0xe/output-buffer/export` chain before any implementation change.")
    elif tiny == "case0010-final-writeback-partial-missing-export":
        messages.append("tiny Rotation: request the missing same-run export byte; `+0xf250/+0xf252/+0xe/direct-sampler/output-buffer` are already the proof material to preserve.")
    elif tiny == "case0010-final-writeback-partial-missing-output-buffer":
        messages.append("tiny Rotation: request the missing output-buffer writeback value before deciding whether the gap is writeback or export/provenance.")
    elif tiny == "case0010-final-writeback-partial-missing-+0xe":
        messages.append("tiny Rotation: request the missing collapsed `+0xe` value before connecting `+0xf250/+0xf252` to final output.")
    elif tiny == "case0010-final-writeback-partial-missing-direct-+0xe-sampler":
        messages.append("tiny Rotation: request the missing direct inverse-sampler result from `+0xe`; the collapsed cells alone do not prove final sampling.")
    elif tiny == "case0010-final-writeback-partial-missing-+0xf252":
        messages.append("tiny Rotation: request the missing preserved validity `+0xf252` side channel before changing caller-collapse behavior.")
    elif tiny == "case0010-final-writeback-partial-missing-+0xf250":
        messages.append("tiny Rotation: request the missing accumulated `+0xf250` RGBA before changing accumulation or normalization behavior.")
    elif tiny == "case0010-final-writeback-partial-missing-same-run-debugger-stop":
        messages.append("tiny Rotation: current return is useful provenance evidence, but still needs one same-run Windows debugger stop tying `+0xf250/+0xf252/+0xe/direct sampler/output-buffer/export` together before changing code.")
    elif tiny == "case0010-final-writeback-partial":
        messages.append("tiny Rotation: final-writeback evidence is partial; keep this as proof material, but request the missing output-buffer/export or `+0xe` link before changing code.")
    elif tiny == "anchor-context-upstream-branch":
        messages.append("tiny Rotation: retain sampled-cell address plus `rsi/rbp/rsp` qword windows and neighboring-row watches so the first upstream promotion branch is captured at `case_0010`.")
    elif tiny == "direct-postreturn-captured-upstream-branch-still-missing":
        messages.append("tiny Rotation: `+0x7b4a` and `+0x41f8` are now retained, so the next useful witness is the first upstream promotion branch itself, plus `+0x7404` or equivalent normalized `+0xe` state that explains how near-black becomes final white at `case_0010`.")
    elif tiny == "upstream-branch-not-isolated":
        messages.append("tiny Rotation: keep the stable inverse-sampler anchor, but the next useful witness must retain the first upstream promotion/substitute branch rather than another anchor-only replay.")
    elif tiny == "substitute-or-upstream-rgb":
        messages.append("tiny Rotation: compare substitute/fallback branch state plus source-population, `+0xf252`, `+0xf250`, and normalized `+0xe` RGBA at `case_0010`.")
    elif tiny == "normalization-or-writeback":
        messages.append("tiny Rotation: denominator/writeback is concrete, but sampler/validity still needs proof.")
    elif tiny == "final-writeback-only":
        messages.append("tiny Rotation: add sampler/validity and pre-writeback values; final bytes alone are not enough.")
    elif tiny == "pre-writeback-values-without-final":
        messages.append("tiny Rotation: add final byte/writeback operation to connect pre-writeback values to the PNG residual.")
    elif tiny == "tiny-rotation-final-values-need-sampler":
        messages.append("tiny Rotation: add inverse sampler/polar coordinate and border validity before changing code.")
    elif tiny and tiny.startswith("trace"):
        messages.append("tiny Rotation: rerun with typed numeric witness values, not placeholders.")
    if messages:
        return " ".join(messages)
    return "Record the concrete witness that explains this focus before changing RadialBlur implementation."


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations_for(row)
    final_writeback = None
    if row is not None and row.get("request_id") == CASE0010_FINAL_WRITEBACK_REQUEST_ID:
        case = case_by_id(observations, "case_0010") or observations.get("case_0010") or observations
        if isinstance(case, dict):
            final_writeback = {
                "module_base_or_aex_version": case.get("module_base_or_aex_version")
                or case.get("module_base")
                or case.get("aex_version"),
                "inverse_sampler_input_xy": case.get("inverse_sampler_input_xy")
                or case.get("aex_inverse_sampler_input_xy"),
                "contributing_polar_cells": case.get("contributing_polar_cells")
                or case.get("four_contributing_polar_cells"),
                "accumulated_f250_rgba": case.get("accumulated_f250_rgba") or case.get("+0xf250_rgba"),
                "preserved_validity_f252": case.get("preserved_validity_f252") or case.get("+0xf252"),
                "collapsed_e_rgba": case.get("collapsed_e_rgba")
                or case.get("normalized_e_rgba")
                or case.get("+0xe_rgba"),
                "direct_inverse_sampler_result_from_e": case.get("direct_inverse_sampler_result_from_e")
                or case.get("direct_inverse_sampler_e_rgba")
                or case.get("direct_e_sampler_rgba")
                or case.get("+0xe_direct_inverse_sampler_rgba"),
                "output_buffer_rgba_after_writeback": case.get("output_buffer_rgba_after_writeback")
                or case.get("output_buffer_rgba"),
                "exported_rgba8_or_png_byte": case.get("exported_rgba8_or_png_byte")
                or case.get("exported_rgba8")
                or case.get("exported_byte")
                or case.get("final_exported_rgba8"),
                "alternate_final_output_path": case.get("alternate_final_output_path"),
            }
    return {
        "present": row is not None,
        "status": row.get("status") if row else None,
        "summary": row.get("summary") if row else None,
        "source_file": safe_source_file(row.get("source_file")) if row else None,
        "ae_context": observations.get("ae_context") if observations else None,
        "cases": case_rows(observations),
        "case0010_final_writeback": final_writeback,
        "directly_observed_vs_inferred": observations.get("directly_observed_vs_inferred")
        if observations
        else None,
    }


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    residual_request_id, residual_row = find_first_result(
        summary,
        [
            ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID,
            ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID,
            CASE0010_FINAL_WRITEBACK_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_RETRY_REQUEST_ID,
            TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_POINTER_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_WATCH_REQUEST_ID,
            TINY_ROTATION_BACKSTEP_REQUEST_ID,
            TINY_ROTATION_FOLLOWUP_REQUEST_ID,
            FOLLOWUP_CALLER_COLLAPSE_REQUEST_ID,
            CALLER_COLLAPSE_REQUEST_ID,
            LEGACY_RESIDUAL_WITNESS_REQUEST_ID,
        ],
    )
    if residual_row is not None:
        observations = observations_for(residual_row)
        if residual_request_id == ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID:
            classification, typed_witness = classify_zoom_case0009_final_plane_typed(
                residual_row, observations
            )
            focus = f"zoom_case0009:final-plane-typed-{classification}"
        elif residual_request_id == ZOOM_CASE0009_FINAL_PLANE_CELLS_REQUEST_ID:
            focus = classify_zoom_case0009_final_plane(residual_row, observations)
        else:
            focus = classify_residual(residual_row, observations, residual_request_id)
        comparison = {
            "kind": "olmradialblur_trace_comparison",
            "schema": 2,
            "request_id": residual_request_id,
            "legacy_request_id": DENSE_REQUEST_ID,
            "likely_next_focus": focus,
            "recommended_next_evidence": recommended_next_evidence(focus),
            "windows": summarize_windows(residual_row),
        }
        if residual_request_id == ZOOM_CASE0009_FINAL_PLANE_TYPED_REQUEST_ID:
            comparison["classification"] = classification
            comparison["windows"]["case0009_final_plane_typed"] = typed_witness
        if residual_request_id in {
            TINY_ROTATION_FOLLOWUP_REQUEST_ID,
            TINY_ROTATION_BACKSTEP_REQUEST_ID,
            TINY_ROTATION_ANCHOR_POINTER_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_RETRY_REQUEST_ID,
            TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID,
            CASE0010_FINAL_WRITEBACK_REQUEST_ID,
        } and TINY_ROTATION_LANE_AUDIT.exists():
            audit = load_json(TINY_ROTATION_LANE_AUDIT)
            comparison["local_tiny_rotation_context"] = {
                "decision": audit.get("decision"),
                "witness_xy": audit.get("witness_xy"),
                "current_candidate_rgba": audit.get("current_candidate_rgba"),
                "windows_reference_rgba": audit.get("windows_reference_rgba"),
                "same_row_structure": audit.get("same_row_structure"),
                "source_polar_structure": audit.get("source_polar_structure"),
                "row_coupling_probe": audit.get("row_coupling_probe"),
            }
        if residual_request_id in {
            TINY_ROTATION_FOLLOWUP_REQUEST_ID,
            TINY_ROTATION_BACKSTEP_REQUEST_ID,
            TINY_ROTATION_ANCHOR_POINTER_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_REQUEST_ID,
            TINY_ROTATION_ANCHOR_CONTEXT_WATCH_RETRY_REQUEST_ID,
            TINY_ROTATION_DIRECT_POSTRETURN_REQUEST_ID,
            CASE0010_FINAL_WRITEBACK_REQUEST_ID,
        } and TINY_ROTATION_LANE_STATE.exists():
            state = load_json(TINY_ROTATION_LANE_STATE)
            comparison["local_tiny_rotation_lane_state"] = {
                "status": state.get("status"),
                "safe_claim": state.get("safe_claim"),
                "pending_windows_followup": state.get("pending_windows_followup"),
                "decision_ladder": state.get("decision_ladder"),
                "forbidden_actions": state.get("forbidden_actions"),
            }
        return comparison
    row = find_result(summary, DENSE_REQUEST_ID)
    observations = observations_for(row)
    focus = classify_dense(row, observations)
    return {
        "kind": "olmradialblur_trace_comparison",
        "schema": 2,
        "request_id": DENSE_REQUEST_ID,
        "likely_next_focus": focus,
        "recommended_next_evidence": recommended_next_evidence(focus),
        "windows": summarize_windows(row),
    }


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    local_tiny = comparison.get("local_tiny_rotation_context")
    local_lane_state = comparison.get("local_tiny_rotation_lane_state")
    lines = [
        "# OLMRadialBlur Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Recommended next evidence: {comparison['recommended_next_evidence']}",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- AE context: {md_value(windows.get('ae_context'))}",
        f"- Cases: {md_value(windows.get('cases'))}",
        f"- Observed/inferred split: {md_value(windows.get('directly_observed_vs_inferred'))}",
        "",
    ]
    if local_tiny:
        lines.extend(
            [
                "## Local tiny Rotation Context",
                "",
                f"- Decision: {md_value(local_tiny.get('decision'))}",
                f"- Witness XY: {md_value(local_tiny.get('witness_xy'))}",
                f"- Current candidate RGBA: {md_value(local_tiny.get('current_candidate_rgba'))}",
                f"- Windows reference RGBA: {md_value(local_tiny.get('windows_reference_rgba'))}",
                f"- Same-row structure: {md_value(local_tiny.get('same_row_structure'))}",
                f"- Source-polar structure: {md_value(local_tiny.get('source_polar_structure'))}",
                f"- Row-coupling probe: {md_value(local_tiny.get('row_coupling_probe'))}",
                "",
            ]
        )
    if local_lane_state:
        lines.extend(
            [
                "## Local tiny Rotation Lane State",
                "",
                f"- Status: {md_value(local_lane_state.get('status'))}",
                f"- Safe claim: {local_lane_state.get('safe_claim') or '-'}",
                f"- Pending Windows follow-up: {md_value(local_lane_state.get('pending_windows_followup'))}",
                f"- Decision ladder: {md_value(local_lane_state.get('decision_ladder'))}",
                f"- Forbidden actions: {md_value(local_lane_state.get('forbidden_actions'))}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- `sampler-scatter-or-writeback-values`: compare concrete residual witness values before changing code.",
            "- `sampler-scatter-or-normalization-values`: focus span/count/denominator and scatter normalization.",
            "- `sampler-branch-or-order`: update sampler order/branch IR before tuning pixels.",
            "- `inner-span-31-registers-only`: keep the span-31 fact, but do not treat this as a dense residual answer.",
            "- `trace-structure-present-values-missing`: repeat with typed numeric witness values.",
            "- `trace-too-sparse`: do not tune from broad PNGs or placeholders.",
            "- `tiny_rotation:anchor-context-upstream-branch`: this is now the narrow live lane; preserve sampled-cell address, neighboring-row context, and first promotion-branch ownership.",
            "- `tiny_rotation:upstream-branch-not-isolated`: anchor-only or backstep-only evidence is still insufficient; keep chasing the first upstream promotion/substitute branch.",
            "- `tiny_rotation:substitute-or-upstream-rgb`: prefer substitute/fallback or source-population ownership over validity-only or final-byte stories.",
            "- `zoom:*; tiny_rotation:*`: focused residual witness classification for the mixed outer follow-up lanes.",
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
