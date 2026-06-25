#!/usr/bin/env python3
"""Build the next OLMSmoother2 narrow proof plan.

This combines the current-AEX witness contract and 5x5 neighborhood report
into an ordered list of facts needed before touching the implementation again.
It is intentionally a blocker-shaping report, not a tuner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmsmoother2_current_aex_witness_contract_20260624"
        / "witness_contract.json",
    )
    parser.add_argument(
        "--neighborhood-json",
        type=Path,
        default=ROOT
        / "refs"
        / "reports"
        / "olmsmoother2_witness_neighborhood_20260624"
        / "neighborhood.json",
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
    return {str(row["case_id"]): row for row in rows}


def top_neighbor_xys(case: dict[str, Any]) -> list[list[int]]:
    strongest = case.get("classification", {}).get("strongest_neighbor_deltas") or []
    return [row["xy"] for row in strongest[:3]]


def plan_for_case(contract_case: dict[str, Any], neighborhood_case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(contract_case["case_id"])
    local_path = str(contract_case["local_classification"])
    shape = neighborhood_case.get("classification", {}).get("kind")

    if case_id == "legacy_case_0004_current_aex":
        static_dispatch = {
            "idx": 208,
            "hex": "0xd0",
            "dispatch": "FUN_180013140",
            "case_map_evidence": "disasm/OLMSmoother2_case_map.txt maps 0xd0/0xd1 to FUN_180013140.",
            "port_evidence": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp dispatches case 0xd0/0xd1 to win_FUN_180013140(poly).",
            "helper_shape": [
                "guard returns when y == height - 1 or x == 0",
                "scans dbd0 and d6a0, then derives spanX/spanY",
                "rejects when both spans are >= 4",
                "for spans >= 2, side-channel byte at (x-1,y) byte index 3 can reject",
                "appends (x-1,y), (x-1,y-1), and (x,y-1) with corner weights",
            ],
        }
        probes = [
            {
                "name": "writer-anchor",
                "question": "Does the target still store Windows `[103,103,103,113]` at the final 8bpc writer?",
                "values": ["final writer bytes", "writer stack x/y", "output buffer pointer"],
            },
            {
                "name": "cce0-return",
                "question": "Does Windows cce0 return a nonzero semitransparent value for the transparent center?",
                "values": ["cce0 output floats", "poly count before b120", "passthrough/fallback flag"],
            },
            {
                "name": "c280-polygon",
                "question": "Does the 0xd0/FUN_180013140 path pass the span/side-channel guards and append neighbor-derived samples?",
                "values": ["idx", "class-plane bits", "append list", "sample source xy/rgba/weight"],
            },
            {
                "name": "neighbor-correlation",
                "question": "Does the missing center value match one of the strongest neighboring cells?",
                "values": [f"neighbor {xy}" for xy in top_neighbor_xys(neighborhood_case)],
            },
        ]
        stop_line = (
            "Do not add a global transparent-center fallback. This witness only proves a "
            "0004-local path if cce0/c280 emits a neighbor sample for the same call."
        )
    elif case_id == "legacy_case_0012_gamma5_red_blue_current_aex":
        static_dispatch = {
            "idx": 105,
            "hex": "0x69",
            "dispatch": "FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70",
            "case_map_evidence": "disasm/OLMSmoother2_case_map.txt maps 0x49/0x4d/0x61/0x69/0x6d to FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70.",
            "port_evidence": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp dispatches case 0x69 to win_FUN_1800125c0(poly), win_cardinal_6(poly), normalize; win_cardinal_6 is the local FUN_180010760 model.",
            "helper_shape": [
                "FUN_1800125c0 emits the 12-o-clock/NW-end contribution",
                "FUN_180010760 returns when x == width - 1",
                "FUN_180010760 scans d3b0 and da50, builds a six-int descriptor, then dispatches through fef0",
                "FUN_18000cc70 normalizes the accumulated polygon after both emitters",
            ],
        }
        probes = [
            {
                "name": "writer-anchor",
                "question": "Does Windows still store transparent output at the final 8bpc writer?",
                "values": ["final writer bytes", "writer stack x/y", "output buffer pointer"],
            },
            {
                "name": "descriptor",
                "question": "Does Windows FUN_180010760 enter the same cardinal6 descriptor/key as local?",
                "values": ["idx", "cardinal6 desc", "key", "polygon count before append"],
            },
            {
                "name": "emit-chain",
                "question": "Where does the local f270/e3a0 append disappear in Windows?",
                "values": ["d3b0/da50 state", "e170 bits/code", "f270 branch", "e3a0 trap/weight", "append/no-append"],
            },
            {
                "name": "blend",
                "question": "If Windows appends the same sample, does cce0/b120 zero it later?",
                "values": ["pre-b120 rgba", "post-b120 rgba", "final writer bytes"],
            },
        ]
        stop_line = (
            "Do not suppress f270 or transparent-center appends globally. Prior probes show "
            "global f270 suppression worsens the case set."
        )
    else:
        static_dispatch = {
            "idx": None,
            "hex": None,
            "dispatch": "unknown",
            "case_map_evidence": "not classified",
            "port_evidence": "not classified",
        }
        probes = [
            {
                "name": "first-divergence",
                "question": "Classify the first stage where Windows and local differ.",
                "values": ["writer", "cce0", "c280", "emitter"],
            }
        ]
        stop_line = "Do not tune until the first divergence is classified."

    return {
        "case_id": case_id,
        "xy": contract_case["xy"],
        "reference_rgba": contract_case["reference_rgba"],
        "candidate_rgba": contract_case["candidate_rgba"],
        "local_path": local_path,
        "neighborhood_shape": shape,
        "static_dispatch": static_dispatch,
        "required_proof": contract_case["required_proof"],
        "ordered_probes": probes,
        "stop_line": stop_line,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    contract = read_json(args.contract_json)
    neighborhood = read_json(args.neighborhood_json)
    neighborhoods = by_case(neighborhood.get("cases") or [])
    plans = [
        plan_for_case(row, neighborhoods[str(row["case_id"])])
        for row in contract.get("witnesses", [])
        if str(row.get("case_id")) in neighborhoods
    ]
    return {
        "kind": "olmsmoother2_current_aex_proof_plan",
        "schema": 1,
        "inputs": {
            "contract_json": str(args.contract_json),
            "neighborhood_json": str(args.neighborhood_json),
        },
        "decision": "runtime-or-asm-first-divergence-required",
        "recommended_action": (
            "Keep the Smooth Range threshold fix and do not request broad PNGs. "
            "Only a writer-anchored runtime trace or equivalent asm proof for "
            "these two witness paths can justify another implementation change."
        ),
        "global_rejections": contract.get("rejected_global_toggles", {}),
        "plans": plans,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLMSmoother2 Current-AEX Proof Plan",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        "",
        "## Witnesses",
        "",
        "| Case | XY | Static dispatch | Shape | Local path | Stop line |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for plan in report["plans"]:
        lines.append(
            f"| `{plan['case_id']}` | `{plan['xy']}` | "
            f"`{plan['static_dispatch']['hex']} -> {plan['static_dispatch']['dispatch']}` | "
            f"`{plan['neighborhood_shape']}` | "
            f"`{plan['local_path']}` | {plan['stop_line']} |"
        )
    lines.extend(["", "## Ordered Probes", ""])
    for plan in report["plans"]:
        lines.extend([f"### {plan['case_id']} `{plan['xy']}`", ""])
        lines.append(
            f"- Static dispatch: `{plan['static_dispatch']['hex']}` -> "
            f"`{plan['static_dispatch']['dispatch']}`"
        )
        lines.append(f"- Case-map evidence: {plan['static_dispatch']['case_map_evidence']}")
        lines.append(f"- Port evidence: {plan['static_dispatch']['port_evidence']}")
        helper_shape = plan["static_dispatch"].get("helper_shape") or []
        for fact in helper_shape:
            lines.append(f"- Helper fact: {fact}")
        lines.append(f"- Required proof: {plan['required_proof']}")
        lines.append("")
        for index, probe in enumerate(plan["ordered_probes"], start=1):
            values = "; ".join(probe["values"])
            lines.append(f"{index}. `{probe['name']}`: {probe['question']} Values: {values}.")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = build_report(args)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
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
