#!/usr/bin/env python3
"""Consolidate the current OLMKiraKira hotspot compose/writeback lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

WITNESS_JSON = ROOT / "refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json"
DIAGNOSTIC_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_local_compose_diagnostic_20260701.json"
WINDOWS_COMPARE_JSON = (
    ROOT / "refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json"
)
PENDING_JSON = ROOT / "refs/reports/pending_runtime_trace_packages.json"
OUT_JSON = ROOT / "refs/conformance/olmkirakira_hotspot_lane_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmkirakira_hotspot_lane_audit_20260701.md"
REQUEST_ID = "kirakira_hotspot_compose_writeback_witness_20260701"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--witness-json", type=Path, default=WITNESS_JSON)
    parser.add_argument("--diagnostic-json", type=Path, default=DIAGNOSTIC_JSON)
    parser.add_argument("--windows-compare-json", type=Path, default=WINDOWS_COMPARE_JSON)
    parser.add_argument("--pending-json", type=Path, default=PENDING_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def pending_row(report: dict[str, Any]) -> dict[str, Any]:
    for row in report["requests"]:
        if row.get("request_id") == REQUEST_ID:
            return row
    raise KeyError(f"missing pending request {REQUEST_ID}")


def witness_point(report: dict[str, Any], xy: str) -> dict[str, Any]:
    return report["points"][xy]


def compose_sample(report: dict[str, Any], label: str) -> dict[str, Any]:
    for row in report["windows"]["merge_mode_1_compose"]["sample_inputs_outputs"]:
        if row["label"] == label:
            return row
    raise KeyError(f"missing compose sample {label}")


def hotspot_row(report: dict[str, Any], label: str) -> dict[str, Any]:
    for row in report["windows"]["residual_hotspot"]:
        if row["label"] == label:
            return row
    raise KeyError(f"missing residual hotspot {label}")


def approx_equal_list(lhs: list[float], rhs: list[float], tol: float = 1e-6) -> bool:
    if len(lhs) != len(rhs):
        return False
    return all(abs(float(a) - float(b)) <= tol for a, b in zip(lhs, rhs))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    witness = read_json(args.witness_json)
    diagnostic = read_json(args.diagnostic_json)
    compare = read_json(args.windows_compare_json)
    pending = pending_row(read_json(args.pending_json))

    mac_hotspot = witness_point(witness, "934,118")
    windows_hotspot = compose_sample(compare, "hotspot")
    residual_hotspot = hotspot_row(compare, "primary_vertical_case_hotspot")
    control = diagnostic["hotspot_vs_grayscale_controls"]

    same_glow = approx_equal_list(windows_hotspot["glow_after_opacity_rgba_float"], mac_hotspot["glow_rgba_float"])
    same_compose = approx_equal_list(windows_hotspot["composed_rgba_float"], mac_hotspot["out_prequantized_rgba_float"])
    same_prewrite = approx_equal_list(
        windows_hotspot["pre_writeback_rgba_float"], mac_hotspot["out_prequantized_rgba_float"]
    )
    same_u8 = windows_hotspot["final_writeback_or_png_rgba"] == mac_hotspot["out_u8"]
    delta_to_reference = [
        int(windows_hotspot["final_writeback_or_png_rgba"][i]) - int(mac_hotspot["windows_reference_u8"][i]) for i in range(4)
    ]

    return {
        "kind": "olmkirakira_hotspot_lane_audit",
        "schema": 1,
        "case_id": witness["case_id"],
        "witness_xy": [934, 118],
        "mac_compose_boundary": {
            "src_rgba_float": mac_hotspot["src_rgba_float"],
            "glow_rgba_float": mac_hotspot["glow_rgba_float"],
            "out_prequantized_rgba_float": mac_hotspot["out_prequantized_rgba_float"],
            "out_u8": mac_hotspot["out_u8"],
            "windows_reference_u8": mac_hotspot["windows_reference_u8"],
        },
        "control_projection": {
            "projected_hotspot_u8_from_control_ratio": control["projected_hotspot_u8_from_control_ratio"],
            "extra_u8_drop_needed_beyond_control_ratio": control["extra_u8_drop_needed_beyond_control_ratio"],
            "windows_hotspot_alpha_mid": control["windows_hotspot_alpha_mid"],
        },
        "windows_hotspot_witness": {
            "glow_after_opacity_rgba_float": windows_hotspot["glow_after_opacity_rgba_float"],
            "composed_rgba_float": windows_hotspot["composed_rgba_float"],
            "pre_writeback_rgba_float": windows_hotspot["pre_writeback_rgba_float"],
            "final_writeback_or_png_rgba": windows_hotspot["final_writeback_or_png_rgba"],
            "residual_hotspot_row": residual_hotspot,
        },
        "agreement_checks": {
            "same_glow_after_opacity": same_glow,
            "same_compose_float": same_compose,
            "same_pre_writeback_float": same_prewrite,
            "same_final_writeback_or_png_rgba": same_u8,
            "writeback_minus_reference_rgba": delta_to_reference,
        },
        "pending_windows_followup": {
            "request_id": pending["request_id"],
            "status": pending["status"],
            "package": pending["package"],
            "latest_known_result_status": pending["latest_known_result_status"],
            "latest_known_result_summary": pending["latest_known_result_summary"],
        },
        "decision": {
            "status": "hotspot-proof-shifted-to-reference-or-witness-placement",
            "reason": (
                "The answered 2026-07-01 Windows hotspot witness no longer supports a KiraKira compose or "
                "pre-writeback patch. At `(934,118)`, the Windows trace reports the same glow-after-opacity "
                "alpha, the same composed float, the same pre-writeback float, and the same final sampled "
                "RGBA8 as the current Mac compose-boundary witness: 144, not the canonical Windows reference 131. "
                "That moves the live lane away from broad compose/gain/quantization tuning and toward "
                "reference/export provenance or witness-placement drift."
            ),
            "forbidden_action": (
                "Do not reopen BT.709, boxFilter, ray-helper, global compose scale, hotspot-local attenuation, "
                "or final quantization tuning from this witness alone."
            ),
            "next_allowed_action": (
                "Treat the hotspot algorithm lane as provisionally matched through the traced writeback sample, "
                "and only spend more effort here on reference/export provenance, witness-placement validation, "
                "or the still-missing endgame control coverage."
            ),
        },
    }


def render_md(report: dict[str, Any]) -> str:
    checks = report["agreement_checks"]
    mac = report["mac_compose_boundary"]
    windows = report["windows_hotspot_witness"]
    pending = report["pending_windows_followup"]
    lines = [
        "# OLMKiraKira Hotspot Lane Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Decision: `{report['decision']['status']}`",
        f"- Reason: {report['decision']['reason']}",
        f"- Forbidden action: {report['decision']['forbidden_action']}",
        f"- Next allowed action: {report['decision']['next_allowed_action']}",
        "",
        "## Mac Compose-Boundary Witness",
        "",
        f"- src_rgba_float: `{mac['src_rgba_float']}`",
        f"- glow_rgba_float: `{mac['glow_rgba_float']}`",
        f"- out_prequantized_rgba_float: `{mac['out_prequantized_rgba_float']}`",
        f"- out_u8: `{mac['out_u8']}`",
        f"- canonical Windows reference: `{mac['windows_reference_u8']}`",
        "",
        "## Windows Hotspot Witness",
        "",
        f"- glow_after_opacity_rgba_float: `{windows['glow_after_opacity_rgba_float']}`",
        f"- composed_rgba_float: `{windows['composed_rgba_float']}`",
        f"- pre_writeback_rgba_float: `{windows['pre_writeback_rgba_float']}`",
        f"- final_writeback_or_png_rgba: `{windows['final_writeback_or_png_rgba']}`",
        "",
        "## Agreement Checks",
        "",
        f"- same glow-after-opacity: `{checks['same_glow_after_opacity']}`",
        f"- same compose float: `{checks['same_compose_float']}`",
        f"- same pre-writeback float: `{checks['same_pre_writeback_float']}`",
        f"- same final writeback/sample RGBA: `{checks['same_final_writeback_or_png_rgba']}`",
        f"- writeback minus canonical reference: `{checks['writeback_minus_reference_rgba']}`",
        "",
        "## Control-Ratio Sanity Check",
        "",
        f"- projected hotspot u8 from grayscale control ratio: `{report['control_projection']['projected_hotspot_u8_from_control_ratio']}`",
        f"- extra u8 drop formerly needed beyond control ratio: `{report['control_projection']['extra_u8_drop_needed_beyond_control_ratio']}`",
        f"- Windows hotspot alpha midpoint implied by canonical ref: `{report['control_projection']['windows_hotspot_alpha_mid']}`",
        "",
        "## Runtime Request Record",
        "",
        f"- Request: `{pending['request_id']}`",
        f"- Status: `{pending['status']}`",
        f"- Package: `{pending['package']}`",
        f"- Latest known result status: `{pending['latest_known_result_status']}`",
        f"- Latest known result summary: `{pending['latest_known_result_summary']}`",
        "",
        "## Reading",
        "",
        "- This witness does not say the exported Windows reference PNG is wrong; it says the traced hotspot sample no longer justifies changing KiraKira compose math.",
        "- The traced Windows hotspot matches the current Mac compose-boundary values through pre-writeback and sampled RGBA8, while the canonical reference PNG still says 131.",
        "- So the algorithm lane is no longer a broad compose/gain/quantization lane. The remaining lane is reference/export provenance, witness placement, or other endgame coverage outside this hotspot trace.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(f"report_json={args.output_json}")
    print(f"report_md={args.output_md}")
    print(f"decision={report['decision']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
