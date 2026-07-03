#!/usr/bin/env python3
"""Freeze the remaining source-side candidate lanes for OLMDirectionalBlur."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRESETS_JSON = ROOT / "refs" / "reports" / "olmdirectionalblur_algorithm_presets_20260629.json"
DEFAULT_SCATTER_JSON = ROOT / "refs" / "reports" / "olmdirectionalblur_scatter_ownership_20260629.json"
DEFAULT_ENDPOINT_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_angle0_endpoint_constraint_20260630.json"
DEFAULT_PENDING_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_pending_witness_proof_20260629.json"
DEFAULT_PROOF_LANES_JSON = ROOT / "refs" / "reports" / "runtime_trace_bundle" / "olm_runtime_trace_requests_20260630_4pack_windows_return" / "runtime_trace_summary_directionalblur_helper_coverage_witness_20260630_160321_proof_lanes.json"
DEFAULT_SOURCE = ROOT / "cli" / "OLMDirectionalBlur" / "main.cpp"
DEFAULT_OUT_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_source_candidates_audit_20260701.json"
DEFAULT_OUT_MD = ROOT / "refs" / "conformance" / "olmdirectionalblur_source_candidates_audit_20260701.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_line(path: Path, needle: str) -> int:
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return idx
    raise ValueError(f"needle not found in {path}: {needle}")


def build_payload(
    presets: dict[str, Any],
    scatter: dict[str, Any],
    endpoint: dict[str, Any],
    pending: dict[str, Any],
    proof_lanes: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    case0001 = scatter["cases"]["case_0001"]
    case0005 = scatter["cases"]["case_0005"]
    comparisons = presets["comparisons"]
    angle0_lane = pending["angle0_lane"]
    diagonal_lane = pending["diagonal_lane"]
    lane_requests = {row["request_id"]: row for row in proof_lanes["requests"]}

    return {
        "kind": "olmdirectionalblur_source_candidates_audit",
        "date": "2026-07-01",
        "decision": "freeze-rejected-global-toggles-keep-two-narrow-lanes",
        "source": {
            "main_cpp": str(source_path.relative_to(ROOT)),
            "render_rotated_line": find_line(source_path, "Image render_rotated("),
            "full_choreo_line": find_line(source_path, 'args.algorithm == "rotated-aex-full-choreo"'),
            "prepass_full_choreo_line": find_line(source_path, 'args.algorithm == "rotated-aex-prepass-full-choreo"'),
            "exact_scatter_line": find_line(source_path, 'args.algorithm == "rotated-aex-exact-scatter-helper"'),
            "exact_rowdriver_line": find_line(source_path, 'args.algorithm == "rotated-aex-exact-rowdriver"'),
            "front_strength_line": find_line(source_path, 'args.algorithm == "rotated-front-strength"'),
        },
        "current_structural_base": {
            "candidate": "rotated-aex-full-choreo",
            "why_keep": [
                "It preserves the confirmed A/B choreography instead of falling back to measurement-only scaffolds.",
                "The best broad-mean presets are still non-AEX baselines and remain forbidden as implementation truth.",
                "Later toggle families only make sense as narrow witness-driven patches on top of this base.",
            ],
        },
        "rejected_as_global_fix": [
            {
                "toggle_family": "rowdriver_prepass_and_alpha_fade_gather",
                "preset_transition": comparisons["full_vs_prepass"],
                "evidence": [
                    "Broad measurements already classify rotated-rowdriver-prepass as worse than the current AEX-shaped base.",
                    "The current Mac notes report prepass/full-choreo as neutral on the tracked opaque witnesses.",
                    "No successful Windows typed rowdriver values were captured, so this cannot be promoted from PNGs.",
                ],
            },
            {
                "toggle_family": "source_driven_scatter",
                "preset_transition": comparisons["full_vs_scatter"],
                "evidence": [
                    f"case_0001 witness-row masks stay identical: {case0001['witness_row']['full_segments']} vs {case0001['witness_row']['scatter_segments']}.",
                    f"case_0001 scatter-vs-full max abs is only {case0001['scatter_vs_full']['max_abs']}, so the dominant long strip does not move.",
                    f"case_0005 scatter-vs-full max abs is only {case0005['scatter_vs_full']['max_abs']}; this is diagnostic drift, not proof of the final lane.",
                ],
            },
            {
                "toggle_family": "combined_exact_rowdriver_bundle",
                "preset_transition": comparisons["full_vs_exact_rowdriver"],
                "evidence": [
                    "Exact-rowdriver still differs from full-choreo only by the same prepass/scatter family and remains in the same residual band.",
                    "The latest helper-coverage return still says module trace not captured, so there is no typed proof that the combined bundle matches Windows internals.",
                    "Therefore exact-rowdriver remains a diagnostic preset, not a patch target.",
                ],
            },
            {
                "toggle_family": "measurement_scaffolds_direct_or_rotated_front_strength",
                "preset_transition": {
                    "forbidden_candidates": ["direct", "rotated-front-strength"],
                },
                "evidence": [
                    "They score better numerically in broad PNG matrices, but they do not preserve the confirmed AEX buffer choreography.",
                    "The witness contract explicitly forbids promoting them from means alone.",
                ],
            },
        ],
        "surviving_narrow_lanes": [
            {
                "family": "angle0-rowdriver-valid-alpha",
                "primary_witness": angle0_lane["primary_witness"],
                "endpoint_constraint": endpoint["endpoint_reasoning"],
                "still_missing": angle0_lane["required_next_proof"],
                "latest_runtime_status": lane_requests["olmdirectionalblur_helper_coverage_witness_20260630"]["status"],
            },
            {
                "family": "diagonal-rotate-validity",
                "primary_witness": diagonal_lane["primary_witness"],
                "companions": diagonal_lane["companion_witnesses"],
                "still_missing": diagonal_lane["required_next_proof"],
                "latest_runtime_status": lane_requests["olmdirectionalblur_angle0_diagonal_residual_witness_20260622"]["status"],
            },
        ],
        "allowed_next_actions": [
            "Keep the current AEX-shaped base and patch only after typed Windows witness values land for one lane.",
            "Use angle-0 endpoint (579,169) plus interior witness (494,169) to prove helper coverage or alternate path membership.",
            "Use diagonal witnesses only for rotate sampler / validity / normalization proof, not for angle-0 tuning.",
        ],
        "forbidden_actions": [
            "Do not retune prepass/scatter/direct/front-strength globally from PNG means.",
            "Do not merge angle-0 and diagonal residuals into one generic rowdriver theory.",
            "Do not treat the current helper-coverage return as actionable binary proof; it failed before module-local values were captured.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Source Candidates Audit",
        "",
        f"- Date: `{payload['date']}`",
        f"- Decision: `{payload['decision']}`",
        "",
        "## Current Structural Base",
        "",
        f"- Candidate: `{payload['current_structural_base']['candidate']}`",
        "- Source loci:",
    ]
    for key, value in payload["source"].items():
        lines.append(f"  - `{key}`: `{value}`")
    lines.append("- Why keep it:")
    for item in payload["current_structural_base"]["why_keep"]:
        lines.append(f"  - {item}")

    lines.extend(["", "## Rejected As Global Fix", ""])
    for item in payload["rejected_as_global_fix"]:
        lines.append(f"### `{item['toggle_family']}`")
        lines.append("")
        lines.append(f"- Preset transition: `{item['preset_transition']}`")
        for evidence in item["evidence"]:
            lines.append(f"- {evidence}")
        lines.append("")

    lines.extend(["## Surviving Narrow Lanes", ""])
    for lane in payload["surviving_narrow_lanes"]:
        lines.append(f"### `{lane['family']}`")
        lines.append("")
        lines.append(f"- Primary witness: `{lane['primary_witness']}`")
        if "companions" in lane:
            lines.append(f"- Companion witnesses: `{lane['companions']}`")
        if "endpoint_constraint" in lane:
            lines.append(f"- Endpoint constraint: `{lane['endpoint_constraint']}`")
        lines.append(f"- Latest runtime status: `{lane['latest_runtime_status']}`")
        lines.append(f"- Still missing: {lane['still_missing']}")
        lines.append("")

    lines.extend(["## Allowed Next Actions", ""])
    for item in payload["allowed_next_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden Actions", ""])
    for item in payload["forbidden_actions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--presets-json", type=Path, default=DEFAULT_PRESETS_JSON)
    parser.add_argument("--scatter-json", type=Path, default=DEFAULT_SCATTER_JSON)
    parser.add_argument("--endpoint-json", type=Path, default=DEFAULT_ENDPOINT_JSON)
    parser.add_argument("--pending-json", type=Path, default=DEFAULT_PENDING_JSON)
    parser.add_argument("--proof-lanes-json", type=Path, default=DEFAULT_PROOF_LANES_JSON)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(
        read_json(args.presets_json),
        read_json(args.scatter_json),
        read_json(args.endpoint_json),
        read_json(args.pending_json),
        read_json(args.proof_lanes_json),
        args.source,
    )
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
