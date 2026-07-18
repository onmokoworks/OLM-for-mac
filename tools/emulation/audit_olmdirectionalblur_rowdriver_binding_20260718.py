#!/usr/bin/env python3
"""Bound the actual DirectionalBlur rowdriver-to-helper ABI on one row.

This is a binary witness, not a PNG tuner.  It calls the checked-in Windows
AEX under Unicorn for one real row and verifies the pointer/stack binding that
the decompilation assigns to FUN_1800038d0 and FUN_1800013e0.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
import probe_dblur_case0001_row169_typed_classifier as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_rowdriver_binding_20260718.json"
ROWDRIVER = 0x1800038D0
HELPER = 0x1800013E0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u64(loader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def f32(loader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def main() -> int:
    width, height, rgba = base.load_source(SOURCE)
    loader = base.AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    count = width * height
    source = base.allocate_f32(loader, rgba)
    destination = base.allocate_f32(loader, [0.0] * (count * 4))
    denominator = base.allocate_f32(loader, [0.0] * count)
    alpha = base.allocate_f32(loader, [rgba[i * 4 + 3] for i in range(count)])
    component, max_area = base.build_component_map(loader, width, height, rgba)
    front_strength = 8

    source_slot = loader.bump_alloc(8, align=8)
    destination_slot = loader.bump_alloc(8, align=8)
    loader.write_bytes(source_slot, struct.pack("<Q", source))
    loader.write_bytes(destination_slot, struct.pack("<Q", destination))
    context = loader.bump_alloc(0x8200, align=16)
    loader.write_bytes(context, b"\x00" * 0x8200)
    for offset, value in ((0x20, 0), (0x30, 1.0), (0x38, max_area or 1.0),
                          (0x40, 1.0), (0x44, 1.0), (0x48, front_strength),
                          (0x4C, front_strength), (0x50, 0), (0x54, 0)):
        blob = struct.pack("<I", value) if isinstance(value, int) else struct.pack("<f", value)
        loader.write_bytes(context + offset, blob)
    table = context + 0x58
    back_table = context + 0x4068
    loader.write_bytes(table, struct.pack("<32f", *([1.0] * 32)))
    loader.write_bytes(back_table, struct.pack("<32f", *([1.0] * 32)))
    for offset, value in ((0x8080, denominator), (0x8088, alpha), (0x8118, component)):
        loader.write_bytes(context + offset, struct.pack("<Q", value))

    rowdriver_entry: dict = {}
    helper_calls: list[dict] = []

    def on_rowdriver(ld, _address, _size):
        if rowdriver_entry:
            return
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        source_slot_seen = ld.uc.reg_read(UC_X86_REG_R8)
        destination_slot_seen = ld.uc.reg_read(UC_X86_REG_R9)
        rowdriver_entry.update({
            "row_start": ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF,
            "row_end": ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF,
            "source_slot": hex(source_slot_seen),
            "destination_slot": hex(destination_slot_seen),
            "source": hex(u64(ld, source_slot_seen)),
            "destination": hex(u64(ld, destination_slot_seen)),
            "width": struct.unpack("<I", ld.read_bytes(rsp + 0x28, 4))[0],
            "params": hex(u64(ld, rsp + 0x38)),
        })

    def on_helper(ld, _address, _size):
        if len(helper_calls) >= 16:
            return
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        source_x = ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF
        row_base = ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF
        direction = ld.uc.reg_read(UC_X86_REG_R8) & 0xFF
        source_ptr = ld.uc.reg_read(UC_X86_REG_R9)
        # The helper is entered after the CALL pushed its return address.
        # Therefore its seventh argument is at entry RSP+0x28, not +0x20.
        destination_ptr = u64(ld, rsp + 0x28)
        denom_ptr = u64(ld, rsp + 0x30)
        alpha_ptr = u64(ld, rsp + 0x38)
        table_ptr = u64(ld, rsp + 0x40)
        strength = struct.unpack("<i", ld.read_bytes(rsp + 0x48, 4))[0]
        row_width = struct.unpack("<i", ld.read_bytes(rsp + 0x50, 4))[0]
        coeff = f32(ld, rsp + 0x58)
        cell = row_base + source_x
        helper_calls.append({
            "source_x": source_x, "row_base": row_base, "direction": direction,
            "source": hex(source_ptr), "destination": hex(destination_ptr),
            "denominator": hex(denom_ptr), "alpha_or_valid": hex(alpha_ptr),
            "table": hex(table_ptr), "strength": strength, "width": row_width,
            "coefficient": coeff,
            "source_rgba": list(struct.unpack("<4f", ld.read_bytes(source_ptr + cell * 16, 16))),
            "source_alpha_or_valid": f32(ld, alpha_ptr + cell * 4),
        })

    loader.add_code_hook(ROWDRIVER, on_rowdriver)
    loader.add_code_hook(HELPER, on_helper)
    loader.call_function(ROWDRIVER, int_args=[base.ROW, base.ROW + 1, source_slot,
                                               destination_slot, width, 0, context],
                         max_instructions=0)

    errors: list[str] = []
    if rowdriver_entry.get("source") != hex(source):
        errors.append("rowdriver source slot does not resolve to A")
    if rowdriver_entry.get("destination") != hex(destination):
        errors.append("rowdriver destination slot does not resolve to B")
    if rowdriver_entry.get("width") != width:
        errors.append("rowdriver width binding mismatch")
    for call in helper_calls:
        expected = {
            "source": hex(source), "destination": hex(destination),
            "denominator": hex(denominator), "alpha_or_valid": hex(alpha),
            "width": width,
        }
        for key, value in expected.items():
            if call.get(key) != value:
                errors.append(f"helper {key} binding mismatch")
        expected_table = table if call["direction"] == 1 else back_table
        expected_strength = front_strength if call["direction"] == 1 else 0
        if call["direction"] not in (0, 1):
            errors.append("helper direction is neither front nor back")
        if call["table"] != hex(expected_table):
            errors.append("helper direction-selected table mismatch")
        if call["strength"] != expected_strength:
            errors.append("helper direction-selected strength mismatch")
    if not helper_calls:
        errors.append("no actual FUN_1800013E0 call observed")

    result = {
        "schema": 1,
        "kind": "olmdirectionalblur_rowdriver_binding_actual_aex_20260718",
        "status": "pass" if not errors else "blocked",
        "scope": "Mac-local Unicorn direct actual-AEX one-row PF8 rowdriver/helper binding",
        "claim_scope": "Binary ABI and buffer ownership only; no Windows live values, PNG tuning, or AE-exact claim",
        "provenance": {"aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX),
                       "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha256(SOURCE)},
        "rowdriver_entry": rowdriver_entry,
        "helper_entries": helper_calls,
        "invariants": {
            "source_A": hex(source), "destination_B": hex(destination),
            "denominator": hex(denominator), "alpha_or_valid": hex(alpha),
            "front_table": hex(table), "back_table": hex(back_table), "front_direction": 1,
            "decomp_stack_contract": "callee entry [RSP+28]=B, +30=denom, +38=alpha_or_valid, +40=table, +48=strength, +50=width, +58=coeff",
        },
        "next_unresolved_boundary": {
            "status": "blocked",
            "boundary": "natural worker scheduling and its real rowdriver parameter values",
            "reason": "the bounded natural fixture exits through rotate/output without entering 0x1800038d0; this direct call proves the binary ABI but not natural dispatch",
            "required_future_evidence": "one Windows or successfully continued natural-AEX run capturing rowdriver entry plus helper values for case_0001 angle=0",
        },
        "fail_closed": {"production_source_edited": False, "ledger_edited": False,
                        "windows_values_fabricated": False, "png_tuned": False,
                        "ae_exact_claim": False},
        "errors": errors,
        "command": "python3 tools/emulation/audit_olmdirectionalblur_rowdriver_binding_20260718.py",
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "report": str(REPORT.relative_to(ROOT)),
                      "helper_calls": len(helper_calls), "errors": errors}))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
