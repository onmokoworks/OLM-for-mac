#!/usr/bin/env python3
"""Prepare witness-level logging asks for the active OLMDirectionalBlur lanes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOOK_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_hook_anchor_audit_20260701.json"
SOURCE_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_source_candidates_audit_20260701.json"
PENDING_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_pending_witness_proof_20260629.json"
TRACE_JSON = ROOT / "refs" / "reports" / "runtime_trace_comparisons" / "olmdirectionalblur_residual_witness_20260624.json"
DECOMP = ROOT / "decomp" / "OLMDirectionalBlur.aex.c.txt"
CLI_SOURCE = ROOT / "cli" / "OLMDirectionalBlur" / "main.cpp"
OUT_JSON = ROOT / "refs" / "conformance" / "olmdirectionalblur_witness_logging_prep_20260702.json"
OUT_MD = ROOT / "refs" / "conformance" / "olmdirectionalblur_witness_logging_prep_20260702.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hook-json", type=Path, default=HOOK_JSON)
    parser.add_argument("--source-candidates-json", type=Path, default=SOURCE_JSON)
    parser.add_argument("--pending-proof-json", type=Path, default=PENDING_JSON)
    parser.add_argument("--trace-json", type=Path, default=TRACE_JSON)
    parser.add_argument("--decomp", type=Path, default=DECOMP)
    parser.add_argument("--cli-source", type=Path, default=CLI_SOURCE)
    parser.add_argument("--output-json", type=Path, default=OUT_JSON)
    parser.add_argument("--output-md", type=Path, default=OUT_MD)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def find_line(path: Path, needle: str) -> int:
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return idx
    raise ValueError(f"needle not found in {path}: {needle}")


def witness_label(witness: dict[str, Any]) -> str:
    xy = witness.get("xy")
    ref = witness.get("reference_rgba") or witness.get("reference")
    cand = witness.get("candidate_rgba") or witness.get("candidate")
    return f"{xy} ref={ref} cand={cand}"


def build_lane(
    *,
    family: str,
    hook_lane: dict[str, Any],
    pending_lane: dict[str, Any],
    shared_fields: list[str],
    family_fields: list[str],
    witness_focus: list[str],
    answerable_when: list[str],
    not_answered_when: list[str],
) -> dict[str, Any]:
    primary = hook_lane["primary_witness"]
    payload = {
        "family": family,
        "classification": hook_lane["classification"],
        "primary_witness": primary,
        "primary_label": witness_label(primary),
        "required_fields": shared_fields + family_fields,
        "witness_focus": witness_focus,
        "answerable_when": answerable_when,
        "not_answered_when": not_answered_when,
        "required_next_proof": hook_lane["required_next_proof"],
    }
    if "scan_order_max_witness" in hook_lane:
        payload["scan_order_max_witness"] = hook_lane["scan_order_max_witness"]
    if "companion_witnesses" in hook_lane:
        payload["companion_witnesses"] = hook_lane["companion_witnesses"]
    if "endpoint_constraint" in hook_lane:
        payload["endpoint_constraint"] = hook_lane["endpoint_constraint"]
    if "helper_local_static_facts" in pending_lane:
        payload["helper_local_static_facts"] = pending_lane["helper_local_static_facts"]
    return payload


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    hook = read_json(args.hook_json)
    source = read_json(args.source_candidates_json)
    pending = read_json(args.pending_proof_json)
    trace = read_json(args.trace_json)

    shared_fields = [
        "witness case id and output xy",
        "normalized effect parameters actually consumed by the call",
        "A/B image pointers plus output-to-A/B buffer xy mapping",
        "denominator plane pointer/value at the witness",
        "alpha_or_valid side-channel pointer/value at the witness",
        "accumulation numerator RGBA before normalization",
        "pre-writeback RGBA float/hex after normalization",
        "final stored RGBA bytes",
    ]
    angle0_fields = [
        "helper-local source x/y and actual touched destination x range on row y=169",
        "rowdriver/group membership for both (494,169) and endpoint (579,169)",
        "effective span inputs/outputs for the front helper",
    ]
    diagonal_fields = [
        "rotate sampler source coordinates and sample order",
        "border or validity decision for the sampled source set",
        "group-size or opacity gate feeding the diagonal witness",
    ]

    angle0_lane = build_lane(
        family="angle0-rowdriver-valid-alpha",
        hook_lane=hook["angle0_lane"],
        pending_lane=pending["angle0_lane"],
        shared_fields=shared_fields,
        family_fields=angle0_fields,
        witness_focus=[
            "Primary interior witness stays (494,169), but the return should include the right-edge endpoint (579,169) in the same pass.",
            "The point of this lane is to decide whether the missing red strip is a rowdriver/group-membership miss or a valid-alpha side-channel miss.",
            "A useful answer must expose touched destination coverage, not only final bytes.",
        ],
        answerable_when=[
            "The same return covers both (494,169) and (579,169) with typed rowdriver/group and alpha_or_valid values.",
            "The helper-local source-to-destination coverage proves whether the right endpoint is inside or outside the front-helper write range.",
            "Numerator, denominator, pre-writeback, and final bytes are all present at the witness.",
        ],
        not_answered_when=[
            "Only final PNG bytes or broad means are returned.",
            "The run confirms the witness coordinates but omits helper-local touched destination range.",
            "The run logs rowdriver-ish prose without typed values for denominator, alpha_or_valid, and pre-writeback RGBA.",
        ],
    )
    diagonal_lane = build_lane(
        family="diagonal-rotate-validity",
        hook_lane=hook["diagonal_lane"],
        pending_lane=pending["diagonal_lane"],
        shared_fields=shared_fields,
        family_fields=diagonal_fields,
        witness_focus=[
            "Primary diagonal witness stays (507,367); keep a signed-red companion such as (423,187) in the same answer when possible.",
            "The point of this lane is to separate rotate sampler order/border-validity from later normalization/writeback.",
            "A useful answer must expose the sampled source coordinates/order and the validity decision feeding the witness.",
        ],
        answerable_when=[
            "The return includes typed rotate source coordinates/order plus border-validity or equivalent substitute-path facts.",
            "The return includes group-size/opacity gate, denominator, pre-writeback, and final bytes at the diagonal witness.",
            "The same answer keeps diagonal evidence separate from the angle-0 strip theory.",
        ],
        not_answered_when=[
            "Only the final diagonal byte is logged.",
            "Sampler order is described qualitatively but no typed source coordinates or border-validity values are returned.",
            "The answer collapses diagonal behavior into the angle-0 rowdriver theory.",
        ],
    )

    windows = trace.get("windows") if isinstance(trace.get("windows"), dict) else {}
    return {
        "kind": "olmdirectionalblur_witness_logging_prep",
        "schema": 1,
        "date": "2026-07-02",
        "decision": "ready-for-next-witness-level-ab-denominator-validity-logging",
        "inputs": {
            "hook_json": str(args.hook_json),
            "source_candidates_json": str(args.source_candidates_json),
            "pending_proof_json": str(args.pending_proof_json),
            "trace_json": str(args.trace_json),
        },
        "structural_base": source["current_structural_base"]["candidate"],
        "runtime_package": hook["runtime_package"],
        "current_runtime_status": windows.get("status"),
        "current_runtime_summary": windows.get("summary"),
        "source_anchors": {
            "rotate_helper_line": find_line(args.decomp, "void FUN_180001ec0(longlong param_1,longlong param_2,int param_3,int param_4,float param_5)"),
            "rowdriver_line": find_line(args.decomp, "void FUN_1800038d0(int param_1,int param_2,longlong *param_3,longlong *param_4,int param_5,"),
            "rowdriver_front_helper_call_line": find_line(args.decomp, "FUN_1800013e0(iVar7,iVar9,'\\x01',lVar2,lVar1,*(longlong *)(param_7 + 0x8080),"),
            "rowdriver_back_helper_call_line": find_line(args.decomp, "FUN_1800013e0(iVar7,iVar9,'\\0',lVar2,lVar1,*(longlong *)(param_7 + 0x8080),"),
            "rotate_into_b_call_line": find_line(args.decomp, "FUN_180001ec0((longlong)_Dst,(longlong)_Src,*(int *)(param_6 + 0x1014),"),
            "copy_b_back_into_a_line": find_line(args.decomp, "memcpy(_Dst,_Src,"),
            "rowdriver_dispatch_line": find_line(args.decomp, "FUN_1800038d0(uVar20 - iVar9,uVar6,(longlong *)&local_ac0,(longlong *)&local_ac8,"),
            "rotate_back_output_call_line": find_line(args.decomp, "FUN_180001ec0((longlong)_Src,(longlong)_Dst,iVar17,iVar9,"),
            "cli_full_choreo_line": find_line(args.cli_source, 'args.algorithm == "rotated-aex-full-choreo"'),
            "cli_exact_rowdriver_line": find_line(args.cli_source, 'args.algorithm == "rotated-aex-exact-rowdriver"'),
            "cli_rowdriver_prepass_line": find_line(args.cli_source, 'args.algorithm == "rotated-rowdriver-prepass"'),
            "cli_front_strength_line": find_line(args.cli_source, 'args.algorithm == "rotated-front-strength"'),
        },
        "shared_logging_principles": [
            "Stay on the AEX-shaped full choreography base while logging; direct and rotated-front-strength remain measurement baselines only.",
            "Capture typed values for A/B mapping, denominator, alpha_or_valid, numerator, pre-writeback, and final bytes in the same witness record.",
            "Treat angle-0 and diagonal as separate lanes even if one pass can log both.",
        ],
        "lanes": [angle0_lane, diagonal_lane],
        "parent_follow_up": [
            "Use this prep artifact to shape the next Windows witness request or local logging harness fields.",
            "When a new return lands, feed it through compare_directionalblur_trace.py and check it against the per-lane answerable/not-answered rules here.",
            "Do not start source edits until at least one lane returns typed denominator + validity/alpha_or_valid + pre-writeback evidence.",
        ],
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OLMDirectionalBlur Witness Logging Prep",
        "",
        f"- Date: `{payload['date']}`",
        f"- Decision: `{payload['decision']}`",
        f"- Structural base: `{payload['structural_base']}`",
        f"- Runtime package: `{payload['runtime_package']}`",
        f"- Current runtime status: `{payload['current_runtime_status']}`",
        f"- Current runtime summary: {payload['current_runtime_summary']}",
        "",
        "## Source Anchors",
        "",
    ]
    for key, value in payload["source_anchors"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Shared Logging Principles", ""])
    for item in payload["shared_logging_principles"]:
        lines.append(f"- {item}")
    for lane in payload["lanes"]:
        lines.extend(
            [
                "",
                f"## {lane['family']}",
                "",
                f"- Classification: `{lane['classification']}`",
                f"- Primary witness: `{lane['primary_label']}`",
            ]
        )
        if "scan_order_max_witness" in lane:
            lines.append(f"- Scan-order max witness: `{witness_label(lane['scan_order_max_witness'])}`")
        if "companion_witnesses" in lane:
            lines.append(
                "- Companion witnesses: "
                + ", ".join(f"`{witness_label(row)}`" for row in lane["companion_witnesses"])
            )
        if "endpoint_constraint" in lane:
            lines.append(f"- Endpoint constraint: {lane['endpoint_constraint']}")
        lines.append(f"- Required next proof: {lane['required_next_proof']}")
        if "helper_local_static_facts" in lane:
            lines.append("- Helper-local static facts:")
            for item in lane["helper_local_static_facts"]:
                lines.append(f"  - {item}")
        lines.extend(["", "Witness focus:", ""])
        for item in lane["witness_focus"]:
            lines.append(f"- {item}")
        lines.extend(["", "Required fields:", ""])
        for item in lane["required_fields"]:
            lines.append(f"- {item}")
        lines.extend(["", "Treat as answered when:", ""])
        for item in lane["answerable_when"]:
            lines.append(f"- {item}")
        lines.extend(["", "Treat as not answered when:", ""])
        for item in lane["not_answered_when"]:
            lines.append(f"- {item}")
    lines.extend(["", "## Parent Follow-up", ""])
    for item in payload["parent_follow_up"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
