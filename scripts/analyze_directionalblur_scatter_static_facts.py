#!/usr/bin/env python3
"""Extract static scatter-helper facts for OLMDirectionalBlur from asm."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISASM = ROOT / "disasm/OLMDirectionalBlur.aex.asm.txt"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_line(lines: list[str], needle: str) -> dict[str, object]:
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return {"line": index, "text": line}
    raise ValueError(f"missing disasm evidence: {needle}")


def analyze(disasm: Path) -> dict[str, object]:
    lines = read_lines(disasm)
    helper = find_line(lines, "; === FUN_1800013e0")
    rowdriver = find_line(lines, "; === FUN_1800038d0")

    effective_span_trunc = find_line(lines, "180001450  CVTTSS2SI R9D,XMM0")
    inv_coeff = find_line(lines, "180001465  DIVSS XMM3,XMM1")
    front_direction = find_line(lines, "180003aef  MOV R8B,0x1")
    back_direction = find_line(lines, "180003b79  XOR R8D,R8D")
    front_clip_cmp = find_line(lines, "18000147e  CMP ECX,R9D")
    front_clip_take_x = find_line(lines, "180001487  MOV R9D,ECX")
    back_clip_cmp = find_line(lines, "1800014a1  CMP EAX,EDX")
    back_clip_width_minus_x = find_line(lines, "1800014a5  MOV R9D,EDX")
    front_start_delta = find_line(lines, "180001481  LEA R11D,[R8 + -0x2]")
    back_start_delta = find_line(lines, "18000149e  MOV R11D,R8D")
    dst_start = find_line(lines, "1800014bb  LEA R10D,[R11 + RCX*0x1]")
    tail_gate = find_line(lines, "1800014c2  CMP R9D,R8D")
    offset_unit = find_line(lines, "180001473  MOV R8D,0x1")
    front_tail = find_line(lines, "180003b02  MULSS XMM1,dword ptr [RBX + 0x40]")
    back_tail = find_line(lines, "180003b89  MULSS XMM6,dword ptr [RBX + 0x44]")
    source_alpha_gate = find_line(lines, "180003a32  MOVSS XMM0,dword ptr [R12 + RDI*0x1 + 0xc]")
    source_alpha_skip = find_line(lines, "180003a3f  JZ 0x180003be3")
    front_strength = find_line(lines, "180003b0d  MOV EAX,dword ptr [RBX + 0x48]")
    back_strength = find_line(lines, "180003b94  MOV EAX,dword ptr [RBX + 0x50]")

    return {
        "kind": "olmdirectionalblur_scatter_static_facts",
        "schema": 1,
        "helper_function": "FUN_1800013e0",
        "helper_start": helper,
        "rowdriver_function": "FUN_1800038d0",
        "rowdriver_start": rowdriver,
        "evidence": {
            "effective_span_truncation": effective_span_trunc,
            "inverse_coeff_when_gate_positive": inv_coeff,
            "front_call_direction_flag": front_direction,
            "back_call_direction_flag": back_direction,
            "front_clip_compare_x_vs_span": front_clip_cmp,
            "front_clip_span_to_x": front_clip_take_x,
            "back_clip_compare_x_plus_span_vs_width": back_clip_cmp,
            "back_clip_span_to_width_minus_x": back_clip_width_minus_x,
            "front_start_delta_minus_one": front_start_delta,
            "back_start_delta_plus_one": back_start_delta,
            "destination_start_x": dst_start,
            "tail_gate_requires_span_gt_one": tail_gate,
            "offset_unit_one": offset_unit,
            "front_tail_factor_uses_0x40": front_tail,
            "back_tail_factor_uses_0x44": back_tail,
            "rowdriver_reads_source_alpha": source_alpha_gate,
            "rowdriver_zero_alpha_skip": source_alpha_skip,
            "front_strength_field_0x48": front_strength,
            "back_strength_field_0x50": back_strength,
        },
        "conclusions": {
            "effective_span_rule": "span = trunc(front_or_back_strength * coeff)",
            "front_boundary_rule": "front call clips span to x and starts at destination x-1",
            "back_boundary_rule": "back call clips span to width-x and starts at destination x+1",
            "write_direction_rule": "front helper writes strictly left of the source x; back helper writes strictly right",
            "tail_rule": "helper returns when effective span <= 1, so no zero-length or center write is emitted",
            "rowdriver_skip_rule": "scatter is skipped when source A alpha is exactly zero before helper dispatch",
            "shape_rule": (
                "per-column taper multiplies the coefficient passed into the helper and also steepens "
                "table indexing through 1/coeff when coeff > 0"
            ),
            "implementation_implication": (
                "broad scatter toggles should not be promoted globally; the remaining proof target is "
                "rowdriver/group-membership or hidden validity-side-channel behavior within these fixed "
                "left/right helper boundaries"
            ),
        },
    }


def render_markdown(report: dict[str, object]) -> str:
    evidence = report["evidence"]
    conclusions = report["conclusions"]
    lines = [
        "# OLMDirectionalBlur Scatter Static Facts",
        "",
        "This report is generated from the exported Windows AEX disassembly.",
        "It freezes helper-local scatter facts so PNG-only candidates do not get",
        "promoted without binary support.",
        "",
        "## Conclusions",
        "",
    ]
    for key, value in conclusions.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Evidence", "", "| Fact | Disasm line | Instruction |", "| --- | ---: | --- |"])
    for key, row in evidence.items():
        lines.append(f"| `{key}` | {row['line']} | `{row['text']}` |")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disasm", type=Path, default=DEFAULT_DISASM)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "refs/reports/olmdirectionalblur_scatter_static_facts.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "refs/reports/olmdirectionalblur_scatter_static_facts.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = analyze(args.disasm)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote: {args.output_json}")
    print(f"wrote: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
