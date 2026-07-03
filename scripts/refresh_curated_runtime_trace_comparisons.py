#!/usr/bin/env python3
"""Refresh curated runtime-trace comparison outputs from archived summary JSONs."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RefreshTarget:
    slug: str
    runtime_summary_json: Path
    output_json: Path
    output_md: Path
    command: list[str]
    description: str


TARGETS: dict[str, RefreshTarget] = {
    "distancegradation-case0023-refcon-wordmap": RefreshTarget(
        slug="distancegradation-case0023-refcon-wordmap",
        runtime_summary_json=ROOT
        / "refs/reports/runtime_trace_summary_distancegradation_case0023_refcon_wordmap_followup_20260702_165307.json",
        output_json=ROOT
        / "refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_wordmap_followup_20260702.json",
        output_md=ROOT
        / "refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_refcon_wordmap_followup_20260702.md",
        command=["python3", "scripts/compare_distancegradation_trace.py"],
        description="OLMDistanceGradation case_0023 refcon/wordmap follow-up",
    ),
    "radialblur-tiny-rotation-anchor-pointer": RefreshTarget(
        slug="radialblur-tiny-rotation-anchor-pointer",
        runtime_summary_json=ROOT
        / "refs/reports/runtime_trace_summary_radialblur_tiny_rotation_anchor_pointer_watch_followup_20260702_165307.json",
        output_json=ROOT
        / "refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702.json",
        output_md=ROOT
        / "refs/reports/runtime_trace_comparisons/olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702.md",
        command=["python3", "scripts/compare_radialblur_trace.py"],
        description="OLMRadialBlur tiny Rotation anchor-pointer watch follow-up",
    ),
    "kirakira-aggregation-compose-bt709": RefreshTarget(
        slug="kirakira-aggregation-compose-bt709",
        runtime_summary_json=ROOT
        / "refs/reports/runtime_trace_summary_kirakira_aggregation_compose_bt709_20260624_231804.json",
        output_json=ROOT
        / "refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.json",
        output_md=ROOT
        / "refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md",
        command=[
            "python3",
            "scripts/compare_kirakira_stage_trace.py",
            "--local-trace-json",
            "refs/reports/olmkirakira_trace_baseline_20260624_bt709_mac/trace.json",
        ],
        description="OLMKiraKira aggregation/compose BT.709 witness",
    ),
    "smoother2-producer-path-diff": RefreshTarget(
        slug="smoother2-producer-path-diff",
        runtime_summary_json=ROOT
        / "refs/reports/runtime_trace_summary_smoother2_current_aex_producer_path_diff_20260702_220800.json",
        output_json=ROOT
        / "refs/reports/runtime_trace_comparisons/olmsmoother2_current_aex_producer_path_diff_20260702.json",
        output_md=ROOT
        / "refs/reports/runtime_trace_comparisons/olmsmoother2_current_aex_producer_path_diff_20260702.md",
        command=["python3", "scripts/compare_smoother2_legacy_trace.py"],
        description="OLMSmoother2 current-AEX producer-path diff retry",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        action="append",
        choices=sorted(TARGETS),
        help="Curated target to refresh. Repeat to select more than one. Defaults to all.",
    )
    parser.add_argument(
        "--index-json",
        type=Path,
        default=ROOT / "refs/reports/runtime_trace_comparisons/curated_refresh_index.json",
    )
    parser.add_argument(
        "--index-md",
        type=Path,
        default=ROOT / "refs/reports/runtime_trace_comparisons/curated_refresh_index.md",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_target(target: RefreshTarget) -> dict[str, Any]:
    target.output_json.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        *target.command,
        "--runtime-summary-json",
        str(target.runtime_summary_json),
        "--output-json",
        str(target.output_json),
        "--output-md",
        str(target.output_md),
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    row: dict[str, Any] = {
        "slug": target.slug,
        "description": target.description,
        "runtime_summary_json": display_path(target.runtime_summary_json),
        "output_json": display_path(target.output_json),
        "output_md": display_path(target.output_md),
        "command": [display_path(Path(part)) if part.startswith(str(ROOT)) else part for part in cmd],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
    }
    if proc.returncode == 0 and target.output_json.exists():
        data = load_json(target.output_json)
        if isinstance(data, dict):
            row["request_id"] = data.get("request_id")
            row["likely_next_focus"] = data.get("likely_next_focus")
            windows = data.get("windows")
            if isinstance(windows, dict):
                row["windows_status"] = windows.get("status")
    return row


def render_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Curated Runtime Trace Refresh Index",
        "",
        "| Target | Status | Windows status | Likely next focus | Output |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in index["targets"]:
        status = "OK" if row.get("returncode") == 0 else f"FAIL {row.get('returncode')}"
        lines.append(
            f"| `{row['slug']}` | {status} | `{row.get('windows_status', '-')}` | "
            f"`{row.get('likely_next_focus', '-')}` | `{row['output_md']}` |"
        )
    if not index["targets"]:
        lines.append("| - | - | - | - | - |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    slugs = args.target or sorted(TARGETS)
    rows: list[dict[str, Any]] = []
    for slug in slugs:
        target = TARGETS[slug]
        if not target.runtime_summary_json.exists():
            print(f"[FAIL] missing runtime summary: {display_path(target.runtime_summary_json)}", file=sys.stderr)
            return 1
        rows.append(run_target(target))
    index = {
        "kind": "olm_curated_runtime_trace_refresh_index",
        "targets": rows,
    }
    args.index_json.parent.mkdir(parents=True, exist_ok=True)
    args.index_json.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.index_md.write_text(render_markdown(index), encoding="utf-8")
    failed = [row for row in rows if row.get("returncode") != 0]
    if failed:
        for row in failed:
            print(row.get("stdout", ""), end="", file=sys.stderr)
        return 1
    print(f"[OK] refreshed {len(rows)} curated runtime-trace comparison target(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
