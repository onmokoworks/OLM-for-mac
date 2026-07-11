#!/usr/bin/env python3
"""Materialize a committed Windows fresh defaults/ranges parity summary."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from audit_windows_fresh_defaults import audit_manifest as audit_defaults_manifest
from audit_windows_fresh_ranges import audit as audit_ranges_manifest
from summarize_windows_fresh_param_parity import render_markdown, summarize


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEFAULTS_MANIFEST = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_fresh_instance_defaults_20260629"
    / "OLMmulti-effectdefaultcapture"
    / "reference_manifest.json"
)
DEFAULT_RANGES_MANIFEST = (
    ROOT
    / "refs"
    / "win_references"
    / "olm_fresh_instance_ranges_20260629"
    / "OLMmulti-effectrangecapture"
    / "reference_manifest.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--defaults-manifest", type=Path, default=DEFAULT_DEFAULTS_MANIFEST)
    parser.add_argument("--ranges-manifest", type=Path, default=DEFAULT_RANGES_MANIFEST)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for the committed conformance artifacts (default: today in local time).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        help="Optional explicit JSON output path. Defaults to refs/conformance/windows_fresh_param_parity_<stamp>.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        help="Optional explicit markdown output path. Defaults to refs/conformance/windows_fresh_param_parity_<stamp>.md",
    )
    return parser.parse_args()


def committed_markdown(report: dict[str, Any], defaults_manifest: Path, ranges_manifest: Path) -> str:
    lines = [
        f"# Windows Fresh Parameter Parity Audit - {report['materialized_at'][:10]}",
        "",
        "This note freezes the current Windows cold-start defaults/ranges parity state",
        "into `refs/conformance` so later host/debug work does not depend on ignored",
        "`refs/reports` artifacts.",
        "",
        "Inputs:",
        f"- Defaults manifest: `{defaults_manifest.relative_to(ROOT)}`",
        f"- Ranges manifest: `{ranges_manifest.relative_to(ROOT)}`",
        f"- Mac schema snapshot: `{report['schema_snapshot']}`",
        "",
        "Status meaning:",
        "- `fixed`: no actionable parity gap in the current cold-start defaults/ranges lane.",
        "- `mostly-fixed`: narrow remaining drift, typically aliases, symbolic defaults, or grouped placeholder rows.",
        "- `needs-followup`: there is still a real Windows-visible default/range mismatch worth fixing.",
        "",
        "| Plug-in | Defaults | Ranges | Overall | Next gap |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["plugins"]:
        lines.append(
            f"| `{row['plugin']}` | `{row['defaults_status']}` | `{row['ranges_status']}` | "
            f"`{row['overall_status']}` | {row['next_gap']} |"
        )
    lines.extend(
        [
            "",
            "## Operational read",
            "",
            "- This lane is about AE-visible defaults and slider/range metadata, not algorithm exactness.",
            "- A `fixed` or `mostly-fixed` row does not promote the plug-in to `AE exact`.",
            "- `needs-followup` means Mac host/UI work can still remove ambiguity before image-path debugging.",
            "",
            "## Per plug-in notes",
            "",
        ]
    )
    for row in report["plugins"]:
        lines.extend(
            [
                f"### {row['plugin']}",
                "",
                f"- Defaults: `{row['defaults_status']}` ({', '.join(row['defaults_reasons'])})",
                f"- Ranges: `{row['ranges_status']}` ({', '.join(row['ranges_reasons'])})",
                f"- Next gap: {row['next_gap']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    defaults_manifest = args.defaults_manifest.resolve()
    ranges_manifest = args.ranges_manifest.resolve()
    if not defaults_manifest.exists():
        raise SystemExit(f"defaults manifest not found: {defaults_manifest}")
    if not ranges_manifest.exists():
        raise SystemExit(f"ranges manifest not found: {ranges_manifest}")

    defaults_audit = audit_defaults_manifest(defaults_manifest)
    ranges_audit = audit_ranges_manifest(ranges_manifest)
    report = summarize(defaults_audit, ranges_audit, defaults_manifest, ranges_manifest)
    report["materialized_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    report["schema_snapshot"] = "refs/reports/mac_plugin_param_schema_20260629.json"

    output_json = args.output_json or ROOT / "refs" / "conformance" / f"windows_fresh_param_parity_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs" / "conformance" / f"windows_fresh_param_parity_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(committed_markdown(report, defaults_manifest, ranges_manifest), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
