#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} top-level JSON must be an object")
    return data


def latest_runtime_observations(runtime_summary: dict) -> dict:
    results = runtime_summary.get("results", [])
    if not isinstance(results, list) or not results:
        raise ValueError("runtime summary results missing")
    observations = results[0].get("observations", {})
    if not isinstance(observations, dict):
        raise ValueError("runtime summary observations missing")
    return observations


def build_summary(
    trace_compare: str,
    baseline: dict,
    runtime_summary: dict,
    runtime_summary_path: Path,
) -> dict:
    ray0 = baseline["rays"][0]
    center_point = next(point for point in ray0["sample_points"] if point["label"] == "center")
    up_point = next(point for point in ray0["sample_points"] if point["label"] == "ray_length_up")
    right_point = next(point for point in ray0["sample_points"] if point["label"] == "ray_length_right")
    ray = ray0["box_filters"][0]["samples"][0]
    runtime_obs = latest_runtime_observations(runtime_summary)
    return {
        "kind": "olmkirakira_pending_compose_proof",
        "date": "2026-06-29",
        "status": "historical-superseded-by-hotspot-provenance-lane",
        "superseded_by": {
            "report": str(repo_root() / "refs" / "conformance" / "olmkirakira_hotspot_export_contract_audit_20260701.md"),
            "reason": (
                "The answered 2026-07-01 hotspot witness already matches the current Mac compose-boundary values "
                "through pre-writeback and sampled RGBA8. The remaining lane is no longer live compose/quantization "
                "isolation; it is same-run export provenance, witness-placement validation, or endgame-control coverage."
            ),
        },
        "latest_runtime_summary": str(runtime_summary_path),
        "decision_boundary": (
            "Determine whether the remaining KiraKira 8bpc Software residual comes from the internal "
            "merge-mode-1 compose site itself, from the pre-writeback float->u8 quantization/export step, "
            "or from a narrower residual hotspot not yet instrumented."
        ),
        "why_rejected_paths_stay_rejected": [
            "BT.709 seed luma now explains the prior pass-1 upstream source-buffer mismatch.",
            "Ray helper stages and fd90 aggregation are already grounded within float print precision at the traced witnesses.",
            "The compose model audit rejects global gain or premultiplied-compose retuning as worsening total mean/max or breaking strength0 anchors.",
        ],
        "grounded_up_to_here": {
            "ray_helper": "grounded-within-float-print-precision",
            "boxfilter_pass1_window": "resolved and explained by BT.709 seed correction",
            "fd90_aggregation": {
                "center_glow_rgba": [1.0, 1.0, 1.0, 0.71891218],
                "up_glow_rgba": [1.0, 1.0, 1.0, 0.76832885],
                "right_glow_rgba": [1.0, 1.0, 1.0, 0.71564364],
            },
        },
        "current_local_baseline": {
            "ray_center_after_box_1": ray["value"],
            "sample_points": {
                "center": center_point["values"],
                "ray_length_up": up_point["values"],
                "ray_length_right": right_point["values"],
            },
        },
        "hotspot_targets": {
            "primary_vertical_case": {
                "case_id": "kk_vertical_len50_brightness1_strength100",
                "xy": [934, 118],
                "windows_rgba": [131, 131, 131, 255],
                "mac_bt709_candidate_rgba": [145, 145, 145, 255],
                "delta": [14, 14, 14, 0],
            },
            "optional_rotation13_case": {
                "case_id": "kk_diagonal_len50_rotation13",
                "xy": [1098, 202],
                "windows_rgba": [112, 112, 112, 255],
                "mac_bt709_candidate_rgba": [46, 46, 46, 255],
                "delta": [-66, -66, -66, 0],
            },
        },
        "windows_trace_gap": {
            "compose_internal_float": "not isolated",
            "pre_writeback_rgba_float": "not isolated",
            "residual_hotspot_xy": [934, 118],
            "current_trace_report": trace_compare,
            "latest_runtime_note": {
                "directly_observed_vs_inferred": runtime_obs.get("directly_observed_vs_inferred"),
                "merge_mode_1_compose": runtime_obs.get("merge_mode_1_compose"),
            },
        },
        "actionable_return_if": [
            "It captures the internal merge-mode-1 compose-site floats or equivalent pre-writeback RGBA float at a residual hotspot.",
            "It captures the source RGBA float, glow RGBA float, composed RGBA float, and final u8/writeback value at the same coordinate.",
            "It distinguishes 'compose math already matches, only final quantization differs' from 'compose-site float is already different'.",
        ],
        "not_actionable_if": [
            "It only returns final PNG-facing RGBA bytes that are downstream of the unresolved compose/writeback split.",
            "It reopens seed luma, first-pass boxFilter, ray-helper choreography, or global compose gain without contradicting the existing grounded evidence.",
            "It lacks a residual hotspot coordinate and only samples already-near-matching center/up/right witnesses.",
        ],
        "recommended_next_windows_probe": [
            "At one BT.709 residual hotspot from the 9 Software cases, capture source RGBA float, glow RGBA float after fd90/opacities, merge-mode-1 composed RGBA float, pre-writeback RGBA float, and final written u8/PNG byte.",
            "If the compose-site float is unavailable, capture the last float before quantization/export plus the exact quantization helper or clamp path.",
            "Prefer a residual hotspot over center/up/right because those witnesses already ground fd90 aggregation but do not isolate the failing branch.",
        ],
    }


def write_markdown(summary: dict, out: Path) -> None:
    lines = [
        "# OLMKiraKira Pending Compose Proof",
        "",
        f"- Historical status: `{summary['status']}`",
        f"- Superseded by: `{summary['superseded_by']['report']}`",
        f"- Why superseded: {summary['superseded_by']['reason']}",
        "",
        "## Decision Boundary",
        "",
        summary["decision_boundary"],
        "",
        "## Why Earlier Theories Stay Rejected",
        "",
    ]
    for item in summary["why_rejected_paths_stay_rejected"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Grounded Up To Here",
            "",
            f"- Ray helper: `{summary['grounded_up_to_here']['ray_helper']}`",
            f"- BoxFilter pass1 window: `{summary['grounded_up_to_here']['boxfilter_pass1_window']}`",
            f"- fd90 aggregation witnesses: `{summary['grounded_up_to_here']['fd90_aggregation']}`",
            "",
            "## Missing Windows Trace Values",
            "",
        ]
    )
    lines.append(f"- Latest runtime summary: `{summary['latest_runtime_summary']}`")
    for key, value in summary["windows_trace_gap"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Residual Hotspot Targets", ""])
    for name, target in summary["hotspot_targets"].items():
        lines.append(f"- {name}: `{target}`")
    lines.extend(["", "## Actionable Return Criteria", ""])
    for item in summary["actionable_return_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Actionable", ""])
    for item in summary["not_actionable_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Next Windows Probe", ""])
    for item in summary["recommended_next_windows_probe"]:
        lines.append(f"- {item}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-json",
        type=Path,
        default=repo_root() / "refs" / "reports" / "olmkirakira_trace_baseline_20260624_bt709_mac" / "trace.json",
    )
    parser.add_argument(
        "--trace-compare-report",
        type=Path,
        default=repo_root() / "refs" / "reports" / "runtime_trace_comparisons" / "olmkirakira_aggregation_compose_bt709_20260624.md",
    )
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        default=(
            repo_root()
            / "refs"
            / "reports"
            / "runtime_trace_bundle"
            / "olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows"
            / "runtime_trace_summary_kirakira_aggregation_compose_bt709_20260629_235638.json"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmkirakira_pending_compose_proof_20260629.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=repo_root() / "refs" / "conformance" / "olmkirakira_pending_compose_proof_20260629.md",
    )
    args = parser.parse_args()

    summary = build_summary(
        str(args.trace_compare_report),
        load_json(args.baseline_json),
        load_json(args.runtime_summary_json),
        args.runtime_summary_json,
    )
    args.output_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(args.output_json)
    print(args.output_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
