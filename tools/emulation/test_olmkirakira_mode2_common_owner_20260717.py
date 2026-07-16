#!/usr/bin/env python3
"""Mac-only natural-lineage attempt through OLMKiraKira's common owner.

This enters the actual AEX orchestrator that owns the world handles and
selects the PF32 owner.  Host suite callbacks are not fabricated: the first
unavailable callback/ABI is captured and the harness exits 2.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RBX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DECOMP = ROOT / "decomp/OLMKiraKira.aex.c.txt"
ASM = ROOT / "disasm/OLMKiraKira.aex.asm.txt"
EXISTING_CALLBACK_HARNESS = ROOT / "tools/emulation/test_dblur_case0001_rowdriver.py"
KIRA_SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
KIRA_MANIFEST = ROOT / "refs/win_references/20260604_olm/OLMKiraKira/reference_manifest.json"
REPORT = ROOT / "refs/conformance/olmkirakira_mode2_common_owner_20260717.json"

COMMON_OWNER = 0x18114C8F0
PF32_OWNER = 0x18114D7F0
MODE2_DISPATCH = 0x18114F4A0
PF32_TYPED_OWNER = 0x18114E460
PF32_CALLSITES = (0x18114E5D7, 0x18114E739)

# Values are the grounded case_0001 defaults from the Windows manifest. The
# disk selectors match the Kira source's ParamsSetup disk IDs.
PARAM_DEFAULTS = {
    0x01: {"match_name": "OLM OLM Kira Kira-0001", "name": "Glow Rotation", "kind": "double", "value": 0.0, "disk_id": 1},
    0x02: {"match_name": "OLM OLM Kira Kira-0002", "name": "Brightness Gain", "kind": "double", "value": 1.0, "disk_id": 2},
    0x03: {"match_name": "OLM OLM Kira Kira-0003", "name": "Vertical Length", "kind": "int32", "value": 50, "disk_id": 3},
    0x04: {"match_name": "OLM OLM Kira Kira-0004", "name": "Horizontal Length", "kind": "int32", "value": 50, "disk_id": 4},
    0x05: {"match_name": "OLM OLM Kira Kira-0005", "name": "Diagonal Length", "kind": "int32", "value": 50, "disk_id": 5},
    0x06: {"match_name": "OLM OLM Kira Kira-0006", "name": "Highlight Radius", "kind": "int32", "value": 0, "disk_id": 6},
    0x07: {"match_name": "OLM OLM Kira Kira-0007", "name": "Glow Opacity", "kind": "int32", "value": 100, "disk_id": 7},
    0x08: {"match_name": "OLM OLM Kira Kira-0008", "name": "Channel", "kind": "int32", "value": 2, "disk_id": 8, "enum": "Channel popup default 2"},
    0x09: {"match_name": "OLM OLM Kira Kira-0009", "name": "Blur Mode", "kind": "int32", "value": 2, "disk_id": 9, "enum": "Blur Mode popup default 2"},
    0x0A: {"match_name": "OLM OLM Kira Kira-0010", "name": "Approximated Input", "kind": "int32", "value": 0, "disk_id": 10},
    0x0B: {"match_name": "OLM OLM Kira Kira-0011", "name": "Strength multiplier", "kind": "int32", "value": 100, "disk_id": 11},
    0x0C: {"match_name": "OLM OLM Kira Kira-0012", "name": "Source Opacity", "kind": "int32", "value": 100, "disk_id": 12},
    0x0D: {"match_name": "OLM OLM Kira Kira-0013", "name": "Vertical Color", "kind": "color", "value": [255, 255, 255, 255], "disk_id": 13},
    0x0E: {"match_name": "OLM OLM Kira Kira-0014", "name": "Horizontal Color", "kind": "color", "value": [255, 255, 255, 255], "disk_id": 14},
    0x0F: {"match_name": "OLM OLM Kira Kira-0015", "name": "Diagonal Color", "kind": "color", "value": [255, 255, 255, 255], "disk_id": 15},
    0x10: {"match_name": "OLM OLM Kira Kira-0016", "name": "Highlight Color", "kind": "color", "value": [255, 255, 255, 255], "disk_id": 16},
    0x11: {"match_name": "OLM OLM Kira Kira-0017", "name": "Merge mode", "kind": "int32", "value": 1, "disk_id": 17, "enum": "Merge mode popup default 1"},
    0x12: {"match_name": "OLM OLM Kira Kira-0018", "name": "Vertical Use Ramp", "kind": "int32", "value": 0, "disk_id": 18},
    0x14: {"match_name": "OLM OLM Kira Kira-0020", "name": "Horizontal Use Ramp", "kind": "int32", "value": 0, "disk_id": 20},
    0x16: {"match_name": "OLM OLM Kira Kira-0022", "name": "Diagonal Use Ramp", "kind": "int32", "value": 0, "disk_id": 22},
    0x18: {"match_name": "OLM OLM Kira Kira-0024", "name": "Highlight Use Ramp", "kind": "int32", "value": 0, "disk_id": 24},
    0x1A: {"match_name": "OLM OLM Kira Kira-0026", "name": "Diagonal 2 length", "kind": "int32", "value": 50, "disk_id": 26},
    0x1B: {"match_name": "OLM OLM Kira Kira-0027", "name": "Fade Out", "kind": "int32", "value": 0, "disk_id": 27},
    0x1C: {"match_name": "OLM OLM Kira Kira-0028", "name": "Diagonal Color2", "kind": "color", "value": [255, 255, 255, 255], "disk_id": 28},
    0x23: {"match_name": "OLM OLM Kira Kira-0035", "name": "Diagonal 2 Use Ramp", "kind": "int32", "value": 0, "disk_id": 35},
}
PARAM_SELECTOR_ORDER = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 22, 24, 26, 27, 28, 35)
PARAM_BY_SELECTOR = {selector: PARAM_DEFAULTS[disk_id] for selector, disk_id in enumerate(PARAM_SELECTOR_ORDER)}

sys.path.insert(0, str(ROOT / "tools" / "emulation"))
from aex_loader import AexLoader  # noqa: E402


def slice_between(text: str, start: str, end: str) -> str:
    left = text.index(start)
    return text[left:text.index(end, left)]


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    owner = slice_between(asm, "; === FUN_18114c8f0", "; === FUN_18114ca70")
    owner_c = slice_between(decomp, "// === FUN_18114c8f0", "// === FUN_18114ca70")
    pf32 = slice_between(asm, "; === FUN_18114d7f0", "; === FUN_18114ddc0")
    typed = slice_between(asm, "; === FUN_18114e460", "; === FUN_18114e7b0")
    return {
        "common_owner_present": "18114c8f0  PUSH RBX" in owner and "FUN_18114c8f0" in owner_c,
        "common_owner_reads_pf_depth": "MOVZX R14D,word ptr [RAX + 0x2c]" in owner,
        "common_owner_selects_pf32_owner": "18114ca15  CALL 0x18114d7f0" in owner,
        "common_owner_obtains_worlds_via_suite": "18114c945  CALL R9" in owner and "18114c963  CALL R9" in owner,
        "param_table_scan_is_grounded": "1811542b0  MOV qword ptr [RSP + 0x8],RBX" in asm and "181154300  CMP dword ptr [RAX],EDI" in asm,
        "param_table_request_id_is_grounded": "18114e87f  MOV R8D,0x1" in asm and "1811542b0" in decomp,
        "param_context_fields_are_grounded": "1811542b0" in decomp and "[RSI + 0xf0]" in asm and "[RSI + 0xe0]" in asm and "[RSI + 0xe4]" in asm,
        "param_checkin_contract_is_grounded": "(**(code **)(param_1 + 8))(*(undefined8 *)(param_1 + 0xb8))" in decomp and "181232764  MOV RAX,qword ptr [RCX + 0x8]" in asm and "181232771  MOV ECX,EAX" in asm and "def pf_checkin" in EXISTING_CALLBACK_HARNESS.read_text(encoding="utf-8"),
        "param_checkout_contract_is_grounded": "181232742  CALL R10" in asm and "def pf_checkout" in EXISTING_CALLBACK_HARNESS.read_text(encoding="utf-8") and "PF_CHECKOUT_PARAM" in KIRA_SOURCE.read_text(encoding="utf-8"),
        "kira_defaults_are_grounded": len(PARAM_DEFAULTS) == 25 and PARAM_SELECTOR_ORDER == tuple(spec["disk_id"] for spec in PARAM_BY_SELECTOR.values()) and "OLM OLM Kira Kira-0001" in KIRA_MANIFEST.read_text(encoding="utf-8") and "CHANNEL_DISK_ID = 8" in (ROOT / "mac/OLMKiraKira/OLMKiraKira.h").read_text(encoding="utf-8"),
        "next_callback_pointer_abi_is_grounded": "181232764  MOV RAX,qword ptr [RCX + 0x8]" in asm and "181232768  MOV RCX,qword ptr [RCX + 0xb8]" in asm and "18123276f  CALL RAX" in asm,
        "pf32_owner_enters_mode2_dispatch": "18114dbfc  CALL 0x18114f4a0" in pf32,
        "pf32_owner_enters_typed_owner": "18114dd0d  CALL 0x18114e460" in pf32,
        "typed_owner_has_pf32_sites": all(f"{address:x}  CALL 0x181230c20" in typed for address in PF32_CALLSITES),
        "typed_writer_uses_rsp_plus_0x28": "181230c20  MOV RAX,qword ptr [RSP + 0x28]" in asm,
    }


def run_owner_probe() -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    events: list[dict[str, object]] = []
    loader.add_code_hook(COMMON_OWNER, lambda ld, _address, _size: events.append({
        "event": "common_owner_entry",
        "register_args": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
    }))
    suite_call_trace: list[dict[str, object]] = []
    internal_boundary_trace: list[dict[str, object]] = []

    pixel_size = 16
    rowbytes = pixel_size + 8
    input_canary = b"\x3c" * 8
    output_canary = b"\xc3" * 8
    input_payload = loader.host_alloc(rowbytes, align=64)
    output_payload = loader.host_alloc(rowbytes, align=64)
    loader.write_bytes(input_payload, struct.pack("<4f", 1.0, 0.25, 0.5, 0.75) + input_canary)
    loader.write_bytes(output_payload, b"\xa5" * pixel_size + output_canary)

    def world(payload: int) -> int:
        header = bytearray(0x30)
        struct.pack_into("<Q", header, 0x18, payload)
        struct.pack_into("<i", header, 0x20, rowbytes)
        struct.pack_into("<i", header, 0x24, 1)
        struct.pack_into("<i", header, 0x28, 1)
        struct.pack_into("<h", header, 0x2C, 32)
        return _write_world(header)

    def _write_world(header: bytearray) -> int:
        address = loader.host_alloc(len(header), align=16)
        loader.write_bytes(address, bytes(header))
        return address

    input_world = world(input_payload)
    output_world = world(output_payload)
    refcon = loader.host_alloc(0x20, align=16)
    loader.write_bytes(refcon, b"\0" * 0x20)
    context = loader.host_alloc(0x200, align=16)
    loader.write_bytes(context, b"\0" * 0x200)
    loader.write_bytes(context + 0xB8, struct.pack("<Q", refcon))
    param_table = loader.host_alloc(0xB0, align=16)
    loader.write_bytes(param_table, b"\0" * 0xB0)
    # FUN_1811542b0 scans [param1+0x8, param1+0xac) for disk IDs and returns
    # their zero-based ordinal to PF_ParamCheckout. The entries are exactly
    # the grounded ParamsSetup order used by this render path.
    loader.write_bytes(param_table + 0x8, struct.pack(f"<{len(PARAM_SELECTOR_ORDER)}I", *PARAM_SELECTOR_ORDER))
    vtable = loader.host_alloc(0x40, align=16)
    loader.write_bytes(vtable, b"\0" * 0x40)
    descriptor = loader.host_alloc(0x20, align=16)
    suite = loader.host_alloc(0x28, align=16)
    loader.write_bytes(descriptor, struct.pack("<2Q", input_world, suite))
    loader.write_bytes(suite, b"\0" * 0x28)
    callback_state: dict[str, object] = {}

    def param_checkin(current: AexLoader, args: list[int]) -> int:
        if args[0] != refcon:
            raise RuntimeError("invalid PF_ParamCheckin ABI")
        callback_state.setdefault("param_checkin", []).append({
            "abi_registers_rcx_rdx_r8_r9": [hex(value) for value in args],
            "refcon": hex(refcon),
            "return": 0,
            "return_semantics": "PF_Err_NONE",
            "source": "tools/emulation/test_dblur_case0001_rowdriver.py:91-100",
        })
        return 0

    param_checkin_ptr = loader.install_callback("PF_ParamCheckin", param_checkin)
    loader.write_bytes(context + 0x8, struct.pack("<Q", param_checkin_ptr))

    def param_checkout(current: AexLoader, args: list[int]) -> int:
        if args[0] != refcon:
            raise RuntimeError("invalid PF_ParamCheckout refcon ABI")
        rsp = current.uc.reg_read(UC_X86_REG_RSP)
        index = args[1] & 0xFFFFFFFF
        spec = PARAM_BY_SELECTOR.get(index)
        if spec is None:
            raise RuntimeError(f"unprovided Kira parameter selector 0x{index:x}")
        param_def = struct.unpack("<Q", current.read_bytes(rsp + 0x30, 8))[0]
        current.write_bytes(param_def, b"\0" * 0xB0)
        if spec["kind"] == "double":
            current.write_bytes(param_def + 0x38, struct.pack("<d", spec["value"]))
        elif spec["kind"] == "int32":
            current.write_bytes(param_def + 0x38, struct.pack("<i", spec["value"]))
        elif spec["kind"] == "color":
            current.write_bytes(param_def + 0x38, bytes(spec["value"]))
        else:
            raise RuntimeError(f"unsupported grounded parameter kind {spec['kind']}")
        callback_state.setdefault("param_checkout", []).append({
            "selector_index": index,
            "requested_disk_id": spec["disk_id"],
            "match_name": spec["match_name"],
            "name": spec["name"],
            "disk_id": spec["disk_id"],
            "enum": spec.get("enum"),
            "kind": spec["kind"],
            "grounded_value": spec["value"],
            "abi_registers_rcx_rdx_r8_r9": [hex(value) for value in args],
            "stack_time_scale": hex(struct.unpack("<Q", current.read_bytes(rsp + 0x28, 8))[0]),
            "param_def_pointer": hex(param_def),
            "param_def_size": "0xb0",
            "param_def_u_plus_0x38_raw": current.read_bytes(param_def + 0x38, 16).hex(),
            "return": 0,
            "return_semantics": "PF_Err_NONE",
            "source": {
                "defaults": "refs/win_references/20260604_olm/OLMKiraKira/reference_manifest.json case_0001",
                "selectors": "mac/OLMKiraKira/OLMKiraKira.h disk IDs",
                "checkout_shape": "tools/emulation/test_dblur_case0001_rowdriver.py:84-100",
            },
        })
        return 0

    param_checkout_ptr = loader.install_callback("PF_ParamCheckout", param_checkout)
    loader.write_bytes(context, struct.pack("<Q", param_checkout_ptr))

    def record_callback(label: str, args: list[int], out_address: int, world_ptr: int) -> int:
        rsp = loader.uc.reg_read(UC_X86_REG_RSP)
        loader.write_bytes(out_address, struct.pack("<Q", world_ptr))
        callback_state.setdefault("callbacks", []).append({
            "label": label,
            "abi_registers_rcx_rdx_r8_r9": [hex(value) for value in args],
            "out_pointer_address": hex(out_address),
            "returned_world_pointer": hex(world_ptr),
            "rsp": hex(rsp),
            "stack_at_callback_entry": loader.read_bytes(rsp, 0x30).hex(),
        })
        return 0

    def checkout_layer(current: AexLoader, args: list[int]) -> int:
        if args[0] != refcon or args[1] != 0:
            raise RuntimeError("invalid PFWorldSuite checkout_layer ABI")
        return record_callback("PFWorldSuite.param4[1] slot +0x0", args, args[2], input_world)

    def checkout_output(current: AexLoader, args: list[int]) -> int:
        if args[0] != refcon:
            raise RuntimeError("invalid PFWorldSuite checkout_output ABI")
        return record_callback("PFWorldSuite.param4[1] slot +0x10", args, args[1], output_world)

    layer_ptr = loader.install_callback("PFWorldSuite.param4[1] slot +0x0", checkout_layer)
    output_ptr = loader.install_callback("PFWorldSuite.param4[1] slot +0x10", checkout_output)
    loader.write_bytes(suite, struct.pack("<Q", layer_ptr) + b"\0" * 8 + struct.pack("<Q", output_ptr))
    loader.add_code_hook(0x18114C945, lambda ld, _address, _size: suite_call_trace.append({
        "callsite": "0x18114c945",
        "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
        "suite_slot0": hex(struct.unpack("<Q", ld.read_bytes(suite, 8))[0]),
        "suite_slot1": hex(struct.unpack("<Q", ld.read_bytes(suite + 0x10, 8))[0]),
    }))
    loader.add_code_hook(0x18114C963, lambda ld, _address, _size: suite_call_trace.append({
        "callsite": "0x18114c963",
        "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
        "suite_slot0": hex(struct.unpack("<Q", ld.read_bytes(suite, 8))[0]),
        "suite_slot1": hex(struct.unpack("<Q", ld.read_bytes(suite + 0x10, 8))[0]),
    }))
    def capture_internal(address: int, label: str):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            internal_boundary_trace.append({
                "address": hex(address),
                "label": label,
                "registers_rcx_rdx_r8_r9_rax_rbx": [
                    hex(ld.uc.reg_read(reg))
                    for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8,
                                UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RBX)
                ],
                "rsp": hex(ld.uc.reg_read(UC_X86_REG_RSP)),
            })
        return hook

    loader.add_code_hook(0x1811542B0, capture_internal(0x1811542B0, "FUN_1811542b0 entry"))
    loader.add_code_hook(0x181154300, capture_internal(0x181154300, "parameter-table compare before invalid read"))
    loader.add_code_hook(0x1812326E0, capture_internal(0x1812326E0, "PF_ParamCheckout callback pointer before CALL R10"))
    loader.add_code_hook(0x181232350, capture_internal(0x181232350, "PF ColorParamSuite acquire path"))
    loader.add_code_hook(0x181232760, capture_internal(0x181232760, "context callback pointer before CALL RAX"))
    try:
        loader.call_function(
            COMMON_OWNER,
            int_args=[param_table, context, 0, descriptor],
            max_instructions=50_000,
        )
        return {
            "status": "FAILED",
            "events": events,
            "callback": callback_state,
            "suite_call_trace": suite_call_trace,
            "internal_boundary_trace": internal_boundary_trace,
            "natural_writer_reached": False,
            "worlds": {
                "input": {"pointer": hex(input_world), "payload": hex(input_payload), "rowbytes": rowbytes},
                "output": {"pointer": hex(output_world), "payload": hex(output_payload), "rowbytes": rowbytes},
            },
            "parameter_table": {
                "pointer": hex(param_table),
                "size": "0xb0",
                "proven_entries": {"address": hex(param_table + 0x8), "count": len(PARAM_SELECTOR_ORDER), "disk_ids": list(PARAM_SELECTOR_ORDER), "source": "mac/OLMKiraKira/OLMKiraKira.h disk IDs; first request FUN_18114e860 0x18114e87f MOV R8D,0x1"},
                "context_defaults": {"+0xe0": 0, "+0xe4": 0, "+0xf0": 0, "source": "zero-initialized fixture; exact FUN_1811542b0 reads"},
            },
            "reason": "common owner returned without reaching the required natural PF32 writer callsite",
        }
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "events": events,
            "callback": callback_state,
            "suite_call_trace": suite_call_trace,
            "internal_boundary_trace": internal_boundary_trace,
            "natural_writer_reached": False,
            "worlds": {
                "input": {"pointer": hex(input_world), "payload": hex(input_payload), "rowbytes": rowbytes,
                           "raw_after": loader.read_bytes(input_payload, rowbytes).hex(),
                           "padding_preserved": loader.read_bytes(input_payload + pixel_size, 8) == input_canary},
                "output": {"pointer": hex(output_world), "payload": hex(output_payload), "rowbytes": rowbytes,
                           "raw_after": loader.read_bytes(output_payload, rowbytes).hex(),
                           "padding_preserved": loader.read_bytes(output_payload + pixel_size, 8) == output_canary},
            },
            "parameter_table": {
                "pointer": hex(param_table),
                "size": "0xb0",
                "proven_entries": {"address": hex(param_table + 0x8), "count": len(PARAM_SELECTOR_ORDER), "disk_ids": list(PARAM_SELECTOR_ORDER), "source": "mac/OLMKiraKira/OLMKiraKira.h disk IDs; first request FUN_18114e860 0x18114e87f MOV R8D,0x1"},
                "context_defaults": {"+0xe0": 0, "+0xe4": 0, "+0xf0": 0, "source": "zero-initialized fixture; exact FUN_1811542b0 reads"},
            },
            "first_unavailable_boundary": "unprovided PF ColorParamSuite/SPBasic suite at FUN_181232350 +0x3b (MOV RAX,[RBX]); RBX=[outer context+0x180]=0; required AcquireSuite output at RSP+0x78",
            "exception": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    static = static_checks()
    runtime = run_owner_probe()
    report = {
        "kind": "olmkirakira_mode2_common_owner_natural_lineage_attempt",
        "schema": 1,
        "date": "2026-07-17",
        "status": runtime["status"] if all(static.values()) else "FAILED",
        "ae_exact_claim": False,
        "platform_scope": "Mac-only Unicorn execution of the checked-in Windows PE AEX; no Windows/AE claim",
        "common_owner": {
            "function": f"FUN_{COMMON_OWNER:x}",
            "role": "reads PF depth, obtains source/output worlds through host suite, selects PF8/PF16/PF32 owner",
            "pf32_selection": f"PF depth 0x20 -> FUN_{PF32_OWNER:x}",
            "mode2_dispatch": f"FUN_{PF32_OWNER:x} -> FUN_{MODE2_DISPATCH:x}",
            "typed_owner": f"FUN_{PF32_OWNER:x} -> FUN_{PF32_TYPED_OWNER:x}",
            "writer_callsites": [f"0x{address:x}" for address in PF32_CALLSITES],
        },
        "inputs": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(),
            "fixture": "1x1 PF32 descriptor attempt; no Python world/data copying",
        },
        "static_checks": static,
        "runtime": runtime,
        "lineage_gate": {
            "natural_writer_reached": runtime.get("natural_writer_reached", False),
            "passed": False,
            "fail_closed": True,
        },
        "limits": [
            "The host PF world-suite callback ABI was not fabricated.",
            "No Mode2 output pointer reached a typed writer in this run.",
            "No Windows execution, After Effects host binding, final pixel, or AE exactness claim.",
            "No production source or ledger was changed.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "status": report["status"],
        "static": f"{sum(static.values())}/{len(static)}",
        "common_owner_entered": bool(runtime.get("events")),
        "first_unavailable": runtime.get("first_unavailable_boundary"),
        "report": str(REPORT),
    }
    print(json.dumps(summary, sort_keys=True))
    return 2 if report["status"] == "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
