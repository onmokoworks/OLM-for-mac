#!/usr/bin/env python3
"""Summarize OLMBlur conformance and max=1 residual decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provenance-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmblur_reference_provenance_20260622_025614" / "audit.json",
    )
    parser.add_argument(
        "--canonicalization-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "software_reference_canonicalization_8bpc.json",
    )
    parser.add_argument(
        "--trace-comparison-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "runtime_trace_comparisons"
        / "olmblur_repeat_threshold_20260620"
        / "olmblur_repeat_threshold.json",
    )
    parser.add_argument(
        "--bitdepth16-summary-json",
        type=Path,
        default=ROOT / "refs" / "conformance" / "bitdepth_16bpc_reference_return_20260625.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def blur_feature(canonicalization: dict[str, Any]) -> dict[str, Any]:
    for feature in canonicalization.get("features", []):
        if isinstance(feature, dict) and feature.get("name") == "OLMBlur":
            return feature
    raise ValueError("OLMBlur feature not found in canonicalization report")


def bitdepth16_reference(path: Path, group: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = read_json(path)
    groups = data.get("groups") or {}
    count = int(groups.get(group, 0))
    if count <= 0:
        return None
    return {
        "bit_depth": data.get("bit_depth"),
        "case_count": count,
        "manifest": data.get("imported_manifest"),
        "request_id": data.get("request_id"),
        "status": data.get("status"),
    }


def residual_summary(trace: dict[str, Any]) -> dict[str, Any]:
    diff = ((trace.get("local_baseline") or {}).get("diff") or {})
    cases = [row for row in diff.get("cases", []) if isinstance(row, dict)]
    max_diff = max((int(row.get("max_diff", 0)) for row in cases), default=0)
    nonzero_px = sum(int(row.get("nonzero_px", 0)) for row in cases)
    names = [str(row.get("id")) for row in cases]
    windows = trace.get("windows") or {}
    case_0006 = windows.get("case_0006") or {}
    case_0007 = windows.get("case_0007") or {}

    return {
        "case_ids": names,
        "max_diff": max_diff,
        "nonzero_px": nonzero_px,
        "diff_summary": diff.get("summary", {}),
        "case_0006_prewriteback": (
            ((case_0006.get("residual_pixels") or [{}])[0]).get("aex_pre_writeback_rgb_hex")
            if case_0006.get("residual_pixels")
            else None
        ),
        "case_0006_cli_prewriteback": (
            ((case_0006.get("residual_pixels") or [{}])[0]).get("cli_pre_writeback_rgb_hex")
            if case_0006.get("residual_pixels")
            else None
        ),
        "case_0007_writer_family": "OLMBlur+0x7FDF"
        if "0x7FDF" in str(case_0007.get("accumulation_order_notes", ""))
        else "unknown",
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    provenance = read_json(args.provenance_json)
    canonical = blur_feature(read_json(args.canonicalization_json))
    trace = read_json(args.trace_comparison_json)
    ref16 = bitdepth16_reference(args.bitdepth16_summary_json, "olmblur")
    classification = provenance.get("classification", {})
    trace_focus = str(trace.get("likely_next_focus", "missing-trace-comparison"))

    case_count = int(canonical.get("case_count", 0))
    normalized_nonzero = int(canonical.get("normalized_nonzero_count", -1))
    normalized_status = str(canonical.get("canonical_8bpc_status"))
    legacy_drift_cases = canonical.get("legacy_drift_cases", [])
    residuals = residual_summary(trace)

    if (
        normalized_status == "normalized-software-exact"
        and normalized_nonzero == 0
        and classification.get("status") == "normalized-software-exact-with-legacy-drift"
        and residuals["max_diff"] <= 1
    ):
        decision = "preserve-normalized-ae-exact"
        action = (
            "Do not tune OLMBlur from the old 20260604 drift or from AE-free CLI max=1 witnesses. "
            "The current trace points at accumulation/helper state before byte output, while packaged 8bpc AE slices are exact; "
            "16bpc Windows references are covered and now need Mac AE comparison."
        )
    elif normalized_status != "normalized-software-exact" or normalized_nonzero != 0:
        decision = "current-residual-needs-proof"
        action = "Treat normalized 8bpc residuals as active and gather narrow runtime/AE proof before changing code."
    else:
        decision = "needs-review"
        action = "Review provenance, trace, and AE-host evidence before changing OLMBlur behavior."

    return {
        "kind": "olmblur_decision_matrix",
        "schema": 1,
        "inputs": {
            "provenance_json": str(args.provenance_json),
            "canonicalization_json": str(args.canonicalization_json),
            "trace_comparison_json": str(args.trace_comparison_json),
            "bitdepth16_summary_json": str(args.bitdepth16_summary_json),
        },
        "normalized_8bpc": {
            "status": normalized_status,
            "case_count": case_count,
            "normalized_nonzero_count": normalized_nonzero,
            "exact_count": case_count - max(normalized_nonzero, 0),
            "classification": "exact" if normalized_status == "normalized-software-exact" and normalized_nonzero == 0 else "residual",
        },
        "legacy_drift": {
            "classification": classification.get("status"),
            "legacy_nonzero_count": int(canonical.get("legacy_nonzero_count", 0)),
            "cases": legacy_drift_cases,
            "recommended_action": classification.get("recommended_action"),
        },
        "cli_residuals": {
            "classification": "diagnostic-max1" if residuals["max_diff"] <= 1 else "active-residual",
            **residuals,
        },
        "runtime_trace": {
            "likely_next_focus": trace_focus,
            "present": bool((trace.get("windows") or {}).get("present")),
            "classification": "prewriteback-or-helper-state" if trace_focus == "nonlegacy-accumulation-or-writeback" else "review",
        },
        "windows_16bpc_reference": ref16,
        "decision": decision,
        "recommended_action": action,
        "next_evidence": [
            "Packaged Mac AE exact against canonical normalized 8bpc OLMBlur refs is already established; preserve it.",
            "Run Mac AE-host 16bpc validation against the covered Windows Software reference cases.",
            "32bpc Software reference coverage.",
            "Only continue CLI max=1 closure if binary-grounding the true accumulation/helper and Legacy border/all-same state becomes necessary.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMBlur Decision Matrix",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Evidence",
        "",
        f"- Normalized 8bpc: `{report['normalized_8bpc']['status']}` "
        f"({report['normalized_8bpc']['exact_count']}/{report['normalized_8bpc']['case_count']} exact)",
        (
            f"- Windows 16bpc reference: `{report['windows_16bpc_reference']['status']}` "
            f"({report['windows_16bpc_reference']['case_count']} cases)"
            if report.get("windows_16bpc_reference")
            else "- Windows 16bpc reference: `missing`"
        ),
        f"- Legacy drift: `{report['legacy_drift']['classification']}` "
        f"({report['legacy_drift']['legacy_nonzero_count']} cases)",
        f"- CLI residuals: `{report['cli_residuals']['classification']}` "
        f"(max `{report['cli_residuals']['max_diff']}`, nonzero px `{report['cli_residuals']['nonzero_px']}`)",
        f"- Runtime trace: `{report['runtime_trace']['classification']}` "
        f"(focus `{report['runtime_trace']['likely_next_focus']}`)",
        "",
        "## Runtime Witness Classification",
        "",
        f"- `case_0006`: Windows pre-writeback `{report['cli_residuals']['case_0006_prewriteback']}`, "
        f"Mac CLI pre-writeback `{report['cli_residuals']['case_0006_cli_prewriteback']}`.",
        f"- `case_0007`: writer family `{report['cli_residuals']['case_0007_writer_family']}`; "
        "Legacy border/all-same state is not isolated.",
        "",
        "## Legacy Drift Cases",
        "",
        "| Case | Max | Mean | Witness |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in report["legacy_drift"]["cases"]:
        witness = row.get("max_at", {})
        lines.append(
            f"| `{row.get('id')}` | {row.get('max_diff')} | {float(row.get('mean_diff', 0.0)):.9f} | "
            f"`x={witness.get('x')} y={witness.get('y')} c={witness.get('channel')} "
            f"ref={witness.get('reference')} cand={witness.get('candidate')}` |"
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
