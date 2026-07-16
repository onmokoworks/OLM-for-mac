#!/usr/bin/env python3
"""Feed the natural class-plane matrix into actual c280/cce0.

Only the empty-polygon/default-dispatch branch is portable-grounded here.
The first non-empty dispatch index stops the portable comparison closed.
"""

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
from test_olmsmoother2_case0012_ada0_matrix_oracle_20260717 import (  # noqa: E402
    ADA0,
    EXPECTED_AEX_SHA256,
    fixture,
    descriptors,
)
from test_olmsmoother2_case0012_classplane_natural_caller_20260717 import SerialVcomp  # noqa: E402
from test_smoother2_fullchain_diff import call_c280_entry, call_cce0_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, SmootherStruct  # noqa: E402

WIDTH = HEIGHT = 16
CENTER = (8, 8)
MATRIX_ORDER = [(raw, gate, multiplier) for raw in (200, 100, 10, 0, 1) for gate in (0, 1) for multiplier in (0.0, 1.0, 2.0)]
ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def classifier_index(plane: bytes, x: int = CENTER[0], y: int = CENTER[1]) -> int:
    def cb(xx: int, yy: int, channel: int) -> int:
        if xx < 0 or xx >= WIDTH or yy < 0 or yy >= HEIGHT:
            return 0
        return plane[(yy * WIDTH + xx) * 4 + channel]

    c_a, c_r, c_g, c_b = (cb(x, y, channel) for channel in range(4))
    east_zero = 1 if x >= WIDTH - 1 or cb(x + 1, y, 0) == 0 else 0
    sw = cb(x - 1, y + 1, 3) != 0 if x > 0 and y < HEIGHT - 1 else False
    south = cb(x, y + 1, 1) != 0 if y < HEIGHT - 1 else False
    southeast_zero = 1 if y >= HEIGHT - 1 or cb(x + 1, y + 1, 2) == 0 else 0
    return ((0 if sw else 2) + east_zero + (((0 if south else 1) + southeast_zero * 2) * 4)) * 0x10 + (4 if c_b == 0 else 0) + (1 if c_g == 0 else 0) + (2 if c_r == 0 else 0) + (8 if c_a == 0 else 0)


def actual_case(source: list[list[tuple[float, float, float, float]]], raw: int, gate: int, multiplier: float) -> dict[str, Any]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    smoother = SmootherStruct(loader, WIDTH, HEIGHT)
    for y, row in enumerate(source):
        for x, rgba in enumerate(row):
            smoother.set_src_pixel(x, y, rgba)
    loader.write_bytes(smoother.class_base, b"\xA5" * (WIDTH * HEIGHT * 4))
    source_desc, class_desc, rectangle, config = descriptors(loader, smoother, raw, gate, multiplier)
    vcomp = SerialVcomp(loader)
    ada_result = loader.call_function(ADA0, int_args=[source_desc, class_desc, rectangle, config], max_instructions=5_000_000)
    plane = loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4)
    require(0xA5 not in plane, f"class-plane canary survived raw={raw} gate={gate} multiplier={multiplier}")
    require(set(plane).issubset({0, 255}), "natural class plane is not boolean")
    require(vcomp.worker_entries == 1 and vcomp.classifier_entries == WIDTH * HEIGHT, "natural coverage changed")
    c280 = call_c280_entry(loader, smoother, *CENTER)
    cce0 = call_cce0_entry(loader, smoother, *CENTER)
    return {
        "raw": raw,
        "gate": gate,
        "multiplier": multiplier,
        "ada_instructions": ada_result["instructions"],
        "classifier_index": classifier_index(plane),
        "class_plane_sha256": hashlib.sha256(plane).hexdigest(),
        "c280": {"count": c280["count"], "vertices": c280["vertices"]},
        "cce0": {"rgba": cce0["rgba"]},
    }


def grounding() -> None:
    require(hashlib.sha256(AEX_PATH.read_bytes()).hexdigest() == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    require("; === FUN_18000c280" in asm and "; === FUN_18000cce0" in asm, "c280/cce0 assembly owners missing")
    require("switch((iVar3 + uVar9" in decomp and "*param_1 = local_148" in decomp, "c280 switch/output owner missing")
    require("FUN_18000c280(local_148" in decomp and "if (local_58 != 0)" in decomp, "cce0 count-gated owner missing")
    require("case 0xff" not in decomp.lower(), "0xff gained an explicit switch case; portable default proof needs review")


def portable_empty_oracle(row: dict[str, Any], source: list[list[tuple[float, float, float, float]]]) -> dict[str, Any]:
    require(row["classifier_index"] == 0xFF, "empty oracle called for non-default dispatch")
    center = list(source[CENTER[1]][CENTER[0]])
    require(row["c280"]["count"] == 0 and row["c280"]["vertices"] == [], "default c280 branch was not empty")
    require(row["cce0"]["rgba"] == center, "zero-count cce0 did not return the center sample")
    return {"status": "exact", "portable_count": 0, "portable_vertices": [], "portable_cce0_rgba": center}


def render(report: dict[str, Any]) -> str:
    lines = ["# OLMSmoother2 case0012 c280/cce0 polygon contract gate", "", "## Verdict", "", f"`{report['verdict']}`", "", f"Actual c280/cce0 consumed all `{len(report['actual_cases'])}` naturally generated class planes.", ""]
    exact = [row for row in report["portable_checks"] if row["status"] == "exact"]
    lines.append(f"Portable exact subset: `{len(exact)}` default-dispatch (`0xff`) cases.")
    lines.append("")
    missing = report.get("first_missing_semantic")
    if missing:
        lines += ["## Closed Boundary", "", f"Stopped at `{missing['case']}`: {missing['reason']}", "", "No portable geometry was guessed for the non-empty helper dispatch."]
    lines += ["", "No Windows/AE, production, or ledger claim is made.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding()
    source = fixture()
    actual = [actual_case(source, raw, gate, multiplier) for raw, gate, multiplier in MATRIX_ORDER]
    checks = []
    first_missing = None
    for row in actual:
        if first_missing is not None:
            checks.append({"raw": row["raw"], "gate": row["gate"], "multiplier": row["multiplier"], "classifier_index": row["classifier_index"], "status": "not_evaluated_after_first_missing_semantic"})
            continue
        if row["classifier_index"] != 0xFF:
            first_missing = {
                "case": {"raw": row["raw"], "gate": row["gate"], "multiplier": row["multiplier"], "classifier_index": row["classifier_index"]},
                "reason": f"FUN_18000c280 dispatch index 0x{row['classifier_index']:02x} is non-empty, but its helper composition and vertex geometry are not independently grounded for this portable oracle.",
                "owner": "FUN_18000c280 switch case plus helper chain",
            }
            checks.append({"raw": row["raw"], "gate": row["gate"], "multiplier": row["multiplier"], "classifier_index": row["classifier_index"], "status": "stopped_first_missing_semantic"})
            continue
        checks.append({"raw": row["raw"], "gate": row["gate"], "multiplier": row["multiplier"], "classifier_index": row["classifier_index"], **portable_empty_oracle(row, source)})
    report = {
        "verdict": "PASS_ACTUAL_C280_CCE0_WITH_FAIL_CLOSED_PORTABLE_POLYGON_BOUNDARY" if first_missing else "PASS_EXACT_PORTABLE_POLYGON_MATRIX",
        "scope": "actual AEX c280/cce0 over all 30 natural class planes; portable comparison only for grounded default dispatch",
        "actual_cases": actual,
        "portable_checks": checks,
        "first_missing_semantic": first_missing,
        "claims_not_made": ["No portable geometry claim for non-empty dispatch", "No Windows/AE execution claim", "No production Mac source or ledger edit"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text(render(report), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
