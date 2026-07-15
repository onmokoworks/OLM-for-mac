#!/usr/bin/env python3
"""Check the local KiraKira screen-over and 8-bit quantization invariant."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WITNESS = ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"
DEFAULT_AEX = ROOT / "refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.json"
DEFAULT_OPENCV = ROOT / "refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.json"
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_aggregation_quantization_invariant_20260715.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_aggregation_quantization_invariant_20260715.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--witness", type=Path, default=DEFAULT_WITNESS)
    parser.add_argument("--aex-report", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--opencv-report", type=Path, default=DEFAULT_OPENCV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    return parser.parse_args()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def quantize(value: float) -> int:
    # The local Mac witness is 8bpc and records the post-compose byte.
    return max(0, min(255, math.floor(value * 255.0 + 0.5)))


def check_point(label: str, point: dict[str, Any]) -> dict[str, Any]:
    source = point.get("src_rgba_float")
    glow = point.get("glow_rgba_float")
    observed = point.get("out_prequantized_rgba_float")
    observed_u8 = point.get("out_u8")
    if not all(isinstance(value, list) for value in (source, glow, observed, observed_u8)):
        return {"label": label, "status": "incomplete", "reason": "missing complete float/u8 witness fields"}

    alpha = float(glow[3])
    predicted = [float(glow[i]) * alpha + float(source[i]) * (1.0 - alpha) for i in range(3)]
    predicted.append(float(source[3]))
    errors = [abs(predicted[i] - float(observed[i])) for i in range(4)]
    predicted_u8 = [quantize(value) for value in predicted[:3]] + [quantize(predicted[3])]
    exact_quantization = predicted_u8 == [int(value) for value in observed_u8]
    passed = max(errors) <= 1e-6 and exact_quantization
    return {
        "label": label,
        "status": "pass" if passed else "fail",
        "source_rgba_float": source,
        "glow_rgba_float": glow,
        "predicted_rgba_float": predicted,
        "observed_rgba_float": observed,
        "max_abs_error": max(errors),
        "predicted_u8": predicted_u8,
        "observed_u8": observed_u8,
        "exact_quantization": exact_quantization,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    witness = load(args.witness)
    points = witness.get("points", {})
    checks = [check_point(label, point) for label, point in points.items()]
    complete = [item for item in checks if item["status"] != "incomplete"]
    status = "local-invariant-proven" if complete and all(item["status"] == "pass" for item in complete) else "invariant-failed-or-no-complete-witness"
    aex = load(args.aex_report)
    opencv = load(args.opencv_report)
    return {
        "kind": "olmkirakira_aggregation_quantization_invariant",
        "schema": 1,
        "status": status,
        "scope": "Mac/local aggregation and final 8bpc quantization only",
        "invariant": {
            "rgb": "glow_rgb * glow_alpha + source_rgb * (1 - glow_alpha)",
            "alpha": "source_alpha",
            "u8": "clamp(floor(float * 255 + 0.5), 0, 255)",
            "tolerance_float": 1e-6,
        },
        "inputs": {
            "mac_compose_witness": str(args.witness.relative_to(ROOT)),
            "actual_aex_forward_warp_report": str(args.aex_report.relative_to(ROOT)),
            "opencv_455_stage_report": str(args.opencv_report.relative_to(ROOT)),
            "actual_aex_forward_warp_status": aex.get("status"),
            "opencv_stage_kind": opencv.get("kind"),
        },
        "checks": checks,
        "summary": {
            "point_count": len(checks),
            "complete_count": len(complete),
            "passed_count": sum(item["status"] == "pass" for item in complete),
            "incomplete_count": sum(item["status"] == "incomplete" for item in checks),
        },
        "limits": [
            "This proves a local compose/quantization invariant for the complete Mac witness rows only.",
            "It does not claim AE exactness, Windows equivalence, or a correction to the remaining hotspot residual.",
        ],
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Aggregation and Final Quantization Invariant",
        "",
        f"Status: **{report['status']}**",
        "",
        "## FACT",
        "",
        "- Local merge-mode-1 RGB is checked as `glow_rgb * glow_alpha + source_rgb * (1 - glow_alpha)`.",
        "- Alpha is checked as source-alpha passthrough.",
        "- 8bpc output is checked as nearest integer quantization with clamping.",
        f"- Complete witness rows: `{report['summary']['complete_count']}`; passing rows: `{report['summary']['passed_count']}`.",
        "",
        "## Witness checks",
        "",
        "| Label | Status | Max float error | Predicted u8 | Observed u8 |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in report["checks"]:
        lines.append(
            f"| `{item['label']}` | `{item['status']}` | "
            f"`{item.get('max_abs_error', '-')}` | `{item.get('predicted_u8', '-')}` | `{item.get('observed_u8', '-')}` |"
        )
    lines += ["", "## Evidence pairing", "", f"- Actual-AEX report: `{report['inputs']['actual_aex_forward_warp_report']}` (`{report['inputs']['actual_aex_forward_warp_status']}`)", f"- OpenCV stage report: `{report['inputs']['opencv_455_stage_report']}` (`{report['inputs']['opencv_stage_kind']}`)", "", "## LIMIT", ""]
    lines += [f"- {limit}" for limit in report["limits"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "complete": report["summary"]["complete_count"], "json": str(args.output_json), "md": str(args.output_md)}, sort_keys=True))
    return 0 if report["status"] == "local-invariant-proven" else 1


if __name__ == "__main__":
    raise SystemExit(main())
