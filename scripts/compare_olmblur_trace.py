#!/usr/bin/env python3
"""Classify returned OLMBlur repeat/writeback runtime trace facts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "olmblur_repeat_threshold_runtime_trace_20260619"
DEFAULT_BASELINE_DIR = Path("refs/reports/olmblur_trace_baseline_20260619_030633_mac")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument("--local-baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR)
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
            "floorf(value + 0.5) | cvt/trunc | other",
            "",
            "none",
            "null",
            "n/a",
            "unknown",
        }:
            return False
        if re.fullmatch(r"[-+]?0x[0-9a-f]+(?:\.[0-9a-f]*)?p[-+]?\d+", text):
            return True
        placeholder_needles = (
            "not isolated",
            "not reached",
            "inferred",
            "likely",
            "expected",
            "runtime",
            "still needs",
            "untraced",
            "unknown",
            "needs live",
            "was not captured",
        )
        if any(needle in text for needle in placeholder_needles):
            return False
        return False
    return False


def read_local_baseline(path: Path) -> dict[str, Any]:
    traces: dict[str, list[dict[str, Any]]] = {}
    pattern = re.compile(
        r"OLMBLUR_TRACE x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
        r"rgb=\((?P<rgb>[^)]*)\) rgb_hex=\((?P<rgb_hex>[^)]*)\) "
        r"floor05=\((?P<floor05>[^)]*)\) nearby=\((?P<nearby>[^)]*)\) "
        r"legacy=(?P<legacy>\d+) repeat=(?P<repeat>\d+)"
    )
    for log_path in sorted(path.glob("case_*_trace.log")):
        rows = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            match = pattern.search(line)
            if not match:
                continue
            rows.append(
                {
                    "x": int(match.group("x")),
                    "y": int(match.group("y")),
                    "rgb": [part.strip() for part in match.group("rgb").split(",")],
                    "rgb_hex": [part.strip() for part in match.group("rgb_hex").split(",")],
                    "floor05": [part.strip() for part in match.group("floor05").split(",")],
                    "nearby": [part.strip() for part in match.group("nearby").split(",")],
                    "legacy": int(match.group("legacy")),
                    "repeat": int(match.group("repeat")),
                }
            )
        traces[log_path.stem.replace("_trace", "")] = rows
    diff_path = path / "diff.json"
    diff = load_json(diff_path) if diff_path.exists() else None
    return {"baseline_dir": str(path), "traces": traces, "diff": diff}


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    cases = observations.get("cases", [])
    if not isinstance(cases, list):
        cases = []
    by_case = {case.get("case_id"): case for case in cases if isinstance(case, dict)}
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": row.get("source_file"),
        "cases": cases,
        "case_0006": by_case.get("case_0006"),
        "case_0007": by_case.get("case_0007"),
    }


def has_prewriteback(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    for pixel in case.get("residual_pixels", []):
        if not isinstance(pixel, dict):
            continue
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("aex_writeback_operation")):
            return True
        if concrete_trace_value(pixel.get("aex_final_rgba")):
            return True
    return False


def has_legacy_state(case: dict[str, Any] | None) -> bool:
    if not isinstance(case, dict):
        return False
    for pixel in case.get("residual_pixels", []):
        if not isinstance(pixel, dict):
            continue
        if concrete_trace_value(pixel.get("legacy_all_same_state")):
            return True
        if concrete_trace_value(pixel.get("legacy_border_sample_included")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb")):
            return True
        if concrete_trace_value(pixel.get("aex_pre_writeback_rgb_hex")):
            return True
        if concrete_trace_value(pixel.get("aex_final_rgba")):
            return True
    return False


def classify_next_focus(windows: dict[str, Any]) -> str:
    if not windows.get("present"):
        return "await-windows-trace"
    case_0006 = windows.get("case_0006")
    case_0007 = windows.get("case_0007")
    if has_prewriteback(case_0006):
        return "nonlegacy-accumulation-or-writeback"
    if has_legacy_state(case_0007):
        return "legacy-border-or-all-same"
    if case_0006 or case_0007:
        return "trace-structure-present-values-missing"
    return "trace-too-sparse"


def build_comparison(summary: dict[str, Any], baseline_dir: Path) -> dict[str, Any]:
    windows = summarize_windows(find_result(summary))
    return {
        "kind": "olmblur_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "likely_next_focus": classify_next_focus(windows),
        "local_baseline": read_local_baseline(baseline_dir),
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
    baseline = comparison["local_baseline"]
    lines = [
        "# OLMBlur Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        f"- Local baseline: `{baseline.get('baseline_dir')}`",
        "",
        "## Local Baseline",
        "",
        f"- Trace cases: {md_value(sorted(baseline.get('traces', {}).keys()))}",
        f"- Diff summary: {md_value((baseline.get('diff') or {}).get('summary'))}",
        "",
        "## Windows Observations",
        "",
        f"- Status: {md_value(windows.get('status'))}",
        f"- Summary: {windows.get('summary') or '-'}",
        f"- Case 0006: {md_value(windows.get('case_0006'))}",
        f"- Case 0007: {md_value(windows.get('case_0007'))}",
        "",
        "## Interpretation",
        "",
        "- `nonlegacy-accumulation-or-writeback`: decide whether case_0006 differs before or only at byte writeback.",
        "- `legacy-border-or-all-same`: settle case_0007 border inclusion and all-same helper state.",
        "- `trace-structure-present-values-missing`: return the requested per-pixel values before changing code.",
        "- `trace-too-sparse`: request missing residual-pixel values instead of PNG tuning.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    summary_path = resolve(root, args.runtime_summary_json)
    baseline_dir = resolve(root, args.local_baseline_dir)
    if not summary_path.exists():
        return fail(f"runtime summary JSON not found: {summary_path}")
    if not baseline_dir.exists():
        return fail(f"local baseline dir not found: {baseline_dir}")
    summary = load_json(summary_path)
    if not isinstance(summary, dict):
        return fail("runtime summary JSON must be an object")
    comparison = build_comparison(summary, baseline_dir)
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
