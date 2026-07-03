#!/usr/bin/env python3
"""Freeze the KiraKira historical-8bpc vs live-16bpc witness split."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rgba(path: Path, xy: tuple[int, int]) -> list[int]:
    return list(Image.open(path).convert("RGBA").getpixel(xy))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-png", type=Path, required=True)
    parser.add_argument("--historical-output-png", type=Path, required=True)
    parser.add_argument("--live-output-png", type=Path, required=True)
    parser.add_argument("--historical-debug-json", type=Path, required=True)
    parser.add_argument("--live-debug-json", type=Path, required=True)
    parser.add_argument("--historical-request-reference-manifest", type=Path, required=True)
    parser.add_argument("--live-request-reference-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    xy = (934, 118)
    historical_manifest = read_json(args.historical_request_reference_manifest)
    live_manifest = read_json(args.live_request_reference_manifest)
    historical_debug = read_json(args.historical_debug_json)
    live_debug = read_json(args.live_debug_json)

    hist_point = historical_debug["points"]["934,118"]
    live_center = live_debug["center_point"]

    report = {
        "kind": "olmkirakira_witness_path_split",
        "schema": 1,
        "focus_xy": list(xy),
        "reference_png": {
            "path": rel(args.reference_png),
            "rgba8": rgba(args.reference_png, xy),
        },
        "historical_8bpc_lane": {
            "request_reference_manifest": rel(args.historical_request_reference_manifest),
            "project_bits_per_channel": historical_manifest.get("project", {}).get("bits_per_channel"),
            "output_png": rel(args.historical_output_png),
            "rgba8": rgba(args.historical_output_png, xy),
            "debug_out_u8": hist_point["out_u8"],
            "debug_src_rgba_float": hist_point["src_rgba_float"],
            "debug_glow_alpha_after_opacity": hist_point["glow_rgba_float"][3],
        },
        "live_16bpc_lane": {
            "request_reference_manifest": rel(args.live_request_reference_manifest),
            "project_bits_per_channel": live_manifest.get("project", {}).get("bits_per_channel"),
            "output_png": rel(args.live_output_png),
            "rgba8": rgba(args.live_output_png, xy),
            "debug_out_u8": live_center["out_u8"],
            "debug_out_u8_times_2_rgb": [int(live_center["out_u8"][i] * 2) for i in range(3)] + [live_center["out_u8"][3]],
            "debug_out_prequantized_rgba_float": live_center["out_prequantized_rgba_float"],
            "debug_glow_alpha_after_opacity": live_center["glow_alpha_after_opacity"],
        },
        "decision": {
            "status": "historical-8bpc-and-live-16bpc-lanes-must-not-be-mixed",
            "summary": (
                "The old 144-valued KiraKira hotspot witness belongs to an explicit 8bpc request lane, while the "
                "2026-07-03 live probe was run through a request with no project bits_per_channel metadata and executed "
                "as a 16bpc host path. Those are different host contexts."
            ),
            "reason": (
                "At the same hotspot `(934,118)`, the historical 8bpc rerun reproduces `[144,144,144,255]`, while the "
                "live 16bpc lane exports `[91,91,91,255]` and logs plugin-local `out_u8=[45,45,45,128]`. So the current "
                "KiraKira discrepancy is not permission to collapse the lane into a single provenance statement."
            ),
            "next_action": (
                "Keep 8bpc witness reasoning and 16bpc/live-host reasoning separate. Reopen provenance/export claims only "
                "after matching bit-depth and host context."
            ),
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# OLMKiraKira Witness Path Split",
        "",
        f"- Focus: `{tuple(report['focus_xy'])}`",
        f"- Status: `{report['decision']['status']}`",
        "",
        "## Reference",
        "",
        f"- RGBA8: `{report['reference_png']['rgba8']}`",
        "",
        "## Historical 8bpc lane",
        "",
        f"- bitsPerChannel: `{report['historical_8bpc_lane']['project_bits_per_channel']}`",
        f"- Output PNG: `{report['historical_8bpc_lane']['rgba8']}`",
        f"- Debug out_u8: `{report['historical_8bpc_lane']['debug_out_u8']}`",
        f"- Debug source: `{report['historical_8bpc_lane']['debug_src_rgba_float']}`",
        "",
        "## Live 16bpc lane",
        "",
        f"- bitsPerChannel metadata: `{report['live_16bpc_lane']['project_bits_per_channel']}`",
        f"- Output PNG: `{report['live_16bpc_lane']['rgba8']}`",
        f"- Debug out_u8: `{report['live_16bpc_lane']['debug_out_u8']}`",
        f"- Debug out_u8 * 2 RGB: `{report['live_16bpc_lane']['debug_out_u8_times_2_rgb']}`",
        "",
        "## Reading",
        "",
        f"- {report['decision']['summary']}",
        f"- {report['decision']['reason']}",
        f"- Next: {report['decision']['next_action']}",
        "",
    ]
    args.output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"report_json={rel(args.output_json)}")
    print(f"report_md={rel(args.output_md)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
