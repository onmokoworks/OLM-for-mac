#!/usr/bin/env python3
"""Classify returned OLMSmoother2 legacy key/gamma runtime trace facts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "olmsmoother2_legacy_key_gamma_runtime_trace_20260620"


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


def fail(message: str) -> int:
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == REQUEST_ID:
            return row
    return None


def meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value not in {
            "0x...",
            "floorf(value+0.5) | trunc | cvt | other",
            "floorf(value + 0.5) | trunc | cvt | other",
        }
    if isinstance(value, list):
        return any(meaningful(item) for item in value)
    if isinstance(value, dict):
        return any(meaningful(item) for item in value.values())
    return True


def observations_for(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {}
    observations = row.get("observations", {})
    return observations if isinstance(observations, dict) else {"raw": observations}


def case_rows(observations: dict[str, Any]) -> list[dict[str, Any]]:
    rows = observations.get("cases", [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def requested(observations: dict[str, Any]) -> dict[str, Any]:
    value = observations.get("requested_for_each_case", {})
    return value if isinstance(value, dict) else {}


def classify(observations: dict[str, Any]) -> str:
    if not observations:
        return "await-windows-trace"
    req = requested(observations)
    setup = req.get("setup_and_keying", {}) if isinstance(req.get("setup_and_keying"), dict) else {}
    writeback = (
        req.get("smoothing_and_writeback", {})
        if isinstance(req.get("smoothing_and_writeback"), dict)
        else {}
    )
    params = req.get("parameter_struct", {}) if isinstance(req.get("parameter_struct"), dict) else {}

    if meaningful(setup.get("active_palette_filter_value")) or meaningful(setup.get("scalar_key_filter_value")):
        return "key-mask-polarity-or-class-plane"
    if meaningful(setup.get("class_plane_byte_before_smoothing")) or meaningful(setup.get("class_plane_neighbors")):
        return "class-plane-generation"
    if meaningful(writeback.get("before_FUN_1800036e0_rgba_float_hex")):
        return "premultiply-gamma-or-writeback"
    if meaningful(writeback.get("final_rgba_8bit")):
        return "final-byte-writeback"
    if meaningful(params):
        return "parameter-struct-only"
    if case_rows(observations):
        return "trace-structure-present-values-missing"
    return "trace-too-sparse"


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    observations = observations_for(row)
    return {
        "present": row is not None,
        "status": row.get("status") if row else None,
        "summary": row.get("summary") if row else None,
        "source_file": row.get("source_file") if row else None,
        "cases": case_rows(observations),
        "requested_for_each_case": requested(observations),
    }


def build_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    row = find_result(summary)
    observations = observations_for(row)
    return {
        "kind": "olmsmoother2_legacy_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "likely_next_focus": classify(observations),
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
        "# OLMSmoother2 Legacy Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- Cases: {md_value(windows.get('cases'))}",
        f"- Requested values: {md_value(windows.get('requested_for_each_case'))}",
        "",
        "## Interpretation",
        "",
        "- `key-mask-polarity-or-class-plane`: compare Color Key keep/drop decisions before smoothing.",
        "- `class-plane-generation`: patch mask/class-plane creation before touching polygon weights.",
        "- `premultiply-gamma-or-writeback`: inspect case_0001 first because alpha matches but RGB differs.",
        "- `parameter-struct-only`: the trace found params but not per-pixel state; request witness values next.",
        "- `trace-too-sparse`: do not tune from PNGs; repeat with the requested witness fields.",
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
