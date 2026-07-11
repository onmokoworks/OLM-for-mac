#!/usr/bin/env python3
"""Classify returned OLMDirectionalBlur sampler/writeback trace facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DENSE_REQUEST_ID = "olmdirectionalblur_dense_sampler_trace_20260620"
SINGLE_SHOT_WITNESS_REQUEST_ID = "olmdirectionalblur_angle0_single_shot_witness_20260708"
HELPER_GATE_RETRY_REQUEST_ID = "olmdirectionalblur_angle0_helper_gate_retry_20260702"
HELPER_COVERAGE_REQUEST_ID = "olmdirectionalblur_helper_coverage_witness_20260630"
LEGACY_RESIDUAL_WITNESS_REQUEST_ID = "olmdirectionalblur_angle0_diagonal_residual_witness_20260622"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, default=None)
    parser.add_argument("--witness-json", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    args = parser.parse_args()
    if args.runtime_summary_json is None and args.witness_json is None:
        parser.error("at least one of --runtime-summary-json or --witness-json is required")
    return args


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
            "fill with",
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
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(rows, dict):
        return [rows]
    return []


def per_pixel_witness_records(case: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(case, dict):
        return []
    records = case.get("aex_per_pixel_witness_records")
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def complete_angle0_per_pixel_record(record: dict[str, Any]) -> bool:
    required = [
        "aex_output_to_ab_buffer_xy",
        "aex_output_buffer_identity",
        "aex_helper_local_source_xy",
        "aex_rowdriver_or_group_membership",
        "aex_validity_or_alpha_side_channel",
        "aex_accumulation_denominator",
        "aex_pre_writeback_rgba_float_or_hex",
        "aex_final_rgba_u8",
    ]
    return all(concrete_trace_value(record.get(key)) for key in required)


def angle0_per_pixel_status(case: dict[str, Any] | None) -> str | None:
    records = per_pixel_witness_records(case)
    if not records:
        return None
    complete = [record for record in records if complete_angle0_per_pixel_record(record)]
    concrete = [record for record in records if concrete_trace_value(record)]
    if len(complete) >= 2:
        return "per-pixel-witness-complete"
    if complete:
        return "per-pixel-witness-partial"
    if concrete:
        return "per-pixel-witness-values-incomplete"
    return "per-pixel-witness-placeholders-only"


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


def helper_gate_breakpoint_partial(row: dict[str, Any] | None, observations: dict[str, Any]) -> bool:
    if row is None or row.get("request_id") != HELPER_GATE_RETRY_REQUEST_ID:
        return False
    if str(row.get("status") or "").lower() != "answered_partial":
        return False
    for witness in witness_rows(observations):
        branch = str(witness.get("branch_or_dispatch") or "").lower()
        intermediate = witness.get("intermediate_values")
        if not isinstance(intermediate, dict):
            continue
        if "front-scatter-helper" not in branch:
            continue
        if intermediate.get("confirm_module_load") is not True:
            continue
        if intermediate.get("confirm_breakpoint_offsets") is not True:
            continue
        if intermediate.get("per_pixel_isolation") != "not_achieved":
            continue
        note = " ".join(
            str(intermediate.get(key) or "")
            for key in ("hit_storm_note", "previous_stall_root_cause")
        ).lower()
        if any(token in note for token in ("conditional", "single-shot", "hit storm", "storm", "excessive hits")):
            return True
    return False


def witness_case_xy(case: dict[str, Any]) -> tuple[int, int] | None:
    witness = case.get("witness")
    if isinstance(witness, dict):
        x = witness.get("x")
        y = witness.get("y")
        if isinstance(x, int) and isinstance(y, int):
            return (x, y)
    return None


def load_cli_witness(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("witness JSON must be an object")
    kind = payload.get("kind")
    if kind != "olmdirectionalblur_cli_witness":
        raise ValueError(f"unsupported witness kind: {kind!r}")
    return payload


def summarize_cli_witness(witness: dict[str, Any], path: Path) -> dict[str, Any]:
    points = witness.get("points", [])
    point_rows = [row for row in points if isinstance(row, dict)] if isinstance(points, list) else []
    return {
        "present": True,
        "kind": witness.get("kind"),
        "source_file": safe_source_file(path),
        "algorithm_family": witness.get("algorithm_family"),
        "width": witness.get("width"),
        "height": witness.get("height"),
        "pad_width": witness.get("pad_width"),
        "pad_height": witness.get("pad_height"),
        "crop_x": witness.get("crop_x"),
        "crop_y": witness.get("crop_y"),
        "front_strength_scaled": witness.get("front_strength_scaled"),
        "back_strength_scaled": witness.get("back_strength_scaled"),
        "strength_scale": witness.get("strength_scale"),
        "front_strength_rgb_denom": witness.get("front_strength_rgb_denom"),
        "aex_two_stage_output": witness.get("aex_two_stage_output"),
        "points": point_rows,
    }


def windows_coordinate_rows(row: dict[str, Any] | None) -> list[dict[str, Any]]:
    observations = observations_for(row)
    out: list[dict[str, Any]] = []
    for case in case_rows(observations):
        case_id = case.get("case_id")
        for witness in case.get("witness_pixels", []) if isinstance(case.get("witness_pixels", []), list) else []:
            if not isinstance(witness, dict):
                continue
            x = witness.get("x")
            y = witness.get("y")
            if isinstance(x, int) and isinstance(y, int):
                out.append({"kind": "dense", "case_id": case_id, "x": x, "y": y, "fields": witness})
        xy = witness_case_xy(case)
        if xy is not None:
            out.append({"kind": "residual", "case_id": case_id, "x": xy[0], "y": xy[1], "fields": case})
    return out


def local_witness_points(witness: dict[str, Any]) -> list[dict[str, Any]]:
    points = witness.get("points", [])
    if not isinstance(points, list):
        return []
    return [row for row in points if isinstance(row, dict)]


def compare_point_fields(local_point: dict[str, Any], windows_fields: dict[str, Any], field_map: dict[str, str]) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    for local_key, windows_key in field_map.items():
        comparisons[local_key] = {
            "local": local_point.get(local_key),
            "windows_field": windows_key,
            "windows": windows_fields.get(windows_key),
        }
    return comparisons


def build_local_windows_comparisons(row: dict[str, Any] | None, witness: dict[str, Any] | None) -> list[dict[str, Any]]:
    if witness is None:
        return []
    windows_rows = {(item["x"], item["y"]): item for item in windows_coordinate_rows(row)}
    comparisons: list[dict[str, Any]] = []
    for point in local_witness_points(witness):
        x = point.get("x")
        y = point.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            continue
        match = windows_rows.get((x, y))
        entry = {
            "x": x,
            "y": y,
            "local_fields": point,
            "windows_match_present": match is not None,
        }
        if match is None:
            comparisons.append(entry)
            continue
        windows_fields = match["fields"]
        entry.update(
            {
                "windows_match_kind": match["kind"],
                "windows_case_id": match.get("case_id"),
                "windows_fields": windows_fields,
                "field_comparison": compare_point_fields(
                    point,
                    windows_fields,
                    {
                        "source_alpha": "source_alpha",
                        "accum_sum_denominator": "aex_accumulation_denominator"
                        if match["kind"] == "residual"
                        else "loop_bounds_or_sample_count",
                        "effective_rgb_denominator": "aex_accumulation_denominator"
                        if match["kind"] == "residual"
                        else "intermediate_values",
                        "source_rgb": "aex_rotate_sampler_source_coordinates_order"
                        if match["kind"] == "residual"
                        else "sample_order",
                        "accum_rgb": "aex_accumulation_numerator_rgba_float_or_hex"
                        if match["kind"] == "residual"
                        else "intermediate_values",
                        "blurred_rgba_pre_rotateback": "aex_pre_writeback_rgba_float_or_hex",
                        "final_sample_rgba_pre_quant": "aex_pre_writeback_rgba_float_or_hex",
                        "final_rgba8": "aex_final_rgba_u8" if match["kind"] == "residual" else "final_rgba",
                    },
                ),
            }
        )
        comparisons.append(entry)
    return comparisons


def classify_dense(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    status = str(row.get("status") or "").lower()
    if "failed_before_module_load" in status or "before_module_load" in status:
        return "trace-failed-before-module-load"
    if helper_gate_breakpoint_partial(row, observations):
        return "loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup"
    for witness in witness_rows(observations):
        if concrete_trace_value(witness.get("pre_writeback_rgba_float_hex")) or concrete_trace_value(
            witness.get("final_rgba")
        ):
            return "sampler-or-writeback-values"
        if concrete_trace_value(witness.get("intermediate_values")) or concrete_trace_value(
            witness.get("loop_bounds_or_sample_count")
        ):
            return "sample-count-or-accumulation-values"
        if concrete_trace_value(witness.get("sample_order")) or concrete_trace_value(
            witness.get("branch_or_dispatch")
        ):
            return "sample-order-or-branch-values"
    if case_rows(observations):
        return "trace-structure-present-values-missing"
    if observations:
        return "trace-too-sparse"
    return "trace-too-sparse"


def classify_residual_case(case: dict[str, Any] | None, *, angle0: bool) -> str:
    if case is None:
        return "await-windows-trace"
    explicit = case.get("classification")
    if isinstance(explicit, str):
        lowered = explicit.strip().lower()
        if lowered and "|" not in lowered and "unresolved" not in lowered:
            return lowered
    final_rgba = case.get("aex_final_rgba_u8")
    pre_writeback = case.get("aex_pre_writeback_rgba_float_or_hex")
    numerator = case.get("aex_accumulation_numerator_rgba_float_or_hex") or case.get(
        "aex_accumulation_numerator_rgba"
    )
    denominator = case.get("aex_accumulation_denominator") or case.get("aex_normalization_denominator")
    ab_xy = case.get("aex_output_to_ab_buffer_xy")
    if angle0:
        per_pixel = angle0_per_pixel_status(case)
        if per_pixel in {"per-pixel-witness-complete", "per-pixel-witness-partial"}:
            return per_pixel
        rowdriver = case.get("aex_rowdriver_or_group_membership")
        validity = case.get("aex_validity_or_alpha_side_channel") or case.get(
            "aex_alpha_or_valid_side_channel"
        )
        if per_pixel:
            return per_pixel
        if concrete_trace_value(rowdriver):
            return "rowdriver-or-group-membership"
        if concrete_trace_value(validity):
            return "valid-alpha-side-channel"
        if concrete_trace_value(denominator) or concrete_trace_value(numerator):
            return "normalization-or-accumulation"
        if concrete_trace_value(pre_writeback) or concrete_trace_value(final_rgba):
            return "writeback-or-prewriteback"
        if concrete_trace_value(ab_xy):
            return "ab-buffer-mapping-only"
        return "trace-structure-present-values-missing"
    sampler = case.get("aex_rotate_sampler_source_coordinates_order")
    border = case.get("aex_border_or_validity_decision")
    gate = case.get("aex_group_size_or_opacity_gate")
    if concrete_trace_value(sampler):
        return "rotate-sampler"
    if concrete_trace_value(border):
        return "border-or-validity"
    if concrete_trace_value(gate):
        return "group-size-or-opacity"
    if concrete_trace_value(denominator) or concrete_trace_value(numerator):
        return "normalization-or-accumulation"
    if concrete_trace_value(pre_writeback) or concrete_trace_value(final_rgba):
        return "writeback-or-prewriteback"
    if concrete_trace_value(ab_xy):
        return "ab-buffer-mapping-only"
    return "trace-structure-present-values-missing"


def classify_residual(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    angle0 = classify_residual_case(case_by_id(observations, "case_0001"), angle0=True)
    diagonal = classify_residual_case(case_by_id(observations, "case_0005"), angle0=False)
    if angle0 == "trace-structure-present-values-missing" and diagonal == "trace-structure-present-values-missing":
        return "trace-structure-present-values-missing"
    return f"angle0:{angle0}; diagonal:{diagonal}"


def recommended_next_evidence(focus: str) -> str:
    if focus == "await-windows-trace":
        return "Import the focused Windows runtime trace return before changing DirectionalBlur behavior."
    if focus == "trace-failed-before-module-load":
        return "No algorithm fact was captured; rerun after the plug-in module loads."
    if focus == "trace-too-sparse":
        return "Do not tune from this return; rerun with concrete witness values or an exact breakpoint/watchpoint failure reason."
    if focus == "trace-structure-present-values-missing" or focus.endswith("trace-structure-present-values-missing"):
        return "Repeat with typed numeric witness values for sampler, group/validity, numerator, denominator, pre-writeback, and final byte."
    if focus == "sampler-or-writeback-values":
        return "Compare concrete sampler/pre-writeback/final values before changing implementation."
    if focus == "sample-count-or-accumulation-values":
        return "Ground loop bounds, weights, numerator/denominator, and accumulation before changing writeback."
    if focus == "sample-order-or-branch-values":
        return "Update sampler order/branch IR before tuning pixels."
    if focus == "loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup":
        return (
            "Loader and helper/normalize/writeback breakpoints are answered, but the per-pixel typed witness is still "
            "missing; rerun with conditional or single-shot breakpointing that isolates `(494,169)` / `(579,169)` "
            "without another hit storm."
        )
    parts = {}
    for segment in focus.split(";"):
        if ":" not in segment:
            continue
        key, value = segment.split(":", 1)
        parts[key.strip()] = value.strip()
    angle0 = parts.get("angle0")
    diagonal = parts.get("diagonal")
    messages: list[str] = []
    if angle0 == "rowdriver-or-group-membership":
        messages.append("angle-0: update rowdriver/group membership IR before changing sampler math.")
    elif angle0 == "per-pixel-witness-complete":
        messages.append("angle-0: compare the two independent per-pixel witness records before changing implementation.")
    elif angle0 == "per-pixel-witness-partial":
        messages.append("angle-0: one required pixel is complete; keep the request open for the missing per-pixel record.")
    elif angle0 == "per-pixel-witness-values-incomplete":
        messages.append("angle-0: per-pixel records exist but lack enough typed values to classify the lane.")
    elif angle0 == "per-pixel-witness-placeholders-only":
        messages.append("angle-0: per-pixel fields are present but only placeholders; rerun or fill concrete values.")
    elif angle0 == "valid-alpha-side-channel":
        messages.append("angle-0: prove the hidden validity/alpha side-channel used by the final pass.")
    elif angle0 == "normalization-or-accumulation":
        messages.append("angle-0: compare numerator/denominator and final normalization at `case_0001`.")
    elif angle0 == "writeback-or-prewriteback":
        messages.append("angle-0: add rowdriver/validity/normalization proof before treating this as byte writeback.")
    elif angle0 == "ab-buffer-mapping-only":
        messages.append("angle-0: map A/B buffer coordinates to output, then capture group or normalization values.")
    elif angle0 and angle0.startswith("trace"):
        messages.append("angle-0: rerun with typed numeric witness values, not placeholders.")
    if diagonal == "rotate-sampler":
        messages.append("diagonal: update rotate source-coordinate order and border behavior first.")
    elif diagonal == "border-or-validity":
        messages.append("diagonal: ground border/validity decisions before changing normalization/writeback.")
    elif diagonal == "group-size-or-opacity":
        messages.append("diagonal: ground group-size/opacity gate before changing sampler weights.")
    elif diagonal == "normalization-or-accumulation":
        messages.append("diagonal: compare numerator/denominator and final normalization at `case_0005`.")
    elif diagonal == "writeback-or-prewriteback":
        messages.append("diagonal: add sampler/validity/normalization proof before treating this as byte writeback.")
    elif diagonal == "ab-buffer-mapping-only":
        messages.append("diagonal: map A/B buffer coordinates to output, then capture sampler or validity values.")
    elif diagonal and diagonal.startswith("trace"):
        messages.append("diagonal: rerun with typed numeric witness values, not placeholders.")
    if messages:
        return " ".join(messages)
    return "Record the concrete witness that explains this focus before changing DirectionalBlur implementation."


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations_for(row)
    return {
        "present": row is not None,
        "status": row.get("status") if row else None,
        "summary": row.get("summary") if row else None,
        "source_file": safe_source_file(row.get("source_file")) if row else None,
        "ae_context": observations.get("ae_context") if observations else None,
        "cases": case_rows(observations),
        "directly_observed_vs_inferred": observations.get("directly_observed_vs_inferred")
        if observations
        else None,
    }


def select_windows_row(summary: dict[str, Any] | None) -> tuple[str, dict[str, Any] | None, str]:
    if summary is None:
        return DENSE_REQUEST_ID, None, "dense"
    helper_gate_request_id, helper_gate_row = find_first_result(
        summary,
        [SINGLE_SHOT_WITNESS_REQUEST_ID, HELPER_GATE_RETRY_REQUEST_ID],
    )
    if helper_gate_row is not None:
        mode = "residual" if helper_gate_request_id == SINGLE_SHOT_WITNESS_REQUEST_ID else "dense"
        return helper_gate_request_id, helper_gate_row, mode
    residual_request_id, residual_row = find_first_result(
        summary,
        [HELPER_COVERAGE_REQUEST_ID, LEGACY_RESIDUAL_WITNESS_REQUEST_ID],
    )
    if residual_row is not None:
        return residual_request_id, residual_row, "residual"
    return DENSE_REQUEST_ID, find_result(summary, DENSE_REQUEST_ID), "dense"


def build_comparison(summary: dict[str, Any] | None, witness: dict[str, Any] | None, witness_path: Path | None) -> dict[str, Any]:
    request_id, row, mode = select_windows_row(summary)
    observations = observations_for(row)
    focus = classify_residual(row, observations) if mode == "residual" else classify_dense(row, observations)
    comparison = {
        "kind": "olmdirectionalblur_trace_comparison",
        "schema": 3,
        "request_id": request_id,
        "likely_next_focus": focus,
        "recommended_next_evidence": recommended_next_evidence(focus),
        "windows": summarize_windows(row),
    }
    if mode == "residual":
        comparison["legacy_request_id"] = DENSE_REQUEST_ID
    if witness is not None and witness_path is not None:
        comparison["local_witness"] = summarize_cli_witness(witness, witness_path)
        comparison["local_vs_windows"] = build_local_windows_comparisons(row, witness)
    return comparison


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    windows = comparison["windows"]
    lines = [
        "# OLMDirectionalBlur Trace Comparison",
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
    local_witness = comparison.get("local_witness")
    if isinstance(local_witness, dict):
        lines.extend(
            [
                "## Local CLI Witness",
                "",
                f"- Source file: {md_value(local_witness.get('source_file'))}",
                f"- Algorithm family: {md_value(local_witness.get('algorithm_family'))}",
                f"- Output size: `{local_witness.get('width')}x{local_witness.get('height')}`",
                f"- Pad size: `{local_witness.get('pad_width')}x{local_witness.get('pad_height')}`",
                f"- Crop: `({local_witness.get('crop_x')}, {local_witness.get('crop_y')})`",
                f"- Front strength scaled: {md_value(local_witness.get('front_strength_scaled'))}",
                f"- RGB denom mode: {md_value(local_witness.get('front_strength_rgb_denom'))}",
                f"- Two-stage output: {md_value(local_witness.get('aex_two_stage_output'))}",
                f"- Points: {md_value(local_witness.get('points'))}",
                "",
            ]
        )
    local_vs_windows = comparison.get("local_vs_windows")
    if isinstance(local_vs_windows, list):
        lines.extend(
            [
                "## Coordinate Cross-Compare",
                "",
            ]
        )
        if local_vs_windows:
            for row in local_vs_windows:
                lines.append(
                    f"- ({row.get('x')}, {row.get('y')}): "
                    f"windows_match={md_value(row.get('windows_match_present'))}, "
                    f"case={md_value(row.get('windows_case_id'))}, "
                    f"kind={md_value(row.get('windows_match_kind'))}, "
                    f"fields={md_value(row.get('field_comparison'))}"
                )
        else:
            lines.append("- No local witness points were available for coordinate comparison.")
        lines.extend(
            [
                "",
            ]
        )
    lines.extend(
        [
        "## Interpretation",
        "",
        "- `sampler-or-writeback-values`: compare concrete residual witness values before changing code.",
        "- `sample-count-or-accumulation-values`: focus loop bounds, weights, denominator, and scatter accumulation.",
        "- `sample-order-or-branch-values`: update sampler order/branch IR before tuning pixels.",
        "- `loader-breakpoints-answered-per-pixel-typed-witness-missing-hit-storm-followup`: loader and broad helper/normalize/writeback reachability are proven, but typed per-pixel witness values still need a narrower rerun.",
        "- `trace-failed-before-module-load`: the run did not reach the plug-in; no algorithm fact was captured.",
        "- `trace-structure-present-values-missing`: repeat with typed numeric witness values.",
        "- `trace-too-sparse`: do not tune from broad PNGs or placeholders.",
        "- `angle0:*; diagonal:*`: focused residual witness classification for the 2026-06-22 package.",
        "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary = None
    witness = None
    witness_path = None
    if args.runtime_summary_json is not None:
        summary_path = resolve(root, args.runtime_summary_json)
        if not summary_path.exists():
            return fail(f"runtime summary JSON not found: {summary_path}")
        summary = load_json(summary_path)
        if not isinstance(summary, dict):
            return fail("runtime summary JSON must be an object")
    if args.witness_json is not None:
        witness_path = resolve(root, args.witness_json)
        if not witness_path.exists():
            return fail(f"witness JSON not found: {witness_path}")
        try:
            witness = load_cli_witness(witness_path)
        except ValueError as exc:
            return fail(str(exc))
    comparison = build_comparison(summary, witness, witness_path)
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
