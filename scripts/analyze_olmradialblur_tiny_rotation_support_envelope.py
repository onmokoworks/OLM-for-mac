#!/usr/bin/env python3
"""Summarize which probed outputs can directly see the row-843 bright cluster."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SAME_ROW_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_same_row_audit_20260701.json"
SOURCE_POLAR_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_polar_probe_20260701.json"
OUT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.json"
OUT_MD = ROOT / "refs/conformance/olmradialblur_tiny_rotation_support_envelope_20260701.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--same-row-json", type=Path, default=SAME_ROW_JSON)
    parser.add_argument("--source-polar-json", type=Path, default=SOURCE_POLAR_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    same_row = read_json(args.same_row_json)
    source_polar = read_json(args.source_polar_json)

    cluster = source_polar["dominant_local_positive_cluster"]
    cluster_rows = sorted({int(row["xy"][1]) for row in cluster})
    cluster_angles = sorted({int(row["xy"][0]) for row in cluster})
    cluster_xy = [row["xy"] for row in cluster]

    outputs = []
    for row in same_row["rows"]:
        xy = row["xy"]
        supporting_cells = []
        supporting_angles = set()
        for cell in row["cells"]:
            if int(cell["radius_row"]) not in cluster_rows:
                continue
            taps = [int(v) for v in cell["same_row_source_taps"]]
            touched = [angle for angle in cluster_angles if angle in taps]
            if not touched:
                continue
            supporting_cells.append(
                {
                    "cell": cell["cell"],
                    "radius_row": int(cell["radius_row"]),
                    "same_row_source_taps": taps,
                    "touched_cluster_angles": touched,
                    "cell_rgb": cell["cell_rgb"],
                }
            )
            supporting_angles.update(touched)
        outputs.append(
            {
                "xy": xy,
                "sample_u8": row["sample_u8"],
                "indices": row["indices"],
                "can_directly_see_cluster": bool(supporting_cells),
                "supporting_cells": supporting_cells,
                "supported_cluster_angles": sorted(supporting_angles),
            }
        )

    witness = next(row for row in outputs if row["xy"] == [1614, 6])
    visible = [row for row in outputs if row["can_directly_see_cluster"]]

    return {
        "kind": "olmradialblur_tiny_rotation_support_envelope",
        "schema": 1,
        "case_id": "case_0010",
        "witness_xy": [1614, 6],
        "positive_cluster_xy": cluster_xy,
        "positive_cluster_rows": cluster_rows,
        "positive_cluster_angles": cluster_angles,
        "outputs": outputs,
        "decision": {
            "status": "witness-cannot-directly-see-row843-cluster-in-current-branch",
            "reason": (
                "Within the probed neighborhood, the current same-row Rotation branch only gives direct row-843 "
                "cluster visibility to nearby outputs whose bilinear support includes radius row 843. The active "
                "witness `(1614,6)` samples rows 844/845 only, so it cannot directly receive the row-843 bright "
                "cluster under the current branch. The few nearby outputs that do directly see the cluster are "
                "still dim (`[5,5,5]`, `[1,1,1]`, `[0,0,0]`), which supports the existing reading that the "
                "missing white lobe needs upstream neighbor-row ownership or a substitute/fallback path."
            ),
            "forbidden_action": (
                "Do not promote a same-row-only tweak, simple validity tweak, or final writeback tweak as the "
                "tiny-Rotation fix from this neighborhood alone."
            ),
            "next_allowed_action": (
                "Keep the Windows ask focused on substitute/fallback or upstream neighboring-row contribution "
                "ownership before final inverse sampling, now anchored from the stable inverse-sampler hit with "
                "sampled-cell / neighboring-row pointer-watch context."
            ),
        },
        "summary_counts": {
            "outputs_with_direct_cluster_visibility": len(visible),
            "outputs_without_direct_cluster_visibility": len(outputs) - len(visible),
            "witness_has_direct_cluster_visibility": witness["can_directly_see_cluster"],
        },
    }


def render_md(report: dict[str, Any]) -> str:
    decision = report["decision"]
    lines = [
        "# OLMRadialBlur tiny Rotation Support Envelope Audit",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `{tuple(report['witness_xy'])}`",
        f"- Positive cluster XY: `{report['positive_cluster_xy']}`",
        f"- Decision: `{decision['status']}`",
        f"- Reason: {decision['reason']}",
        f"- Forbidden action: {decision['forbidden_action']}",
        f"- Next allowed action: {decision['next_allowed_action']}",
        "",
        "## Neighborhood Visibility",
        "",
        "| XY | sample_u8 | indices | directly sees row-843 cluster | supporting cells |",
        "| - | - | - | - | - |",
    ]
    for row in report["outputs"]:
        cells = ", ".join(
            f"{cell['cell']} row={cell['radius_row']} taps={cell['touched_cluster_angles']}"
            for cell in row["supporting_cells"]
        ) or "-"
        lines.append(
            f"| `{tuple(row['xy'])}` | `{row['sample_u8']}` | `{row['indices']}` | "
            f"`{row['can_directly_see_cluster']}` | {cells} |"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            f"- outputs with direct cluster visibility: `{report['summary_counts']['outputs_with_direct_cluster_visibility']}`",
            f"- outputs without direct cluster visibility: `{report['summary_counts']['outputs_without_direct_cluster_visibility']}`",
            f"- witness has direct cluster visibility: `{report['summary_counts']['witness_has_direct_cluster_visibility']}`",
            "- The row-843 bright cluster is not globally invisible; some nearby outputs can directly sample it in the current branch.",
            "- But the active witness `(1614,6)` is not one of them, because its bilinear support stays on rows 844/845.",
            "- So the current branch cannot explain the missing white witness as a same-row-only effect from that row-843 cluster.",
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
    print(f"decision={report['decision']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
