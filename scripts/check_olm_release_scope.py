#!/usr/bin/env python3
"""Validate and summarize the declared OLM release-completion scope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCOPE = ROOT / "refs/conformance/olm_release_scope.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-json", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="return nonzero unless every declared release gate is complete",
    )
    return parser.parse_args()


def evaluate(data: dict) -> dict:
    required_depths = data.get("required_depths", [])
    plugins = data.get("plugins", [])
    issues: list[dict[str, str]] = []
    exact_depth_cells = 0
    total_depth_cells = 0

    for plugin in plugins:
        name = plugin.get("plugin", "<unnamed>")
        depths = plugin.get("depths", {})
        for depth in required_depths:
            total_depth_cells += 1
            cell = depths.get(depth)
            if cell is None:
                issues.append({"plugin": name, "gate": depth, "reason": "missing depth cell"})
                continue
            reference_status = cell.get("reference_status")
            result_status = cell.get("result_status")
            if depth == "32bpc" and reference_status != "float-preserving":
                issues.append(
                    {
                        "plugin": name,
                        "gate": depth,
                        "reason": f"reference_status={reference_status!r}, expected 'float-preserving'",
                    }
                )
            elif reference_status not in {"available", "float-preserving"}:
                issues.append(
                    {
                        "plugin": name,
                        "gate": depth,
                        "reason": f"reference_status={reference_status!r}",
                    }
                )
            if result_status == "AE exact":
                exact_depth_cells += 1
            else:
                issues.append(
                    {
                        "plugin": name,
                        "gate": depth,
                        "reason": f"result_status={result_status!r}, expected 'AE exact'",
                    }
                )

        if plugin.get("host_status") != "host-stable":
            issues.append(
                {
                    "plugin": name,
                    "gate": "host",
                    "reason": f"host_status={plugin.get('host_status')!r}, expected 'host-stable'",
                }
            )
        if plugin.get("ir_status") != "complete":
            issues.append(
                {
                    "plugin": name,
                    "gate": "IR",
                    "reason": f"ir_status={plugin.get('ir_status')!r}, expected 'complete'",
                }
            )
        if "policy_status" in plugin and plugin.get("policy_status") != "fixed":
            issues.append(
                {
                    "plugin": name,
                    "gate": "policy",
                    "reason": f"policy_status={plugin.get('policy_status')!r}, expected 'fixed'",
                }
            )

    return {
        "kind": "olm_release_scope_result",
        "schema": 1,
        "complete": not issues,
        "plugin_count": len(plugins),
        "required_depths": required_depths,
        "depth_cells": total_depth_cells,
        "ae_exact_depth_cells": exact_depth_cells,
        "open_gate_count": len(issues),
        "open_gates": issues,
    }


def render_md(report: dict) -> str:
    lines = [
        "# OLM Release Scope Check",
        "",
        f"- Complete: `{'yes' if report['complete'] else 'no'}`",
        f"- Target plug-ins: `{report['plugin_count']}`",
        f"- AE-exact depth cells: `{report['ae_exact_depth_cells']}/{report['depth_cells']}`",
        f"- Open gates: `{report['open_gate_count']}`",
        "",
        "| Plug-in | Gate | Reason |",
        "| --- | --- | --- |",
    ]
    for item in report["open_gates"]:
        lines.append(f"| {item['plugin']} | {item['gate']} | {item['reason']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    data = json.loads(args.scope_json.read_text(encoding="utf-8"))
    if data.get("kind") != "olm_release_scope" or data.get("schema") != 1:
        raise SystemExit("unsupported OLM release scope schema")
    report = evaluate(data)

    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.report_md:
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(render_md(report), encoding="utf-8")

    print(
        "OLM release scope: "
        f"complete={report['complete']} "
        f"ae_exact_depth_cells={report['ae_exact_depth_cells']}/{report['depth_cells']} "
        f"open_gates={report['open_gate_count']}"
    )
    return 1 if args.require_complete and not report["complete"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
