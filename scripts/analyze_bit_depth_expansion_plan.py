#!/usr/bin/env python3
"""Build the next bit-depth expansion plan from normalized 8bpc evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonicalization-json",
        type=Path,
        default=ROOT / "refs" / "reports" / "software_reference_canonicalization_8bpc.json",
    )
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--output-md", type=Path, default=None)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def case_ids(feature: dict[str, Any]) -> list[str]:
    cases = feature.get("cases") or []
    ids = [str(row.get("id")) for row in cases if isinstance(row, dict) and row.get("id")]
    if ids:
        return ids
    return [str(row.get("id")) for row in feature.get("legacy_drift_cases", []) if isinstance(row, dict) and row.get("id")]


def feature_ready_for_depth(feature: dict[str, Any]) -> bool:
    return (
        feature.get("canonical_8bpc_status") == "normalized-software-exact"
        and int(feature.get("normalized_nonzero_count", -1)) == 0
        and int(feature.get("case_count", 0)) > 0
    )


def plugin_key(name: str) -> str:
    if name.startswith("OLMDistanceGradation"):
        return "OLMDistanceGradation"
    return name


def request_id_for(name: str) -> str:
    safe = name.lower().replace(" ", "_")
    return f"{safe}_bitdepth_16bpc_YYYYMMDD"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    canonical = read_json(args.canonicalization_json)
    ready_features = [
        feature
        for feature in canonical.get("features", [])
        if isinstance(feature, dict) and feature_ready_for_depth(feature)
    ]
    rows = []
    for feature in ready_features:
        name = str(feature.get("name"))
        ids = case_ids(feature)
        rows.append(
            {
                "name": name,
                "plugin": plugin_key(name),
                "case_count": int(feature.get("case_count", 0)),
                "case_ids": ids,
                "normalized_ref_dir": feature.get("normalized_ref_dir"),
                "candidate_dir": feature.get("candidate_dir"),
                "legacy_drift_count": int(feature.get("legacy_nonzero_count", 0)),
                "request_id": request_id_for(name),
                "next_depth": "16bpc",
                "after_16bpc": "Only expand to 32bpc after 16bpc compare format and exactness are proven.",
            }
        )

    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        group = grouped.setdefault(
            row["plugin"],
            {
                "plugin": row["plugin"],
                "features": [],
                "case_count": 0,
                "request_ids": [],
                "next_depth": "16bpc",
            },
        )
        group["features"].append(row["name"])
        group["case_count"] += row["case_count"]
        group["request_ids"].append(row["request_id"])

    total_cases = sum(row["case_count"] for row in rows)
    return {
        "kind": "olm_bit_depth_expansion_plan",
        "schema": 1,
        "inputs": {"canonicalization_json": str(args.canonicalization_json)},
        "decision": "request-16bpc-for-normalized-8bpc-exact-features",
        "scope": (
            "Only features with normalized 8bpc Software exact evidence are included. "
            "This is not a completion claim for 16bpc/32bpc."
        ),
        "comparator_policy": {
            "8bpc": "byte exact, max_diff=0",
            "16bpc": "integer-sample exact; define/export the 16bpc comparison representation before claiming exact",
            "32bpc": "do not request as completion evidence until float exact/epsilon policy is fixed",
        },
        "features": rows,
        "groups": sorted(grouped.values(), key=lambda row: row["plugin"]),
        "totals": {
            "feature_count": len(rows),
            "plugin_count": len(grouped),
            "case_count": total_cases,
        },
        "stop_lines": [
            "Do not use legacy-drift cases to tune 8bpc behavior.",
            "Do not claim all-bit-depth compatibility from this plan alone.",
            "Do not mix GPU/CUDA renders into this Software conformance request.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLM Bit-Depth Expansion Plan",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Scope: {report['scope']}",
        f"- Totals: {report['totals']['feature_count']} feature groups, "
        f"{report['totals']['plugin_count']} plug-ins, {report['totals']['case_count']} cases.",
        "",
        "## Comparator Policy",
        "",
    ]
    for depth, policy in report["comparator_policy"].items():
        lines.append(f"- `{depth}`: {policy}")
    lines.extend(
        [
            "",
            "## 16bpc Request Candidates",
            "",
            "| Feature | Plug-in | Cases | Request ID | Legacy drift |",
            "| --- | --- | ---: | --- | ---: |",
        ]
    )
    for row in report["features"]:
        lines.append(
            f"| `{row['name']}` | `{row['plugin']}` | {row['case_count']} | "
            f"`{row['request_id']}` | {row['legacy_drift_count']} |"
        )
    lines.extend(["", "## Plug-in Groups", "", "| Plug-in | Features | Cases |", "| --- | --- | ---: |"])
    for group in report["groups"]:
        features = ", ".join(f"`{name}`" for name in group["features"])
        lines.append(f"| `{group['plugin']}` | {features} | {group['case_count']} |")
    lines.extend(["", "## Stop Lines", ""])
    lines.extend(f"- {item}" for item in report["stop_lines"])
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
