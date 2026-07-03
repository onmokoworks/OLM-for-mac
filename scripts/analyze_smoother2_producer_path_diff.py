#!/usr/bin/env python3
"""Build a writer-anchored OLMSmoother2 producer-path diff report.

This is local harness groundwork for the remaining current-AEX legacy witness
lanes. It does not tune the implementation. It assembles the exact local
producer checkpoints already known for 0004/0012, aligns them with the
Windows-confirmed writer-frame anchor, and spells out the first still-missing
producer proof needed for a c280/cce0 trace-diff harness.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


STATIC_DISPATCH = {
    "legacy_case_0004_current_aex": {
        "idx": 208,
        "hex": "0xd0",
        "dispatch": "FUN_180013140",
        "unresolved_stage": "c280-polygon-or-cce0-fallback",
        "required_windows_fields": [
            "c280 switch index at exact writer-frame pixel",
            "polygon vertex count before bb10/b120",
            "helper append src xy / rgba / weight if any",
            "cce0 output floats before final u8 packing",
        ],
    },
    "legacy_case_0012_gamma5_red_blue_current_aex": {
        "idx": 105,
        "hex": "0x69",
        "dispatch": "FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70",
        "unresolved_stage": "cardinal6-e170-f270-e3a0-emit-chain",
        "required_windows_fields": [
            "c280 switch index at exact writer-frame pixel",
            "cardinal6 descriptor/key and polygon count before append",
            "e170 bits/code plus f270/e3a0 append/no-append",
            "cce0 output floats before final u8 packing",
        ],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--witness-contract-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmsmoother2_current_aex_witness_contract_20260624"
        / "witness_contract.json",
    )
    parser.add_argument(
        "--writer-frame-analysis-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "smoother2_current_aex_writer_frame_followup_20260625"
        / "writer_frame_analysis.json",
    )
    parser.add_argument(
        "--proof-plan-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmsmoother2_current_aex_proof_plan_20260625"
        / "proof_plan.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def by_case(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["case_id"]): row for row in rows if isinstance(row, dict)}


def probe_statuses(plan: dict[str, Any]) -> dict[str, str]:
    return {
        str(row["name"]): str(row.get("status", "unresolved"))
        for row in plan.get("ordered_probes") or []
        if isinstance(row, dict) and "name" in row
    }


def local_stage_summary(case_id: str, witness: dict[str, Any]) -> dict[str, Any]:
    trace = witness.get("local_trace") or {}
    build_polygon = trace.get("build_polygon") or {}
    cce0_entry = trace.get("cce0_entry") or {}
    summary = {
        "local_path": witness.get("local_classification"),
        "class_threshold": (trace.get("class_threshold") or {}).get("threshold"),
        "idx": int(build_polygon["idx"]) if build_polygon.get("idx") is not None else None,
        "polygon_count": int((trace.get("polygon_done") or {}).get("count", 0)),
        "center_rgba_float": cce0_entry.get("center"),
        "append": trace.get("append"),
        "cce0_after_b120": (trace.get("cce0_after_b120") or {}).get("out"),
        "passthrough": (trace.get("passthrough") or {}).get("out"),
        "cardinal6": trace.get("cardinal6"),
        "e170": trace.get("e170"),
        "f270": trace.get("f270"),
        "e3a0": trace.get("e3a0"),
    }
    if case_id == "legacy_case_0004_current_aex":
        summary["producer_shape"] = "empty polygon -> transparent passthrough"
    elif case_id == "legacy_case_0012_gamma5_red_blue_current_aex":
        summary["producer_shape"] = "cardinal6 append -> nonzero cce0 blend"
    else:
        summary["producer_shape"] = "unknown"
    return summary


def stage_rows(case_id: str, witness: dict[str, Any], writer: dict[str, Any], plan: dict[str, Any]) -> list[dict[str, Any]]:
    trace = witness.get("local_trace") or {}
    static = STATIC_DISPATCH[case_id]
    statuses = probe_statuses(plan)
    build_polygon = trace.get("build_polygon") or {}
    stage_rows = [
        {
            "stage": "writer-anchor",
            "local": writer.get("candidate_rgba"),
            "windows": writer.get("reference_rgba"),
            "status": statuses.get("writer-anchor", "satisfied"),
            "note": f"Windows raw {writer.get('writer_raw')} already explains reference PNG.",
        },
        {
            "stage": "cce0-result",
            "local": (trace.get("cce0_after_b120") or {}).get("out") or (trace.get("passthrough") or {}).get("out"),
            "windows": writer.get("writer_frame_rgba_float"),
            "status": statuses.get("cce0-return", statuses.get("blend", "unresolved")),
            "note": "Writer frame contains post-cce0 local result block, but the exact producer into that block is not isolated.",
        },
        {
            "stage": "c280-dispatch",
            "local": {
                "idx": build_polygon.get("idx"),
                "hex": static["hex"],
                "dispatch": static["dispatch"],
            },
            "windows": "unknown",
            "status": statuses.get("c280-polygon", statuses.get("descriptor", "unresolved")),
            "note": f"Expected local dispatch shape for {case_id}.",
        },
    ]
    if case_id == "legacy_case_0004_current_aex":
        stage_rows.append(
            {
                "stage": "producer-branch",
                "local": {
                    "polygon_count": (trace.get("polygon_done") or {}).get("count"),
                    "passthrough": (trace.get("passthrough") or {}).get("out"),
                },
                "windows": "unknown",
                "status": statuses.get("c280-polygon", "unresolved"),
                "note": "Need to learn whether Windows also has zero vertices or appends a neighbor-derived sample before cce0.",
            }
        )
    elif case_id == "legacy_case_0012_gamma5_red_blue_current_aex":
        stage_rows.append(
            {
                "stage": "producer-branch",
                "local": {
                    "cardinal6": trace.get("cardinal6"),
                    "e170": trace.get("e170"),
                    "f270": trace.get("f270"),
                    "e3a0": trace.get("e3a0"),
                    "append": trace.get("append"),
                },
                "windows": "unknown",
                "status": statuses.get("emit-chain", "unresolved"),
                "note": "Need the first Windows-vs-local difference inside the cardinal6/e170/f270/e3a0 chain.",
            }
        )
    return stage_rows


def build_case(case_id: str, witness: dict[str, Any], writer: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    static = STATIC_DISPATCH[case_id]
    return {
        "case_id": case_id,
        "xy": witness.get("xy"),
        "reference_rgba": witness.get("reference_rgba"),
        "candidate_rgba": witness.get("candidate_rgba"),
        "static_dispatch": static,
        "local_summary": local_stage_summary(case_id, witness),
        "windows_writer_anchor": {
            "xy": writer.get("xy"),
            "writer_raw": writer.get("writer_raw"),
            "writer_frame_rgba_float": writer.get("writer_frame_rgba_float"),
            "writer_explains_reference": writer.get("writer_explains_reference"),
        },
        "first_unresolved_stage": static["unresolved_stage"],
        "required_windows_fields": static["required_windows_fields"],
        "ordered_probes": plan.get("ordered_probes"),
        "stage_rows": stage_rows(case_id, witness, writer, plan),
        "stop_line": plan.get("stop_line"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    witnesses = by_case(read_json(args.witness_contract_json).get("witnesses") or [])
    writers = by_case(read_json(args.writer_frame_analysis_json).get("cases") or [])
    plans = by_case(read_json(args.proof_plan_json).get("plans") or [])
    target_cases = [
        "legacy_case_0004_current_aex",
        "legacy_case_0012_gamma5_red_blue_current_aex",
    ]
    cases = [build_case(case_id, witnesses[case_id], writers[case_id], plans[case_id]) for case_id in target_cases]
    return {
        "kind": "olmsmoother2_current_aex_producer_path_diff",
        "schema": 1,
        "inputs": {
            "witness_contract_json": str(args.witness_contract_json),
            "writer_frame_analysis_json": str(args.writer_frame_analysis_json),
            "proof_plan_json": str(args.proof_plan_json),
        },
        "decision": "writer-anchored-producer-trace-ready",
        "recommended_action": (
            "Anchor the next local/Windows trace-diff harness at the confirmed writer frame, then capture only the "
            "listed producer fields until the first c280/cce0 divergence is observed."
        ),
        "cases": cases,
    }


def dump(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Producer-Path Diff",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Summary",
        "",
        "| Case | XY | Local path | Static dispatch | First unresolved stage |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in report["cases"]:
        lines.append(
            f"| `{case['case_id']}` | `{case['xy']}` | `{case['local_summary']['local_path']}` | "
            f"`{case['static_dispatch']['hex']} -> {case['static_dispatch']['dispatch']}` | "
            f"`{case['first_unresolved_stage']}` |"
        )
    for case in report["cases"]:
        lines.extend(["", f"## {case['case_id']}", ""])
        lines.append(f"- Witness xy: `{case['xy']}`")
        lines.append(f"- Reference RGBA: `{case['reference_rgba']}`")
        lines.append(f"- Local candidate RGBA: `{case['candidate_rgba']}`")
        lines.append(
            f"- Windows writer anchor: raw `{case['windows_writer_anchor']['writer_raw']}`, "
            f"float `{case['windows_writer_anchor']['writer_frame_rgba_float']}`, "
            f"explains reference `{case['windows_writer_anchor']['writer_explains_reference']}`"
        )
        lines.append(f"- Local producer shape: `{case['local_summary']['producer_shape']}`")
        lines.append(f"- Stop line: {case['stop_line']}")
        lines.extend(["", "### Stage Matrix", "", "| Stage | Local checkpoint | Windows checkpoint | Status | Note |", "| --- | --- | --- | --- | --- |"])
        for row in case["stage_rows"]:
            lines.append(
                f"| `{row['stage']}` | `{dump(row['local'])}` | `{dump(row['windows'])}` | "
                f"`{row['status']}` | {row['note']} |"
            )
        lines.extend(["", "### Required Windows Fields", ""])
        for item in case["required_windows_fields"]:
            lines.append(f"- {item}")
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
