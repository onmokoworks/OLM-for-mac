#!/usr/bin/env python3
"""Summarize OLMKiraKira BT.709/ray-helper/compose decision state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remeasure-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmkirakira_remeasure_20260624_bt709_software" / "reports" / "diff.json",
    )
    parser.add_argument(
        "--deep-stage-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmkirakira_deep_stage_values_20260624_bt709.json",
    )
    parser.add_argument(
        "--boxfilter-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmkirakira_boxfilter_pass1_microprobe_20260624_bt709.json",
    )
    parser.add_argument(
        "--aggregation-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmkirakira_aggregation_compose_bt709_20260624.json",
    )
    parser.add_argument(
        "--compose-audit-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmkirakira_compose_model_audit_20260625" / "compose_model_audit.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def software_cases(diff: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    seen = set()
    for row in diff.get("cases", []):
        if not isinstance(row, dict):
            continue
        frame = str(row.get("frame", ""))
        if "__software__" not in frame:
            continue
        case_id = str(row.get("id"))
        if case_id in seen:
            continue
        seen.add(case_id)
        rows.append(row)
    return rows


def case_group(row: dict[str, Any]) -> str:
    case_id = str(row.get("id", ""))
    if "strength0" in case_id:
        return "strength0_anchor"
    if "rotation13" in case_id:
        return "rotation13"
    return "strength100_single_ray"


def summarize_remeasure(diff: dict[str, Any]) -> dict[str, Any]:
    rows = software_cases(diff)
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(case_group(row), []).append(row)

    summaries = {}
    for name, group_rows in sorted(groups.items()):
        summaries[name] = {
            "case_count": len(group_rows),
            "max_diff_max": max((int(row.get("max_diff", 0)) for row in group_rows), default=0),
            "mean_sum": sum(float(row.get("mean_diff", 0.0)) for row in group_rows),
            "exact_count": sum(1 for row in group_rows if int(row.get("max_diff", 0)) == 0 and float(row.get("mean_diff", 0.0)) == 0.0),
            "cases": [
                {
                    "id": row.get("id"),
                    "max_diff": int(row.get("max_diff", 0)),
                    "mean_diff": float(row.get("mean_diff", 0.0)),
                    "nonzero_px_percent": float(row.get("nonzero_px_percent", 0.0)),
                }
                for row in group_rows
            ],
        }
    return {
        "case_count": len(rows),
        "max_diff_max": max((int(row.get("max_diff", 0)) for row in rows), default=0),
        "mean_sum": sum(float(row.get("mean_diff", 0.0)) for row in rows),
        "exact_count": sum(1 for row in rows if int(row.get("max_diff", 0)) == 0 and float(row.get("mean_diff", 0.0)) == 0.0),
        "groups": summaries,
    }


def max_stage_delta(deep_stage: dict[str, Any]) -> float | None:
    deltas = [abs(float(row.get("delta", 0.0))) for row in deep_stage.get("deep_stage_deltas", []) if isinstance(row, dict)]
    return max(deltas) if deltas else None


def fd90_samples(aggregation: dict[str, Any]) -> list[dict[str, Any]]:
    fd90 = ((aggregation.get("windows") or {}).get("fun_18114fd90_aggregation") or {})
    rows = []
    for row in fd90.get("sample_outputs", []):
        if isinstance(row, dict):
            rows.append(
                {
                    "label": row.get("label"),
                    "xy": row.get("source_xy"),
                    "ray_inputs": row.get("ray_inputs"),
                    "post_normalize_glow_rgba": row.get("post_normalize_glow_rgba"),
                }
            )
    return rows


def implied_screen_alpha(source: float, final: float) -> float | None:
    denom = 1.0 - source
    if abs(denom) <= 1.0e-8:
        return None
    return max(0.0, min(1.0, 1.0 - (1.0 - final) / denom))


def compose_scale_samples(aggregation: dict[str, Any]) -> list[dict[str, Any]]:
    merge = ((aggregation.get("windows") or {}).get("merge_mode_1_compose") or {})
    samples = merge.get("sample_inputs_outputs", [])
    rows = []
    for row in samples:
        if not isinstance(row, dict):
            continue
        src = row.get("source_rgba_float")
        final = row.get("final_png_rgba_float")
        glow = row.get("glow_rgba_float")
        if not (isinstance(src, list) and isinstance(final, list) and isinstance(glow, list)):
            continue
        if len(src) < 3 or len(final) < 3 or len(glow) < 4 or glow[3] in (None, 0):
            continue
        implied = []
        ratios = []
        for channel in range(3):
            if src[channel] is None or final[channel] is None:
                continue
            alpha = implied_screen_alpha(float(src[channel]), float(final[channel]))
            if alpha is None:
                continue
            implied.append(alpha)
            ratios.append(alpha / float(glow[3]))
        if not implied:
            continue
        rows.append(
            {
                "label": row.get("label"),
                "xy": row.get("source_xy"),
                "source_rgb": src[:3],
                "final_rgb": final[:3],
                "fd90_glow_alpha": float(glow[3]),
                "implied_screen_alpha_min": min(implied),
                "implied_screen_alpha_max": max(implied),
                "implied_screen_alpha_mean": sum(implied) / len(implied),
                "implied_scale_min": min(ratios),
                "implied_scale_max": max(ratios),
                "implied_scale_mean": sum(ratios) / len(ratios),
            }
        )
    return rows


def summarize_compose_audit(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": str(path),
            "status": "missing",
            "decision": None,
            "best_by_mean": None,
            "best_by_max": None,
            "current_total": None,
            "rejected_variants": [],
        }
    data = read_json(path)
    variants = {str(row.get("id")): row for row in data.get("variants", []) if isinstance(row, dict)}
    current = variants.get("current_gain_0_62")
    rejected = [
        variant_id
        for variant_id in ("gain_0_60", "gain_0_5811", "gain_0_5436", "scale_override_1_0", "premul_gain_0_62")
        if variant_id in variants
    ]
    return {
        "path": str(path),
        "status": "available",
        "decision": (data.get("decision") or {}).get("status"),
        "best_by_mean": (data.get("decision") or {}).get("best_by_mean"),
        "best_by_max": (data.get("decision") or {}).get("best_by_max"),
        "current_total": (current or {}).get("total"),
        "rejected_variants": rejected,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    remeasure = summarize_remeasure(read_json(args.remeasure_json))
    deep = read_json(args.deep_stage_json)
    box = read_json(args.boxfilter_json)
    aggregation = read_json(args.aggregation_json)
    compose_audit = summarize_compose_audit(args.compose_audit_json)
    stage_delta = max_stage_delta(deep)
    box_focus = str(box.get("likely_next_focus", ""))
    agg_focus = str(aggregation.get("likely_next_focus", ""))
    fd90 = fd90_samples(aggregation)
    compose_scales = compose_scale_samples(aggregation)

    if stage_delta is not None and stage_delta <= 1e-5 and fd90:
        grounded = "ray-helper-and-fd90-grounded"
    else:
        grounded = "needs-review"

    return {
        "kind": "olmkirakira_decision_matrix",
        "schema": 1,
        "inputs": {
            "remeasure_json": str(args.remeasure_json),
            "deep_stage_json": str(args.deep_stage_json),
            "boxfilter_json": str(args.boxfilter_json),
            "aggregation_json": str(args.aggregation_json),
            "compose_audit_json": str(args.compose_audit_json),
        },
        "bt709_remeasure": remeasure,
        "ray_helper": {
            "decision": "grounded-within-float-print-precision" if stage_delta is not None and stage_delta <= 1e-5 else "needs-review",
            "max_stage_delta": stage_delta,
            "deep_stage_focus": deep.get("likely_next_focus"),
            "boxfilter_focus": box_focus,
        },
        "aggregation": {
            "decision": "fd90-grounded-compose-unisolated" if fd90 else "needs-review",
            "likely_next_focus": agg_focus,
            "samples": fd90,
            "compose_scale_samples": compose_scales,
            "current_local_compose_scale": 0.62,
            "rejected_probe": {
                "gain_scale_0_60": "worsened total Software mean versus current 0.62 in prior Mac probe",
                "scale_override_1_0": "breaks strength-0 anchors",
            },
        },
        "compose_model_audit": compose_audit,
        "decision": "blocked-compose-or-final-quantization",
        "classification": grounded,
        "recommended_action": (
            "Do not reopen luma, boxFilter window, ray-helper choreography, or global compose scale. "
            "The remaining KiraKira residual belongs to merge-mode-1 compose/writeback/final quantization or a narrower residual hotspot."
        ),
        "next_evidence": [
            "Do not change global gain/premul compose unless new binary evidence contradicts the 2026-06-25 compose audit.",
            "If Windows is needed later, request a compose-site/pre-writeback witness at the BT.709 residual hotspot, not broad PNGs.",
            "Add 16/32bpc refs only after 8bpc compose/writeback behavior is stable.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMKiraKira Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Classification: `{report['classification']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## BT.709 Remeasure",
        "",
        f"- Software cases: `{report['bt709_remeasure']['case_count']}`",
        f"- Exact cases: `{report['bt709_remeasure']['exact_count']}`",
        f"- Max diff max: `{report['bt709_remeasure']['max_diff_max']}`",
        f"- Mean sum: `{report['bt709_remeasure']['mean_sum']:.6f}`",
        "",
        "| Group | Cases | Max | Mean sum | Exact |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, group in report["bt709_remeasure"]["groups"].items():
        lines.append(
            f"| `{name}` | {group['case_count']} | {group['max_diff_max']} | "
            f"{float(group['mean_sum']):.6f} | {group['exact_count']} |"
        )
    lines.extend(
        [
            "",
            "## Grounded Stages",
            "",
            f"- Ray helper: `{report['ray_helper']['decision']}` (max delta `{report['ray_helper']['max_stage_delta']}`)",
            f"- BoxFilter focus: `{report['ray_helper']['boxfilter_focus']}`",
            f"- Aggregation: `{report['aggregation']['decision']}`",
            f"- Aggregation focus: `{report['aggregation']['likely_next_focus']}`",
            f"- Compose audit: `{report['compose_model_audit']['decision']}`",
            f"- Compose audit best by mean/max: `{report['compose_model_audit']['best_by_mean']}` / `{report['compose_model_audit']['best_by_max']}`",
            "",
            "## fd90 Samples",
            "",
            "| Label | XY | Ray inputs | Glow RGBA |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["aggregation"]["samples"]:
        lines.append(
            f"| `{row['label']}` | `{row['xy']}` | `{row['ray_inputs']}` | `{row['post_normalize_glow_rgba']}` |"
        )
    lines.extend(
        [
            "",
            "## Implied Screen Compose Scale",
            "",
            "| Label | XY | fd90 alpha | implied alpha mean | implied scale mean | scale range |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in report["aggregation"]["compose_scale_samples"]:
        lines.append(
            f"| `{row['label']}` | `{row['xy']}` | {row['fd90_glow_alpha']:.8f} | "
            f"{row['implied_screen_alpha_mean']:.8f} | {row['implied_scale_mean']:.8f} | "
            f"`{row['implied_scale_min']:.8f}..{row['implied_scale_max']:.8f}` |"
        )
    lines.extend(["", "## Next Evidence", ""])
    lines.extend(f"- {item}" for item in report["next_evidence"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(f"report_json={args.output_json}")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(render_markdown(report), encoding="utf-8")
        print(f"report_md={args.output_md}")
    if not args.output_json and not args.output_md:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
