#!/usr/bin/env python3
"""Materialize the current OLMSmoother2 legacy current-AEX lane state."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRODUCER_DIFF_JSON = ROOT / "refs/conformance/olmsmoother2_producer_path_diff_20260702.json"
DECISION_JSON = ROOT / "refs/conformance/olmsmoother2_current_aex_8bpc_decision.json"
BRANCH_TABLE_JSON = ROOT / "refs/conformance/olmsmoother2_producer_branch_table_20260707.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-diff-json", type=Path, default=PRODUCER_DIFF_JSON)
    parser.add_argument("--decision-json", type=Path, default=DECISION_JSON)
    parser.add_argument("--branch-table-json", type=Path, default=BRANCH_TABLE_JSON)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_report(
    producer_diff: dict[str, Any],
    decision: dict[str, Any],
    branch_table: dict[str, Any] | None,
    inputs: dict[str, Path],
) -> dict[str, Any]:
    by_case = {row["case_id"]: row for row in producer_diff["cases"]}
    case_0004 = by_case["legacy_case_0004_current_aex"]
    case_0012 = by_case["legacy_case_0012_gamma5_red_blue_current_aex"]
    latest_return = decision.get("latest_windows_return") or {}
    return {
        "kind": "olmsmoother2_legacy_lane_state",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "feature": decision["feature"],
        "status": decision["status"],
        "decision": decision["decision"],
        "recommended_action": producer_diff["recommended_action"],
        "safe_claim": (
            "final writer bytes/floats are already grounded for the active legacy witnesses; the unresolved lane is "
            "the first producer divergence feeding c280/cce0, not PNG export or final u8 packing."
        ),
        "latest_windows_return": latest_return,
        "inputs": {name: rel(path) for name, path in inputs.items()},
        "cases": [
            {
                "case_id": case_0004["case_id"],
                "witness_xy": case_0004["xy"],
                "reference_rgba": case_0004["reference_rgba"],
                "local_candidate_rgba": case_0004["candidate_rgba"],
                "local_path": case_0004["local_summary"]["local_path"],
                "static_dispatch": case_0004["static_dispatch"],
                "first_unresolved_stage": case_0004["first_unresolved_stage"],
                "stop_line": case_0004["stop_line"],
                "required_windows_fields": case_0004["required_windows_fields"],
            },
            {
                "case_id": case_0012["case_id"],
                "witness_xy": case_0012["xy"],
                "reference_rgba": case_0012["reference_rgba"],
                "local_candidate_rgba": case_0012["candidate_rgba"],
                "local_path": case_0012["local_summary"]["local_path"],
                "static_dispatch": case_0012["static_dispatch"],
                "first_unresolved_stage": case_0012["first_unresolved_stage"],
                "stop_line": case_0012["stop_line"],
                "required_windows_fields": case_0012["required_windows_fields"],
            },
        ],
        "local_aex_producer_branch_table": branch_table,
        "global_rejections": decision["global_rejections"],
    }


def render_case(case: dict[str, Any]) -> list[str]:
    wx, wy = case["witness_xy"]
    lines = [
        f"## {case['case_id']}",
        "",
        f"- Witness: `({wx},{wy})`",
        f"- Reference / local: `{case['reference_rgba']}` vs `{case['local_candidate_rgba']}`",
        f"- Local path: `{case['local_path']}`",
        f"- Static dispatch: `{case['static_dispatch']}`",
        f"- First unresolved stage: `{case['first_unresolved_stage']}`",
        f"- Stop line: {case['stop_line']}",
        "",
        "### Required Windows Fields",
        "",
    ]
    for item in case["required_windows_fields"]:
        lines.append(f"- {item}")
    lines.append("")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMSmoother2 Legacy Lane State - {report['materialized_at'][:10]}",
        "",
        f"- Feature: `{report['feature']}`",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        f"- Recommended action: {report['recommended_action']}",
        f"- Safe claim: {report['safe_claim']}",
    ]
    latest = report.get("latest_windows_return") or {}
    if latest:
        lines.extend(
            [
                f"- Latest Windows return: `{latest.get('request_id')}` / `{latest.get('status')}`",
                f"- Return summary: {latest.get('summary')}",
            ]
        )
    lines.extend([""])
    for case in report["cases"]:
        lines.extend(render_case(case))
    branch_table = report.get("local_aex_producer_branch_table")
    if branch_table:
        lines.extend(
            [
                "## Local AEX Producer Branch Table",
                "",
                f"- Status: `{branch_table.get('status')}`",
                f"- Source: `{branch_table.get('source')}`",
                f"- Leaf check: `{'PASS' if (branch_table.get('leaf_check') or {}).get('all_match') else 'FAIL'}`",
                "",
                "| Scenario | Entry | iVar6 | iVar5 | Emit | vcount |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for row in ((branch_table.get("case_0004") or {}).get("rows") or []):
            lines.append(
                f"| `{row.get('scenario')}` | `{row.get('entry_guard')}` | `{row.get('iVar6_right')}` | "
                f"`{row.get('iVar5_down')}` | `{row.get('emit_guard')}` | `{row.get('vcount')}` |"
            )
        result_0012 = ((branch_table.get("case_0012") or {}).get("result") or {})
        lines.extend(
            [
                "",
                f"- case_0012 local e170 bitsum c: `{result_0012.get('e170_c')}`",
                f"- case_0012 local f270 append count: `{(result_0012.get('f270') or {}).get('count')}`",
                "- Reading: local AEX CPU emulation narrows the remaining proof to Windows-side producer/class-plane state; it does not prove AE exact.",
                "",
            ]
        )
    lines.extend(["## Global Rejections", ""])
    for key, value in report["global_rejections"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Inputs", ""])
    for name, path in report["inputs"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    inputs = {
        "producer_diff_json": args.producer_diff_json.resolve(),
        "decision_json": args.decision_json.resolve(),
    }
    for path in inputs.values():
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
    branch_table = None
    branch_path = args.branch_table_json.resolve()
    if branch_path.exists():
        inputs["branch_table_json"] = branch_path
        branch_table = load_json(branch_path)
    report = build_report(
        load_json(inputs["producer_diff_json"]),
        load_json(inputs["decision_json"]),
        branch_table,
        inputs,
    )
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmsmoother2_legacy_lane_state_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmsmoother2_legacy_lane_state_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
