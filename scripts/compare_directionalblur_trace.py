#!/usr/bin/env python3
"""Classify returned OLMDirectionalBlur dense sampler/writeback trace facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "olmdirectionalblur_dense_sampler_trace_20260620"


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
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == REQUEST_ID:
            return row
    return None


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


def case_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows = observations.get("cases", [])
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(rows, dict):
        return [rows]
    return []


def witness_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in case_rows(observations):
        witnesses = case.get("witness_pixels", [])
        if isinstance(witnesses, dict):
            witnesses = [witnesses]
        if isinstance(witnesses, list):
            rows.extend(row for row in witnesses if isinstance(row, dict))
    return rows


def classify(row: dict[str, Any] | None, observations: dict[str, Any]) -> str:
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


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations_for(row)
    return {
        "present": row is not None,
        "status": row.get("status") if row else None,
        "summary": row.get("summary") if row else None,
        "source_file": row.get("source_file") if row else None,
        "ae_context": observations.get("ae_context") if observations else None,
        "cases": case_rows(observations),
        "directly_observed_vs_inferred": observations.get("directly_observed_vs_inferred")
        if observations
        else None,
    }


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    row = find_result(summary)
    observations = observations_for(row)
    return {
        "kind": "olmdirectionalblur_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "likely_next_focus": classify(row, observations),
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
