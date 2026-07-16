#!/usr/bin/env python3
"""Mac-only natural-lineage attempt through OLMKiraKira's common owner.

This enters the actual AEX orchestrator that owns the world handles and
selects the PF32 owner.  Host suite callbacks are not fabricated: the first
unavailable callback/ABI is captured and the harness exits 2.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RAX,
    UC_X86_REG_RBX,
    UC_X86_REG_RBP,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RDI,
    UC_X86_REG_RIP,
    UC_X86_REG_RSI,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM2,
)
from aex_loader import TEB_BASE

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
DISPATCH_LOOP_ENTRY = 0x181294AD5
DISPATCH_PROGRESS = 0x181294C2E
DISPATCH_CHUNK_INSTRUCTIONS = 10_000
DISPATCH_MAX_CHUNKS = 64
OPENCV_DISPATCH_GLOBAL = 0x181843990
OPENCV_DISPATCH_TABLE_BYTES = 0x10000
OPENCV_DISPATCH_READY_FLAG = 0x181843998
OPENCV_DISPATCH_COEFFICIENT_BYTES = 0x8000
OPENCV_BOOTSTRAP_MAX_INSTRUCTIONS = 2_500_000

FILTER_SIZE_PRIMARY_ZERO_WIDTH = 0x1812982EC
FILTER_SIZE_PRIMARY_HEIGHT_LOAD = 0x1812982F1
FILTER_SIZE_PRIMARY_CALL = 0x1812983B4
FILTER_SIZE_SIBLING_ZERO_WIDTH = 0x1812977B8
FILTER_SIZE_SIBLING_HEIGHT_LOAD = 0x1812977C0
FILTER_SIZE_SIBLING_CALL = 0x181297811
OPENCV_DISPATCH_BOOTSTRAP = 0x18114BE60

FILTER_SIZE_PRIMARY_BYTES = bytes.fromhex(
    "4533c9418bd1488bbdf805000085c97e51488bce4c8bc3f20f101d7f6b24000f1f8000000000"
    "660f6ed2f30fe6d20f28c2f20f5907f20f59c3f20f2dc0418900f20f595718f20f59d30f28c2f2"
    "0f2dc08901ffc24d8d4004488d49043b54244c7cc444894c24388b4424488944243c48"
)
FILTER_SIZE_SIBLING_BYTES = bytes.fromhex("c7442458000000008b8424280100008944245c488d8c2420")
FILTER_SIZE_SIBLING_CALL_BYTES = bytes.fromhex("488d9424a0010000488d4c2458e8aa10")
OPENCV_DISPATCH_BOOTSTRAP_BYTES = bytes.fromhex(
    "4883ec2833d28d4a01e8e28a14004885c0745db201b901000000e8d18a14004885c0744c33d28d4a02"
    "e8c28a14004885c0743db201b902000000e8b18a14004885c0742c33d28d4a04e8a28a14004885c074"
    "1db201b904000000e8918a14004885c0740cc605cd7a6f000148"
)

TLS_INDEX_GLOBAL = 0x1818C3EA8
GS_TLS_OFFSET = 0x58
TLS_EPOCH_OFFSET = 0x04
TLS_TABLE_SIZE = 0x08
TLS_SLOT_SIZE = 0x100
TLS_UNINITIALIZED_EPOCH = -1

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


def read_u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def mat_snapshot(loader: AexLoader, address: int) -> dict[str, object]:
    dims = struct.unpack("<i", loader.read_bytes(address + 0x4, 4))[0]
    result: dict[str, object] = {
        "address": hex(address),
        "flags": hex(struct.unpack("<I", loader.read_bytes(address, 4))[0]),
        "dims": dims,
        "rows": struct.unpack("<i", loader.read_bytes(address + 0x8, 4))[0],
        "cols": struct.unpack("<i", loader.read_bytes(address + 0xC, 4))[0],
        "data": hex(read_u64(loader, address + 0x18)),
        "datastart": hex(read_u64(loader, address + 0x10)),
        "dataend": hex(read_u64(loader, address + 0x20)),
        "datalimit": hex(read_u64(loader, address + 0x28)),
        "sizes": hex(read_u64(loader, address + 0x40)),
        "steps": hex(read_u64(loader, address + 0x48)),
    }
    if 0 <= dims <= 32:
        sizes = result["sizes"]
        steps = result["steps"]
        if isinstance(sizes, str) and isinstance(steps, str):
            sizes_address = int(sizes, 16)
            steps_address = int(steps, 16)
            result["size_values"] = [
                struct.unpack("<i", loader.read_bytes(sizes_address + i * 4, 4))[0]
                for i in range(dims)
            ]
            result["step_values"] = [
                read_u64(loader, steps_address + i * 8)
                for i in range(dims)
            ]
    return result


def read_std_string(loader: AexLoader, address: int) -> str:
    size = read_u64(loader, address + 0x10)
    capacity = read_u64(loader, address + 0x18)
    source = address if capacity < 0x10 else read_u64(loader, address)
    return loader.read_bytes(source, min(size, 4096)).decode("ascii", errors="replace")


def collect_static_fact_witnesses() -> dict[str, dict[str, object]]:
    asm = ASM.read_text(encoding="utf-8")
    decomp = DECOMP.read_text(encoding="utf-8")
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    return {
        "filter_size_primary": {
            "function": "FUN_181298180",
            "bytes": {
                "address": hex(0x18129828A),
                "hex": loader.read_bytes(0x18129828A, len(FILTER_SIZE_PRIMARY_BYTES)).hex(),
                "expected_hex": FILTER_SIZE_PRIMARY_BYTES.hex(),
            },
            "disasm": [
                "18129828a  XOR R9D,R9D",
                "1812982ec  MOV dword ptr [RSP + 0x38],R9D",
                "1812982f1  MOV EAX,dword ptr [RSP + 0x48]",
                "1812982f5  MOV dword ptr [RSP + 0x3c],EAX",
                "1812983af  LEA RCX,[RSP + 0x38]",
                "1812983b4  CALL 0x1811d88c0",
            ],
            "semantics": "FUN_181298180 explicitly zeroes Size.width/x at [RSP+0x38] after XOR R9D,R9D, then copies Size.height/y from [RSP+0x48] into [RSP+0x3c] before calling FUN_1811d88c0.",
            "decomp_grounding": "local_670 = 0; local_66c = local_660; ... FUN_1811d88c0(&local_670,&local_608,...)",
            "decomp_present": "local_670 = 0;" in decomp and "local_66c = local_660;" in decomp and "FUN_1811d88c0(&local_670,&local_608,(double)uVar9 * DAT_1814d6750);" in decomp,
            "asm_present": all(line in asm for line in (
                "18129828a  XOR R9D,R9D",
                "1812982ec  MOV dword ptr [RSP + 0x38],R9D",
                "1812982f1  MOV EAX,dword ptr [RSP + 0x48]",
                "1812982f5  MOV dword ptr [RSP + 0x3c],EAX",
                "1812983af  LEA RCX,[RSP + 0x38]",
                "1812983b4  CALL 0x1811d88c0",
            )),
        },
        "filter_size_sibling": {
            "function": "FUN_181297ac0 caller frame before return 0x181297816",
            "bytes": {
                "setup_address": hex(FILTER_SIZE_SIBLING_ZERO_WIDTH),
                "setup_hex": loader.read_bytes(FILTER_SIZE_SIBLING_ZERO_WIDTH, len(FILTER_SIZE_SIBLING_BYTES)).hex(),
                "setup_expected_hex": FILTER_SIZE_SIBLING_BYTES.hex(),
                "call_address": hex(FILTER_SIZE_SIBLING_CALL - 0xD),
                "call_hex": loader.read_bytes(FILTER_SIZE_SIBLING_CALL - 0xD, len(FILTER_SIZE_SIBLING_CALL_BYTES)).hex(),
                "call_expected_hex": FILTER_SIZE_SIBLING_CALL_BYTES.hex(),
            },
            "disasm": [
                "1812977b8  MOV dword ptr [RSP + 0x58],0x0",
                "1812977c0  MOV EAX,dword ptr [RSP + 0x128]",
                "1812977c7  MOV dword ptr [RSP + 0x5c],EAX",
                "181297804  LEA RDX,[RSP + 0x1a0]",
                "18129780c  LEA RCX,[RSP + 0x58]",
                "181297811  CALL 0x1811d88c0",
            ],
            "semantics": "The sibling setup repeats the same pattern: width/x is written as 0, height/y is copied from a caller local at [RSP+0x128], then FUN_1811d88c0 consumes the resulting Size from [RSP+0x58].",
            "decomp_grounding": "local_320 = 0; local_31c = local_250; ... FUN_1811d88c0(&local_320,&local_1d8,...)",
            "decomp_present": "local_320 = 0;" in decomp and "local_31c = local_250;" in decomp and "FUN_1811d88c0(&local_320,&local_1d8,(double)uVar5 * DAT_1814d6750);" in decomp,
            "asm_present": all(line in asm for line in (
                "1812977b8  MOV dword ptr [RSP + 0x58],0x0",
                "1812977c0  MOV EAX,dword ptr [RSP + 0x128]",
                "1812977c7  MOV dword ptr [RSP + 0x5c],EAX",
                "181297804  LEA RDX,[RSP + 0x1a0]",
                "18129780c  LEA RCX,[RSP + 0x58]",
                "181297811  CALL 0x1811d88c0",
            )),
        },
        "opencv_dispatch_state": {
            "bootstrap_function": "FUN_18114be60",
            "bytes": {
                "address": hex(OPENCV_DISPATCH_BOOTSTRAP),
                "hex": loader.read_bytes(OPENCV_DISPATCH_BOOTSTRAP, len(OPENCV_DISPATCH_BOOTSTRAP_BYTES)).hex(),
                "expected_hex": OPENCV_DISPATCH_BOOTSTRAP_BYTES.hex(),
            },
            "disasm": [
                "18114be69  CALL 0x181294950",
                "18114be7a  CALL 0x181294950",
                "18114be89  CALL 0x181294950",
                "18114be9a  CALL 0x181294950",
                "18114bea9  CALL 0x181294950",
                "18114beba  CALL 0x181294950",
                "18114bec4  MOV byte ptr [0x181843998],0x1",
                "181292f59  MOV RAX,qword ptr [0x181843990]",
            ],
            "semantics": "OpenCV bootstrap calls FUN_181294950 with (channels, table_write) = (1,0), (1,1), (2,0), (2,1), (4,0), (4,1), sets DAT_181843998 only after all six calls return nonzero, and later code reads qword ptr [0x181843990].",
            "asm_present": all(line in asm for line in (
                "18114be69  CALL 0x181294950",
                "18114be7a  CALL 0x181294950",
                "18114be89  CALL 0x181294950",
                "18114be9a  CALL 0x181294950",
                "18114bea9  CALL 0x181294950",
                "18114beba  CALL 0x181294950",
                "18114bec4  MOV byte ptr [0x181843998],0x1",
                "181292f59  MOV RAX,qword ptr [0x181843990]",
            )),
        },
    }


def static_checks() -> dict[str, bool]:
    decomp = DECOMP.read_text(encoding="utf-8")
    asm = ASM.read_text(encoding="utf-8")
    static_facts = collect_static_fact_witnesses()
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
        "filter_size_primary_static_bytes_and_semantics_are_grounded": static_facts["filter_size_primary"]["bytes"]["hex"] == static_facts["filter_size_primary"]["bytes"]["expected_hex"] and static_facts["filter_size_primary"]["asm_present"] and static_facts["filter_size_primary"]["decomp_present"],
        "filter_size_sibling_static_bytes_and_semantics_are_grounded": static_facts["filter_size_sibling"]["bytes"]["setup_hex"] == static_facts["filter_size_sibling"]["bytes"]["setup_expected_hex"] and static_facts["filter_size_sibling"]["bytes"]["call_hex"] == static_facts["filter_size_sibling"]["bytes"]["call_expected_hex"] and static_facts["filter_size_sibling"]["asm_present"] and static_facts["filter_size_sibling"]["decomp_present"],
        "opencv_dispatch_state_reference_is_grounded": static_facts["opencv_dispatch_state"]["bytes"]["hex"] == static_facts["opencv_dispatch_state"]["bytes"]["expected_hex"] and static_facts["opencv_dispatch_state"]["asm_present"],
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
    allocation_trace: list[dict[str, object]] = []
    mat_trace: list[dict[str, object]] = []
    oom_request: dict[str, object] = {}
    aligned_lifecycle: list[dict[str, object]] = []
    aligned_live: dict[int, dict[str, int]] = {}
    aligned_max_request = 0x100000
    aligned_max_alignment = 0x1000
    fls_lifecycle: list[dict[str, object]] = []
    fls_live_keys: dict[int, dict[str, int]] = {}
    fls_thread_values: dict[int, dict[int, int]] = {}
    control_flow_trace: list[dict[str, object]] = []
    mode2_call_args: dict[str, object] = {}
    mode2_instruction_trace: list[dict[str, object]] = []
    inner_entry: dict[str, object] = {}
    inner_instruction_trace: list[dict[str, object]] = []
    execution_stop: dict[str, object] = {}
    next_runtime_boundary: dict[str, object] = {}
    dispatch_checkpoints: list[dict[str, object]] = []
    filter_setup_trace: list[dict[str, object]] = []

    def dispatch_checkpoint(ld: AexLoader, label: str) -> dict[str, object]:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        inner = struct.unpack("<I", ld.read_bytes(rsp + 0x38, 4))[0]
        outer = struct.unpack("<I", ld.read_bytes(rsp + 0x3C, 4))[0]
        return {
            "label": label,
            "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
            "rsp": hex(rsp),
            "inner": inner,
            "outer": outer,
            "work_coordinate": outer * 0x20 + inner,
            "work_source": hex(read_u64(ld, rsp + 0x68)),
            "work_destination": hex(read_u64(ld, rsp + 0x70)),
        }

    def capture_dispatch_checkpoint(label: str):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            if len(dispatch_checkpoints) < DISPATCH_MAX_CHUNKS * 2:
                dispatch_checkpoints.append(dispatch_checkpoint(ld, label))
        return hook

    loader.add_code_hook(DISPATCH_LOOP_ENTRY, capture_dispatch_checkpoint("dispatch_loop_entry"))
    loader.add_code_hook(DISPATCH_PROGRESS, capture_dispatch_checkpoint("dispatch_outer_progress"))

    def aligned_malloc_probe(_uc: object, args: list[int]) -> int:
        requested, alignment = int(args[0]), int(args[1])
        event: dict[str, object] = {
            "operation": "_aligned_malloc",
            "requested_bytes": requested,
            "alignment": alignment,
            "bounded_contract": {
                "requested_bytes": {"min": 1, "max": aligned_max_request},
                "alignment": {"min": 8, "max": aligned_max_alignment, "power_of_two": True},
            },
        }
        aligned_lifecycle.append(event)
        if (
            requested <= 0
            or requested > aligned_max_request
            or alignment < 8
            or alignment > aligned_max_alignment
            or alignment & (alignment - 1)
        ):
            event.update({"accepted": False, "return": "0x0", "reason": "outside positive bounded power-of-two contract"})
            return 0
        try:
            pointer = loader.host_alloc(requested, align=alignment)
            loader.write_bytes(pointer, b"\0" * requested)
        except Exception as exc:
            event.update({"accepted": False, "return": "0x0", "probe_error": f"{type(exc).__name__}: {exc}"})
            raise
        if pointer <= 0 or pointer % alignment:
            event.update({"accepted": False, "return": "0x0", "reason": "host allocation violated requested alignment"})
            raise RuntimeError(f"_aligned_malloc returned misaligned pointer 0x{pointer:x}")
        aligned_live[pointer] = {"size": requested, "alignment": alignment}
        event.update({"accepted": True, "return": hex(pointer), "lifecycle": "live"})
        return pointer

    def aligned_free_probe(_uc: object, args: list[int]) -> int:
        pointer = int(args[0])
        spec = aligned_live.pop(pointer, None)
        event: dict[str, object] = {"operation": "_aligned_free", "pointer": hex(pointer)}
        aligned_lifecycle.append(event)
        if spec is None:
            event.update({"accepted": False, "reason": "unknown or already-freed pointer"})
            raise RuntimeError(f"_aligned_free lifecycle violation for 0x{pointer:x}")
        if pointer % spec["alignment"]:
            event.update({"accepted": False, "reason": "live pointer no longer satisfies recorded alignment"})
            raise RuntimeError(f"_aligned_free alignment violation for 0x{pointer:x}")
        event.update({"accepted": True, "size": spec["size"], "alignment": spec["alignment"], "lifecycle": "freed"})
        return 0

    loader.register_import_impl("_aligned_malloc", aligned_malloc_probe)
    loader.register_import_impl("_aligned_free", aligned_free_probe)

    # OpenCV's observed TlsAbstraction uses one FLS key on this emulated
    # thread. Keep key allocation and value ownership explicit so a stale key
    # or cross-thread value cannot silently pass the runtime boundary.
    fls_thread_id = TEB_BASE

    def fls_alloc_probe(_uc: object, args: list[int]) -> int:
        callback = int(args[0])
        event: dict[str, object] = {
            "operation": "FlsAlloc",
            "callback": hex(callback),
            "bounded_contract": {"key": 0, "thread": hex(fls_thread_id)},
        }
        fls_lifecycle.append(event)
        if fls_live_keys:
            event.update({"accepted": False, "return": 0xFFFFFFFF, "reason": "one-key contract already allocated"})
            return 0xFFFFFFFF
        if callback != 0x181164520:
            event.update({"accepted": False, "return": 0xFFFFFFFF, "reason": "callback outside observed contract"})
            return 0xFFFFFFFF
        fls_live_keys[0] = {"thread": fls_thread_id, "callback": callback}
        fls_thread_values[fls_thread_id] = {}
        event.update({"accepted": True, "key": 0, "return": 0, "lifecycle": "allocated"})
        return 0

    def fls_get_probe(_uc: object, args: list[int]) -> int:
        key = int(args[0])
        event: dict[str, object] = {"operation": "FlsGetValue", "key": key, "thread": hex(fls_thread_id)}
        fls_lifecycle.append(event)
        if key not in fls_live_keys:
            event.update({"accepted": False, "return": 0, "reason": "unknown or freed key"})
            raise RuntimeError(f"FlsGetValue lifecycle violation for key {key}")
        value = fls_thread_values[fls_thread_id].get(key, 0)
        event.update({"accepted": True, "return": hex(value), "lifecycle": "read"})
        return value

    def fls_set_probe(_uc: object, args: list[int]) -> int:
        key, value = int(args[0]), int(args[1])
        event: dict[str, object] = {
            "operation": "FlsSetValue",
            "key": key,
            "value": hex(value),
            "thread": hex(fls_thread_id),
        }
        fls_lifecycle.append(event)
        if key not in fls_live_keys:
            event.update({"accepted": False, "return": 0, "reason": "unknown or freed key"})
            raise RuntimeError(f"FlsSetValue lifecycle violation for key {key}")
        fls_thread_values[fls_thread_id][key] = value
        event.update({"accepted": True, "return": 1, "lifecycle": "set"})
        return 1

    def fls_free_probe(_uc: object, args: list[int]) -> int:
        key = int(args[0])
        event: dict[str, object] = {"operation": "FlsFree", "key": key, "thread": hex(fls_thread_id)}
        fls_lifecycle.append(event)
        spec = fls_live_keys.pop(key, None)
        if spec is None:
            event.update({"accepted": False, "return": 0, "reason": "unknown or already-freed key"})
            raise RuntimeError(f"FlsFree lifecycle violation for key {key}")
        value = fls_thread_values[fls_thread_id].pop(key, 0)
        event.update({"accepted": True, "return": 1, "cleared_value": hex(value), "lifecycle": "freed"})
        return 1

    loader.register_import_impl("FlsAlloc", fls_alloc_probe)
    loader.register_import_impl("FlsGetValue", fls_get_probe)
    loader.register_import_impl("FlsSetValue", fls_set_probe)
    loader.register_import_impl("FlsFree", fls_free_probe)

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
    suite_events: list[dict[str, object]] = []

    def color_from_def(current: AexLoader, args: list[int]) -> int:
        if args[0] != refcon or args[1] == 0 or args[2] == 0:
            raise RuntimeError("invalid PF ColorParamSuite1 color conversion ABI")
        raw = current.read_bytes(args[1] + 0x38, 4)
        alpha, red, green, blue = raw
        current.write_bytes(
            args[2],
            struct.pack(
                "<4f",
                alpha / 255.0,
                red / 255.0,
                green / 255.0,
                blue / 255.0,
            ),
        )
        callback_state.setdefault("color_conversion", []).append({
            "abi_registers_rcx_rdx_r8_r9": [hex(value) for value in args],
            "param_def_pointer": hex(args[1]),
            "output_pointer": hex(args[2]),
            "input_color_bytes_alpha_red_green_blue": list(raw),
            "return": 0,
            "return_semantics": "PF_Err_NONE",
        })
        return 0

    color_suite = loader.host_alloc(0x08, align=16)
    loader.write_bytes(
        color_suite,
        struct.pack("<Q", loader.install_callback("PFColorParamSuite1.PF_GetFloatingPointColorFromColorDef", color_from_def)),
    )
    handle_events: list[dict[str, object]] = []

    def handle_new(current: AexLoader, args: list[int]) -> int:
        size = args[0] & 0xFFFFFFFFFFFFFFFF
        if size > 0x1000000:
            raise RuntimeError(f"unbounded PF Handle Suite new size 0x{size:x}")
        data = current.bump_alloc(max(size, 1), align=64)
        current.write_bytes(data, b"\0" * max(size, 1))
        handle = current.host_alloc(0x08, align=16)
        current.write_bytes(handle, struct.pack("<Q", data))
        handle_events.append({
            "callback": "PF_HandleSuite1.new",
            "size": size,
            "handle": hex(handle),
            "data": hex(data),
            "return": hex(handle),
        })
        return handle

    def handle_lock(current: AexLoader, args: list[int]) -> int:
        handle = args[0]
        data = struct.unpack("<Q", current.read_bytes(handle, 8))[0] if handle else 0
        handle_events.append({
            "callback": "PF_HandleSuite1.lock",
            "handle": hex(handle),
            "data": hex(data),
            "return": hex(data),
        })
        return data

    def handle_unlock(current: AexLoader, args: list[int]) -> int:
        handle_events.append({
            "callback": "PF_HandleSuite1.unlock",
            "handle": hex(args[0]),
            "return": 0,
            "return_semantics": "PF_Err_NONE",
        })
        return 0

    def handle_dispose(current: AexLoader, args: list[int]) -> int:
        handle_events.append({
            "callback": "PF_HandleSuite1.dispose",
            "handle": hex(args[0]),
            "return": 0,
            "return_semantics": "PF_Err_NONE",
        })
        return 0

    handle_suite = loader.host_alloc(0x20, align=16)
    loader.write_bytes(
        handle_suite,
        struct.pack(
            "<4Q",
            loader.install_callback("PF_HandleSuite1.new", handle_new),
            loader.install_callback("PF_HandleSuite1.lock", handle_lock),
            loader.install_callback("PF_HandleSuite1.unlock", handle_unlock),
            loader.install_callback("PF_HandleSuite1.dispose", handle_dispose),
        ),
    )

    def read_c_string(current: AexLoader, address: int) -> str:
        raw = bytearray()
        for offset in range(128):
            byte = current.read_bytes(address + offset, 1)
            if byte == b"\0":
                break
            raw.extend(byte)
        return raw.decode("ascii", errors="replace")

    def acquire_suite(current: AexLoader, args: list[int]) -> int:
        name = read_c_string(current, args[0])
        version = args[1] & 0xFFFFFFFF
        out_pointer = args[2]
        if name == "PF ColorParamSuite" and version == 1:
            returned_suite = color_suite
            contract = "PF ColorParamSuite1 v1"
        elif name == "PF Handle Suite" and version == 2:
            returned_suite = handle_suite
            contract = "PF Handle Suite v2"
        else:
            returned_suite = None
            contract = "rejected"
        accepted = returned_suite is not None
        if accepted:
            current.write_bytes(out_pointer, struct.pack("<Q", returned_suite))
        suite_events.append({
            "callback": "SPBasic.AcquireSuite",
            "name": name,
            "version": version,
            "out_pointer": hex(out_pointer),
            "returned_suite": hex(returned_suite) if accepted else None,
            "return": 0 if accepted else 1,
            "contract": contract,
        })
        return 0 if accepted else 1

    def release_suite(current: AexLoader, args: list[int]) -> int:
        suite_events.append({
            "callback": "SPBasic.ReleaseSuite",
            "name": read_c_string(current, args[0]),
            "version": args[1] & 0xFFFFFFFF,
            "return": 0,
            "return_semantics": "PF_Err_NONE",
        })
        return 0

    spbasic = loader.host_alloc(0x10, align=16)
    loader.write_bytes(
        spbasic,
        struct.pack(
            "<2Q",
            loader.install_callback("SPBasic.AcquireSuite", acquire_suite),
            loader.install_callback("SPBasic.ReleaseSuite", release_suite),
        ),
    )
    loader.write_bytes(context + 0x180, struct.pack("<Q", spbasic))

    # FUN_181159da0's lazy C++ runtime path reads the Windows TLS pointer
    # table through GS:[0x58], then reads the selected slot's epoch at +0x4.
    # The checked-in image has _tls_index == 0; install only that bounded
    # single-thread storage contract and leave initialization to the AEX.
    tls_table = loader.host_alloc(TLS_TABLE_SIZE, align=16)
    tls_slot = loader.host_alloc(TLS_SLOT_SIZE, align=16)
    loader.write_bytes(tls_table, struct.pack("<Q", tls_slot))
    loader.write_bytes(tls_slot, b"\0" * TLS_SLOT_SIZE)
    loader.write_bytes(tls_slot + TLS_EPOCH_OFFSET, struct.pack("<i", TLS_UNINITIALIZED_EPOCH))
    loader.write_bytes(TEB_BASE + GS_TLS_OFFSET, struct.pack("<Q", tls_table))
    # The actual-AEX bootstrap expects this process global to name writable
    # storage. The binary itself populates it through FUN_18114be60.
    opencv_dispatch_table = loader.host_alloc(OPENCV_DISPATCH_TABLE_BYTES, align=64)
    loader.write_bytes(opencv_dispatch_table, b"\0" * OPENCV_DISPATCH_TABLE_BYTES)
    loader.write_bytes(OPENCV_DISPATCH_GLOBAL, struct.pack("<Q", opencv_dispatch_table))
    loader.write_bytes(OPENCV_DISPATCH_READY_FLAG, b"\0")
    opencv_bootstrap_calls: list[dict[str, object]] = []

    def capture_opencv_bootstrap_call(ld: AexLoader, _address: int, _size: int) -> None:
        opencv_bootstrap_calls.append({
            "call": len(opencv_bootstrap_calls) + 1,
            "function": "FUN_181294950",
            "channels": ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF,
            "table_write": ld.uc.reg_read(UC_X86_REG_RDX) & 0xFF,
            "return_address": hex(read_u64(ld, ld.uc.reg_read(UC_X86_REG_RSP))),
        })

    loader.add_code_hook(0x181294950, capture_opencv_bootstrap_call)
    bootstrap_ready_before = loader.read_bytes(OPENCV_DISPATCH_READY_FLAG, 1)[0]
    bootstrap_result = loader.call_function(
        OPENCV_DISPATCH_BOOTSTRAP,
        max_instructions=OPENCV_BOOTSTRAP_MAX_INSTRUCTIONS,
    )
    bootstrap_terminal_rip = loader.uc.reg_read(UC_X86_REG_RIP)
    coefficient_region = loader.read_bytes(
        opencv_dispatch_table,
        OPENCV_DISPATCH_COEFFICIENT_BYTES,
    )
    coefficient_nonzero_bytes = sum(byte != 0 for byte in coefficient_region)
    bootstrap_ready_after = loader.read_bytes(OPENCV_DISPATCH_READY_FLAG, 1)[0]
    expected_bootstrap_args = [(1, 0), (1, 1), (2, 0), (2, 1), (4, 0), (4, 1)]
    observed_bootstrap_args = [
        (int(item["channels"]), int(item["table_write"]))
        for item in opencv_bootstrap_calls
    ]
    bootstrap_call_witness = list(opencv_bootstrap_calls)
    if bootstrap_terminal_rip != 0x90000000:
        raise RuntimeError(
            f"FUN_18114be60 did not return within {OPENCV_BOOTSTRAP_MAX_INSTRUCTIONS} instructions; "
            f"RIP=0x{bootstrap_terminal_rip:x} ready={bootstrap_ready_after} "
            f"coefficient_nonzero_bytes={coefficient_nonzero_bytes}"
        )
    if observed_bootstrap_args != expected_bootstrap_args:
        raise RuntimeError(
            f"FUN_18114be60 call sequence mismatch: observed={observed_bootstrap_args!r}"
        )
    if bootstrap_ready_after != 1 or coefficient_nonzero_bytes == 0:
        raise RuntimeError(
            f"FUN_18114be60 incomplete state: ready={bootstrap_ready_after} "
            f"coefficient_nonzero_bytes={coefficient_nonzero_bytes}"
        )
    # Bootstrap checkpoints are initialization evidence, not Mode2 progress.
    dispatch_checkpoints.clear()
    runtime_state = {
        "tls_index_global": hex(TLS_INDEX_GLOBAL),
        "tls_index_value": struct.unpack("<I", loader.read_bytes(TLS_INDEX_GLOBAL, 4))[0],
        "gs_tls_address": hex(TEB_BASE + GS_TLS_OFFSET),
        "tls_table": hex(tls_table),
        "tls_slot": hex(tls_slot),
        "tls_epoch_address": hex(tls_slot + TLS_EPOCH_OFFSET),
        "tls_epoch_initial": TLS_UNINITIALIZED_EPOCH,
        "contract": "GS:[0x58] -> TLS table; table[0] -> slot; slot+0x04 -> lazy-init epoch",
        "opencv_dispatch_global": hex(OPENCV_DISPATCH_GLOBAL),
        "opencv_dispatch_table": hex(opencv_dispatch_table),
        "opencv_dispatch_table_bytes": OPENCV_DISPATCH_TABLE_BYTES,
        "opencv_dispatch_table_contract": "emulated writable 0x10000-byte backing store, 64-byte aligned; populated only by actual FUN_18114be60 -> FUN_181294950 execution",
        "opencv_bootstrap": {
            "function": "FUN_18114be60",
            "boundary": "complete actual bootstrap; no narrower direct-call fallback required",
            "max_instructions": OPENCV_BOOTSTRAP_MAX_INSTRUCTIONS,
            "instructions": bootstrap_result["instructions"],
            "terminal_rip": hex(bootstrap_terminal_rip),
            "calls": bootstrap_call_witness,
            "expected_arguments": [list(args) for args in expected_bootstrap_args],
            "arguments_match": observed_bootstrap_args == expected_bootstrap_args,
            "ready_flag": {
                "address": hex(OPENCV_DISPATCH_READY_FLAG),
                "before": bootstrap_ready_before,
                "after": bootstrap_ready_after,
                "verified": bootstrap_ready_after == 1,
            },
            "coefficient_region": {
                "pointer_source": hex(OPENCV_DISPATCH_GLOBAL),
                "pointer": hex(opencv_dispatch_table),
                "bytes": OPENCV_DISPATCH_COEFFICIENT_BYTES,
                "nonzero_bytes": coefficient_nonzero_bytes,
                "contains_nonzero": coefficient_nonzero_bytes > 0,
                "sha256": hashlib.sha256(coefficient_region).hexdigest(),
                "head_64_hex": coefficient_region[:64].hex(),
            },
        },
    }

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

    def capture_mat_constructor(ld: AexLoader, _address: int, _size: int) -> None:
        args = [ld.uc.reg_read(reg) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8)]
        entry = {"address": "0x181157450", "args": [hex(value) for value in args]}
        entry["source_mat"] = mat_snapshot(ld, args[1])
        ranges = args[2]
        dims = struct.unpack("<i", ld.read_bytes(args[1] + 0x4, 4))[0]
        if ranges and 0 <= dims <= 32:
            entry["ranges"] = [
                hex(read_u64(ld, ranges + i * 8)) for i in range(dims)
            ]
        mat_trace.append(entry)

    def capture_mat_copy(ld: AexLoader, _address: int, _size: int) -> None:
        args = [ld.uc.reg_read(reg) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX)]
        mat_trace.append({
            "address": "0x181157ed0",
            "destination": mat_snapshot(ld, args[0]),
            "source": mat_snapshot(ld, args[1]),
        })

    def capture_allocation_request(ld: AexLoader, _address: int, _size: int) -> None:
        request = ld.uc.reg_read(UC_X86_REG_RCX)
        allocation_trace.append({
            "allocator": "FUN_18115eb30",
            "mat_storage_request": request,
            "malloc_request_if_memalign_disabled": request + 0x48,
            "aligned_malloc_request_if_memalign_enabled": request,
            "alignment": 0x40,
        })

    def capture_oom_request(ld: AexLoader, _address: int, _size: int) -> None:
        request = ld.uc.reg_read(UC_X86_REG_RCX)
        oom_request.update({
            "address": "0x18115ea40",
            "requested_bytes": request,
            "message": f"Failed to allocate {request} bytes",
        })

    def capture_error_message(ld: AexLoader, _address: int, _size: int) -> None:
        message_address = ld.uc.reg_read(UC_X86_REG_RDX)
        try:
            message = read_std_string(ld, message_address)
        except Exception as exc:
            message = f"<unreadable std::string: {type(exc).__name__}: {exc}>"
        runtime_error_boundary["message"] = message

    loader.add_code_hook(0x1811542B0, capture_internal(0x1811542B0, "FUN_1811542b0 entry"))
    loader.add_code_hook(0x181154300, capture_internal(0x181154300, "parameter-table compare before invalid read"))
    loader.add_code_hook(0x1812326E0, capture_internal(0x1812326E0, "PF_ParamCheckout callback pointer before CALL R10"))
    loader.add_code_hook(0x181232350, capture_internal(0x181232350, "PF ColorParamSuite acquire path"))
    loader.add_code_hook(0x181232760, capture_internal(0x181232760, "context callback pointer before CALL RAX"))
    loader.add_code_hook(0x181159deb, capture_internal(0x181159deb, "lazy runtime TLS epoch read"))
    loader.add_code_hook(0x181162610, capture_internal(0x181162610, "next runtime exception boundary"))

    def capture_control_flow(label: str, address: int):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            rdi = ld.uc.reg_read(UC_X86_REG_RDI)
            entry: dict[str, object] = {
                "address": hex(address),
                "label": label,
                "registers_rcx_rdx_r8_r9_rax_rdi": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RDI)],
            }
            if label.startswith("PF32 mode compare"):
                mode_value = struct.unpack("<i", ld.read_bytes(rdi + 0x40, 4))[0]
                entry.update({
                    "mode_field_address": hex(rdi + 0x40),
                    "mode_value": mode_value,
                    "binary_branch": {"1": "FUN_18114edb0", "2": "FUN_1811505c0", "4": "FUN_18114ec20", "other": "FUN_18114eed0"}.get(str(mode_value), "ambiguous"),
                })
            if label.startswith("Mode2 inner mode"):
                rbp = ld.uc.reg_read(UC_X86_REG_RBP)
                inner_value = struct.unpack("<i", ld.read_bytes(rbp + 0x198, 4))[0]
                entry.update({
                    "inner_mode_field_address": hex(rbp + 0x198),
                    "inner_mode_value": inner_value,
                    "binary_branch": {"1": "0x18115122e", "2": "0x18115110a", "3": "0x1811510a9", "other": "0x181150f3d"}.get(str(inner_value), "ambiguous"),
                })
            control_flow_trace.append(entry)
        return hook

    loader.add_code_hook(0x18114c924, capture_control_flow("common PF depth read/dispatch compare", 0x18114c924))
    loader.add_code_hook(0x18114c9a4, capture_control_flow("common PF depth branch", 0x18114c9a4))
    loader.add_code_hook(0x18114c9cc, capture_control_flow("common PF depth branch", 0x18114c9cc))
    loader.add_code_hook(0x18114c9f4, capture_control_flow("common PF depth branch", 0x18114c9f4))
    loader.add_code_hook(0x18114ca15, capture_control_flow("PF32 owner entry", 0x18114ca15))
    loader.add_code_hook(0x18114daeb, capture_control_flow("PF32 mode compare value load", 0x18114daeb))
    loader.add_code_hook(0x18114daf3, capture_control_flow("PF32 mode compare branch 1", 0x18114daf3))
    loader.add_code_hook(0x18114db13, capture_control_flow("PF32 mode compare branch 2", 0x18114db13))
    loader.add_code_hook(0x18114db33, capture_control_flow("PF32 mode compare branch 4", 0x18114db33))
    loader.add_code_hook(MODE2_DISPATCH, capture_control_flow("Mode2 dispatch entry", MODE2_DISPATCH))
    loader.add_code_hook(PF32_TYPED_OWNER, capture_control_flow("PF32 typed owner entry", PF32_TYPED_OWNER))
    for writer_address in PF32_CALLSITES:
        loader.add_code_hook(writer_address, capture_control_flow("PF32 typed writer callsite", writer_address))

    def capture_mode2_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        mode2_call_args.update({
            "entry_stack": {f"+0x{offset:x}": hex(read_u64(ld, rsp + offset)) for offset in range(0x20, 0x58, 8)},
            "param10_stack_value": struct.unpack("<i", ld.read_bytes(rsp + 0x50, 4))[0],
            "param10_source": "FUN_18114d7f0 caller [RSP+0x50] = PF32 local param_5 + 0x4c",
        })
    loader.add_code_hook(MODE2_DISPATCH, capture_mode2_entry)

    def capture_mode2_branch(label: str, address: int):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            entry: dict[str, object] = {
                "address": hex(address),
                "label": label,
                "registers_rcx_rdx_r8_r9_rax_rbx_rsi_rdi": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RSI, UC_X86_REG_RDI)],
            }
            if label == "Mode2 plane branch":
                entry["plane_test_value"] = ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF
            control_flow_trace.append(entry)
        return hook
    loader.add_code_hook(0x18114dc01, capture_control_flow("Mode2 dispatch return site", 0x18114dc01))
    loader.add_code_hook(0x18114dd0d, capture_control_flow("PF32 typed owner callsite", 0x18114dd0d))
    loader.add_code_hook(0x18114f760, capture_mode2_branch("Mode2 plane branch", 0x18114f760))
    loader.add_code_hook(0x18114f770, capture_mode2_branch("Mode2 special-plane branch", 0x18114f770))
    loader.add_code_hook(0x18114f9a1, capture_mode2_branch("Mode2 early-exit target", 0x18114f9a1))
    loader.add_code_hook(0x18114fd54, capture_control_flow("Mode2 epilogue before return", 0x18114fd54))
    for address, label in (
        (0x181150790, "Mode2 inner helper entry"),
        (0x18115094f, "Mode2 inner mode value load"),
        (0x181150955, "Mode2 inner mode branch 1"),
        (0x18115095e, "Mode2 inner mode branch 2"),
        (0x181150967, "Mode2 inner mode branch 3"),
        (0x181150970, "Mode2 inner mode branch 4"),
    ):
        loader.add_code_hook(address, capture_control_flow(label, address))

    mode2_asm = slice_between(ASM.read_text(encoding="utf-8"), "; === FUN_18114f4a0", "; === FUN_18114fd90")
    for line in mode2_asm.splitlines():
        match = re.match(r"([0-9a-f]+)\s+(.+)$", line)
        if not match:
            continue
        address = int(match.group(1), 16)
        if not 0x18114f770 <= address <= 0x18114fd54:
            continue
        mnemonic = match.group(2).strip()

        def trace_mode2_instruction(ld: AexLoader, _address: int, _size: int, *, address=address, mnemonic=mnemonic) -> None:
            if len(mode2_instruction_trace) < 512:
                mode2_instruction_trace.append({
                    "address": hex(address),
                    "instruction": mnemonic,
                    "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
                    "rax": hex(ld.uc.reg_read(UC_X86_REG_RAX)),
                    "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
                    "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
                    "r8": hex(ld.uc.reg_read(UC_X86_REG_R8)),
                    "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
                })
        loader.add_code_hook(address, trace_mode2_instruction)

    inner_asm = slice_between(ASM.read_text(encoding="utf-8"), "; === FUN_181150790", "; === FUN_1811512a0")
    for line in inner_asm.splitlines():
        match = re.match(r"([0-9a-f]+)\s+(.+)$", line)
        if not match:
            continue
        address = int(match.group(1), 16)
        mnemonic = match.group(2).strip()

        def trace_inner_instruction(ld: AexLoader, _address: int, _size: int, *, address=address, mnemonic=mnemonic) -> None:
            if len(inner_instruction_trace) < 512:
                inner_instruction_trace.append({
                    "address": hex(address),
                    "instruction": mnemonic,
                    "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
                    "rax": hex(ld.uc.reg_read(UC_X86_REG_RAX)),
                    "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
                    "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
                    "r8": hex(ld.uc.reg_read(UC_X86_REG_R8)),
                    "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
                    "kind": "branch_or_call" if mnemonic.startswith(("CALL", "J", "RET")) else "instruction",
                })
        loader.add_code_hook(address, trace_inner_instruction)

    def capture_inner_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        inner_entry.update({
            "address": "0x181150790",
            "registers_rcx_rdx_r8_r9": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
            "stack_args": {f"+0x{offset:x}": hex(read_u64(ld, rsp + offset)) for offset in range(0x20, 0x50, 8)},
            "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
        })
    loader.add_code_hook(0x181150790, capture_inner_entry)
    loader.add_code_hook(0x181157450, capture_mat_constructor)
    loader.add_code_hook(0x181157ed0, capture_mat_copy)
    loader.add_code_hook(0x18115eb30, capture_allocation_request)
    loader.add_code_hook(0x18115ea40, capture_oom_request)
    loader.add_code_hook(0x181162610, capture_error_message)

    runtime_error_boundary: dict[str, object] = {}

    def capture_runtime_error(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        error_code = ld.uc.reg_read(UC_X86_REG_RCX) & 0xFFFFFFFF
        if error_code & 0x80000000:
            error_code -= 0x100000000
        runtime_error_boundary.update({
            "address": "0x181162610",
            "kind": "cv::Exception construction and non-returning throw path",
            "error_code": error_code,
            "exception_class": read_c_string(ld, ld.uc.reg_read(UC_X86_REG_R8)),
            "source_file": read_c_string(ld, ld.uc.reg_read(UC_X86_REG_R9)),
            "line": struct.unpack("<I", ld.read_bytes(rsp + 0x170, 4))[0],
            "caller_return_address": hex(read_u64(ld, rsp)),
            "throw_helper": "FUN_181162500 -> _CxxThrowException; 0x181162672 INT3 fallback",
        })

    loader.add_code_hook(0x181162610, capture_runtime_error)
    def capture_filter_setup(label: str):
        def hook(ld: AexLoader, _address: int, _size: int) -> None:
            rsp = ld.uc.reg_read(UC_X86_REG_RSP)
            rcx = ld.uc.reg_read(UC_X86_REG_RCX)
            rdx = ld.uc.reg_read(UC_X86_REG_RDX)
            entry: dict[str, object] = {
                "label": label,
                "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
                "return_address": hex(read_u64(ld, rsp)),
                "rcx": hex(rcx),
                "rdx": hex(rdx),
                "xmm2_f64": struct.unpack("<d", int(ld.uc.reg_read(UC_X86_REG_XMM2) & ((1 << 64) - 1)).to_bytes(8, "little"))[0],
            }
            if label == "FilterEngine setup entry":
                entry.update({
                    "rcx_size_xy_i32": [struct.unpack("<i", ld.read_bytes(rcx + offset, 4))[0] for offset in (0, 4)],
                    "rdx_structure_0x00_0x40": ld.read_bytes(rdx, 0x40).hex(),
                })
            filter_setup_trace.append(entry)
        return hook

    loader.add_code_hook(0x1811D88C0, capture_filter_setup("FilterEngine setup entry"))
    loader.add_code_hook(0x1811D8A50, capture_filter_setup("FilterEngine init body"))

    def capture_filter_engine_init(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        structure = ld.uc.reg_read(UC_X86_REG_RCX)
        filter_setup_trace.append({
            "label": "FilterEngine::init entry",
            "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
            "return_address": hex(read_u64(ld, rsp)),
            "structure": hex(structure),
            "structure_i32": {
                f"+0x{offset:x}": struct.unpack("<i", ld.read_bytes(structure + offset, 4))[0]
                for offset in (0x8, 0xc, 0x10, 0x14, 0x18, 0x1c, 0x20, 0x60)
            },
            "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(ld.uc.reg_read(UC_X86_REG_R8)),
            "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
        })

    loader.add_code_hook(0x1812B9DB0, capture_filter_engine_init)
    loader.add_code_hook(0x1812AEB72, capture_filter_engine_init)
    loader.add_code_hook(0x1812B9DA8, lambda ld, _address, _size: filter_setup_trace.append({
        "label": "FilterEngine assertion callsite",
        "rip": hex(ld.uc.reg_read(UC_X86_REG_RIP)),
        "return_address": hex(read_u64(ld, ld.uc.reg_read(UC_X86_REG_RSP))),
        "rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
        "rdx": hex(ld.uc.reg_read(UC_X86_REG_RDX)),
        "r8": hex(ld.uc.reg_read(UC_X86_REG_R8)),
        "r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
        "rbp": hex(ld.uc.reg_read(UC_X86_REG_RBP)),
    }))
    loader.add_code_hook(0x18132c184, lambda ld, _address, _size: next_runtime_boundary.update({
        "address": "0x18132c184",
        "kind": "CRT exception object construction before _CxxThrowException",
        "registers_rcx_rdx_r8_r9": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
    }))
    loader.add_code_hook(0x18132d5d6, lambda ld, _address, _size: next_runtime_boundary.update({
        "address": "0x18132d5d6",
        "kind": "_CxxThrowException import boundary",
        "registers_rcx_rdx_r8_r9": [hex(ld.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
        "caller_return_address": hex(read_u64(ld, ld.uc.reg_read(UC_X86_REG_RSP))),
    }))

    def runtime_imports() -> list[dict[str, object]]:
        return [
            {"name": item.name, "args": [hex(arg) for arg in item.args], "ret": hex(item.ret)}
            for item in loader.import_log
            if item.name in {"malloc", "_aligned_malloc", "_aligned_free", "free", "FlsAlloc", "FlsGetValue", "FlsSetValue", "FlsFree", "_CxxThrowException"}
        ]

    def unimplemented_imports() -> list[str]:
        return sorted({
            item.name for item in loader.import_log
            if item.name not in loader.import_impls
        })

    def aligned_request_trace() -> list[dict[str, object]]:
        return [
            {
                "requested_bytes": event["requested_bytes"],
                "alignment": event["alignment"],
                "accepted": event["accepted"],
                "return": event["return"],
            }
            for event in aligned_lifecycle
            if event["operation"] == "_aligned_malloc"
        ]

    def selector_diagnosis() -> dict[str, object]:
        mode_compares = [item for item in control_flow_trace if item["label"] == "PF32 mode compare value load"]
        blur_readbacks = [
            item for item in callback_state.get("param_checkout", [])
            if item.get("disk_id") == 9
        ]
        mode_values = [item.get("mode_value") for item in mode_compares]
        ambiguous = [item for item in mode_compares if item.get("binary_branch") == "ambiguous"]
        inner_modes = [item for item in control_flow_trace if item["label"] == "Mode2 inner mode value load"]
        inner_ambiguous = [item for item in inner_modes if item.get("binary_branch") == "ambiguous"]
        mode2_entered = any(item["label"] == "Mode2 dispatch entry" for item in control_flow_trace)
        typed_entered = any(item["label"] == "PF32 typed owner entry" for item in control_flow_trace)
        return {
            "parameter_disk_id": 9,
            "parameter_name": "Blur Mode",
            "checkout_readback": blur_readbacks,
            "pf32_mode_field_values": mode_values,
            "mode2_dispatch_entered": mode2_entered,
            "typed_owner_entered": typed_entered,
            "mode2_epilogue_reached": any(item["label"] == "Mode2 epilogue before return" for item in control_flow_trace),
            "ambiguous_branch": bool(ambiguous or inner_ambiguous),
            "ambiguous_branch_trace": ambiguous + inner_ambiguous,
            "mode2_inner_selector_values": [item.get("inner_mode_value") for item in inner_modes],
            "mode2_inner_selector_trace": inner_modes,
            "fixture_intended_mode2_selected": bool(mode2_entered and not ambiguous and mode_values and all(value == 2 for value in mode_values)),
            "binary_grounding": "PF32 owner compares [param_5+0x40] against 1, 2, and 4; value 2 selects FUN_1811505c0 before FUN_18114f4a0 Mode2 dispatch",
        }

    def allocation_diagnosis() -> dict[str, object]:
        source = mat_trace[0].get("source", {}) if mat_trace else {}
        flags = int(source.get("flags", "0"), 16) if isinstance(source, dict) else 0
        type_code = flags & 0xFFF
        aligned_return = next(
            (event.get("return") for event in aligned_lifecycle if event.get("operation") == "_aligned_malloc"),
            "0x0",
        )
        if oom_request:
            requested = int(oom_request["requested_bytes"])
            next_contract: object = {
                "kind": "bounded aligned allocator extension",
                "boundary": "FUN_18115eb30 -> _aligned_malloc",
                "requested_bytes": requested,
                "alignment": 64,
                "success_return": "aligned writable storage",
                "lifecycle": "match _aligned_free; reject unknown or double-freed pointers",
                "fail_closed": True,
            }
            classification = "bounded_fls_lifecycle_crossed_next_aligned_allocator_boundary"
            owner_tail = "FUN_18115ea40 OOM constructor (requested bytes recorded below)"
        elif runtime_error_boundary.get("exception_class") == "cv::FilterEngine::init":
            next_contract = {
                "kind": "binary-generated invalid FilterEngine anchor/ksize relation after verified OpenCV bootstrap",
                "boundary": "FUN_181162610",
                "exception_class": runtime_error_boundary.get("exception_class"),
                "source_file": runtime_error_boundary.get("source_file"),
                "line": runtime_error_boundary.get("line"),
                "assertion": runtime_error_boundary.get("message"),
                "static_size_fact": "Size=(0,5) is binary-generated here: width/x is explicitly zeroed and height/y is loaded from the stack local observed as 5; do not classify it as missing fixture geometry and do not invent width",
                "opencv_bootstrap_result": "Actual FUN_18114be60 returned, set DAT_181843998=1, and populated a nonzero 0x8000-byte coefficient region; the assertion persisted, so the former zero-table shortcut is not the cause of this stop.",
                "fail_closed": True,
            }
            classification = "verified_opencv_bootstrap_crossed_then_filterengine_anchor_assertion_persisted"
            owner_tail = "FUN_181162610 cv::FilterEngine::init anchor/ksize throw path from filter.dispatch.cpp:5"
        elif runtime_error_boundary:
            next_contract = {
                "kind": "OpenCV cv::Exception boundary",
                "boundary": "FUN_181162610",
                "exception_class": runtime_error_boundary.get("exception_class"),
                "source_file": runtime_error_boundary.get("source_file"),
                "line": runtime_error_boundary.get("line"),
                "assertion": runtime_error_boundary.get("message"),
                "fail_closed": True,
            }
            classification = "bounded_aligned_allocator_contract_crossed_next_opencv_exception_boundary"
            owner_tail = "FUN_181162610 cv::Exception throw path"
        else:
            next_contract = {
                "kind": "common-owner return / natural writer gate",
                "boundary": "FUN_18114c8f0 return",
                "condition": "required PF32 typed writer callsite was not reached",
                "fail_closed": True,
            }
            classification = "bounded_allocator_and_fls_lifecycle_crossed_writer_gate"
            owner_tail = "FUN_18114c8f0 returned without typed writer call"
        return {
            "classification": classification,
            "owner_chain": [
                "FUN_181157ed0 cv::Mat copy",
                "FUN_181159ff0 / cv::Mat storage creation",
                "FUN_18115eb30 allocation wrapper",
                owner_tail,
            ],
            "source_geometry": {
                "rows": source.get("rows") if isinstance(source, dict) else None,
                "cols": source.get("cols") if isinstance(source, dict) else None,
                "flags": source.get("flags") if isinstance(source, dict) else None,
                "type_code": type_code,
                "depth_code": type_code & 0x7,
                "channels": ((type_code >> 3) & 0x1FF) + 1,
                "step_values": source.get("step_values") if isinstance(source, dict) else None,
                "data_bytes": 16,
            },
            "allocation_request": oom_request,
            "allocator_import": {
                "name": "_aligned_malloc",
                "requested_bytes": 16,
                "alignment": 64,
                "returned": aligned_return,
                "all_requests": aligned_request_trace(),
                "grounding": "FUN_18115eb30 selects _aligned_malloc(size, 0x40) when OPENCV_ENABLE_MEMALIGN is enabled",
            },
            "next_contract": next_contract,
            "fail_closed": True,
        }
    try:
        call_result = loader.call_function(
            COMMON_OWNER,
            int_args=[param_table, context, 0, descriptor],
            max_instructions=DISPATCH_CHUNK_INSTRUCTIONS,
        )
        chunk_results = [{"chunk": 1, "instructions": call_result.get("instructions"), "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP))}]
        progress_history: list[dict[str, object]] = []
        previous_progress: tuple[int, int, int, int] | None = None
        repeated_checkpoint: dict[str, object] | None = None
        dispatch_fault: dict[str, object] | None = None
        while loader.uc.reg_read(UC_X86_REG_RIP) != 0x90000000 and len(chunk_results) < DISPATCH_MAX_CHUNKS:
            current_rip = loader.uc.reg_read(UC_X86_REG_RIP)
            if current_rip == DISPATCH_LOOP_ENTRY:
                checkpoint = dispatch_checkpoint(loader, "chunk_boundary")
                progress = (
                    int(checkpoint["work_coordinate"]),
                    int(checkpoint["inner"]),
                    int(checkpoint["outer"]),
                    int(checkpoint["work_source"], 16),
                )
                if previous_progress is not None and progress <= previous_progress:
                    repeated_checkpoint = checkpoint
                    break
                previous_progress = progress
                progress_history.append(checkpoint)
            before = loader.instructions_executed
            try:
                loader.uc.emu_start(current_rip, 0x90000000, count=DISPATCH_CHUNK_INSTRUCTIONS)
            except Exception as exc:
                dispatch_fault = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
                    "registers_rcx_rdx_r8_r9": [hex(loader.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)],
                }
                break
            chunk_results.append({
                "chunk": len(chunk_results) + 1,
                "instructions": loader.instructions_executed - before,
                "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            })
        terminal_rip = loader.uc.reg_read(UC_X86_REG_RIP)
        if repeated_checkpoint:
            execution_stop.update({
                "condition": "repeated checkpoint; fail closed",
                "rip": hex(terminal_rip),
                "dispatch": {
                    "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
                    "max_chunks": DISPATCH_MAX_CHUNKS,
                    "chunks": chunk_results,
                    "progress_history": progress_history,
                    "repeated_checkpoint": repeated_checkpoint,
                },
            })
        elif dispatch_fault:
            terminal = "fixture_state_fault"
            condition = "dispatch fixture-state fault; fail closed"
            if runtime_error_boundary.get("exception_class") == "cv::FilterEngine::init":
                terminal = "filterengine_anchor_assertion_after_verified_bootstrap"
                condition = "FilterEngine anchor assertion persisted after verified bootstrap; fail closed"
            execution_stop.update({
                "condition": condition,
                "rip": dispatch_fault["rip"],
                "dispatch_fault": dispatch_fault,
                "dispatch": {
                    "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
                    "max_chunks": DISPATCH_MAX_CHUNKS,
                    "chunks": chunk_results,
                    "progress_history": progress_history,
                    "terminal": terminal,
                },
            })
        elif terminal_rip == 0x90000000:
            execution_stop.update({
                "condition": "RETURN_TRAMPOLINE emulation stop",
                "rip": hex(terminal_rip),
                "dispatch": {
                    "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
                    "max_chunks": DISPATCH_MAX_CHUNKS,
                    "chunks": chunk_results,
                    "progress_history": progress_history,
                    "terminal": "returned",
                },
            })
        elif len(chunk_results) >= DISPATCH_MAX_CHUNKS:
            execution_stop.update({
                "condition": "dispatch chunk cap exhausted; fail closed",
                "rip": hex(terminal_rip),
                "dispatch": {
                    "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
                    "max_chunks": DISPATCH_MAX_CHUNKS,
                    "chunks": chunk_results,
                    "progress_history": progress_history,
                    "terminal": "chunk_cap",
                },
            })
        stop_rip = loader.uc.reg_read(UC_X86_REG_RIP)
        execution_stop.update({
            "rip": hex(stop_rip),
            "rsp": hex(loader.uc.reg_read(UC_X86_REG_RSP)),
            "instructions": sum(item["instructions"] for item in chunk_results),
            "rax": hex(loader.uc.reg_read(UC_X86_REG_RAX)),
            "registers_rcx_rdx_r8_r9_rbp_rsi_rdi": [hex(loader.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RBP, UC_X86_REG_RSI, UC_X86_REG_RDI)],
            "grounded_location": "FUN_181294950 dispatch loop at 0x181294ad5" if stop_rip == DISPATCH_LOOP_ENTRY else None,
        })
        dispatch_terminal = execution_stop.get("dispatch", {}).get("terminal")
        dispatch_diagnosis = {
            "strategy": "resume the original call frame at the current RIP; do not re-enter FUN_181150790",
            "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
            "max_chunks": DISPATCH_MAX_CHUNKS,
            "progress_invariant": "work_coordinate = outer*0x20 + inner; each dispatch_loop_entry checkpoint must strictly increase it",
            "terminal_classification": {
                "typed_writer": False,
                "returned": dispatch_terminal == "returned",
                "repeated_fixture_state": execution_stop.get("condition") == "repeated checkpoint; fail closed",
                "fixture_state_fault": dispatch_terminal == "fixture_state_fault",
                "classification": dispatch_terminal or "unknown",
            },
        }
        filter_failure = None
        if runtime_error_boundary.get("exception_class") == "cv::FilterEngine::init":
            size_entry = next((item for item in filter_setup_trace if item.get("label") == "FilterEngine setup entry"), {})
            filter_failure = {
                "smallest_invalid_state": {
                    "kind": "generated cv::Size kernel geometry",
                    "owner": "FUN_181298180 / sibling stack locals passed to FUN_1811d88c0",
                    "passed_to": "FUN_1811d88c0 RCX",
                    "observed_xy": size_entry.get("rcx_size_xy_i32"),
                    "observed_height_y": size_entry.get("rcx_size_xy_i32", [None, None])[1],
                    "invalid_field": "binary-generated width/x == 0",
                },
                "associated_mat": {
                    "owner": "FUN_1811d88c0 RDX structure",
                    "observed_shape": "5x5",
                    "observed_header_hex": size_entry.get("rdx_structure_0x00_0x40"),
                },
                "static_fact_witness_keys": ["filter_size_primary", "filter_size_sibling", "opencv_dispatch_state"],
                "derivable_from_current_mat_tls_parameter_contracts": False,
                "reason": "Size=(0,5) is generated inside the binary filter path itself. The fixture did not omit kernel geometry, and this harness must not invent a replacement width.",
                "next_unavailable_boundary": {
                    "kind": "binary-generated invalid FilterEngine anchor/ksize relation after verified OpenCV bootstrap",
                    "boundary": "FUN_181162610",
                    "exception_class": runtime_error_boundary.get("exception_class"),
                    "source_file": runtime_error_boundary.get("source_file"),
                    "line": runtime_error_boundary.get("line"),
                    "assertion": runtime_error_boundary.get("message"),
                    "opencv_bootstrap_result": "Actual FUN_18114be60 returned, set DAT_181843998=1, and populated a nonzero 0x8000-byte coefficient region before Mode2; the same anchor assertion persisted.",
                },
                "call_chain": [
                    "FUN_181150790",
                    "FUN_181294950",
                    "FUN_181298180 + 0x234 callsite 0x1812983b4",
                    "FUN_1811d88c0",
                    "FUN_1812b9db0 assertion callsite 0x1812b9da8",
                    "FUN_181162610",
                ],
                "assertion": runtime_error_boundary,
                "stop_without_mutation": True,
            }
        return {
            "status": "FAILED",
            "events": events,
            "callback": callback_state,
            "handle_events": handle_events,
            "suite_events": suite_events,
            "suite_call_trace": suite_call_trace,
            "internal_boundary_trace": internal_boundary_trace,
            "runtime_tls": runtime_state,
            "runtime_error_boundary": runtime_error_boundary,
            "allocation_trace": allocation_trace,
            "mat_trace": mat_trace,
            "oom_request": oom_request,
            "aligned_lifecycle": aligned_lifecycle,
            "aligned_request_trace": aligned_request_trace(),
            "aligned_live": {hex(pointer): spec for pointer, spec in aligned_live.items()},
            "control_flow_trace": control_flow_trace,
            "mode2_call_args": mode2_call_args,
            "mode2_instruction_trace": mode2_instruction_trace,
            "inner_entry": inner_entry,
            "inner_instruction_trace": inner_instruction_trace,
            "filter_setup_trace": filter_setup_trace,
            "dispatch_checkpoints": dispatch_checkpoints,
            "dispatch_diagnosis": dispatch_diagnosis,
            "filter_failure": filter_failure,
            "execution_stop": execution_stop,
            "selector_diagnosis": selector_diagnosis(),
            "fls_lifecycle": fls_lifecycle,
            "fls_live_keys": {str(key): spec for key, spec in fls_live_keys.items()},
            "fls_thread_values": {hex(thread): {str(key): hex(value) for key, value in values.items()} for thread, values in fls_thread_values.items()},
            "next_runtime_boundary": next_runtime_boundary,
            "runtime_imports": runtime_imports(),
            "unimplemented_imports": unimplemented_imports(),
            "allocation_diagnosis": allocation_diagnosis(),
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
            "reason": "common owner returned without reaching the required natural PF32 writer callsite",
            "first_unavailable_boundary": (
                f"exact stop: FUN_181150790 entered; dispatch checkpoint repeated at RIP={execution_stop.get('rip')}; fixture state made no progress; no unimplemented import observed, no typed writer claim"
                if execution_stop.get("condition") == "repeated checkpoint; fail closed"
                else "exact stop after actual FUN_18114be60 bootstrap returned with DAT_181843998=1 and nonzero coefficients: FUN_181162610 cv::FilterEngine::init still asserted for binary-generated Size=(0,5); anchor/width was not patched and no typed writer was reached"
                if execution_stop.get("condition") == "FilterEngine anchor assertion persisted after verified bootstrap; fail closed"
                else f"exact stop: FUN_181150790 entered; FUN_181294950 fixture-state fault at RIP={execution_stop.get('rip')}; bounded execution failed closed; no typed writer claim"
                if execution_stop.get("condition") == "dispatch fixture-state fault; fail closed"
                else f"exact stop: FUN_181150790 entered; bounded dispatch chunks exhausted at RIP={execution_stop.get('rip')}; no unimplemented import observed, no typed writer claim"
                if execution_stop.get("condition") == "dispatch chunk cap exhausted; fail closed"
                else "ambiguous control-flow boundary: Mode2 entered FUN_181150790, but no return or inner mode-selector branch was observed before the natural owner return; fail closed, no typed writer claim"
                if any(item["label"] == "Mode2 inner helper entry" for item in control_flow_trace)
                else "common owner returned at 0x18114c8f0 without reaching the required PF32 typed writer callsite; no further host/runtime boundary was entered"
            ),
        }
    except Exception as exc:
        execution_stop.update({
            "condition": "exception",
            "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            "rsp": hex(loader.uc.reg_read(UC_X86_REG_RSP)),
            "registers_rcx_rdx_r8_r9_rbp_rsi_rdi": [hex(loader.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RBP, UC_X86_REG_RSI, UC_X86_REG_RDI)],
        })
        return {
            "status": "BLOCKED",
            "events": events,
            "callback": callback_state,
            "handle_events": handle_events,
            "suite_events": suite_events,
            "suite_call_trace": suite_call_trace,
            "internal_boundary_trace": internal_boundary_trace,
            "runtime_tls": runtime_state,
            "runtime_error_boundary": runtime_error_boundary,
            "allocation_trace": allocation_trace,
            "mat_trace": mat_trace,
            "oom_request": oom_request,
            "aligned_lifecycle": aligned_lifecycle,
            "aligned_request_trace": aligned_request_trace(),
            "aligned_live": {hex(pointer): spec for pointer, spec in aligned_live.items()},
            "control_flow_trace": control_flow_trace,
            "mode2_call_args": mode2_call_args,
            "mode2_instruction_trace": mode2_instruction_trace,
            "inner_entry": inner_entry,
            "inner_instruction_trace": inner_instruction_trace,
            "filter_setup_trace": filter_setup_trace,
            "dispatch_checkpoints": dispatch_checkpoints,
            "dispatch_diagnosis": {
                "strategy": "resume the original call frame at the current RIP; do not re-enter FUN_181150790",
                "chunk_instructions": DISPATCH_CHUNK_INSTRUCTIONS,
                "max_chunks": DISPATCH_MAX_CHUNKS,
                "progress_invariant": "work_coordinate = outer*0x20 + inner; each dispatch_loop_entry checkpoint must strictly increase it",
                "terminal_classification": {"typed_writer": False, "classification": "exception_before_dispatch_completion"},
            },
            "filter_failure": None,
            "execution_stop": execution_stop,
            "selector_diagnosis": selector_diagnosis(),
            "fls_lifecycle": fls_lifecycle,
            "fls_live_keys": {str(key): spec for key, spec in fls_live_keys.items()},
            "fls_thread_values": {hex(thread): {str(key): hex(value) for key, value in values.items()} for thread, values in fls_thread_values.items()},
            "next_runtime_boundary": next_runtime_boundary,
            "runtime_imports": runtime_imports(),
            "unimplemented_imports": unimplemented_imports(),
            "allocation_diagnosis": allocation_diagnosis(),
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
            "first_unavailable_boundary": (
                f"next exact boundary after one-key FLS/TLS lifecycle: FUN_18115eb30 -> _aligned_malloc({oom_request['requested_bytes']}, 64) returned null and reached FUN_18115ea40; no typed writer claim"
                if oom_request else
                "next exact boundary after actual FUN_18114be60 bootstrap and bounded aligned allocation: FUN_181162610 cv::FilterEngine::init anchor/ksize throw path from filter.dispatch.cpp:5; DAT_181843998=1 and nonzero coefficients were verified, Size=(0,5) remained binary-generated, and no typed writer was reached"
            ),
            "exception": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    static_facts = collect_static_fact_witnesses()
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
        "static_fact_witnesses": static_facts,
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
