#!/usr/bin/env python3
"""Freeze the active DirectionalBlur Windows witness anchors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PENDING_PROOF_JSON = ROOT / "refs/conformance/olmdirectionalblur_pending_witness_proof_20260629.json"
ENDPOINT_JSON = ROOT / "refs/conformance/olmdirectionalblur_angle0_endpoint_constraint_20260630.json"
CONTRACT_MD = ROOT / "refs/reports/olmdirectionalblur_witness_contract_20260624/witness_contract.md"
OUT_JSON = ROOT / "refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pending-proof-json", type=Path, default=PENDING_PROOF_JSON)
    parser.add_argument("--endpoint-json", type=Path, default=ENDPOINT_JSON)
    parser.add_argument("--contract-md", type=Path, default=CONTRACT_MD)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    pending = read_json(args.pending_proof_json)
    endpoint = read_json(args.endpoint_json)

    angle0 = pending["angle0_lane"]
    diagonal = pending["diagonal_lane"]

    report = {
        "kind": "olmdirectionalblur_hook_anchor_audit",
        "schema": 1,
        "contract_path": str(args.contract_md.relative_to(ROOT)),
        "angle0_lane": {
            "classification": angle0["classification"],
            "primary_witness": angle0["primary_witness"],
            "scan_order_max_witness": angle0["scan_order_max_witness"],
            "required_next_proof": angle0["required_next_proof"],
            "full_segments": angle0["current_local_readback"]["full_segments"],
            "scatter_segments": angle0["current_local_readback"]["scatter_segments"],
            "identical_mask": angle0["current_local_readback"]["identical_mask"],
            "endpoint_constraint": endpoint["endpoint_reasoning"],
            "helper_local_static_facts": angle0["helper_local_static_facts"],
        },
        "diagonal_lane": {
            "classification": diagonal["classification"],
            "primary_witness": diagonal["primary_witness"],
            "companion_witnesses": diagonal["companion_witnesses"],
            "required_next_proof": diagonal["required_next_proof"],
            "scatter_vs_full_bbox": diagonal["current_local_readback"]["scatter_vs_full_bbox"],
            "scatter_vs_full_max_abs": diagonal["current_local_readback"]["scatter_vs_full_max_abs"],
        },
        "hook_reading": {
            "status": "two-independent-hook-anchors-still-missing-typed-runtime-values",
            "reason": (
                "DirectionalBlur no longer lacks witness coordinates; it lacks typed runtime values at two already "
                "separated families. Angle-0 is the long RGB-only strip on row `y=169`, where alpha already matches "
                "and the key unresolved question is helper-local destination coverage or a validity-side channel. "
                "Diagonal is a separate rotate/validity family with signed red errors in both directions."
            ),
            "next_windows_hook": (
                "Keep the angle-0 strip witnesses `(494,169)` and `(579,169)` separate from the diagonal witness "
                "`(507,367)`, and return helper-local / rowdriver-group / valid-alpha coverage facts for the former "
                "plus typed rotate-sampler / border-validity / group-size-normalization facts for the latter."
            ),
            "why_this_anchor_matters": (
                "This anchor removes the remaining ambiguity about which DirectionalBlur pixels matter. The next "
                "Windows value should prove one of two bounded theories, not reopen broad candidate fitting."
            ),
        },
        "wanted_angle0_fields": [
            "helper-local source x/y",
            "param_1 / param_3 / param_9 / param_11",
            "effective span and touched destination x range",
            "rowdriver/group membership",
            "valid-alpha side-channel",
            "accumulation numerator/denominator",
            "pre-writeback RGBA and final bytes",
        ],
        "wanted_diagonal_fields": [
            "rotate sampler source coordinates and order",
            "border/validity decision",
            "group-size or opacity gate",
            "accumulation denominator",
            "pre-writeback RGBA",
            "final bytes",
        ],
        "runtime_package": pending["runtime_package"],
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    angle0 = report["angle0_lane"]
    diagonal = report["diagonal_lane"]
    lines = [
        "# OLMDirectionalBlur Hook Anchor Audit",
        "",
        f"- Contract: `{report['contract_path']}`",
        f"- Runtime package: `{report['runtime_package']}`",
        f"- Decision: `{report['hook_reading']['status']}`",
        f"- Reason: {report['hook_reading']['reason']}",
        f"- Why this anchor matters: {report['hook_reading']['why_this_anchor_matters']}",
        "",
        "## Angle-0 Anchor",
        "",
        f"- Classification: `{angle0['classification']}`",
        f"- Primary witness: `{angle0['primary_witness']}`",
        f"- Strip endpoint witness: `{{'xy': [579, 169]}}`",
        f"- Scan-order max witness: `{angle0['scan_order_max_witness']}`",
        f"- full segments: `{angle0['full_segments']}`",
        f"- scatter segments: `{angle0['scatter_segments']}`",
        f"- identical mask under scatter toggle: `{angle0['identical_mask']}`",
        f"- Endpoint constraint: {angle0['endpoint_constraint']}",
        "- Helper-local static facts:",
    ]
    for item in angle0["helper_local_static_facts"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Wanted angle-0 fields:",
        ]
    )
    for item in report["wanted_angle0_fields"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Diagonal Anchor",
            "",
            f"- Classification: `{diagonal['classification']}`",
            f"- Primary witness: `{diagonal['primary_witness']}`",
            f"- Companion witnesses: `{diagonal['companion_witnesses']}`",
            f"- scatter_vs_full_bbox: `{diagonal['scatter_vs_full_bbox']}`",
            f"- scatter_vs_full_max_abs: `{diagonal['scatter_vs_full_max_abs']}`",
            "",
            "Wanted diagonal fields:",
        ]
    )
    for item in report["wanted_diagonal_fields"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Windows Hook Ask",
            "",
            f"- {report['hook_reading']['next_windows_hook']}",
            "",
            "## Reading",
            "",
            "- Angle-0 and diagonal are still independent lanes.",
            "- Angle-0 is already bounded to helper-local destination coverage / rowdriver-group / valid-alpha facts on row 169.",
            "- Diagonal is already bounded to rotate-sampler / border-validity / group-size-normalization facts at the high-residual rotate path.",
            "- The next useful Windows return should prove one of those bounded theories, not repeat broad PNGs or module-load failures.",
            "",
        ]
    )
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
    print(f"decision={report['hook_reading']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
