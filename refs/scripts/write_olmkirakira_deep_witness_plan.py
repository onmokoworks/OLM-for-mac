#!/usr/bin/env python3
"""Write a focused OLMKiraKira deep trace witness plan from a local trace JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_TRACE = Path("refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json")
DEFAULT_OUT_DIR = Path("refs/reports/olmkirakira_trace_baseline_20260621_deep_witness_plan")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-json", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_trace(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "olmkirakira_opencv_two_temp_stage_trace":
        raise ValueError(f"{path}: unexpected trace kind {data.get('kind')!r}")
    return data


def build_plan(trace_path: Path, trace: dict[str, Any]) -> dict[str, Any]:
    ray = next(record for record in trace["rays"] if record.get("ray") == "vertical")
    aggregation = next(record for record in trace["rays"] if record.get("stage") == "aggregation_and_compose")
    return {
        "kind": "olmkirakira_deep_stage_witness_plan",
        "schema": 1,
        "source_trace_json": str(trace_path),
        "case_id": "kk_vertical_len50_brightness1_strength100",
        "purpose": (
            "Make the next Windows runtime trace concrete: compare the same "
            "three witness pixels at each FUN_181150790 stage, then compare "
            "aggregation/merge output."
        ),
        "ray_helper": {
            "function": "FUN_181150790",
            "ray": ray["ray"],
            "length": ray["length"],
            "angle": ray["angle"],
            "source_size": ray["source_size"],
            "temp_size": ray["temp_size"],
            "center": ray["center"],
            "copy_origin": ray["copy_origin"],
            "forward_matrix": ray["forward_matrix"],
            "back_matrix": ray["back_matrix"],
            "box_filters": [
                {
                    "pass": item["pass"],
                    "ksize": item["ksize"],
                    "expected_branch": "FUN_1812e39d0 / AVX2",
                    "samples": item.get("samples", []),
                }
                for item in ray["box_filters"]
            ],
            "witness_pixels": ray["sample_points"],
        },
        "aggregation_and_compose": {
            "stage": "FUN_18114fd90 + merge mode 1",
            "scale": aggregation["scale"],
            "strength": aggregation["strength"],
            "glow_opacity": aggregation["glow_opacity"],
            "source_opacity": aggregation["source_opacity"],
            "compose_mode": aggregation["compose_mode"],
            "sample_points": aggregation["sample_points"],
        },
        "success_condition": (
            "The Windows return must include concrete float/byte values for these "
            "witnesses or an exact breakpoint/watchpoint failure reason. Wrapper "
            "hits alone are trace-too-sparse."
        ),
    }


def markdown(plan: dict[str, Any]) -> str:
    ray = plan["ray_helper"]
    lines = [
        "# OLMKiraKira Deep Trace Witness Plan",
        "",
        f"Case: `{plan['case_id']}`",
        "",
        "## Ray Helper",
        "",
        f"- Function: `{ray['function']}`",
        f"- Ray/length/angle: `{ray['ray']}`, `{ray['length']}`, `{ray['angle']}`",
        f"- Source size: `{ray['source_size']}`",
        f"- Temp size: `{ray['temp_size']}`",
        f"- Center: `{ray['center']}`",
        f"- Copy origin: `{ray['copy_origin']}`",
        f"- Forward matrix: `{ray['forward_matrix']}`",
        f"- Back matrix: `{ray['back_matrix']}`",
        "",
        "## Stage Witnesses",
        "",
        "| Label | Source xy | Temp xy | seed | center copy | forward warp | box1 | box2 | box3 | rotate back | final copy |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for point in ray["witness_pixels"]:
        values = point["values"]
        lines.append(
            "| {label} | `{source}` | `{temp}` | {seed:.10f} | {center:.10f} | {forward:.10f} | "
            "{box1:.10f} | {box2:.10f} | {box3:.10f} | {rotate:.10f} | {final:.10f} |".format(
                label=point["label"],
                source=point["source_xy"],
                temp=point["temp_xy"],
                seed=values["seed"],
                center=values["after_center_copy"],
                forward=values["after_forward_warp"],
                box1=values["after_box_1"],
                box2=values["after_box_2"],
                box3=values["after_box_3"],
                rotate=values["after_rotate_back"],
                final=values["after_final_center_copy"],
            )
        )
    lines.extend(
        [
            "",
            "## BoxFilter Input Windows",
            "",
            "Each window is the local OpenCV input row used for the matching output sample. Values are summarized here; full 50-sample arrays are in `witness_plan.json`.",
            "",
            "| Pass | Label | Temp xy | Anchor x | Unbordered x range | Window mean | Output |",
            "| ---: | --- | --- | ---: | --- | ---: | ---: |",
        ]
    )
    for box_filter in ray.get("box_filters", []):
        sample_by_label = {sample["label"]: sample for sample in box_filter.get("samples", [])}
        for point in ray["witness_pixels"]:
            sample = sample_by_label.get(point["label"], {})
            window = sample.get("input_window") or {}
            lines.append(
                "| {pass_index} | {label} | `{temp}` | {anchor} | `{xrange}` | {mean:.10f} | {output:.10f} |".format(
                    pass_index=box_filter["pass"],
                    label=point["label"],
                    temp=point["temp_xy"],
                    anchor=window.get("anchor_x", "-"),
                    xrange=window.get("x_range_unbordered", "-"),
                    mean=float(window.get("mean", 0.0)),
                    output=float(sample.get("value", 0.0)),
                )
            )
    lines.extend(
        [
            "",
            "## Aggregation / Compose Witnesses",
            "",
            "| Label | Source xy | Source RGBA | Glow RGBA | Out float | Out u8 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for point in plan["aggregation_and_compose"]["sample_points"]:
        values = point["values"]
        lines.append(
            f"| {point['label']} | `{point['source_xy']}` | `{values['source_rgba']}` | "
            f"`{values['glow_rgba']}` | `{values['out_rgba_float']}` | `{values['out_rgba_u8']}` |"
        )
    lines.extend(["", f"Success condition: {plan['success_condition']}", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = repo_root()
    trace_path = args.trace_json if args.trace_json.is_absolute() else root / args.trace_json
    out_dir = args.out_dir if args.out_dir.is_absolute() else root / args.out_dir
    trace = load_trace(trace_path)
    plan = build_plan(trace_path.relative_to(root), trace)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "witness_plan.json"
    md_path = out_dir / "witness_plan.md"
    json_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(markdown(plan), encoding="utf-8")
    print(f"[OK] wrote {json_path}")
    print(f"[OK] wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
