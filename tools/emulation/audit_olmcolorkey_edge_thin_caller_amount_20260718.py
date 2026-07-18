#!/usr/bin/env python3
"""Prove the OLMColorKey Edge Thin caller amount contract from the actual AEX."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_R14,
    UC_X86_REG_RBP,
    UC_X86_REG_RSI,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader, STACK_BASE, STACK_SIZE  # noqa: E402

AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"
AEX_SHA256 = "9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"
ASM = ROOT / "disasm/OLMColorKey.aex.asm.txt"
SOURCE = ROOT / "mac/OLMColorKey/OLMColorKey.cpp"
HEADER = ROOT / "mac/OLMColorKey/OLMColorKey.h"

AMOUNT_CONVERT = 0x1800091DF
POSITIVE_BRANCH = 0x1800091F7
NONPOSITIVE_BRANCH = 0x1800092D3
POSITIVE_COMPARE = 0x180009237
POSITIVE_COPY = 0x18000924C
POSITIVE_NO_COPY = 0x1800092B7
NEGATIVE_COMPARE = 0x180009317
NEGATIVE_ZERO = 0x180009332
NEGATIVE_KEEP = 0x180009335
DISTANCE_DISPATCH = 0x180009181
DISTANCE_TARGETS = {
    1: (0x1800066F0, "type1"),
    2: (0x1800058A0, "type2"),
    3: (0x180007CA0, "type3"),
}

AMOUNTS = (-4000, -2, -1, 0, 1, 2, 4000)
DISTANCE_TYPES = (1, 2, 3)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def loader() -> AexLoader:
    return AexLoader(str(AEX), verbose=False, fast=True)


def stop_at(ld: AexLoader, addresses: dict[int, str], hit: list[str]) -> None:
    for address, label in addresses.items():
        def hook(current: AexLoader, _address: int, _size: int, name: str = label) -> None:
            hit.append(name)
            current.uc.emu_stop()
        ld.add_code_hook(address, hook)


def convert_amount(amount: int) -> dict[str, object]:
    ld = loader()
    record = ld.host_alloc(0x60)
    ld.write_bytes(record, b"\0" * 0x60)
    ld.write_bytes(record + 0x28, struct.pack("<i", amount))
    ld.uc.reg_write(UC_X86_REG_R14, record)
    ld.uc.reg_write(UC_X86_REG_RBP, STACK_BASE + STACK_SIZE - 0x400)
    ld.uc.reg_write(UC_X86_REG_RSP, STACK_BASE + STACK_SIZE - 0x800)
    ld.write_xmm_f32(9, 0.0)
    hit: list[str] = []
    stop_at(ld, {POSITIVE_BRANCH: "positive", NONPOSITIVE_BRANCH: "nonpositive"}, hit)
    ld.uc.emu_start(AMOUNT_CONVERT, 0x18000934C, count=100)
    converted = ld.read_xmm_f32(6)
    expected_branch = "positive" if amount > 0 else "nonpositive"
    if converted != float(amount) or hit != [expected_branch]:
        raise RuntimeError(f"fail-closed amount conversion: {amount=} {converted=} {hit=}")
    return {
        "record_int32": amount,
        "xmm6_float32": converted,
        "branch": hit[0],
        "exact_int32_to_float32": converted == float(amount),
    }


def positive_compare(amount: int, distance: float) -> str:
    ld = loader()
    rsp = STACK_BASE + STACK_SIZE - 0x800
    source = ld.host_alloc(2)
    distance_ptr = ld.host_alloc(4)
    ld.write_bytes(source, struct.pack("<H", 0))
    ld.write_bytes(distance_ptr, struct.pack("<f", distance))
    ld.write_bytes(rsp + 0x58, struct.pack("<Q", source))
    ld.write_bytes(rsp + 0x60, struct.pack("<Q", distance_ptr))
    ld.uc.reg_write(UC_X86_REG_RSP, rsp)
    ld.write_xmm_f32(6, float(amount))
    hit: list[str] = []
    stop_at(ld, {POSITIVE_COPY: "copy", POSITIVE_NO_COPY: "no_copy"}, hit)
    ld.uc.emu_start(POSITIVE_COMPARE, 0x1800092C7, count=30)
    expected = "copy" if distance <= amount else "no_copy"
    if hit != [expected]:
        raise RuntimeError(f"fail-closed positive compare: {amount=} {distance=} {hit=}")
    return hit[0]


def dispatch_distance_type(distance_type: int) -> str:
    ld = loader()
    record = ld.host_alloc(0x60)
    ld.write_bytes(record, b"\0" * 0x60)
    ld.write_bytes(record + 0x2C, struct.pack("<i", distance_type))
    ld.uc.reg_write(UC_X86_REG_R14, record)
    ld.uc.reg_write(UC_X86_REG_RSP, STACK_BASE + STACK_SIZE - 0x800)
    ld.uc.reg_write(UC_X86_REG_RBP, STACK_BASE + STACK_SIZE - 0x400)
    ld.write_xmm_f32(8, 4000.0)
    hit: list[str] = []
    stop_at(ld, {address: label for address, label in DISTANCE_TARGETS.values()}, hit)
    ld.uc.emu_start(DISTANCE_DISPATCH, 0x1800091D8, count=50)
    expected = DISTANCE_TARGETS[distance_type][1]
    if hit != [expected]:
        raise RuntimeError(f"fail-closed distance dispatch: {distance_type=} {hit=}")
    return hit[0]


def negative_compare(amount: int, distance: float) -> str:
    ld = loader()
    rsp = STACK_BASE + STACK_SIZE - 0x800
    matte = ld.host_alloc(2)
    distance_ptr = ld.host_alloc(4)
    ld.write_bytes(matte, struct.pack("<H", 1))
    ld.write_bytes(distance_ptr, struct.pack("<f", distance))
    ld.write_bytes(rsp + 0x60, struct.pack("<Q", matte))
    ld.write_bytes(rsp + 0x40, struct.pack("<Q", distance_ptr))
    ld.uc.reg_write(UC_X86_REG_RSP, rsp)
    ld.uc.reg_write(UC_X86_REG_RSI, 0)
    ld.write_xmm_f32(6, float(amount))
    ld.write_xmm_f32(7, -0.0)  # XORPS sign mask loaded from 0x18001f770.
    hit: list[str] = []
    stop_at(ld, {NEGATIVE_ZERO: "zero", NEGATIVE_KEEP: "keep"}, hit)
    ld.uc.emu_start(NEGATIVE_COMPARE, 0x180009341, count=30)
    expected = "zero" if distance < abs(amount) else "keep"
    if hit != [expected]:
        raise RuntimeError(f"fail-closed negative compare: {amount=} {distance=} {hit=}")
    return hit[0]


def static_contract() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    required = {
        "edge_thin_loader_uses_int_accessor": "18000a438  CALL 0x18000dcd0",
        "int_accessor_reads_dword": "180013b00  MOV EAX,dword ptr [RCX + 0x38]",
        "edge_blur_loader_uses_float_accessor": "18000a462  CALL 0x18000de90",
        "caller_loads_edge_thin_int": "1800091df  MOVD XMM6,dword ptr [R14 + 0x28]",
        "caller_converts_edge_thin_once": "1800091e5  CVTDQ2PS XMM6,XMM6",
        "edge_blur_amount_is_separate": "180009414  MOVSS XMM1,dword ptr [R14 + 0x40]",
    }
    checks = {name: text in asm for name, text in required.items()}
    if not all(checks.values()):
        raise RuntimeError("fail-closed static contract: " + ", ".join(k for k, v in checks.items() if not v))
    return {"checks": checks, "required_instructions": required}


def source_contract() -> dict[str, object]:
    source = SOURCE.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    checks = {
        "integer_slider": "PF_ADD_SLIDER(GetStringPtr(StrID_Amount_Param_Name)" in source,
        "integer_param_reads": source.count("edge_thin_amount = p.u.sd.value") == 1
        and source.count("edge_thin_amount = params[OLMCOLORKEY_EDGE_THIN_AMOUNT]->u.sd.value") == 1,
        "integer_info_field": "A_long edge_thin_amount;" in header,
        "positive_predicate": "dist[i] <= info.edge_thin_amount" in source,
        "negative_translation_remains_explicit": "std::fabs(info.edge_thin_amount)" in source,
    }
    return {"checks": checks, "all_pass": all(checks.values())}


def run() -> dict[str, object]:
    if sha256(AEX) != AEX_SHA256:
        raise RuntimeError("fail-closed pinned AEX hash mismatch")
    static = static_contract()
    conversions = [convert_amount(amount) for amount in AMOUNTS]
    distance_dispatch = [
        {"distance_type": distance_type, "target": dispatch_distance_type(distance_type)}
        for distance_type in DISTANCE_TYPES
    ]
    comparisons: list[dict[str, object]] = []
    for distance_type in DISTANCE_TYPES:
        for amount in AMOUNTS:
            if amount > 0:
                for distance in (float(amount - 1), float(amount), float(amount + 1)):
                    comparisons.append({
                        "distance_type": distance_type,
                        "amount": amount,
                        "distance": distance,
                        "path": "positive",
                        "result": positive_compare(amount, distance),
                        "oracle": "copy iff distance <= amount",
                    })
            elif amount < 0:
                magnitude = abs(amount)
                for distance in (float(magnitude - 1), float(magnitude), float(magnitude + 1)):
                    comparisons.append({
                        "distance_type": distance_type,
                        "amount": amount,
                        "distance": distance,
                        "path": "negative",
                        "result": negative_compare(amount, distance),
                        "oracle": "zero iff distance < abs(amount); equality keeps",
                    })
    source = source_contract()
    result = {
        "kind": "olmcolorkey_edge_thin_caller_amount_20260718",
        "schema": 1,
        "status": "pass" if source["all_pass"] else "actual_aex_pass_source_mismatch",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": AEX_SHA256,
            "asm": str(ASM.relative_to(ROOT)),
        },
        "ownership_correction": {
            "edge_thin": "record+0x28 int32, inline caller compare loops",
            "edge_blur": "record+0x40 float32, FUN_180008320 apply leaf",
            "superseded_claim": "FUN_180008320 is not the Edge Thin threshold leaf",
        },
        "normalization_formula": {
            "host_parameter": "signed integer slider in [-4000, 4000]",
            "record": "int32 value copied without scaling",
            "caller": "float32(record_int32) exactly once via CVTDQ2PS",
            "positive": "copy unmatched source iff distance <= amount",
            "negative": "zero matched matte iff distance < abs(amount); equality remains matched",
            "distance_type_effect": "selects the distance primitive only; comparator and amount conversion are identical for types 1/2/3",
        },
        "static_actual_aex": static,
        "distance_dispatch_matrix": distance_dispatch,
        "amount_conversion_matrix": conversions,
        "comparison_matrix": comparisons,
        "matrix_counts": {
            "amounts": len(conversions),
            "comparisons": len(comparisons),
            "distance_types": len(DISTANCE_TYPES),
        },
        "current_source": source,
        "claim_boundary": "Actual-AEX caller arithmetic and branch semantics only. Distance primitive output, AE host rendering, and PNG/EXR export are outside this fixture; no AE exact claim.",
    }
    if result["status"] != "pass":
        raise RuntimeError("fail-closed source contract does not implement the proven parameter boundary")
    return result


def main() -> int:
    result = run()
    output = ROOT / "refs/conformance/olmcolorkey_edge_thin_caller_amount_20260718.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], **result["matrix_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
