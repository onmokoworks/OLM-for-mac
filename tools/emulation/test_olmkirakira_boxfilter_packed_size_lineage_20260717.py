#!/usr/bin/env python3
"""Trace FUN_181280fa0's packed geometry and border arguments.

The existing common-owner runner supplies the natural actual-AEX execution.
This wrapper adds exact-address hooks without changing that runner or the AEX
image.  It is intentionally fail-closed: an incomplete or ambiguous argument
trace is evidence of missing fixture/runtime state, not permission to patch a
value or continue past the assertion.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
REPORT = ROOT / "refs/conformance/olmkirakira_boxfilter_packed_size_lineage_20260717.json"

sys.path.insert(0, str(ROOT / "tools/emulation"))
common = importlib.import_module("test_olmkirakira_mode2_common_owner_20260717")

CALLSITE = 0x181281326
ENTRY = 0x181280FA0
ARG5_BUILD = 0x1812812C3
ARG6_BUILD = 0x181281304
ARG5_LOAD = 0x181281318
ARG6_LOAD = 0x18128130C

EXPECTED_ASM = {
    "upstream_packed_source": [
        "181280e85  MOV RAX,qword ptr [RSP + 0x200]",
        "181280e8d  MOV qword ptr [RSP + 0x20],RAX",
        "181280e92  MOV R9,qword ptr [RSP + 0x1f8]",
        "181280ea2  CALL 0x181281260",
    ],
    "caller_stack_build": [
        "1812812c3  MOV RAX,qword ptr [RSP + 0x90]",
        "1812812cb  MOV qword ptr [RSP + 0x20],RAX",
        "181281304  MOVZX EAX,byte ptr [RSP + 0x98]",
        "18128130c  MOV byte ptr [RSP + 0x28],AL",
        "181281318  MOV qword ptr [RSP + 0x20],RAX",
        "181281326  CALL 0x181280fa0",
    ],
    "packed_param4_setup": [
        "1812812ef  MOV R8D,ESI",
        "1812812f2  MOV EDX,EBP",
        "1812812f4  MOV RCX,RDI",
        "181281326  CALL 0x181280fa0",
    ],
    "callee_forwarding": [
        "181280fc9  MOV RBX,R9",
        "181280fcc  MOV R13D,R8D",
        "181280fcf  MOV EDI,EDX",
        "181280fd4  MOV R14,RCX",
        "18128106c  MOV R9D,EBX",
        "18128106f  MOV R8D,R15D",
        "181281072  MOV EDX,dword ptr [RBP + -0x7d]",
        "181281079  CALL 0x181281e90",
    ],
}


def u64(loader: object, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def i32(value: int) -> int:
    return struct.unpack("<i", struct.pack("<I", value & 0xFFFFFFFF))[0]


def packed_size(value: int) -> dict[str, object]:
    return {
        "raw_hex": f"0x{value & ((1 << 64) - 1):016x}",
        "width_low_i32": i32(value),
        "height_high_i32": i32(value >> 32),
    }


def static_witness() -> dict[str, object]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    observed = {name: [line for line in lines if line in asm] for name, lines in EXPECTED_ASM.items()}
    return {
        "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
        "asm_sha256": hashlib.sha256(ASM.read_bytes()).hexdigest(),
        "decomp_sha256": hashlib.sha256(DECOMP.read_bytes()).hexdigest(),
        "expected": EXPECTED_ASM,
        "observed": observed,
        "all_expected_present": all(len(observed[name]) == len(lines) for name, lines in EXPECTED_ASM.items()),
        "decomp_contract": {
            "fun_181280fa0_signature": "param_4=packed width/height, param_5=stack qword, param_6=stack byte",
            "fun_181280fa0_to_row_sum": "FUN_181281e90(local_90, local_c4, iVar9, param_4 & 0xffffffff)",
            "fun_181281e90_geometry": "param_4 is the row geometry width/height source object argument",
            "source_excerpt_present": all(token in decomp for token in ("FUN_181280fa0", "FUN_181281e90", "param_4 & 0xffffffff")),
        },
    }


def capture_runtime() -> tuple[dict[str, object], dict[str, object]]:
    captures: dict[str, object] = {"upstream_callsite": [], "callsite": [], "entry": []}
    original = common.AexLoader.add_code_hook

    def capture_at(point: str):
        def capture(ld: object, _address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(common.UC_X86_REG_RSP)
            stack_offset = 0x20 if point in ("upstream_callsite", "callsite") else 0x28
            arg5_raw = u64(ld, rsp + stack_offset)
            arg6_raw = ld.read_bytes(rsp + stack_offset + 8, 1)[0]
            record = {
                "point": point,
                "rip": hex(ld.uc.reg_read(common.UC_X86_REG_RIP)),
                "rsp": hex(rsp),
                "registers": {
                    name: hex(ld.uc.reg_read(reg))
                    for name, reg in (("RCX", common.UC_X86_REG_RCX), ("RDX", common.UC_X86_REG_RDX),
                                      ("R8", common.UC_X86_REG_R8), ("R9", common.UC_X86_REG_R9))
                },
                "param_4_packed": packed_size(ld.uc.reg_read(common.UC_X86_REG_R9)),
                "param_5_raw": hex(arg5_raw),
                "param_5_low_i32": i32(arg5_raw),
                "param_5_high_i32": i32(arg5_raw >> 32),
                "param_6_raw": arg6_raw,
                "stack_contract": "caller RSP+0x20/+0x28" if point in ("upstream_callsite", "callsite") else "callee entry RSP+0x28/+0x30",
            }
            captures[point].append(record)
        return capture

    def hook_wrapper(loader: object, address: int, handler: object) -> None:
        original(loader, address, handler)
        if not getattr(loader, "_boxfilter_packed_hooks", False):
            original(loader, 0x181280EA2, capture_at("upstream_callsite"))
            original(loader, CALLSITE, capture_at("callsite"))
            original(loader, ENTRY, capture_at("entry"))
            setattr(loader, "_boxfilter_packed_hooks", True)

    common.AexLoader.add_code_hook = hook_wrapper
    try:
        runtime = common.run_owner_probe()
    finally:
        common.AexLoader.add_code_hook = original
    return runtime, captures


def main() -> int:
    static = static_witness()
    runtime, captures = capture_runtime()
    upstream = captures["upstream_callsite"]
    callsites = captures["callsite"]
    entries = captures["entry"]
    assertion = runtime.get("filter_assertion_capture", {})
    checkout = runtime.get("callback", {}).get("param_checkout", [])
    checkout_values = [item.get("grounded_value") for item in checkout]
    actual = bool(upstream and callsites and entries)
    same_arguments = actual and upstream[-1].get("param_4_packed") == callsites[-1].get("param_4_packed") == entries[-1].get("param_4_packed") and callsites[-1].get("param_5_raw") == entries[-1].get("param_5_raw") and callsites[-1].get("param_6_raw") == entries[-1].get("param_6_raw")
    invalid = assertion.get("compared_fields") == {
        "+0x14 ksize.width": -2147483648,
        "+0x18 ksize.height": 1,
        "+0x1c anchor.x": -1073741824,
        "+0x20 anchor.y": 0,
    }
    packed = entries[-1].get("param_4_packed", {}) if entries else {}
    geometry_is_sentinel = packed.get("width_low_i32") in (-2147483648, -1073741824) or packed.get("height_high_i32") in (-2147483648, -1073741824)
    checks = {
        "static_asm_present": static["all_expected_present"],
        "static_decomp_contract_present": static["decomp_contract"]["source_excerpt_present"],
        "actual_aex_callsite_observed": bool(callsites),
        "actual_aex_entry_observed": bool(entries),
        "actual_aex_upstream_packed_source_observed": bool(upstream),
        "upstream_callsite_entry_packed_argument_identical": same_arguments,
        "filterengine_invalid_geometry_observed": invalid,
        "no_value_patch_or_assertion_suppression": runtime.get("filter_assertion_capture", {}).get("stop_without_mutation") is True,
        "host_checkout_contains_raw_geometry_sentinel": any(value in (0x80000000, 0xC0000000, -2147483648, -1073741824) for value in checkout_values if isinstance(value, int)),
    }
    classification = "AEX_ALGORITHM_OR_OBJECT_VALUE" if all(checks[name] for name in ("static_asm_present", "static_decomp_contract_present", "actual_aex_callsite_observed", "actual_aex_entry_observed", "actual_aex_upstream_packed_source_observed", "upstream_callsite_entry_packed_argument_identical", "filterengine_invalid_geometry_observed", "no_value_patch_or_assertion_suppression")) and geometry_is_sentinel else "UNRESOLVED_FIXTURE_OR_HOST_STATE_FAIL_CLOSED"
    report = {
        "kind": "olmkirakira_boxfilter_packed_size_lineage",
        "schema": 1,
        "date": "2026-07-17",
        "status": "PASS_CLASSIFIED_FAIL_CLOSED_STOP" if classification == "AEX_ALGORITHM_OR_OBJECT_VALUE" else "FAIL_CLOSED",
        "classification": classification,
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn actual-AEX execution of checked-in Windows PE; no Windows/AE claim",
        "question": "Where are FUN_181280fa0 param_4 packed width/height and param_5/param_6 constructed, and are the invalid geometry words sentinel or algorithm values?",
        "answer": {
            "param_4": "FUN_181280e92 loads R9 from [RSP+0x1f8] for FUN_181281260; 0x181281326 forwards R9 unchanged; FUN_181280fa0 retains it in RBX and forwards its low dword to FUN_181281e90",
            "param_5": "constructed by caller stack load 0x1812812c3 -> [RSP+0x20], consumed as fifth Win64 argument",
            "param_6": "constructed by caller byte load 0x181281304 -> [RSP+0x28], consumed as sixth Win64 argument",
            "classification_basis": "Raw argument continuity and the unmodified FilterEngine assertion are required; host checkout values are a negative control only.",
        },
        "checks": checks,
        "static": static,
        "runtime": {
            "common_owner_status": runtime.get("status"),
            "execution_stop": runtime.get("execution_stop"),
            "filterengine_assertion": assertion,
            "upstream_callsite_arguments": upstream,
            "callsite_arguments": callsites,
            "entry_arguments": entries,
            "parameter_checkout_values": [{"disk_id": item.get("disk_id"), "name": item.get("name"), "value": item.get("grounded_value")} for item in checkout],
        },
        "limits": [
            "No invalid value was patched into any object, source plane, or argument slot.",
            "The cv::FilterEngine assertion was not bypassed or suppressed.",
            "No Windows execution, After Effects host binding, final pixel, or AE-exactness claim.",
            "Only this new runner and its two new evidence files are owned by this task.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "classification": classification, "checks": checks, "report": str(REPORT)}, sort_keys=True))
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
