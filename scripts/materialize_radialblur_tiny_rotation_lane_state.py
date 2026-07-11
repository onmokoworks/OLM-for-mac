#!/usr/bin/env python3
"""Materialize the current OLMRadialBlur tiny Rotation lane state."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LANE_AUDIT_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_lane_audit_20260701.json"
SOURCE_CANDIDATES_JSON = ROOT / "refs/conformance/olmradialblur_tiny_rotation_source_candidates_audit_20260701.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane-audit-json", type=Path, default=LANE_AUDIT_JSON)
    parser.add_argument("--source-candidates-json", type=Path, default=SOURCE_CANDIDATES_JSON)
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


def build_report(lane: dict[str, Any], source_candidates: dict[str, Any], inputs: dict[str, Path]) -> dict[str, Any]:
    same_row = lane["same_row_structure"]
    source_polar = lane["source_polar_structure"]
    row_probe = lane["row_coupling_probe"]
    pending = source_candidates["pending_windows_followup"]
    summary = source_candidates["lane_summary"]
    return {
        "kind": "olmradialblur_tiny_rotation_lane_state",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "case_id": lane["case_id"],
        "witness_xy": lane["witness_xy"],
        "inputs": {name: rel(path) for name, path in inputs.items()},
        "status": summary["decision"],
        "safe_claim": (
            "tiny Rotation is not a validity-only or final-byte lane; the remaining live suspicion is upstream "
            "polar RGB / neighboring-row / substitute-path ownership before final inverse sampling."
        ),
        "current_candidate_rgba": lane["current_candidate_rgba"],
        "windows_reference_rgba": lane["windows_reference_rgba"],
        "same_row_boundary": {
            "row_length": same_row["row_length"],
            "row_weights": same_row["row_weights"],
            "direct_source_cells_all_black": same_row["direct_source_cells_all_black"],
        },
        "source_polar_boundary": {
            "witness_sample_rgba": source_polar["witness_sample_rgba"],
            "witness_sample_u8": source_polar["witness_sample_u8"],
            "dominant_local_positive_cluster": source_polar["dominant_local_positive_cluster"],
            "strongest_positive": source_polar["strongest_positive"],
            "strongest_negative": source_polar["strongest_negative"],
        },
        "row_coupling_boundary": {
            "reference_bright_count": row_probe["reference_bright_count"],
            "all_variants_keep_bright_count_zero": row_probe["all_variants_keep_bright_count_zero"],
        },
        "pending_windows_followup": pending,
        "decision_ladder": source_candidates["decision_ladder"],
        "forbidden_actions": source_candidates["forbidden_actions"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    same_row = report["same_row_boundary"]
    source_polar = report["source_polar_boundary"]
    row_probe = report["row_coupling_boundary"]
    pending = report["pending_windows_followup"]
    wx, wy = report["witness_xy"]
    lines = [
        f"# OLMRadialBlur tiny Rotation Lane State - {report['materialized_at'][:10]}",
        "",
        f"- Case: `{report['case_id']}`",
        f"- Witness: `({wx},{wy})`",
        f"- Status: `{report['status']}`",
        f"- Candidate / Windows: `{report['current_candidate_rgba']}` vs `{report['windows_reference_rgba']}`",
        f"- Safe claim: {report['safe_claim']}",
        "",
        "## Same-row boundary",
        "",
        f"- row_length: `{same_row['row_length']}`",
        f"- row_weights: `{same_row['row_weights']}`",
        f"- direct source cells all black: `{same_row['direct_source_cells_all_black']}`",
        "",
        "## Source-polar boundary",
        "",
        f"- witness sample RGBA: `{source_polar['witness_sample_rgba']}`",
        f"- witness sample U8: `{source_polar['witness_sample_u8']}`",
        f"- dominant local positive cluster: `{source_polar['dominant_local_positive_cluster']}`",
        f"- strongest positive: `{source_polar['strongest_positive']}`",
        f"- strongest negative: `{source_polar['strongest_negative']}`",
        "",
        "## Row-coupling boundary",
        "",
        f"- reference bright count in local window: `{row_probe['reference_bright_count']}`",
        f"- all tested local variants keep bright count zero: `{row_probe['all_variants_keep_bright_count_zero']}`",
        "",
        "## Pending Windows Follow-up",
        "",
        f"- Request: `{pending['request_id']}`",
        f"- Status: `{pending['status']}`",
        f"- Package: `{pending['package']}`",
        f"- Acceptance: `{pending['acceptance_note']}`",
        f"- Stop condition: {pending['stop_condition']}",
        "",
        "## Decision Ladder",
        "",
    ]
    for idx, row in enumerate(report["decision_ladder"], start=1):
        lines.append(f"{idx}. {row['condition']} -> {row['action']}")
    lines.extend(["", "## Forbidden", ""])
    for item in report["forbidden_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Inputs", ""])
    for name, path in report["inputs"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    inputs = {
        "lane_audit_json": args.lane_audit_json.resolve(),
        "source_candidates_json": args.source_candidates_json.resolve(),
    }
    for path in inputs.values():
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
    report = build_report(
        load_json(inputs["lane_audit_json"]),
        load_json(inputs["source_candidates_json"]),
        inputs,
    )
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmradialblur_tiny_rotation_lane_state_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmradialblur_tiny_rotation_lane_state_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
