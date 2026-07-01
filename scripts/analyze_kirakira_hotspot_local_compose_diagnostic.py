#!/usr/bin/env python3
"""Summarize a hotspot-local KiraKira compose-boundary diagnostic from existing evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WITNESS_JSON = ROOT / "refs" / "conformance" / "olmkirakira_compose_boundary_mac_witness_20260630.json"
DEFAULT_PENDING_JSON = ROOT / "refs" / "conformance" / "olmkirakira_pending_compose_proof_20260629.json"
DEFAULT_AUDIT_JSON = ROOT / "refs" / "reports" / "olmkirakira_compose_model_audit_20260625" / "compose_model_audit.json"
DEFAULT_OUT_JSON = ROOT / "refs" / "conformance" / "olmkirakira_hotspot_local_compose_diagnostic_20260701.json"
DEFAULT_OUT_MD = ROOT / "refs" / "conformance" / "olmkirakira_hotspot_local_compose_diagnostic_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--witness-json", type=Path, default=DEFAULT_WITNESS_JSON)
    parser.add_argument("--pending-json", type=Path, default=DEFAULT_PENDING_JSON)
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    return data


def screen_over_output_channel(source: float, alpha: float) -> float:
    return source + (1.0 - source) * alpha


def implied_alpha_from_u8(source: float, target_u8: int) -> dict[str, float]:
    lo_out = (target_u8 - 0.5) / 255.0
    hi_out = (target_u8 + 0.5) / 255.0
    lo_alpha = (lo_out - source) / (1.0 - source)
    hi_alpha = (hi_out - source) / (1.0 - source)
    mid_alpha = ((target_u8 / 255.0) - source) / (1.0 - source)
    return {
        "lo": lo_alpha,
        "mid": mid_alpha,
        "hi": hi_alpha,
    }


def u8_from_output(value: float) -> int:
    return int(round(max(0.0, min(1.0, value)) * 255.0))


def build_grayscale_entry(label: str, source_u8: int, mac_alpha: float, mac_u8: int, windows_u8: int) -> dict[str, Any]:
    source = source_u8 / 255.0
    implied = implied_alpha_from_u8(source, windows_u8)
    predicted_output = screen_over_output_channel(source, implied["mid"])
    return {
        "label": label,
        "source_u8": source_u8,
        "source_float": source,
        "mac_compose_alpha": mac_alpha,
        "mac_compose_u8": mac_u8,
        "windows_u8": windows_u8,
        "windows_implied_alpha": implied,
        "alpha_drop_from_mac_mid": mac_alpha - implied["mid"],
        "attenuation_ratio_mid": implied["mid"] / mac_alpha if mac_alpha else None,
        "predicted_windows_output_from_mid_alpha_u8": u8_from_output(predicted_output),
    }


def build_report(witness: dict[str, Any], pending: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    points = witness["points"]
    hotspot = points["934,118"]
    source_hotspot_u8 = int(round(float(hotspot["src_rgba_float"][0]) * 255.0))
    hotspot_entry = build_grayscale_entry(
        label="primary_hotspot",
        source_u8=source_hotspot_u8,
        mac_alpha=float(hotspot["glow_rgba_float"][3]),
        mac_u8=int(hotspot["out_u8"][0]),
        windows_u8=int(hotspot["windows_reference_u8"][0]),
    )
    center_entry = build_grayscale_entry(
        label="center_control",
        source_u8=30,
        mac_alpha=float(points["960,540"]["glow_alpha_after_opacity"]),
        mac_u8=int(points["960,540"]["out_u8"][0]),
        windows_u8=int(points["960,540"]["windows_reference_u8"][0]),
    )
    right_entry = build_grayscale_entry(
        label="right_control",
        source_u8=30,
        mac_alpha=float(points["1010,540"]["glow_alpha_after_opacity"]),
        mac_u8=int(points["1010,540"]["out_u8"][0]),
        windows_u8=int(points["1010,540"]["windows_reference_u8"][0]),
    )

    control_ratio_mid = (
        center_entry["attenuation_ratio_mid"] + right_entry["attenuation_ratio_mid"]
    ) / 2.0
    hotspot_source = hotspot_entry["source_float"]
    hotspot_mac_alpha = hotspot_entry["mac_compose_alpha"]
    hotspot_control_projected_alpha = hotspot_mac_alpha * control_ratio_mid
    hotspot_control_projected_u8 = u8_from_output(
        screen_over_output_channel(hotspot_source, hotspot_control_projected_alpha)
    )

    hotspot_needed_delta_vs_controls = hotspot_control_projected_alpha - hotspot_entry["windows_implied_alpha"]["mid"]

    return {
        "kind": "olmkirakira_hotspot_local_compose_diagnostic",
        "status": "diagnostic",
        "date": "2026-07-01",
        "inputs": {
            "witness_json": str(DEFAULT_WITNESS_JSON),
            "pending_json": str(DEFAULT_PENDING_JSON),
            "audit_json": str(DEFAULT_AUDIT_JSON),
        },
        "decision_boundary": pending["decision_boundary"],
        "focus": {
            "case_id": witness["case_id"],
            "xy": [934, 118],
        },
        "grayscale_witnesses": [
            hotspot_entry,
            center_entry,
            right_entry,
        ],
        "hotspot_vs_grayscale_controls": {
            "control_ratio_mid_average": control_ratio_mid,
            "projected_hotspot_alpha_from_control_ratio": hotspot_control_projected_alpha,
            "projected_hotspot_u8_from_control_ratio": hotspot_control_projected_u8,
            "windows_hotspot_alpha_mid": hotspot_entry["windows_implied_alpha"]["mid"],
            "windows_hotspot_alpha_interval": hotspot_entry["windows_implied_alpha"],
            "extra_alpha_drop_needed_beyond_control_ratio": hotspot_needed_delta_vs_controls,
            "extra_u8_drop_needed_beyond_control_ratio": hotspot_control_projected_u8 - hotspot_entry["windows_u8"],
        },
        "compose_audit_context": {
            "decision_status": audit["decision"]["status"],
            "decision_reason": audit["decision"]["reason"],
            "baseline_id": audit["decision"]["baseline_id"],
        },
        "reading": [
            "The hotspot already mismatches at the Mac compose boundary, and the exact Windows-match alpha interval at that point is 0.446666666667..0.451111111111.",
            "Applying the average grayscale control attenuation to the hotspot still predicts byte 138, not the Windows byte 131.",
            "So the remaining KiraKira gap at (934,118) is narrower than a broad grayscale/global compose retune; it needs an additional hotspot-local attenuation or branch before writeback.",
        ],
    }


def write_md(path: Path, report: dict[str, Any]) -> None:
    hotspot, center, right = report["grayscale_witnesses"]
    compare = report["hotspot_vs_grayscale_controls"]
    lines = [
        "# OLMKiraKira Hotspot-Local Compose Diagnostic - 2026-07-01",
        "",
        "Bounded Mac-side diagnostic using only existing witness/audit evidence to sharpen the remaining compose question at `(934,118)`.",
        "",
        "## Primary hotspot",
        "",
        f"- case: `{report['focus']['case_id']}`",
        f"- point: `{tuple(report['focus']['xy'])}`",
        f"- Mac compose-boundary alpha: `{hotspot['mac_compose_alpha']:.9f}`",
        f"- Mac compose-boundary byte: `{hotspot['mac_compose_u8']}`",
        f"- Windows reference byte: `{hotspot['windows_u8']}`",
        f"- Windows-match implied alpha interval: `[{hotspot['windows_implied_alpha']['lo']:.12f}, {hotspot['windows_implied_alpha']['hi']:.12f}]`",
        f"- Windows-match implied alpha midpoint: `{hotspot['windows_implied_alpha']['mid']:.12f}`",
        f"- Additional alpha drop from Mac boundary midpoint: `{hotspot['alpha_drop_from_mac_mid']:.12f}`",
        f"- Hotspot attenuation ratio midpoint: `{hotspot['attenuation_ratio_mid']:.9f}`",
        "",
        "## Grayscale controls",
        "",
        f"- Center `(960,540)`: Mac alpha `{center['mac_compose_alpha']:.9f}`, Windows-implied alpha midpoint `{center['windows_implied_alpha']['mid']:.12f}`, attenuation ratio `{center['attenuation_ratio_mid']:.9f}`",
        f"- Right `(1010,540)`: Mac alpha `{right['mac_compose_alpha']:.9f}`, Windows-implied alpha midpoint `{right['windows_implied_alpha']['mid']:.12f}`, attenuation ratio `{right['attenuation_ratio_mid']:.9f}`",
        "",
        "## Hotspot-local readout",
        "",
        f"- Average grayscale control attenuation ratio: `{compare['control_ratio_mid_average']:.9f}`",
        f"- If that same ratio is applied at the hotspot, projected hotspot alpha is `{compare['projected_hotspot_alpha_from_control_ratio']:.12f}` and projected byte is `{compare['projected_hotspot_u8_from_control_ratio']}`",
        f"- Windows still needs hotspot alpha midpoint `{compare['windows_hotspot_alpha_mid']:.12f}`, which is `{compare['extra_alpha_drop_needed_beyond_control_ratio']:.12f}` below the control-ratio projection",
        f"- That leaves an extra hotspot-only byte drop of `{compare['extra_u8_drop_needed_beyond_control_ratio']}` beyond the already-grounded grayscale control behavior",
        "",
        "## Decision fit",
        "",
        f"- Compose audit status: `{report['compose_audit_context']['decision_status']}`",
        f"- Compose audit reason: {report['compose_audit_context']['decision_reason']}",
        "",
        "## Bottom line",
        "",
    ]
    lines.extend(f"- {line}" for line in report["reading"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    witness = load_json(args.witness_json)
    pending = load_json(args.pending_json)
    audit = load_json(args.audit_json)
    report = build_report(witness, pending, audit)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_md(args.output_md, report)
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
