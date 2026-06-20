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


REQUEST_ID = "kirakira_fun_181150790_stage_values_20260620"


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


def find_result(summary: dict[str, Any]) -> dict[str, Any] | None:
    for row in summary.get("results", []):
        if isinstance(row, dict) and row.get("request_id") == REQUEST_ID:
            return row
    return None


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


def summarize_windows(row: dict[str, Any] | None) -> dict[str, Any]:
    if row is None:
        return {"present": False}
    observations = row.get("observations", {})
    if not isinstance(observations, dict):
        observations = {"raw": observations}
    entry = observations.get("fun_181150790_entry", {})
    witnesses = observations.get("witness_pixels", [])
    aggregation = observations.get("aggregation_and_compose", {})
    return {
        "present": True,
        "status": row.get("status"),
        "summary": row.get("summary"),
        "source_file": row.get("source_file"),
        "case_id": observations.get("case_id"),
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
        "aggregation_and_compose": aggregation if isinstance(aggregation, dict) else aggregation,
    }


def build_comparison(summary: dict[str, Any], local_trace: dict[str, Any]) -> dict[str, Any]:
    row = find_result(summary)
    windows = summarize_windows(row)
    local = summarize_local(local_trace)
    likely_next_focus = "await-windows-trace"
    if windows.get("present"):
        entry = windows.get("entry", {})
        local_ray = local.get("first_ray", {})
        win_length = entry.get("ray_length")
        win_forward = entry.get("forward_matrix")
        win_witnesses = windows.get("witness_pixels")
        win_box = windows.get("boxfilter_calls")
        win_agg = windows.get("aggregation_and_compose")
        if has_concrete(win_length) and win_length != local_ray.get("length"):
            likely_next_focus = "ray-length-normalization"
        elif has_concrete(win_forward) and win_forward != local_ray.get("forward_matrix"):
            likely_next_focus = "warp-matrix-or-center"
        elif has_concrete_stage_value(win_witnesses) or has_concrete_stage_value(win_box):
            likely_next_focus = "boxfilter-stage-values"
        elif has_concrete_stage_value(win_agg):
            likely_next_focus = "aggregation-or-compose"
        else:
            likely_next_focus = "trace-too-sparse"
    return {
        "kind": "olmkirakira_stage_trace_comparison",
        "schema": 1,
        "request_id": REQUEST_ID,
        "likely_next_focus": likely_next_focus,
        "windows": windows,
        "local": local,
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
        f"- Aggregation/compose: {md_value(windows.get('aggregation_and_compose'))}",
        "",
    ]
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
