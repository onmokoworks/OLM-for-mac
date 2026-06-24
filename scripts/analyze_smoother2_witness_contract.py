#!/usr/bin/env python3
"""Build a compact OLMSmoother2 current-AEX witness contract.

The report is deliberately not an implementation tuner.  It records the two
active localized residual witnesses, the local Mac path observed at each
coordinate, the binary-grounded functions that are already consistent with the
Mac path, and the single unresolved proof needed next.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


TRACE_PATTERNS = {
    "class_threshold": re.compile(
        r"trace class_threshold mode=(?P<mode>\d+) field=(?P<field>\d+) "
        r"threshold=(?P<threshold>[0-9.]+) enable_key=(?P<enable_key>\d+) "
        r"invert_key=(?P<invert_key>\d+) smooth_range=(?P<smooth_range>\d+) "
        r"key_pred=(?P<key_pred>\d+)"
    ),
    "build_polygon": re.compile(
        r"trace build_polygon x=(?P<x>-?\d+) y=(?P<y>-?\d+) idx=(?P<idx>\d+) "
        r"c=(?P<c>[0-9a-fA-F]+).*bits=(?P<bits>[0-9,]+)"
    ),
    "polygon_done": re.compile(r"trace build_polygon_done .* count=(?P<count>\d+)"),
    "cce0_entry": re.compile(
        r"trace cce0_entry x=(?P<x>-?\d+) y=(?P<y>-?\d+) "
        r"center=(?P<center>[0-9.,-]+) poly_count=(?P<poly_count>\d+)"
    ),
    "cardinal6": re.compile(
        r"trace cardinal6 desc=\((?P<desc>[^)]*)\) key=(?P<key>\d+) "
        r"count_before=(?P<count_before>\d+)"
    ),
    "e170": re.compile(
        r"trace e170 p2=\((?P<desc>[^)]*)\) bits Axy-1=(?P<a_prev>\d+) "
        r"R x-1y=(?P<r_left>\d+) Axy=(?P<a_center>\d+) -> c=(?P<c>\d+)"
    ),
    "f270": re.compile(
        r"trace f270 c=(?P<c>\d+) p3=(?P<p3>[0-9.]+) extra_n=(?P<extra_n>[0-9.]+) "
        r"count_before=(?P<count_before>\d+)"
    ),
    "e3a0": re.compile(
        r"trace e3a0 p2=\((?P<desc>[^)]*)\) scale_m=(?P<scale_m>[0-9.]+) "
        r"scale_h=(?P<scale_h>[0-9.]+) trap=\((?P<trap>[^)]*)\) "
        r"weight=(?P<weight>[0-9.]+)"
    ),
    "append": re.compile(
        r"trace append src=\((?P<src>[^)]*)\) dst_center=\((?P<dst>[^)]*)\) "
        r"rgba=\((?P<rgba>[^)]*)\) w=(?P<weight>[0-9.]+)"
    ),
    "cce0_after_b120": re.compile(r"trace cce0_after_b120 out=(?P<out>[0-9.,-]+)"),
    "passthrough": re.compile(r"trace cce0_exit_passthrough out=(?P<out>[0-9.,-]+)"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--residual-audit-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_residual_audit_latest" / "residual_audit.json",
    )
    parser.add_argument(
        "--decision-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "olmsmoother2_current_aex_decision_matrix_20260624" / "decision_matrix.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def parse_trace_log(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    parsed: dict[str, Any] = {"path": str(path)}
    for key, pattern in TRACE_PATTERNS.items():
        match = pattern.search(text)
        if match:
            parsed[key] = match.groupdict()
    parsed["has_cardinal6"] = "cardinal6" in parsed
    parsed["has_append"] = "append" in parsed
    parsed["has_passthrough"] = "passthrough" in parsed
    return parsed


def local_classification(case_id: str, trace: dict[str, Any]) -> str:
    if trace.get("has_passthrough") and trace.get("polygon_done", {}).get("count") == "0":
        return "local-transparent-center-no-polygon-passthrough"
    if trace.get("has_cardinal6") and trace.get("has_append"):
        return "local-cardinal6-f270-e3a0-append"
    return "needs-review"


def required_proof(case_id: str, trace: dict[str, Any]) -> str:
    if "0012" in case_id:
        return (
            "Windows must decide whether this exact witness differs in c280 idx, "
            "cardinal6 desc/key, e170 bits/code, f270/e3a0 emission, cce0 blend, "
            "or final u8 writer."
        )
    if "0004" in case_id:
        return (
            "Windows must decide whether idx=208 also produces zero polygon "
            "vertices, or whether a helper appends neighbor-derived samples "
            "before cce0."
        )
    return "Windows proof must classify the first stage that diverges from the local trace."


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    residual = read_json(args.residual_audit_json)
    decision = read_json(args.decision_json)
    witnesses = []
    for row in residual.get("cases", []):
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("case_id"))
        trace_path = Path(str(row.get("trace_log")))
        trace = parse_trace_log(trace_path)
        witness = row.get("witness", {})
        witnesses.append(
            {
                "case_id": case_id,
                "xy": [witness.get("x"), witness.get("y")],
                "reference_rgba": witness.get("reference_rgba"),
                "candidate_rgba": witness.get("candidate_rgba"),
                "delta_rgba": witness.get("delta_rgba"),
                "max_channel_diff": witness.get("max_channel_diff"),
                "local_classification": local_classification(case_id, trace),
                "local_trace": trace,
                "required_proof": required_proof(case_id, trace),
            }
        )

    return {
        "kind": "olmsmoother2_current_aex_witness_contract",
        "schema": 1,
        "inputs": {
            "residual_audit_json": str(args.residual_audit_json),
            "decision_json": str(args.decision_json),
        },
        "binary_grounded_keep": [
            "Keep key-enabled Smooth Range threshold promotion.",
            "Keep FUN_18000e170 bit mapping: A(x,y-1), R(x-1,y), A(x,y).",
            "Keep FUN_18000f270 shape: suppress only e170==4, otherwise call e3a0.",
            "Keep FUN_18000fef0 key 50 -> f270(..., 1.0).",
            "Keep final 8bpc writer as ruled out for the active residuals.",
        ],
        "rejected_global_toggles": {
            "curve_idx": decision.get("curve_idx", {}).get("classification"),
            "f270_suppression": decision.get("f270_suppression", {}).get("classification"),
        },
        "witnesses": witnesses,
        "decision": "blocked-narrow-proof-only",
        "next_step": (
            "Do not add broad PNGs or global toggles. Read/trace only the "
            "listed witness paths until the first Windows-vs-Mac divergence is "
            "classified."
        ),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Witness Contract",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Next step: {report['next_step']}",
        "",
        "## Keep",
        "",
    ]
    lines.extend(f"- {item}" for item in report["binary_grounded_keep"])
    lines.extend(
        [
            "",
            "## Rejected Global Toggles",
            "",
            f"- curve_idx: `{report['rejected_global_toggles']['curve_idx']}`",
            f"- f270_suppression: `{report['rejected_global_toggles']['f270_suppression']}`",
            "",
            "## Witnesses",
            "",
            "| Case | XY | Reference | Candidate | Local path | Required proof |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["witnesses"]:
        lines.append(
            f"| `{row['case_id']}` | `{row['xy']}` | `{row['reference_rgba']}` | "
            f"`{row['candidate_rgba']}` | `{row['local_classification']}` | "
            f"{row['required_proof']} |"
        )
    lines.extend(["", "## Local Trace Details", ""])
    for row in report["witnesses"]:
        trace = row["local_trace"]
        lines.append(f"### {row['case_id']} `{row['xy']}`")
        for key in (
            "class_threshold",
            "build_polygon",
            "polygon_done",
            "cardinal6",
            "e170",
            "f270",
            "e3a0",
            "append",
            "cce0_after_b120",
            "passthrough",
        ):
            if key in trace:
                lines.append(f"- {key}: `{trace[key]}`")
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
