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
HELPER_COVERAGE_REQUEST_ID = "olmdirectionalblur_helper_coverage_witness_20260630"
LEGACY_RESIDUAL_WITNESS_REQUEST_ID = "olmdirectionalblur_angle0_diagonal_residual_witness_20260622"


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


def classify_dense(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
    if row is None:
        return "await-windows-trace"
    status = str(row.get("status") or "").lower()
    if "failed_before_module_load" in status or "before_module_load" in status:
        return "trace-failed-before-module-load"
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
    numerator = case.get("aex_accumulation_numerator_rgba_float_or_hex")
    denominator = case.get("aex_accumulation_denominator")
    ab_xy = case.get("aex_output_to_ab_buffer_xy")
    if angle0:
        rowdriver = case.get("aex_rowdriver_or_group_membership")
        validity = case.get("aex_validity_or_alpha_side_channel")
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


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    residual_request_id, residual_row = find_first_result(
        summary,
        [HELPER_COVERAGE_REQUEST_ID, LEGACY_RESIDUAL_WITNESS_REQUEST_ID],
    )
    if residual_row is not None:
        observations = observations_for(residual_row)
        focus = classify_residual(residual_row, observations)
        return {
            "kind": "olmdirectionalblur_trace_comparison",
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
        "kind": "olmdirectionalblur_trace_comparison",
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
        "## Interpretation",
        "",
        "- `sampler-or-writeback-values`: compare concrete residual witness values before changing code.",
        "- `sample-count-or-accumulation-values`: focus loop bounds, weights, denominator, and scatter accumulation.",
        "- `sample-order-or-branch-values`: update sampler order/branch IR before tuning pixels.",
        "- `trace-failed-before-module-load`: the run did not reach the plug-in; no algorithm fact was captured.",
        "- `trace-structure-present-values-missing`: repeat with typed numeric witness values.",
        "- `trace-too-sparse`: do not tune from broad PNGs or placeholders.",
        "- `angle0:*; diagonal:*`: focused residual witness classification for the 2026-06-22 package.",
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
