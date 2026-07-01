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
LEGACY_RESIDUAL_WITNESS_REQUEST_ID = "olmradialblur_zoom_tiny_rotation_residual_witness_20260622"


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
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(rows, dict):
        return [rows]
    return []


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
    sampler_xy = case.get("aex_sampler_or_polar_xy") if zoom else case.get("aex_polar_or_source_xy")
    if not concrete_trace_value(final_rgba):
        if any(
            concrete_trace_value(value)
            for value in (pre_writeback, denominator, source_rgba, validity, sampler_xy)
        ):
            return "pre-writeback-values-without-final"
        return "trace-structure-present-values-missing"
    if not concrete_trace_value(pre_writeback):
        return "final-writeback-only"
    if zoom:
        if concrete_trace_value(writeback):
            return "writeback-or-alpha-normalization"
        if concrete_trace_value(denominator):
            return "alpha-normalization-or-writeback"
        return "zoom-final-values-need-denominator"
    if concrete_trace_value(validity) or concrete_trace_value(sampler_xy):
        return "sampler-or-validity"
    if concrete_trace_value(denominator):
        return "normalization-or-writeback"
    return "tiny-rotation-final-values-need-sampler"


def classify_residual(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    zoom = classify_residual_case(case_by_id(observations, "case_0009"), zoom=True)
    tiny = classify_residual_case(case_by_id(observations, "case_0010"), zoom=False)
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


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    residual_request_id, residual_row = find_first_result(
        summary,
        [FOLLOWUP_CALLER_COLLAPSE_REQUEST_ID, CALLER_COLLAPSE_REQUEST_ID, LEGACY_RESIDUAL_WITNESS_REQUEST_ID],
    )
    if residual_row is not None:
        observations = observations_for(residual_row)
        focus = classify_residual(residual_row, observations)
        return {
            "kind": "olmradialblur_trace_comparison",
            "schema": 2,
            "request_id": residual_request_id,
            "legacy_request_id": DENSE_REQUEST_ID,
            "likely_next_focus": focus,
            "recommended_next_evidence": recommended_next_evidence(focus),
            "windows": summarize_windows(residual_row),
        }
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
        "## Interpretation",
        "",
        "- `sampler-scatter-or-writeback-values`: compare concrete residual witness values before changing code.",
        "- `sampler-scatter-or-normalization-values`: focus span/count/denominator and scatter normalization.",
        "- `sampler-branch-or-order`: update sampler order/branch IR before tuning pixels.",
        "- `inner-span-31-registers-only`: keep the span-31 fact, but do not treat this as a dense residual answer.",
        "- `trace-structure-present-values-missing`: repeat with typed numeric witness values.",
        "- `trace-too-sparse`: do not tune from broad PNGs or placeholders.",
        "- `zoom:*; tiny_rotation:*`: focused residual witness classification for the 2026-06-22 package.",
        "",
    ]
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
