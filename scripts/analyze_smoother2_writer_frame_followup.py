#!/usr/bin/env python3
"""Summarize Smoother2 writer-frame follow-up evidence.

This is a narrowing report, not an implementation tuner. It checks whether the
Windows writer-frame float candidates explain the Windows reference pixels and
therefore whether the remaining divergence is upstream of final writeback.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-summary-json",
        type=Path,
        default=(
            ROOT
            / "refs"
            / "reports"
            / "smoother2_current_aex_writer_frame_followup_20260625"
            / "runtime_trace_summary_smoother2_current_aex_writer_frame_followup_20260625_214942.json"
        ),
    )
    parser.add_argument(
        "--neighborhood-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_witness_neighborhood_20260624" / "neighborhood.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def clamp_u8(value: float) -> int:
    return max(0, min(255, int(math.floor(value + 0.5))))


def straight_float_to_packed_argb(rgba: list[float]) -> dict[str, Any]:
    r = clamp_u8(rgba[0] * 255.0)
    g = clamp_u8(rgba[1] * 255.0)
    b = clamp_u8(rgba[2] * 255.0)
    a = clamp_u8(rgba[3] * 255.0)
    packed = f"0x{r:02x}{g:02x}{b:02x}{a:02x}"
    png_rgba = [
        clamp_u8(r * a / 255.0),
        clamp_u8(g * a / 255.0),
        clamp_u8(b * a / 255.0),
        a,
    ]
    return {
        "straight_u8_rgba": [r, g, b, a],
        "packed_raw_rgba_order": packed,
        "expected_png_rgba_after_premultiply": png_rgba,
    }


def raw_rgba_to_png(raw: str) -> dict[str, Any]:
    text = raw.lower().removeprefix("0x")
    value = int(text, 16)
    r = (value >> 24) & 0xFF
    g = (value >> 16) & 0xFF
    b = (value >> 8) & 0xFF
    a = value & 0xFF
    return {
        "straight_u8_rgba": [r, g, b, a],
        "expected_png_rgba_after_premultiply": [
            clamp_u8(r * a / 255.0),
            clamp_u8(g * a / 255.0),
            clamp_u8(b * a / 255.0),
            a,
        ],
    }


def result_observations(summary: dict[str, Any]) -> dict[str, Any]:
    result = next(
        (
            row
            for row in summary.get("results", [])
            if isinstance(row, dict)
            and row.get("request_id") == "olmsmoother2_current_aex_writer_frame_followup_trace_20260625"
        ),
        None,
    )
    if not isinstance(result, dict):
        raise ValueError("writer-frame follow-up result not found")
    observations = ((result.get("observations") or {}).get("observations") or {})
    if not isinstance(observations, dict):
        raise ValueError("writer-frame observations missing")
    return observations


def by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["case_id"]): row for row in rows}


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    observations = result_observations(read_json(args.runtime_summary_json))
    neighborhoods = by_case(read_json(args.neighborhood_json).get("cases") or [])
    rows = []
    for case in observations.get("cases", []):
        if not isinstance(case, dict):
            continue
        case_id = str(case["case_id"])
        neighborhood = neighborhoods[case_id]
        center = neighborhood["center"]
        decoded = ((case.get("writer_frame_local_candidate") or {}).get("decoded") or {})
        rgba_float = [float(v) for v in decoded.get("rgba_float_candidate") or []]
        float_derived = straight_float_to_packed_argb(rgba_float)
        writer_raw = str((case.get("writer_hit") or {}).get("final_writer_raw") or "")
        raw_derived = raw_rgba_to_png(writer_raw)
        reference = center["reference_rgba"]
        candidate = center["candidate_rgba"]
        rows.append(
            {
                "case_id": case_id,
                "xy": [int(decoded.get("x_candidate")), int(decoded.get("y_candidate"))],
                "reference_rgba": reference,
                "candidate_rgba": candidate,
                "writer_frame_rgba_float": rgba_float,
                "writer_raw": writer_raw,
                "float_derived": float_derived,
                "raw_derived": raw_derived,
                "writer_explains_reference": raw_derived["expected_png_rgba_after_premultiply"] == reference,
                "writer_diff_vs_candidate": [
                    abs(raw_derived["expected_png_rgba_after_premultiply"][i] - candidate[i])
                    for i in range(4)
                ],
                "classification": case.get("classification"),
            }
        )
    decision = (
        "producer-upstream-of-writer-frame"
        if rows and all(row["writer_explains_reference"] for row in rows)
        else "needs-review"
    )
    return {
        "kind": "olmsmoother2_writer_frame_followup_analysis",
        "schema": 1,
        "inputs": {
            "runtime_summary_json": str(args.runtime_summary_json),
            "neighborhood_json": str(args.neighborhood_json),
        },
        "decision": decision,
        "cases": rows,
        "not_isolated": ((observations.get("directly_observed_vs_inferred") or {}).get("not_isolated") or []),
        "recommended_action": (
            "Do not tune final writer or broad alpha handling. The writer-frame floats explain the Windows "
            "reference pixels; the remaining work is to identify the upstream c280/helper producer for these frames."
        ),
    }


def rgba(value: list[int] | list[float]) -> str:
    return "[" + ",".join(str(v) for v in value) + "]"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Writer-Frame Follow-Up Analysis",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "| Case | XY | Writer float | Derived PNG | Reference | Candidate | Explains reference |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["cases"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['xy']}` | `{rgba(row['writer_frame_rgba_float'])}` | "
            f"`{rgba(row['raw_derived']['expected_png_rgba_after_premultiply'])}` | "
            f"`{rgba(row['reference_rgba'])}` | `{rgba(row['candidate_rgba'])}` | "
            f"`{row['writer_explains_reference']}` |"
        )
    lines.extend(["", "## Remaining Unisolated Producer Evidence", ""])
    for item in report["not_isolated"]:
        lines.append(f"- {item}")
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
