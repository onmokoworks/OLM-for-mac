#!/usr/bin/env python3
"""Trace packed-size argument generation, ABI spill, and later stack load.

This is a new evidence runner around the existing natural Mode-2/common-owner
fixture.  The write watch is installed when each AexLoader is constructed, so
the first write can precede the 0x181280e92 load.  No stack value is patched
and the existing FilterEngine stop remains the terminal boundary.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE
from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
    UC_X86_REG_RIP,
    UC_X86_REG_RSI,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_packed_size_first_writer_20260717.json"
MARKDOWN = ROOT / "refs/conformance/olmkirakira_packed_size_first_writer_20260717.md"

sys.path.insert(0, str(ROOT / "tools/emulation"))
common = importlib.import_module("test_olmkirakira_mode2_common_owner_20260717")

LOAD = 0x181280E92
FUNCTION_ENTRY = 0x181280BC0
PACKED_CALLSITES = (0x18114FA95, 0x18114FAE7, 0x18114FB39, 0x18114FBB1, 0x18115116F, 0x1811511C2, 0x181151215, 0x181151290)
EXPECTED_RAW = 0x0000000180000000
STACK_LO = 0x0F000000
STACK_HI = 0x10000000
OPEN_CV_RANGES = ((0x1812B0000, 0x1812C0000), (0x1811D0000, 0x1811E0000))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_witness() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    lines = asm.splitlines()
    slot_lines = [line for line in lines if "[RSP + 0x1f8]" in line]
    relevant = [line for line in slot_lines if line.startswith(("181280", "181281"))]
    stores = [line for line in relevant if re.search(r"\b(MOV|VMOV|MOVSD|MOVUPS|VMOVUPS)\s+[^,]*\[RSP \+ 0x1f8\]", line)]
    exact_load = next((line for line in lines if line.startswith("181280e92 ")), None)
    arithmetic = [
        line for line in lines
        if line.startswith(("18114fa31 ", "18114fa35 ", "18114fa39 ", "18114fa88 ",
                            "18115110a ", "18115110d ", "181151117 ", "18115111a ", "181151162 "))
    ]
    source_sequences = [
        ["18114fa31  MOV EAX,EDX", "18114fa35  SHL RBX,0x20", "18114fa39  OR RBX,RAX", "18114fa88  MOV R9,RBX"],
        ["18115110a  MOV RDI,RSI", "18115110d  MOV RAX,0x100000000", "181151117  OR RDI,RAX", "181151162  MOV R9,RDI"],
    ]
    return {
        "aex_sha256": sha256(AEX),
        "asm_sha256": sha256(ASM),
        "decomp_sha256": sha256(DECOMP),
        "exact_load": exact_load,
        "relevant_slot_references": relevant,
        "static_store_candidates_in_nearby_functions": stores,
        "decomp_has_boxfilter_entry": "FUN_181280fa0" in decomp and "FUN_181281260" in decomp,
        "load_present": exact_load == "181280e92  MOV R9,qword ptr [RSP + 0x1f8]",
        "aex_packed_arithmetic_sequence": arithmetic,
        "aex_packed_arithmetic_present": any(all(item in arithmetic for item in sequence) for sequence in source_sequences),
        "aex_packed_source_sequences": source_sequences,
    }


def in_image(rip: int) -> bool:
    return 0x180000000 <= rip < 0x182000000


def in_opencv_range(rip: int) -> bool:
    return any(start <= rip < end for start, end in OPEN_CV_RANGES)


def capture_runtime() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    original_init = common.AexLoader.__init__
    original_add_code_hook = common.AexLoader.add_code_hook
    state: dict[str, object] = {"stack_writes": [], "load": [], "packed_calls": [], "loader_count": 0}

    def wrapped_init(loader: object, *args: object, **kwargs: object) -> None:
        original_init(loader, *args, **kwargs)
        state["loader_count"] = int(state["loader_count"]) + 1

        def watch(uc: object, _access: int, address: int, size: int, value: int, _user_data: object) -> None:
            if not STACK_LO <= address < STACK_HI:
                return
            writes = state["stack_writes"]
            assert isinstance(writes, list)
            writes.append({
                "address": hex(address),
                "size": size,
                "value_raw_hex": int(value & ((1 << (size * 8)) - 1)).to_bytes(size, "little").hex(),
                "instruction_rip": hex(uc.reg_read(UC_X86_REG_RIP)),
                "rsp": hex(uc.reg_read(UC_X86_REG_RSP)),
                "registers": {
                    name: hex(uc.reg_read(reg))
                    for name, reg in (("RAX", UC_X86_REG_RAX), ("RBX", UC_X86_REG_RBX),
                                      ("RCX", UC_X86_REG_RCX), ("RDX", UC_X86_REG_RDX),
                                      ("R8", UC_X86_REG_R8), ("R9", UC_X86_REG_R9))
                },
            })

        loader.uc.hook_add(UC_HOOK_MEM_WRITE, watch)

        def at_load(ld: object, _address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            target = rsp + 0x1F8
            loads = state["load"]
            assert isinstance(loads, list)
            raw = ld.read_bytes(target, 8)
            loads.append({
                "rip": hex(LOAD),
                "rsp": hex(rsp),
                "target_address": hex(target),
                "target_offset": "0x1f8",
                "loaded_raw_hex": raw.hex(),
                "loaded_raw_u64": int.from_bytes(raw, "little"),
            })

        original_add_code_hook(loader, LOAD, at_load)

        for callsite in PACKED_CALLSITES:
            def at_packed_call(ld: object, _address: int, _size: int, callsite: int = callsite) -> None:
                calls = state["packed_calls"]
                assert isinstance(calls, list)
                calls.append({
                    "rip": hex(callsite),
                    "r9_raw_hex": f"0x{ld.uc.reg_read(UC_X86_REG_R9):016x}",
                    "rdx_raw_hex": f"0x{ld.uc.reg_read(UC_X86_REG_RDX):016x}",
                    "rax_raw_hex": f"0x{ld.uc.reg_read(UC_X86_REG_RAX):016x}",
                    "rsi_raw_hex": f"0x{ld.uc.reg_read(UC_X86_REG_RSI):016x}",
                    "rsp": hex(ld.uc.reg_read(UC_X86_REG_RSP)),
                })

            original_add_code_hook(loader, callsite, at_packed_call)

    def wrapped_add_code_hook(loader: object, address: int, handler: object) -> None:
        original_add_code_hook(loader, address, handler)

    common.AexLoader.__init__ = wrapped_init
    common.AexLoader.add_code_hook = wrapped_add_code_hook
    try:
        runtime = common.run_owner_probe()
    finally:
        common.AexLoader.__init__ = original_init
        common.AexLoader.add_code_hook = original_add_code_hook

    loads = state["load"]
    writes = state["stack_writes"]
    assert isinstance(loads, list) and isinstance(writes, list)
    selected: list[dict[str, object]] = []
    if loads:
        target = int(loads[-1]["target_address"], 16)
        for event in writes:
            address = int(event["address"], 16)
            size = int(event["size"])
            if address < target + 8 and address + size > target and int(event["instruction_rip"], 16) == FUNCTION_ENTRY:
                selected.append(event)
    spill = selected[0] if selected else None
    return runtime, {"load_events": loads, "target_writes": selected, "abi_argument_spill": spill, "packed_calls": state["packed_calls"]}, state


def classify(spill: dict[str, object] | None, loaded: dict[str, object] | None) -> tuple[str, str]:
    if spill is None or loaded is None:
        return "ambiguous", "No complete argument-spill and load pair was observed; fail-closed."
    raw = int.from_bytes(bytes.fromhex(str(spill["value_raw_hex"])), "little")
    loaded_raw = int(loaded["loaded_raw_u64"])
    rip = int(spill["instruction_rip"], 16)
    if loaded_raw != EXPECTED_RAW or raw != EXPECTED_RAW:
        return "ambiguous", "The observed slot/load words are not the expected packed sentinel; fail-closed."
    if not in_image(rip):
        return "A", "The observed argument spill is outside the checked-in AEX image, consistent with live host/Mat state."
    if in_opencv_range(rip):
        return "C", "The observed argument spill is in the pinned OpenCV/FilterEngine range."
    return "B", "The caller constructs the packed R9 value in checked-in AEX arithmetic and the callee ABI spill/load preserves it."


def main() -> int:
    static = static_witness()
    runtime, trace, _state = capture_runtime()
    load = trace["load_events"][-1] if trace["load_events"] else None
    classification, basis = classify(trace["abi_argument_spill"], load)
    assertion = runtime.get("filter_assertion_capture", {})
    packed_calls = trace["packed_calls"]
    arithmetic_call = next((item for item in packed_calls if int(item["r9_raw_hex"], 16) == EXPECTED_RAW), None)
    gates = {
        "static_load_present": static["load_present"],
        "actual_aex_load_observed": bool(trace["load_events"]),
        "actual_abi_argument_spill_observed": trace["abi_argument_spill"] is not None,
        "loaded_expected_packed_raw": bool(load and load["loaded_raw_u64"] == EXPECTED_RAW),
        "abi_spill_expected_packed_raw": bool(trace["abi_argument_spill"] and int.from_bytes(bytes.fromhex(str(trace["abi_argument_spill"]["value_raw_hex"])), "little") == EXPECTED_RAW),
        "actual_aex_packed_input_call_observed": arithmetic_call is not None,
        "static_aex_packed_arithmetic_present": static["aex_packed_arithmetic_present"],
        "filterengine_stop_without_mutation": assertion.get("stop_without_mutation") is True,
    }
    status = "PASS_CLASSIFIED_FAIL_CLOSED_STOP" if classification in {"A", "B", "C"} and all(gates.values()) else "FAIL_CLOSED"
    report = {
        "kind": "olmkirakira_packed_size_argument_lineage",
        "schema": 1,
        "date": "2026-07-17",
        "status": status,
        "classification": classification,
        "classification_basis": basis,
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn actual-AEX execution of checked-in Windows PE; no Windows/AE claim",
        "question": "Does checked-in AEX arithmetic construct the packed-size argument, and is that exact value preserved through the callee ABI spill to the 0x181280e92 load?",
        "slot": {"reader": "0x181280e92", "address": "[RSP+0x1f8]", "expected_packed_raw": "0x0000000180000000"},
        "gates": gates,
        "static": static,
        "runtime": {
            "common_owner_status": runtime.get("status"),
            "execution_stop": runtime.get("execution_stop"),
            "filterengine_assertion": assertion,
            "load_events": trace["load_events"],
            "target_writes_in_observation_order": trace["target_writes"],
            "abi_argument_spill_not_semantic_first_writer": trace["abi_argument_spill"],
            "packed_input_callsites": packed_calls,
            "packed_input_call_with_expected_raw": arithmetic_call,
        },
        "limits": [
            "No value was patched into the stack slot, object, source plane, or argument.",
            "The cv::FilterEngine assertion was not bypassed or suppressed.",
            "Classification is fail-closed; missing or contradictory evidence is ambiguous.",
            "The callee prologue spill at 0x181280bc0 is continuity evidence, not the semantic origin of the value.",
            "No Windows execution, After Effects host binding, final pixel, or AE-exactness claim.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md = [
        "# OLMKiraKira packed-size argument lineage",
        "",
        "Date: 2026-07-17",
        "",
        "## Result",
        "",
        f"- Status: **{status}**",
        f"- Classification: **{classification}**",
        f"- Basis: {basis}",
        "- Reader: `0x181280e92 MOV R9,qword ptr [RSP + 0x1f8]`.",
        "- The caller constructs `R9 = RSI | 0x100000000` at `0x18115110a..0x18115116f`.",
        "- The callee prologue at `0x181280bc0` spills that ABI argument; this is continuity evidence and is not labeled the semantic first writer.",
        "- The paired JSON retains the spill RIP, raw bytes, register context, later stack load, and unchanged FilterEngine stop.",
        "",
        "## Fail-Closed Boundary",
        "",
        "- A: observed packed argument arrives from outside the pinned AEX image.",
        "- B: checked-in AEX arithmetic constructs the packed argument and callee spill/load preserves it.",
        "- C: observed construction occurs inside the pinned OpenCV/FilterEngine ranges.",
        "- Any missing, contradictory, or non-sentinel evidence is `ambiguous` and exits non-zero.",
        "",
        "## Limits",
        "",
        "- No value patch, assertion suppression, Windows execution, After Effects host claim, final-pixel claim, or AE-exactness claim.",
        "",
    ]
    MARKDOWN.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"status": status, "classification": classification, "gates": gates, "report": str(REPORT)}, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
