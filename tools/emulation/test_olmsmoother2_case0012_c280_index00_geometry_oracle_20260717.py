#!/usr/bin/env python3
"""Independent geometry oracle for c280 classifier index 0x00."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader  # noqa: E402
from test_olmsmoother2_case0012_ada0_matrix_oracle_20260717 import ADA0, EXPECTED_AEX_SHA256, descriptors, fixture  # noqa: E402
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import SerialVcomp  # noqa: E402
from test_smoother2_fullchain_diff import call_c280_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

WIDTH = HEIGHT = 16
X = Y = 8
RAW = 0
GATE = 0
MULTIPLIER = 0.0
STEP = 0.125
SMOOTHNESS_FIXED = 65536
DAT_100 = 100.0
DAT_OUTER = 0.4
DAT_INNER = 0.2
ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return struct.pack("<f", value).hex()


def ground_helpers() -> dict[str, Any]:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    helper_map = {
        "FUN_1800134c0": ("0x1800134c0", ["FUN_1800104d0(param_1,&local_res8,fVar2)", "local_res8 = (int)param_1[6] + -1", "local_resc = *(int *)((longlong)param_1 + 0x34) + -1"]),
        "FUN_180013570": ("0x180013570", ["FUN_1800104d0(param_1,&local_res8,fVar2)", "local_resc = *(int *)((longlong)param_1 + 0x34) + -1", "local_res8 = (int)param_1[6] + 1"]),
        "FUN_180012ce0": ("0x180012ce0", ["FUN_1800104d0(param_1,&local_res8,fVar2)", "local_resc = *(int *)((longlong)param_1 + 0x34) + 1", "local_res8 = (int)param_1[6] + 1"]),
        "FUN_180012c20": ("0x180012c20", ["FUN_1800104d0(param_1,&local_res8,fVar2)", "local_resc = *(int *)((longlong)param_1 + 0x34) + 1", "local_res8 = (int)param_1[6] + -1"]),
    }
    for name, (address, anchors) in helper_map.items():
        require(f"// === {name}" in decomp, f"missing decomp owner {name}@{address}")
        for anchor in anchors:
            require(anchor in decomp, f"ambiguous {name}@{address}: missing {anchor}")
    append_anchors = [
        "// === FUN_1800104d0",
        "if (uVar2 < 0xc)",
        "puVar1 = (undefined8 *)((longlong)param_1 + uVar2 * 0x14 + 0x40)",
        "*(undefined4 *)((longlong)param_1 + uVar2 * 0x14 + 0x50) = param_3",
        "((longlong)param_2[1] * (longlong)(int)param_1[2] + (longlong)*param_2 * 0x10 + *param_1)",
    ]
    for anchor in append_anchors:
        require(anchor in decomp, f"ambiguous append owner FUN_1800104d0@0x1800104d0: missing {anchor}")
    c280_start = decomp.find("// === FUN_18000c280")
    c280_end = decomp.find("// === FUN_18000cc70", c280_start)
    require(c280_start >= 0 and c280_end > c280_start, "c280 decomp section bounds are ambiguous")
    c280 = decomp[c280_start:c280_end]
    case_zero = c280[c280.find("switch("):c280.find("case 1:", c280.find("switch("))]
    required_order = ["FUN_1800134c0(&local_188,DAT_180022dd4)", "FUN_180013570(&local_188,fVar1)", "FUN_180012ce0(&local_188,fVar1)", "FUN_180012c20(&local_188,fVar1)"]
    positions = [case_zero.find(item) for item in required_order]
    require(all(position >= 0 for position in positions) and positions == sorted(positions), "classifier 0x00 helper order is ambiguous")
    return {"classifier": "0x00", "helpers": {name: address for name, (address, _anchors) in helper_map.items()}, "append": "FUN_1800104d0@0x1800104d0", "order": required_order}


def portable_vertices(source: list[list[tuple[float, float, float, float]]]) -> list[dict[str, Any]]:
    smoothness = f32(SMOOTHNESS_FIXED / DAT_100)
    outer = f32(f32(f32(STEP) * smoothness) * f32(DAT_OUTER))
    inner = f32(f32(f32(STEP) * smoothness) * f32(DAT_INNER))
    points = [
        (X - 1, Y, outer), (X - 1, Y - 1, inner), (X, Y - 1, outer),
        (X, Y - 1, outer), (X + 1, Y - 1, inner), (X + 1, Y, outer),
        (X, Y + 1, outer), (X + 1, Y + 1, inner), (X + 1, Y, outer),
        (X - 1, Y, outer), (X - 1, Y + 1, inner), (X, Y + 1, outer),
    ]
    return [{"rgba": list(source[py][px]), "weight": weight, "point": [px, py]} for px, py, weight in points]


def actual(source: list[list[tuple[float, float, float, float]]]) -> dict[str, Any]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, HEIGHT)
    for y, row in enumerate(source):
        for x, rgba in enumerate(row):
            smoother.set_src_pixel(x, y, rgba)
    loader.write_bytes(smoother.class_base, b"\xA5" * (WIDTH * HEIGHT * 4))
    source_desc, class_desc, rectangle, config = descriptors(loader, smoother, RAW, GATE, MULTIPLIER)
    vcomp = SerialVcomp(loader)
    ada = loader.call_function(ADA0, int_args=[source_desc, class_desc, rectangle, config], max_instructions=5_000_000)
    plane = loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4)
    require(0xA5 not in plane, "class-plane canary survived")
    c280 = call_c280_entry(loader, smoother, X, Y)
    require(vcomp.classifier_entries == WIDTH * HEIGHT, "natural class-plane coverage changed")
    return {"ada_instructions": ada["instructions"], "class_plane_sha256": hashlib.sha256(plane).hexdigest(), "classifier_index": 0, "c280": c280}


def compare(actual_data: dict[str, Any], expected: list[dict[str, Any]]) -> dict[str, Any]:
    actual_vertices = actual_data["c280"]["vertices"]
    require(actual_data["c280"]["count"] == len(expected), f"first count mismatch: actual={actual_data['c280']['count']} portable={len(expected)}")
    require(len(actual_vertices) == len(expected), "c280 returned count exceeds captured vertex capacity")
    for index, (actual_vertex, expected_vertex) in enumerate(zip(actual_vertices, expected)):
        for channel, (actual_value, expected_value) in enumerate(zip(actual_vertex["rgba"], expected_vertex["rgba"])):
            require(bits(actual_value) == bits(expected_value), f"first vertex mismatch at index={index} rgba[{channel}] actual={bits(actual_value)} portable={bits(expected_value)}")
        require(bits(actual_vertex["weight"]) == bits(expected_vertex["weight"]), f"first vertex mismatch at index={index} weight actual={bits(actual_vertex['weight'])} portable={bits(expected_vertex['weight'])}")
    return {"status": "exact", "count_equal": True, "vertices_equal_raw_float_bits": True, "portable_vertices": expected}


def render(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OLMSmoother2 case0012 c280 classifier 0x00 geometry oracle",
        "",
        "## Verdict",
        "",
        f"`{report['verdict']}`",
        "",
        "The first non-empty fixture is grounded as four corner helpers in exact call order, each using the exact append owner and source address formula.",
        "",
        f"- c280 count: `{report['comparison']['portable_count']}`.",
        "- Raw float bits for all RGBA channels and weights: exact.",
        "- Helper order: `0x1800134c0 -> 0x180013570 -> 0x180012ce0 -> 0x180012c20`.",
        "- Append owner: `FUN_1800104d0@0x1800104d0`, vertex stride `0x14`, weight at `+0x10`.",
        "",
        "No production source, ledger, Windows/AE, or ungrounded non-0x00 geometry claim is made.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding = ground_helpers()
    source = fixture()
    expected = portable_vertices(source)
    actual_data = actual(source)
    comparison = compare(actual_data, expected)
    comparison["portable_count"] = len(expected)
    report = {"verdict": "PASS_EXACT_C280_INDEX00_INDEPENDENT_GEOMETRY_ORACLE", "scope": "first non-empty natural case raw=0 gate=0 multiplier=0.0; actual AEX class generation plus c280 geometry", "grounding": grounding, "fixture": {"raw": RAW, "gate": GATE, "multiplier": MULTIPLIER, "center": [X, Y], "smoothness_fixed": SMOOTHNESS_FIXED}, "actual": actual_data, "comparison": comparison, "claims_not_made": ["No c280 geometry claim for other classifier indices", "No Windows/AE execution claim", "No production Mac source or ledger edit"]}
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
