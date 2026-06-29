#!/usr/bin/env python3
"""Summarize the helper-boundary implication for OLMDirectionalBlur angle-0 endpoint witnesses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCATTER_JSON = ROOT / "refs" / "reports" / "olmdirectionalblur_scatter_ownership_20260629.json"
DEFAULT_STATIC_JSON = ROOT / "refs" / "reports" / "olmdirectionalblur_scatter_static_facts.json"
DEFAULT_PLAN_JSON = ROOT / "refs" / "reports" / "olmdirectionalblur_witness_plan_20260625" / "witness_plan.json"
DEFAULT_OUT_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_angle0_endpoint_constraint_20260630.json"
DEFAULT_OUT_MD = ROOT / "refs" / "conformance" / "olmdirectionalblur_angle0_endpoint_constraint_20260630.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scatter-json", type=Path, default=DEFAULT_SCATTER_JSON)
    parser.add_argument("--static-json", type=Path, default=DEFAULT_STATIC_JSON)
    parser.add_argument("--plan-json", type=Path, default=DEFAULT_PLAN_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_payload(scatter: dict[str, Any], static: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    case = scatter["cases"]["case_0001"]
    witness_row = case["witness_row"]
    segment = witness_row["full_segments"][0]
    segment_start, segment_end = int(segment[0]), int(segment[1])

    angle0_plan = next(row for row in plan["plans"] if row["family"] == "angle0-rowdriver-valid-alpha")
    primary_xy = angle0_plan["primary_witness"]["xy"]

    required_min_source_x_for_endpoint = segment_end + 1
    endpoint_supported_by_same_row_segment = required_min_source_x_for_endpoint <= segment_end

    return {
        "kind": "olmdirectionalblur_angle0_endpoint_constraint",
        "date": "2026-06-30",
        "case_id": "case_0001",
        "witness_row_y": int(witness_row["y"]),
        "primary_witness_xy": primary_xy,
        "full_segments": witness_row["full_segments"],
        "scatter_segments": witness_row["scatter_segments"],
        "identical_mask": bool(witness_row["identical_mask"]),
        "static_facts": {
            "write_direction_rule": static["conclusions"]["write_direction_rule"],
            "front_boundary_rule": static["conclusions"]["front_boundary_rule"],
            "tail_rule": static["conclusions"]["tail_rule"],
        },
        "endpoint_reasoning": {
            "rightmost_visible_strip_x": segment_end,
            "required_min_source_x_for_same_row_front_helper": required_min_source_x_for_endpoint,
            "same_row_segment_contains_that_source_x": endpoint_supported_by_same_row_segment,
            "implication": (
                "If the angle-0 endpoint pixel is produced by the documented front helper on the same row, "
                "the contributing source x must be strictly greater than the endpoint destination x because "
                "front writes only to the left. The current local strip row ends at x=579, so a same-row "
                "source inside that visible strip cannot explain the endpoint by itself."
            ),
        },
        "decision": "angle0-endpoint-needs-source-range-or-alternate-path-proof",
        "conclusion": [
            "The local full/scatter masks are identical on row y=169 across x=380..579, so source-driven scatter ownership toggles do not change the existence of the strip itself.",
            "Static helper facts say the front helper writes strictly left of the source x and does not emit a center write.",
            "Therefore the right strip endpoint at x=579 is a high-value witness: a useful Windows trace must reveal either a contributing source x > 579, a rotated-buffer/group-membership explanation, or another validity/alpha side-channel or alternate path.",
            "This makes endpoint (579,169) complementary to interior witness (494,169): the endpoint tests row coverage/boundary logic, while the interior pixel tests accumulation/value logic inside the same strip family.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Angle-0 Endpoint Constraint",
        "",
        f"- Date: `{payload['date']}`",
        f"- Case: `{payload['case_id']}`",
        f"- Witness row: `y={payload['witness_row_y']}`",
        f"- Primary witness: `{payload['primary_witness_xy']}`",
        "",
        "## Local Row Shape",
        "",
        f"- full segments: `{payload['full_segments']}`",
        f"- scatter segments: `{payload['scatter_segments']}`",
        f"- identical mask: `{payload['identical_mask']}`",
        "",
        "## Static Helper Facts",
        "",
        f"- write direction: `{payload['static_facts']['write_direction_rule']}`",
        f"- front boundary: `{payload['static_facts']['front_boundary_rule']}`",
        f"- tail rule: `{payload['static_facts']['tail_rule']}`",
        "",
        "## Endpoint Reasoning",
        "",
        f"- rightmost visible strip x: `{payload['endpoint_reasoning']['rightmost_visible_strip_x']}`",
        f"- required same-row source x for front-helper-only explanation: `{payload['endpoint_reasoning']['required_min_source_x_for_same_row_front_helper']}`",
        f"- source exists inside visible strip: `{payload['endpoint_reasoning']['same_row_segment_contains_that_source_x']}`",
        f"- implication: {payload['endpoint_reasoning']['implication']}",
        "",
        "## Decision",
        "",
        f"- `{payload['decision']}`",
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["conclusion"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    payload = build_payload(
        read_json(args.scatter_json),
        read_json(args.static_json),
        read_json(args.plan_json),
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
