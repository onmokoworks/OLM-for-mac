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
    runtime_state = {
        "tls_index_global": hex(TLS_INDEX_GLOBAL),
        "tls_index_value": struct.unpack("<I", loader.read_bytes(TLS_INDEX_GLOBAL, 4))[0],
        "gs_tls_address": hex(TEB_BASE + GS_TLS_OFFSET),
        "tls_table": hex(tls_table),
        "tls_slot": hex(tls_slot),
        "tls_epoch_address": hex(tls_slot + TLS_EPOCH_OFFSET),
        "tls_epoch_initial": TLS_UNINITIALIZED_EPOCH,
        "contract": "GS:[0x58] -> TLS table; table[0] -> slot; slot+0x04 -> lazy-init epoch",
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
            "throw_helper": "FUN_181162500 -> _CxxThrowException; 0x181162672 INT3 fallback",
        })

    loader.add_code_hook(0x181162610, capture_runtime_error)
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
        elif runtime_error_boundary:
            next_contract = {
                "kind": "OpenCV TLS/FLS setData",
                "boundary": "FUN_181162610",
                "error_code": -215,
                "assertion": "FlsSetValue(tlsKey, pData) == TRUE",
                "required_import": "FlsSetValue",
                "success_return": 1,
                "lifecycle": "preserve the existing TLS/FLS key and value; reject unknown keys or invalid lifecycle",
                "fail_closed": True,
            }
            classification = "bounded_aligned_allocator_contract_crossed_next_fls_boundary"
            owner_tail = "FUN_181162610 TLS/FLS cv::Exception throw path"
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
            max_instructions=50_000,
        )
        stop_rip = loader.uc.reg_read(UC_X86_REG_RIP)
        stop_condition = "instruction budget exhausted" if call_result.get("instructions") == 50_000 else "RETURN_TRAMPOLINE emulation stop"
        execution_stop.update({
            "condition": stop_condition,
            "rip": hex(loader.uc.reg_read(UC_X86_REG_RIP)),
            "rsp": hex(loader.uc.reg_read(UC_X86_REG_RSP)),
            "instructions": call_result.get("instructions"),
            "rax": hex(call_result.get("rax", 0)),
            "registers_rcx_rdx_r8_r9_rbp_rsi_rdi": [hex(loader.uc.reg_read(reg)) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RBP, UC_X86_REG_RSI, UC_X86_REG_RDI)],
            "grounded_location": "FUN_181294950 dispatch loop at 0x181294ad5" if stop_rip == 0x181294AD5 else None,
        })
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
                f"exact stop: FUN_181150790 entered; instruction budget exhausted at RIP={execution_stop.get('rip')} in FUN_181294950 dispatch loop; no unimplemented import observed, no typed writer claim"
                if execution_stop.get("condition") == "instruction budget exhausted"
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
                "next exact boundary after bounded aligned allocation: FUN_181162610 TLS/FLS setData failure, FlsSetValue(tlsKey,pData) == TRUE, error -215; CRT _CxxThrowException is only the physical throw fallback; no typed writer claim"
            ),
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
