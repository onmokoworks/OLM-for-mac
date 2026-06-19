#!/usr/bin/env python3
"""Compare returned OLMColorKey Edge trace facts with local Mac baseline logs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUEST_ID = "colorkey_edge_runtime_trace_20260619"
TRACE_RE = re.compile(r"(?P<key>[A-Za-z0-9_]+)=\\((?P<tuple>[^)]*)\\)|(?P<key2>[A-Za-z0-9_]+)=(?P<value>[^ ]+)")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-summary-json", type=Path, required=True)
    parser.add_argument(
        "--local-baseline-dir",
        type=Path,
        default=Path("refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac"),
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


def parse_scalar(value: str) -> Any:
    if value in {"None", "null"}:
        return None
    try:
        if any(ch in value for ch in ".eE"):
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_trace_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("OLMCOLORKEY_TRACE "):
        return None
    out: dict[str, Any] = {}
    body = line.removeprefix("OLMCOLORKEY_TRACE ").strip()
    for match in TRACE_RE.finditer(body):
        key = match.group("key") or match.group("key2")
        if match.group("tuple") is not None:
            out[key] = [parse_scalar(part.strip()) for part in match.group("tuple").split(",") if part.strip()]
        else:
            out[key] = parse_scalar(match.group("value"))
    if "x" not in out or "y" not in out:
        return None
    return out


def load_local_traces(baseline_dir: Path) -> dict[str, list[dict[str, Any]]]:
    cases: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(baseline_dir.glob("case_*_trace.log")):
        case_id = path.name.removesuffix("_trace.log")
        rows: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            row = parse_trace_line(line)
            if row is not None:
                rows.append(row)
        cases[case_id] = rows
    return cases


def load_local_diff(baseline_dir: Path) -> dict[str, Any]:
    diff_path = baseline_dir / "diff.json"
    if not diff_path.exists():
        return {}
    data = load_json(diff_path)
    if not isinstance(data, dict):
        return {}
    by_id: dict[str, Any] = {}
    for row in data.get("cases", []):
        if isinstance(row, dict) and row.get("id"):
            by_id[str(row["id"])] = row
    return by_id


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == REQUEST_ID:
            return row
    return None


def windows_observations(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": row.get("source_file"),
        "ctx": {
            key: observations.get(key)
            for key in (
                "ctx_0x28_edge_thin_direction_or_mode",
                "ctx_0x2c_edge_blur_direction",
                "ctx_0x40_edge_amount_raw_float",
                "ctx_0x44_distance_type",
                "ctx_0x48_edge_blur_amount_raw_float",
            )
        },
        "edge_thin_erode_cases": observations.get("edge_thin_erode_cases", []),
        "edge_blur_samples": observations.get("edge_blur_samples", []),
        "positive_edge_thin_copy_condition_observed": observations.get("positive_edge_thin_copy_condition_observed"),
        "edge_blur_distance_dispatch_observed": observations.get("edge_blur_distance_dispatch_observed"),
        "edge_blur_apply_formula_summary": observations.get("edge_blur_apply_formula_summary"),
    }


def classify_next_focus(windows: dict[str, Any], local_cases: dict[str, list[dict[str, Any]]]) -> str:
    if not windows.get("present"):
        return "await-windows-trace"
    blur_samples = windows.get("edge_blur_samples") or []
    thin_cases = windows.get("edge_thin_erode_cases") or []
    if thin_cases:
        for row in thin_cases:
            if isinstance(row, dict) and row.get("distance_after_transform") is not None:
                return "edge-thin-border-threshold"
    if blur_samples:
        for row in blur_samples:
            if not isinstance(row, dict):
                continue
            if row.get("boundary_seed_after_FUN_180008c90") is not None:
                return "edge-blur-seed-world"
            if row.get("edge_blur_weight") is not None or row.get("edge_blur_apply_source_rgba") is not None:
                return "edge-blur-apply-or-compose"
    if local_cases:
        return "trace-too-sparse"
    return "missing-local-baseline"


def build_comparison(summary: dict[str, Any], baseline_dir: Path) -> dict[str, Any]:
    local_cases = load_local_traces(baseline_dir)
    local_diff = load_local_diff(baseline_dir)
    windows = windows_observations(find_result(summary))
    return {
        "kind": "olmcolorkey_edge_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "likely_next_focus": classify_next_focus(windows, local_cases),
        "windows": windows,
        "local": {
            "baseline_dir": str(baseline_dir),
            "cases": local_cases,
            "diff": local_diff,
        },
    }


def md_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return f"`{value}`"


def render_markdown(comparison: dict[str, Any]) -> str:
    local = comparison["local"]
    windows = comparison["windows"]
    lines = [
        "# OLMColorKey Edge Trace Comparison",
        "",
        f"- Request: `{comparison['request_id']}`",
        f"- Likely next focus: `{comparison['likely_next_focus']}`",
        f"- Windows trace present: `{bool(windows.get('present'))}`",
        f"- Local baseline: `{local.get('baseline_dir')}`",
        "",
        "## Local Baseline",
        "",
        "| Case | Trace rows | Current diff | First local trace row |",
        "| --- | ---: | --- | --- |",
    ]
    cases = local.get("cases", {})
    diff = local.get("diff", {})
    for case_id in sorted(cases):
        rows = cases[case_id]
        diff_row = diff.get(case_id, {})
        diff_summary = {
            key: diff_row.get(key)
            for key in ("max_diff", "mean_diff", "nonzero_px_percent")
            if key in diff_row
        }
        first = rows[0] if rows else {}
        lines.append(f"| {case_id} | {len(rows)} | {md_value(diff_summary)} | {md_value(first)} |")
    lines.extend(
        [
            "",
            "## Windows Observations",
            "",
            f"- Status: {md_value(windows.get('status'))}",
            f"- Summary: {windows.get('summary') or '-'}",
            f"- Ctx: {md_value(windows.get('ctx'))}",
            f"- Edge Thin erode cases: {md_value(windows.get('edge_thin_erode_cases'))}",
            f"- Edge Blur samples: {md_value(windows.get('edge_blur_samples'))}",
            f"- Copy condition: {md_value(windows.get('positive_edge_thin_copy_condition_observed'))}",
            f"- Distance dispatch: {md_value(windows.get('edge_blur_distance_dispatch_observed'))}",
            f"- Apply formula: {windows.get('edge_blur_apply_formula_summary') or '-'}",
            "",
        ]
    )
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
