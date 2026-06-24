#!/usr/bin/env python3
"""Extract static facts for OLMRadialBlur's scatter helper from exported asm."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISASM = ROOT / "disasm/OLMRadialBlur.aex.asm.txt"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def find_line(lines: list[str], needle: str) -> dict[str, object]:
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return {"line": index, "text": line}
    raise ValueError(f"missing disasm evidence: {needle}")


def line_between(lines: list[str], needle: str, start: int, end: int) -> dict[str, object]:
    for index, line in enumerate(lines, start=1):
        if start <= index <= end and needle in line:
            return {"line": index, "text": line}
    raise ValueError(f"missing disasm evidence in range {start}..{end}: {needle}")


def analyze(disasm: Path) -> dict[str, object]:
    lines = read_lines(disasm)
    helper = find_line(lines, "; === FUN_180001c90")
    caller = find_line(lines, "; === FUN_1800024c0")

    span_cvtt = find_line(lines, "180001d18  CVTTSS2SI R14D,XMM0")
    table_div = find_line(lines, "180001d41  IDIV R14D")
    inner_unrolled_limit = find_line(lines, "180002124  MOV EBP,R12D")
    inner_tail_compare = find_line(lines, "180002487  CMP R10D,R14D")
    inner_tail_loop = find_line(lines, "18000248a  JL 0x1800023e0")
    inner_underflow_next_row = find_line(lines, "1800023e6  LEA EDX,[R12 + 0x1]")
    inner_call = find_line(lines, "1800026e5  CALL 0x180001c90")
    inner_r8 = line_between(lines, "180002699  MOV R8D,dword ptr [RSP + 0x138]", inner_call["line"] - 24, inner_call["line"])
    inner_direction = line_between(lines, "1800026a1  MOV EDX,0x1", inner_call["line"] - 24, inner_call["line"])

    facts = {
        "helper_function": "FUN_180001c90",
        "helper_start": helper,
        "caller_function": "FUN_1800024c0",
        "caller_start": caller,
        "evidence": {
            "effective_span_truncation": span_cvtt,
            "table_step_divides_30000_by_effective_span": table_div,
            "inner_unrolled_loop_uses_r14_minus_3_as_chunk_limit": inner_unrolled_limit,
            "inner_tail_compares_offset_to_r14": inner_tail_compare,
            "inner_tail_loops_while_offset_lt_r14": inner_tail_loop,
            "inner_underflow_advances_to_next_radius_row": inner_underflow_next_row,
            "inner_call_passes_direction_one": inner_direction,
            "inner_call_passes_caller_distance_from_rsp_0x138": inner_r8,
            "inner_callsite": inner_call,
        },
        "conclusions": {
            "global_loop_minus_one_supported_by_asm": False,
            "global_circular_wrap_supported_by_asm": False,
            "effective_span_rule": "R14D = trunc(float(resolved_distance) * span_gate)",
            "table_step_rule": "step = int(30000 / R14D)",
            "tail_loop_rule": "offset starts at 1 and continues while offset < R14D",
            "inner_underflow_rule": "when angular index underflows, target advances to the next radius row tail",
            "candidate_matrix_interpretation": (
                "loop-minus-one/circular-wrap/table-span-minus-one can localize missing behavior, "
                "but the exported asm does not support promoting them as global rules."
            ),
        },
    }
    return facts


def render_markdown(report: dict[str, object]) -> str:
    evidence = report["evidence"]
    conclusions = report["conclusions"]
    lines = [
        "# OLMRadialBlur Scatter Static Facts",
        "",
        "This report is generated from the exported Windows AEX disassembly.",
        "It records static evidence for `FUN_180001c90` / `FUN_1800024c0` so",
        "PNG-only candidate switches do not get promoted without binary support.",
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
        default=ROOT / "refs/reports/olmradialblur_scatter_static_facts.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "refs/reports/olmradialblur_scatter_static_facts.md",
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
