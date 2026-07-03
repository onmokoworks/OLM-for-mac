#!/usr/bin/env python3
"""Freeze the current case_0023 triplet compose-hook anchor for DistanceGradation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THRESHOLD_AUDIT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json"
CONTRACT_MD = ROOT / "refs/conformance/olmdistancegradation_case0023_output_word_triplet_followup_contract_20260701.md"
OUT_JSON = ROOT / "refs/conformance/olmdistancegradation_case0023_triplet_hook_anchor_audit_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmdistancegradation_case0023_triplet_hook_anchor_audit_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold-audit-json", type=Path, default=THRESHOLD_AUDIT_JSON)
    parser.add_argument("--contract-md", type=Path, default=CONTRACT_MD)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    audit = read_json(args.threshold_audit_json)
    roles = audit["threshold_triplet_roles"]
    same_row = [row for row in roles if row["role"] in {
        "below_threshold_same_row",
        "first_above_threshold_same_row",
        "deeper_plateau_same_row",
    }]
    vertical = [row for row in roles if row["role"] in {
        "vertical_contrast_above",
        "vertical_contrast_below",
    }]

    report = {
        "kind": "olmdistancegradation_case0023_triplet_hook_anchor_audit",
        "schema": 1,
        "case_id": audit["case_id"],
        "triplet_xy": [[414, 393], [415, 393], [416, 393]],
        "triplet_roles": same_row,
        "vertical_context": vertical,
        "current_local_field_boundary": {
            "below_threshold_xy": [414, 393],
            "below_threshold_field_x": same_row[0]["field_x"],
            "first_above_xy": [415, 393],
            "first_above_field_x": same_row[1]["field_x"],
            "deeper_plateau_xy": [416, 393],
            "deeper_plateau_field_x": same_row[2]["field_x"],
        },
        "hook_reading": {
            "status": "triplet-bounded-compose-hook-still-missing",
            "reason": (
                "The local threshold triplet is already precise: `(414,393)` is below threshold with "
                "`field_x=0`, `(415,393)` is the first above-threshold point with `field_x=1`, and "
                "`(416,393)` stays on the same plateau side. So the missing Windows fact is no longer "
                "where the transition lives; it is the exact helper/compose hook that retains this XY "
                "identity and shows which typed value is consumed at the boundary."
            ),
            "next_windows_hook": (
                "Bind the triplet from the output-word address or compose refcon at the case-local helper/compose "
                "hook for `(414,393)`, `(415,393)`, `(416,393)`, and dump raw distances, helper-stage field value, "
                "Constant binary fork ordering, compose-consumed value, pre-store RGBA16, and final RGBA16."
            ),
            "why_this_anchor_matters": (
                "This anchor removes the ambiguity around which boundary pixels matter. The remaining uncertainty "
                "is the typed ownership rule at the hook, not the existence of the red/blue endpoint flip."
            ),
        },
        "wanted_fields": [
            "raw inside/outside distances",
            "helper-stage field value",
            "threshold/equality/plateau decision",
            "Constant binary fork order",
            "FUN_181170480 consumed value",
            "compose output before word store",
            "final RGBA16",
        ],
        "pending_windows_followup": audit["pending_windows_followup"],
        "contract_path": str(args.contract_md.relative_to(ROOT)),
    }
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# OLMDistanceGradation case_0023 Triplet Hook Anchor Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Triplet: `{report['triplet_xy']}`",
        f"- Contract: `{report['contract_path']}`",
        f"- Decision: `{report['hook_reading']['status']}`",
        f"- Reason: {report['hook_reading']['reason']}",
        f"- Why this anchor matters: {report['hook_reading']['why_this_anchor_matters']}",
        "",
        "## Same-Row Triplet",
        "",
        "| Role | XY | field_x | raw_inside | raw_outside | inside-threshold | d_alpha | alpha |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["triplet_roles"]:
        lines.append(
            f"| `{row['role']}` | `({row['x']},{row['y']})` | `{row['field_x']}` | `{row['raw_inside']}` | "
            f"`{row['raw_outside']}` | `{row['inside_minus_threshold']}` | `{row['d_alpha']}` | `{row['alpha']}` |"
        )
    lines.extend(
        [
            "",
            "## Vertical Context",
            "",
            "| Role | XY | field_x | raw_inside | inside-threshold |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in report["vertical_context"]:
        lines.append(
            f"| `{row['role']}` | `({row['x']},{row['y']})` | `{row['field_x']}` | `{row['raw_inside']}` | `{row['inside_minus_threshold']}` |"
        )
    lines.extend(
        [
            "",
            "## Windows Hook Ask",
            "",
            f"- {report['hook_reading']['next_windows_hook']}",
            "- Wanted typed fields:",
        ]
    )
    for field in report["wanted_fields"]:
        lines.append(f"- {field}")
    pending = report["pending_windows_followup"]
    lines.extend(
        [
            "",
            "## Pending Windows Follow-up",
            "",
            f"- Request: `{pending['request_id']}`",
            f"- Status: `{pending['status']}`",
            f"- Package: `{pending['package']}`",
            f"- Acceptance: `{pending['acceptance_note']}`",
            "",
            "## Reading",
            "",
            "- The triplet itself is no longer the unknown.",
            "- The first above-threshold point is already pinned locally at `(415,393)`.",
            "- The remaining unknown is the typed ownership rule at the helper/compose hook that turns that local boundary into the final red/blue endpoint split.",
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
