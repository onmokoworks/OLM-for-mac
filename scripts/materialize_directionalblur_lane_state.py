#!/usr/bin/env python3
"""Materialize the current OLMDirectionalBlur lane state."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CANDIDATES_JSON = ROOT / "refs/conformance/olmdirectionalblur_source_candidates_audit_20260701.json"
HOOK_ANCHOR_JSON = ROOT / "refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.json"
WITNESS_PREP_JSON = ROOT / "refs/conformance/olmdirectionalblur_witness_logging_prep_20260702.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-candidates-json", type=Path, default=SOURCE_CANDIDATES_JSON)
    parser.add_argument("--hook-anchor-json", type=Path, default=HOOK_ANCHOR_JSON)
    parser.add_argument("--witness-prep-json", type=Path, default=WITNESS_PREP_JSON)
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
    source_candidates: dict[str, Any],
    hook_anchor: dict[str, Any],
    witness_prep: dict[str, Any],
    inputs: dict[str, Path],
) -> dict[str, Any]:
    return {
        "kind": "olmdirectionalblur_lane_state",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "decision": source_candidates["decision"],
        "structural_base": source_candidates["current_structural_base"]["candidate"],
        "runtime_status": witness_prep["current_runtime_status"],
        "runtime_summary": witness_prep["current_runtime_summary"],
        "safe_claim": (
            "DirectionalBlur remains split into two independent witness families: angle-0 rowdriver/valid-alpha and "
            "diagonal rotate/validity. Broad PNG tuning is still forbidden."
        ),
        "inputs": {name: rel(path) for name, path in inputs.items()},
        "angle0_lane": {
            "classification": hook_anchor["angle0_lane"]["classification"],
            "primary_witness": hook_anchor["angle0_lane"]["primary_witness"],
            "endpoint_witness": hook_anchor["angle0_lane"]["endpoint_constraint"],
            "wanted_fields": hook_anchor["wanted_angle0_fields"],
            "required_next_proof": hook_anchor["angle0_lane"]["required_next_proof"],
        },
        "diagonal_lane": {
            "classification": hook_anchor["diagonal_lane"]["classification"],
            "primary_witness": hook_anchor["diagonal_lane"]["primary_witness"],
            "companion_witnesses": hook_anchor["diagonal_lane"]["companion_witnesses"],
            "wanted_fields": hook_anchor["wanted_diagonal_fields"],
            "required_next_proof": hook_anchor["diagonal_lane"]["required_next_proof"],
        },
        "allowed_next_actions": source_candidates["allowed_next_actions"],
        "forbidden_actions": source_candidates["forbidden_actions"],
        "runtime_package": witness_prep["runtime_package"],
        "shared_logging_principles": witness_prep["shared_logging_principles"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    a0 = report["angle0_lane"]
    dg = report["diagonal_lane"]
    lines = [
        f"# OLMDirectionalBlur Lane State - {report['materialized_at'][:10]}",
        "",
        f"- Decision: `{report['decision']}`",
        f"- Structural base: `{report['structural_base']}`",
        f"- Runtime status: `{report['runtime_status']}`",
        f"- Runtime summary: {report['runtime_summary']}",
        f"- Safe claim: {report['safe_claim']}",
        f"- Runtime package: `{report['runtime_package']}`",
        "",
        "## Angle-0 lane",
        "",
        f"- Classification: `{a0['classification']}`",
        f"- Primary witness: `{a0['primary_witness']}`",
        f"- Required next proof: {a0['required_next_proof']}",
        f"- Endpoint constraint: `{a0['endpoint_witness']}`",
        "",
        "### Wanted fields",
        "",
    ]
    for item in a0["wanted_fields"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Diagonal lane",
            "",
            f"- Classification: `{dg['classification']}`",
            f"- Primary witness: `{dg['primary_witness']}`",
            f"- Required next proof: {dg['required_next_proof']}",
            f"- Companion witnesses: `{dg['companion_witnesses']}`",
            "",
            "### Wanted fields",
            "",
        ]
    )
    for item in dg["wanted_fields"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Allowed next actions", ""])
    for item in report["allowed_next_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden", ""])
    for item in report["forbidden_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Shared logging principles", ""])
    for item in report["shared_logging_principles"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Inputs", ""])
    for name, path in report["inputs"].items():
        lines.append(f"- {name}: `{path}`")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    inputs = {
        "source_candidates_json": args.source_candidates_json.resolve(),
        "hook_anchor_json": args.hook_anchor_json.resolve(),
        "witness_prep_json": args.witness_prep_json.resolve(),
    }
    for path in inputs.values():
        if not path.exists():
            raise SystemExit(f"missing input: {path}")
    report = build_report(
        load_json(inputs["source_candidates_json"]),
        load_json(inputs["hook_anchor_json"]),
        load_json(inputs["witness_prep_json"]),
        inputs,
    )
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmdirectionalblur_lane_state_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmdirectionalblur_lane_state_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
