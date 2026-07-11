#!/usr/bin/env python3
"""Materialize local AEX CPU emulation branch facts for OLMSmoother2 legacy."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EMU_DIR = ROOT / "tools" / "emulation"
sys.path.insert(0, str(EMU_DIR))

import test_smoother2_producer as sm2emu  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Date stamp for output filenames (default: today in local time).",
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    return parser.parse_args()


def set_empty(ss: Any) -> None:
    ss.set_cur(8, 8)


def set_isolated(ss: Any) -> None:
    ss.set_cur(8, 8)
    ss.set_class_pixel(8, 8, b0=1)


def set_edge_x0(ss: Any) -> None:
    ss.set_cur(0, 8)


def set_edge_ybottom(ss: Any) -> None:
    ss.set_cur(8, 15)


def set_dense_nw_block(ss: Any) -> None:
    ss.set_cur(8, 8)
    for yy in range(4, 12):
        for xx in range(4, 12):
            ss.set_class_pixel(xx, yy, b0=1)


def set_force_passthrough(ss: Any) -> None:
    cx, cy = 8, 4
    ss.set_cur(cx, cy)
    for dy in range(1, 8):
        ss.set_class_pixel(cx, cy + dy, b0=1)
    for dx in range(1, 8):
        ss.set_class_pixel(cx + dx, cy, b0=0, b1=1)
    ss.set_class_pixel(cx - 1, cy, b0=0, b1=0, b2=0, b3=1)


SCENARIOS: list[tuple[str, Callable[[Any], None], str]] = [
    ("empty-around-cur", set_empty, "baseline local class-plane around cur=(8,8)"),
    ("isolated-class-at-cur", set_isolated, "class byte0 set only at cur=(8,8)"),
    ("edge-cur-x0", set_edge_x0, "entry guard fails because cur_x == 0"),
    ("edge-cur-ybottom", set_edge_ybottom, "entry guard fails because cur_y == height-1"),
    ("dense-nw-block", set_dense_nw_block, "dense class block near cur=(8,8)"),
    (
        "force-passthrough",
        set_force_passthrough,
        "both scanners run long and class_prev is set, forcing emit_guard false",
    ),
]


def jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    return value


def summarize_0004(row: dict[str, Any]) -> dict[str, Any]:
    right = row["right_scan"]
    down = row["down_scan"]
    return {
        "scenario": row["scenario"],
        "cur": list(row["cur"]),
        "entry_guard": row["entry_guard"],
        "iVar6_right": right["iVar6"],
        "right_out": list(right["out"]),
        "right_code": right["code"],
        "iVar5_down": down["iVar5"],
        "down_out": list(down["out"]),
        "down_code": down["code"],
        "class_prev_byte": row["class_prev_byte"],
        "emit_guard": row["emit_guard"],
        "vcount": row["vcount"],
        "vertex_weights": [vertex["weight"] for vertex in row["vertices"]],
        "vertex_rgba": [list(vertex["rgba"]) for vertex in row["vertices"]],
    }


def build_report() -> dict[str, Any]:
    leaf = sm2emu.run_leaf_check()
    rows_0004 = []
    for name, setup, note in SCENARIOS:
        result = sm2emu.run_0004(name, setup)
        row = summarize_0004(result)
        row["note"] = note
        rows_0004.append(row)
    case_0012 = jsonable(sm2emu.run_0012())
    return {
        "kind": "olmsmoother2_producer_branch_table",
        "materialized_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "tools/emulation/test_smoother2_producer.py",
        "aex": str(sm2emu.AEX_PATH.relative_to(ROOT)),
        "status": "local-aex-cpu-emulation-branch-table",
        "leaf_check": jsonable(leaf),
        "case_0004": {
            "witness": [1903, 519],
            "reference_rgba8": [103, 103, 103, 113],
            "local_problem": "Mac-side path can fall through to count=0 passthrough; Windows writer is already known semitransparent gray.",
            "rows": rows_0004,
            "reading": [
                "FUN_180013140 append/no-append is controlled by entry_guard, scanner spans, class_prev_byte, and emit_guard.",
                "The force-passthrough synthetic class-plane reaches vcount=0 without changing global fallback logic.",
                "This is local AEX branch grounding, not Windows-vs-Mac AE exact proof.",
            ],
        },
        "case_0012": {
            "witness": [91, 841],
            "reference_rgba8": [0, 0, 0, 0],
            "local_candidate_rgba8": [90, 90, 90, 91],
            "reading": [
                "Local e170/f270/e3a0 direct calls show c=2 keeps append alive.",
                "The remaining evidence needed is Windows-side class-plane/bitsum or cce0 producer state, not final writer bytes.",
            ],
            "result": case_0012,
        },
        "next_allowed_actions": [
            "Use this table to choose a narrower producer witness before requesting more Windows debugger work.",
            "If continuing locally, sweep 0012 e170 bitsum c values and 0004 class-plane scanner patterns in the same harness.",
        ],
        "forbidden_actions": [
            "Do not request final writer bytes again for these witnesses.",
            "Do not add global transparent-center fallback or global f270 suppression from this local table alone.",
            "Do not promote this local emulation evidence to AE exact.",
        ],
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        f"# OLMSmoother2 Producer Branch Table - {report['materialized_at'][:10]}",
        "",
        f"- Status: `{report['status']}`",
        f"- Source: `{report['source']}`",
        f"- AEX: `{report['aex']}`",
        f"- Leaf check: `{'PASS' if report['leaf_check']['all_match'] else 'FAIL'}`",
        "",
        "## case_0004",
        "",
        f"- Witness: `{tuple(report['case_0004']['witness'])}`",
        f"- Reference RGBA8: `{report['case_0004']['reference_rgba8']}`",
        f"- Local problem: {report['case_0004']['local_problem']}",
        "",
        "| Scenario | Entry | iVar6 | iVar5 | class_prev | Emit | vcount |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["case_0004"]["rows"]:
        lines.append(
            f"| `{row['scenario']}` | `{row['entry_guard']}` | `{row['iVar6_right']}` | "
            f"`{row['iVar5_down']}` | `{row['class_prev_byte']}` | `{row['emit_guard']}` | `{row['vcount']}` |"
        )
    lines.extend(["", "### case_0004 Reading", ""])
    for item in report["case_0004"]["reading"]:
        lines.append(f"- {item}")

    result_0012 = report["case_0012"]["result"]
    lines.extend(
        [
            "",
            "## case_0012",
            "",
            f"- Witness: `{tuple(report['case_0012']['witness'])}`",
            f"- Reference RGBA8: `{report['case_0012']['reference_rgba8']}`",
            f"- Local candidate RGBA8: `{report['case_0012']['local_candidate_rgba8']}`",
            f"- Desc: `{result_0012['desc']}`",
            f"- e170 bitsum c: `{result_0012['e170_c']}`",
            f"- f270 scale input: `{result_0012['f270_scale_input']}`",
            f"- f270 append count: `{result_0012['f270']['count']}`",
            f"- e3a0 with-source append count: `{result_0012['e3a0_with_src']['count']}`",
            "",
            "### case_0012 Reading",
            "",
        ]
    )
    for item in report["case_0012"]["reading"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Next Allowed Actions", ""])
    for item in report["next_allowed_actions"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden", ""])
    for item in report["forbidden_actions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    report = build_report()
    output_json = args.output_json or ROOT / "refs/conformance" / f"olmsmoother2_producer_branch_table_{args.stamp}.json"
    output_md = args.output_md or ROOT / "refs/conformance" / f"olmsmoother2_producer_branch_table_{args.stamp}.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    output_md.write_text(render_md(report), encoding="utf-8")
    print(f"wrote {output_json}")
    print(f"wrote {output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
