#!/usr/bin/env python3
"""Summarize Windows fresh-instance defaults/ranges parity by plug-in."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_JSON = ROOT / "refs" / "reports" / "windows_fresh_defaults_audit_20260629.json"
RANGES_JSON = ROOT / "refs" / "reports" / "windows_fresh_ranges_audit_20260629.json"
OUT_JSON = ROOT / "refs" / "reports" / "windows_fresh_param_parity_summary_20260630.json"
OUT_MD = ROOT / "refs" / "reports" / "windows_fresh_param_parity_summary_20260630.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defaults-json", type=Path, default=DEFAULTS_JSON)
    parser.add_argument("--ranges-json", type=Path, default=RANGES_JSON)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_defaults(plugin: dict[str, Any]) -> tuple[str, list[str]]:
    counts = plugin.get("compare_counts") or {}
    reasons: list[str] = []
    if counts.get("mismatch", 0):
        reasons.append(f"default mismatch {counts['mismatch']}")
    if counts.get("windows-only", 0):
        reasons.append(f"windows-only labels {counts['windows-only']}")
    if counts.get("source-empty", 0):
        reasons.append(f"source-empty {counts['source-empty']}")
    if counts.get("source-symbolic", 0):
        reasons.append(f"symbolic defaults {counts['source-symbolic']}")
    if not reasons:
        return ("fixed", ["all compared Windows defaults matched current Mac schema"])
    if counts.get("mismatch", 0) or counts.get("windows-only", 0):
        return ("needs-followup", reasons)
    return ("mostly-fixed", reasons)


def classify_ranges(plugin: dict[str, Any]) -> tuple[str, list[str]]:
    counts = Counter(plugin.get("counts") or {})
    reasons: list[str] = []
    if counts["range-mismatch"]:
        reasons.append(f"range mismatch {counts['range-mismatch']}")
    if counts["windows-only-or-unknown"]:
        reasons.append(f"windows-only/unknown {counts['windows-only-or-unknown']}")
    if counts["source-symbolic"]:
        reasons.append(f"symbolic range {counts['source-symbolic']}")
    if counts["source-no-range"]:
        reasons.append(f"source-no-range {counts['source-no-range']}")
    if counts["windows-no-range"]:
        reasons.append(f"windows-no-range {counts['windows-no-range']}")
    if not reasons:
        return ("fixed", ["all Windows-exposed ranges matched current Mac hard min/max"])
    if counts["range-mismatch"] or counts["windows-only-or-unknown"]:
        return ("needs-followup", reasons)
    return ("mostly-fixed", reasons)


def select_next_gap(plugin_name: str, defaults_plugin: dict[str, Any] | None, ranges_plugin: dict[str, Any] | None) -> str:
    if ranges_plugin:
        mismatches = ranges_plugin.get("mismatches") or []
        for row in mismatches:
            status = row.get("status")
            if status in {"range-mismatch", "windows-only-or-unknown"}:
                return f"{row.get('normalized') or row.get('param')}: {status}"
    if defaults_plugin:
        for group_name in ("mismatch_examples", "windows_only_examples", "source_only_examples", "symbolic_examples"):
            rows = defaults_plugin.get(group_name) or []
            if not rows:
                continue
            row = rows[0]
            if isinstance(row, dict):
                name = row.get("normalized_name") or row.get("raw_name")
                if isinstance(name, str) and name.strip():
                    return f"{name}: {group_name}"
                continue
            if isinstance(row, str) and row.strip():
                return f"{row}: {group_name}"
    return f"{plugin_name}: no immediate fresh-instance schema blocker"


def summarize(defaults_data: dict[str, Any], ranges_data: dict[str, Any], defaults_json: Path, ranges_json: Path) -> dict[str, Any]:
    defaults_by_plugin = {row["plugin"]: row for row in defaults_data.get("plugins", []) if isinstance(row, dict)}
    ranges_by_plugin = {row["plugin"]: row for row in ranges_data.get("plugins", []) if isinstance(row, dict)}
    plugin_names = sorted(set(defaults_by_plugin) | set(ranges_by_plugin))

    plugins: list[dict[str, Any]] = []
    for plugin_name in plugin_names:
        defaults_plugin = defaults_by_plugin.get(plugin_name)
        ranges_plugin = ranges_by_plugin.get(plugin_name)
        defaults_status, defaults_reasons = classify_defaults(defaults_plugin or {"compare_counts": {}})
        ranges_status, ranges_reasons = classify_ranges(ranges_plugin or {"counts": {}})
        overall = "fixed"
        if "needs-followup" in {defaults_status, ranges_status}:
            overall = "needs-followup"
        elif "mostly-fixed" in {defaults_status, ranges_status}:
            overall = "mostly-fixed"
        plugins.append(
            {
                "plugin": plugin_name,
                "defaults_status": defaults_status,
                "ranges_status": ranges_status,
                "overall_status": overall,
                "defaults_reasons": defaults_reasons,
                "ranges_reasons": ranges_reasons,
                "next_gap": select_next_gap(plugin_name, defaults_plugin, ranges_plugin),
            }
        )

    return {
        "kind": "windows_fresh_param_parity_summary",
        "defaults_json": str(defaults_json),
        "ranges_json": str(ranges_json),
        "plugins": plugins,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Windows Fresh Parameter Parity Summary",
        "",
        "This report summarizes cold-start default parity and AE-exposed range parity from the Windows fresh-instance captures.",
        "",
        f"- Defaults audit: `{report['defaults_json']}`",
        f"- Ranges audit: `{report['ranges_json']}`",
        "",
        "| Plug-in | Defaults | Ranges | Overall | Next gap |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["plugins"]:
        lines.append(
            f"| `{row['plugin']}` | `{row['defaults_status']}` | `{row['ranges_status']}` | "
            f"`{row['overall_status']}` | {row['next_gap']} |"
        )
    lines.extend(["", "## Notes", ""])
    for row in report["plugins"]:
        lines.extend(
            [
                f"### {row['plugin']}",
                "",
                f"- Defaults: `{row['defaults_status']}`",
                f"- Default reasons: {', '.join(row['defaults_reasons'])}",
                f"- Ranges: `{row['ranges_status']}`",
                f"- Range reasons: {', '.join(row['ranges_reasons'])}",
                f"- Next gap: {row['next_gap']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    defaults_data = load_json(args.defaults_json)
    ranges_data = load_json(args.ranges_json)
    report = summarize(defaults_data, ranges_data, args.defaults_json, args.ranges_json)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.output_json}")
    print(f"wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
