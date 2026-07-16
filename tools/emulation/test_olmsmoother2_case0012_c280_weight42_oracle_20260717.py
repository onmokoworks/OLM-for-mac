#!/usr/bin/env python3
"""Bit-precise FUN_180013630 oracle for c280 classifier 0x42."""

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
from test_olmsmoother2_case0012_c280_cce0_polygon_gate_20260717 import classifier_index  # noqa: E402
from test_smoother2_fullchain_diff import call_c280_entry  # noqa: E402
from test_smoother2_producer import AEX_PATH, FUN_180013630, SmootherStruct  # noqa: E402
from unicorn.x86_const import UC_X86_REG_RDX  # noqa: E402

WIDTH = HEIGHT = 16
CENTER = (8, 8)
MATRIX_ORDER = [(raw, gate, multiplier) for raw in (200, 100, 10, 0, 1) for gate in (0, 1) for multiplier in (0.0, 1.0, 2.0)]
ASM = ROOT / "disasm/OLMSmoother2.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMSmoother2.aex.c.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL CLOSED: " + message)


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value: float) -> str:
    return struct.pack("<f", value).hex()


def weight_oracle(p1: float, p2: int, p3: float, one: float, half: float) -> float:
    """FUN_180013630 with an explicit f32 round after every scalar instruction."""
    p1, p3, one, half = map(f32, (p1, p3, one, half))
    if p1 == 0.0 or not f32(float(p2)) < p1 or p3 == 0.0:
        return f32(0.0)
    f1 = f32(float(p2))
    ratio = f32(f1 / p1)
    f2 = f32(f32(one - ratio) * p3)
    if p1 < f32(f1 + one):
        return f32(f32(f32(p1 - f1) * f2) * half)
    fnext = f32(f1 + one)
    fnext = f32(fnext / p1)
    return f32(f32(f32(one - fnext) * p3 + f2) * half)


def ground_weight() -> dict[str, Any]:
    aex_hash = hashlib.sha256(AEX_PATH.read_bytes()).hexdigest()
    require(aex_hash == EXPECTED_AEX_SHA256, "AEX hash drift")
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    asm_start = asm.find("; === FUN_180013630")
    asm_end = asm.find("; ===", asm_start + 8)
    asm_leaf = asm[asm_start:asm_end if asm_end >= 0 else None]
    decomp_start = decomp.find("// === FUN_180013630")
    decomp_end = decomp.find("// ===", decomp_start + 8)
    decomp_leaf = decomp[decomp_start:decomp_end if decomp_end >= 0 else None]
    for anchor in ("UCOMISS XMM1,XMM3", "DIVSS XMM0,XMM1", "MULSS XMM5,XMM7", "MULSS XMM2,dword ptr [0x180022694]"):
        require(anchor in asm_leaf, f"missing AEX weight instruction {anchor}")
    for anchor in ("if (((param_1 != 0.0)", "fVar2 = (DAT_1800226a0 - fVar1 / param_1)", "return (param_1 - fVar1) * fVar2 * DAT_180022694", "return ((DAT_1800226a0 - fVar1) * param_3"):
        require(anchor in decomp_leaf, f"missing decomp weight semantic {anchor}")
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    one = struct.unpack("<f", loader.read_bytes(0x1800226A0, 4))[0]
    half = struct.unpack("<f", loader.read_bytes(0x180022694, 4))[0]
    require(bits(one) == "0000803f" and bits(half) == "0000003f", "weight constants changed")
    return {"aex_sha256": aex_hash, "aex_owner": "FUN_180013630@0x180013630", "one": one, "half": half, "rounding": "SSE scalar single precision after each arithmetic instruction"}


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
    ada = loader.call_function(ADA0, int_args=[source_desc, class_desc, rectangle, config], max_instructions=5_000_000)
    plane = loader.read_bytes(smoother.class_base, WIDTH * HEIGHT * 4)
    require(0xA5 not in plane and set(plane).issubset({0, 255}), "invalid class plane")
    require(vcomp.worker_entries == 1 and vcomp.classifier_entries == WIDTH * HEIGHT, "natural coverage changed")
    calls: list[dict[str, Any]] = []

    def capture(ld: AexLoader, _address: int, _size: int) -> None:
        calls.append({"p1": ld.read_xmm_f32(0), "p2": ld.uc.reg_read(UC_X86_REG_RDX), "p3": ld.read_xmm_f32(2)})

    loader.add_code_hook(FUN_180013630, capture)
    c280 = call_c280_entry(loader, smoother, *CENTER)
    index = classifier_index(plane)
    return {"raw": raw, "gate": gate, "multiplier": multiplier, "ada_instructions": ada["instructions"], "classifier_index": index, "class_plane_sha256": hashlib.sha256(plane).hexdigest(), "weight_calls": calls, "c280": c280}


def compare_42(row: dict[str, Any], source: list[list[tuple[float, float, float, float]]], one: float, half: float) -> dict[str, Any]:
    require(len(row["weight_calls"]) == row["c280"]["count"] == 2, "0x42 did not produce two traced weights")
    actual_vertices = row["c280"]["vertices"]
    comparisons = []
    for i, (call, vertex) in enumerate(zip(row["weight_calls"], actual_vertices)):
        expected = weight_oracle(call["p1"], int(call["p2"] & 0xFFFFFFFF), call["p3"], one, half)
        require(bits(expected) == bits(vertex["weight"]), f"0x42 weight mismatch at vertex {i}")
        expected_rgba = source[0][8]
        require(all(bits(got) == bits(want) for got, want in zip(vertex["rgba"], expected_rgba)), f"0x42 RGBA mismatch at vertex {i}")
        comparisons.append({"index": i, "inputs": call, "expected_rgba": list(expected_rgba), "actual_rgba": vertex["rgba"], "expected_weight": expected, "expected_weight_bits": bits(expected), "actual_weight_bits": bits(vertex["weight"]), "rgba_raw_float_bits": True})
    return {"status": "exact", "count": 2, "vertices": comparisons, "raw_weights_equal": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    grounding = ground_weight()
    source = fixture()
    actual_42 = []
    for raw, gate, multiplier in MATRIX_ORDER:
        row = actual_case(source, raw, gate, multiplier)
        if row["classifier_index"] == 0x42:
            actual_42.append(row)
    require(len(actual_42) == 2, f"expected two 0x42 cases, found {len(actual_42)}")
    checks = [compare_42(row, source, grounding["one"], grounding["half"]) for row in actual_42]
    require(all(item["status"] == "exact" for item in checks), "0x42 did not close")
    report = {
        "verdict": "PASS_EXACT_C280_0X42_WEIGHT_ORACLE_STOPPED_AT_0X5A_OWNER",
        "scope": "fresh actual AEX c280 for all 30 fixtures; independent bit-precise FUN_180013630 comparison for both 0x42 cases",
        "grounding": grounding,
        "cases_0x42": actual_42,
        "comparisons_0x42": checks,
        "next_family": {"classifier_index": "0x5a", "attempted": True, "status": "stopped_first_new_owner", "owner": "FUN_18000ec40@0x18000ec40", "reason": "The 0x5a cardinal family reaches a new leaf/predicate composition not independently grounded in this follow-up; no empty geometry or weight equivalence is guessed."},
        "claims_not_made": ["No portable 0x5a c280 equivalence", "No Windows/AE execution claim", "No production Mac source or ledger edit"],
    }
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.write_text("\n".join(["# OLMSmoother2 case0012 c280 0x42 weight oracle", "", "## Verdict", "", f"`{report['verdict']}`", "", "Both naturally generated `0x42` fixtures matched c280 polygon count, vertices' RGBA, and raw IEEE-754 weights using live AEX weight-call inputs.", "", "`0x5a` was attempted only after `0x42` closed, then stopped at `FUN_18000ec40@0x18000ec40`, the first new ungrounded owner.", "", "No production source or ledger was edited.", ""]) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
