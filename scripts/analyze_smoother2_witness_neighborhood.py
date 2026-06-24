#!/usr/bin/env python3
"""Summarize OLMSmoother2 current-AEX witness neighborhoods.

This report is a Mac-side narrowing aid.  It does not tune the implementation;
it records the local 5x5 reference/candidate shape around each active witness
so the next Windows trace can target the first real divergence instead of
asking for another broad PNG set.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-audit-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_residual_audit_latest" / "residual_audit.json",
    )
    parser.add_argument("--radius", type=int, default=2)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def read_rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def pixel_kind(rgba: list[int]) -> str:
    if rgba[3] == 0:
        return "transparent"
    if rgba[0] == rgba[1] == rgba[2]:
        return "gray"
    return "color"


def premul_gray_ratio(rgba: list[int]) -> float | None:
    if rgba[3] == 0 or not (rgba[0] == rgba[1] == rgba[2]):
        return None
    return round(float(rgba[0]) / float(rgba[3]), 6)


def neighborhood(reference: np.ndarray, candidate: np.ndarray, x: int, y: int, radius: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    height, width = reference.shape[:2]
    for yy in range(max(0, y - radius), min(height, y + radius + 1)):
        for xx in range(max(0, x - radius), min(width, x + radius + 1)):
            ref = [int(v) for v in reference[yy, xx]]
            cand = [int(v) for v in candidate[yy, xx]]
            delta = [abs(ref[i] - cand[i]) for i in range(4)]
            rows.append(
                {
                    "xy": [xx, yy],
                    "offset": [xx - x, yy - y],
                    "reference_rgba": ref,
                    "candidate_rgba": cand,
                    "delta_rgba": delta,
                    "max_delta": max(delta),
                    "reference_kind": pixel_kind(ref),
                    "candidate_kind": pixel_kind(cand),
                    "reference_gray_over_alpha": premul_gray_ratio(ref),
                    "candidate_gray_over_alpha": premul_gray_ratio(cand),
                }
            )
    return rows


def classify_case(case_id: str, center: dict[str, Any], cells: list[dict[str, Any]]) -> dict[str, Any]:
    ref = center["reference_rgba"]
    cand = center["candidate_rgba"]
    nonzero_cells = [cell for cell in cells if cell["max_delta"] > 0]
    neighbors = [cell for cell in cells if cell["offset"] != [0, 0]]
    same_as_ref_neighbors = [
        cell for cell in neighbors if cell["reference_rgba"] == ref or cell["candidate_rgba"] == ref
    ]
    source_like_neighbors = [
        cell
        for cell in neighbors
        if cell["candidate_rgba"] == cand or cell["reference_rgba"] == cand
    ]
    strongest_neighbor_deltas = sorted(
        (cell for cell in neighbors if cell["max_delta"] > 0),
        key=lambda cell: (cell["max_delta"], abs(cell["offset"][0]) + abs(cell["offset"][1])),
        reverse=True,
    )[:5]

    if ref[3] > 0 and cand[3] == 0:
        kind = "windows-adds-semitransparent-output-where-local-passthrough-is-transparent"
        next_evidence = (
            "Trace whether Windows c280 for this transparent-center cell emits a polygon sample "
            "or whether cce0 receives a nonzero fallback before passthrough."
        )
        trace_focus = [
            "center c280 idx / polygon count / append list",
            "center cce0 input/output before passthrough",
            "neighbor cell whose Windows value equals the missing center output",
        ]
    elif ref[3] == 0 and cand[3] > 0:
        kind = "local-adds-semitransparent-output-where-windows-stays-transparent"
        next_evidence = (
            "Trace whether Windows suppresses the local cardinal/f270/e3a0 append, changes "
            "the class bits, or zeroes the sample before cce0 blend."
        )
        trace_focus = [
            "center c280 idx / cardinal6 descriptor / polygon count",
            "center e170 bits and f270/e3a0 append/no-append decision",
            "strongest non-center cells to prove whether suppression is local-only",
        ]
    else:
        kind = "localized-value-mismatch"
        next_evidence = "Trace exact c280/cce0 state for the center and strongest neighboring deltas."
        trace_focus = [
            "center c280/cce0 state",
            "strongest neighboring delta cells",
        ]

    return {
        "kind": kind,
        "nonzero_cells_in_window": len(nonzero_cells),
        "max_delta_in_window": max((cell["max_delta"] for cell in cells), default=0),
        "neighbor_cells_matching_reference_center": same_as_ref_neighbors,
        "neighbor_cells_matching_candidate_center": source_like_neighbors,
        "strongest_neighbor_deltas": strongest_neighbor_deltas,
        "trace_focus": trace_focus,
        "next_evidence": next_evidence,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    audit = load_json(args.residual_audit_json)
    run_dir = Path(str(audit["run_dir"]))
    rows = []
    for case in audit.get("cases", []):
        if not isinstance(case, dict):
            continue
        witness = case.get("witness", {})
        x = int(witness["x"])
        y = int(witness["y"])
        frame = str(case["frame"])
        reference = read_rgba(run_dir / "reference" / frame)
        candidate = read_rgba(run_dir / "candidate" / frame)
        cells = neighborhood(reference, candidate, x, y, args.radius)
        center = next(cell for cell in cells if cell["offset"] == [0, 0])
        rows.append(
            {
                "case_id": case["case_id"],
                "xy": [x, y],
                "trace_log": case.get("trace_log"),
                "center": center,
                "classification": classify_case(str(case["case_id"]), center, cells),
                "cells": cells,
            }
        )
    return {
        "kind": "olmsmoother2_witness_neighborhood",
        "schema": 1,
        "inputs": {
            "residual_audit_json": str(args.residual_audit_json),
            "radius": args.radius,
        },
        "decision": "narrow-witness-neighborhoods-only",
        "cases": rows,
        "recommended_action": (
            "Do not request broad Smoother2 PNGs. If Windows is needed, ask for "
            "c280/cce0 state only at these center pixels and the listed strongest "
            "neighboring deltas."
        ),
    }


def rgba(value: list[int]) -> str:
    return "[" + ",".join(str(v) for v in value) + "]"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Witness Neighborhoods",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Summary",
        "",
        "| Case | XY | Center reference | Center candidate | Shape | Window nonzero | Next evidence |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for case in report["cases"]:
        center = case["center"]
        cls = case["classification"]
        lines.append(
            f"| `{case['case_id']}` | `{case['xy']}` | `{rgba(center['reference_rgba'])}` | "
            f"`{rgba(center['candidate_rgba'])}` | `{cls['kind']}` | "
        f"{cls['nonzero_cells_in_window']} | {cls['next_evidence']} |"
        )
    lines.extend(["", "## Trace Focus", ""])
    for case in report["cases"]:
        cls = case["classification"]
        lines.append(f"### {case['case_id']} `{case['xy']}`")
        lines.append("")
        lines.extend(f"- {item}" for item in cls["trace_focus"])
        lines.append("")
        lines.append("| Rank | Offset | XY | Ref | Cand | Max |")
        lines.append("| ---: | --- | --- | --- | --- | ---: |")
        for index, cell in enumerate(cls["strongest_neighbor_deltas"], start=1):
            lines.append(
                f"| {index} | `{cell['offset']}` | `{cell['xy']}` | "
                f"`{rgba(cell['reference_rgba'])}` | `{rgba(cell['candidate_rgba'])}` | "
                f"{cell['max_delta']} |"
            )
        lines.append("")
    lines.extend(["", "## Window Cells", ""])
    for case in report["cases"]:
        lines.append(f"### {case['case_id']} `{case['xy']}`")
        lines.append("")
        lines.append("| Offset | XY | Ref | Cand | Max | Ref/A | Cand/A |")
        lines.append("| --- | --- | --- | --- | ---: | ---: | ---: |")
        for cell in case["cells"]:
            ref_ratio = cell["reference_gray_over_alpha"]
            cand_ratio = cell["candidate_gray_over_alpha"]
            lines.append(
                f"| `{cell['offset']}` | `{cell['xy']}` | `{rgba(cell['reference_rgba'])}` | "
                f"`{rgba(cell['candidate_rgba'])}` | {cell['max_delta']} | "
                f"{'-' if ref_ratio is None else ref_ratio} | "
                f"{'-' if cand_ratio is None else cand_ratio} |"
            )
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
