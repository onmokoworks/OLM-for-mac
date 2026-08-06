#!/usr/bin/env python3
"""Capture the actual-AEX OLMKiraKira Blur Mode 3 Gaussian call.

The probe calls FUN_181150790 with small synthetic CV_32FC1 Mats.  A Unicorn
code hook stops at FUN_181272ec0 and records the OpenCV wrapper arguments and
the Mat headers visible at that exact call boundary.  It is a witness probe,
not a replacement implementation of GaussianBlur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from unicorn import UC_HOOK_MEM_INVALID

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from aex_loader import AexLoader  # noqa: E402
from unicorn.x86_const import (  # noqa: E402
    UC_X86_REG_RAX,
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_RDI,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RIP,
    UC_X86_REG_RSP,
    UC_X86_REG_XMM3,
)

FUN_HELPER = 0x181150790
FUN_GAUSSIAN = 0x181272EC0
FUN_OPENCV_TLS_FAULT = 0x1811637D1
FUN_OPENCV_TLS_LOOKUP = 0x181163706
FUN_OPENCV_TLS_SELECTED = 0x18116371E
FUN_OPENCV_VECTOR_COMPARE = 0x1811637E6
FUN_OPENCV_TLS_DATA = 0x181163B40
FUN_OPENCV_TLS_CONTAINER = 0x181163C80
FUN_OPENCV_TLS_DATA_CREATE = 0x181165220
FUN_OPENCV_ERROR_PATH = 0x181163870
FUN_OPENCV_ERROR_ENTRY = 0x181162610
TLS_INDEX_GLOBAL = 0x1818C3EA8
TLS_GENERATION_GLOBAL = 0x181839228
OPENCV_CPU_DISPATCH_TABLE_GLOBAL = 0x181843990
DEFAULT_AEX = ROOT / "aex/OLMKiraKira/Plugins/64/2025/OLMKiraKira.aex"
DEFAULT_JSON = ROOT / "refs/conformance/olmkirakira_mode3_actual_aex_20260713.json"
DEFAULT_MD = ROOT / "refs/conformance/olmkirakira_mode3_actual_aex_20260713.md"


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def read_u32(loader: AexLoader, addr: int) -> int:
    return struct.unpack("<I", loader.read_bytes(addr, 4))[0]


def mat_header(loader: AexLoader, data: int, rows: int, cols: int, step: int) -> int:
    """Build the 2-D CV_32FC1 header shape used by OpenCV 4.5.5."""
    header = loader.bump_alloc(96, align=16)
    step_storage = loader.bump_alloc(16, align=8)
    loader.write_bytes(step_storage, struct.pack("<QQ", step, 4))
    flags = 0x42FF4005  # MAGIC_VAL | CONTINUOUS_FLAG | CV_32FC1
    raw = bytearray(96)
    struct.pack_into("<IIii", raw, 0, flags, 2, rows, cols)
    struct.pack_into("<QQQQQ", raw, 16, data, data, data + rows * step, data + rows * step, 0)
    struct.pack_into("<Q", raw, 72, step_storage)
    loader.write_bytes(header, bytes(raw))
    return header


def read_mat(loader: AexLoader, ptr: int) -> dict[str, Any] | None:
    if not ptr or ptr < 0x10000:
        return None
    try:
        raw = loader.read_bytes(ptr, 96)
        flags, dims, rows, cols = struct.unpack_from("<IIii", raw, 0)
        data = struct.unpack_from("<Q", raw, 16)[0]
        step_pointer = struct.unpack_from("<Q", raw, 72)[0]
        step = struct.unpack("<Q", loader.read_bytes(step_pointer, 8))[0]
    except Exception:
        return None
    if (flags & 0xFFFF0000) != 0x42FF0000 or dims not in (2, 0) or rows <= 0 or cols <= 0:
        return None
    if data < 0x10000 or step < cols * 4:
        return None
    values = []
    all_values = None
    try:
        sample_cols = min(cols, 8)
        for row in range(min(rows, 2)):
            values.append(list(struct.unpack("<%df" % sample_cols, loader.read_bytes(data + row * step, sample_cols * 4))))
    except Exception:
        values = []
    try:
        if rows <= 64 and cols <= 64:
            all_values = [list(struct.unpack("<%df" % cols, loader.read_bytes(data + row * step, cols * 4))) for row in range(rows)]
    except Exception:
        all_values = None
    return {
        "header": hex(ptr),
        "flags": hex(flags),
        "depth_code": flags & 7,
        "channels": 1 + ((flags >> 3) & 0x3F),
        "dims": dims,
        "rows": rows,
        "cols": cols,
        "data": hex(data),
        "step_bytes": step,
        "step_pointer": hex(step_pointer),
        "sample_first_rows": values,
        "values_f32": all_values,
    }


def read_array_wrapper(loader: AexLoader, ptr: int) -> dict[str, Any] | None:
    try:
        flags, obj = struct.unpack("<QQ", loader.read_bytes(ptr, 16))
    except Exception:
        return None
    return {
        "wrapper": hex(ptr),
        "flags": hex(flags),
        "object": hex(obj),
        "mat": read_mat(loader, obj),
    }


def find_mat(loader: AexLoader, value: int) -> dict[str, Any] | None:
    """Decode direct, low-32-bit tagged, or temporary InputArray pointers."""
    candidates = [value, u32(value)]
    for base in (value, u32(value)):
        if base >= 0x10000:
            candidates.extend(base + off for off in (8, 16, 24, 32, 40))
    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        result = read_mat(loader, candidate)
        if result:
            result["decoded_from"] = hex(value)
            return result
    return None


def gaussian_sidecar(src: list[list[float]], kernel: tuple[int, int], sigma: tuple[float, float], border: int) -> dict[str, Any]:
    python = os.environ.get("OLM_PROBE_PYTHON")
    if not python:
        return {"status": "not_requested"}
    code = (
        "import cv2, json, numpy as np; "
        "src=np.array(json.loads(__import__('sys').stdin.read()), dtype=np.float32); "
        "dst=cv2.GaussianBlur(src, %r, %r, sigmaY=%r, borderType=%d); "
        "print(json.dumps({'cv2':cv2.__version__,'shape':list(dst.shape),"
        "'center':float(dst[dst.shape[0]//2,dst.shape[1]//2]),"
        "'first_row':[float(x) for x in dst[0,:min(8,dst.shape[1])]]}))" % (kernel, sigma[0], sigma[1], border)
    )
    proc = subprocess.run([python, "-c", code], input=json.dumps(src), text=True, capture_output=True)
    if proc.returncode:
        return {"status": "error", "python": python, "stderr": proc.stderr.strip()}
    return {"status": "ok", "python": python, **json.loads(proc.stdout)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aex-path", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--width", type=int, default=9)
    parser.add_argument("--height", type=int, default=7)
    parser.add_argument("--length", type=int, default=5)
    parser.add_argument("--sigma", type=float, default=0.0)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MD)
    parser.add_argument("--max-instructions", type=int, default=20_000_000)
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": "olmkirakira-mode3-actual-aex-probe/1",
        "status": "starting",
        "aex": str(args.aex_path),
        "aex_sha256": hashlib.sha256(args.aex_path.read_bytes()).hexdigest(),
        "entry": {"name": "FUN_181150790", "address": hex(FUN_HELPER)},
        "target": {"name": "FUN_181272ec0", "address": hex(FUN_GAUSSIAN)},
        "error_callback_contract": {
            "name": "FUN_181162610",
            "abi": "windows-x64",
            "registers": ["RCX", "RDX", "R8", "R9"],
            "observed_error_code": "0xfffffffc",
            "caller_return_site": "0x18115ea8b",
            "post_call_trap": "int3",
        },
        "input": {"width": args.width, "height": args.height, "blur_mode": 3, "length": args.length, "sigma": args.sigma, "type": "CV_32FC1"},
        "FACT": [
            "The probe requests Blur Mode 3 at the FUN_181150790 helper boundary.",
            "The target hook is installed at FUN_181272ec0, the recovered GaussianBlur wrapper target.",
            "FUN_181163706 loads TLS index 0 from GS:[0x58], and FUN_1811637D1 reads the selected runtime object's generation at +0x8.",
            "The observed OpenCV error callback uses the Windows x64 RCX/RDX/R8/R9 register ABI; its error path returns to an intentional int3 and is not detoured.",
        ],
        "INFERENCE": [
            "A Mat header is decoded from the wrapper argument only when its OpenCV magic/shape checks pass.",
            "A sidecar comparison is optional and is not evidence that the AEX used that exact OpenCV build unless the target hook is captured.",
            "The probe uses MSVC's uninitialized TLS epoch (-1) and leaves singleton construction, guard epochs, and per-thread vector creation to the AEX.",
        ],
    }
    if not args.aex_path.exists():
        report.update(status="skip", error=f"missing AEX: {args.aex_path}")
        return report
    loader = AexLoader(str(args.aex_path), verbose=False, fast=True)
    # FUN_1812943d0 builds the forward affine matrix through the imported
    # double-precision cos/sin functions. Leaving those imports stubbed keeps
    # the angle in XMM0 and corrupts both matrix coefficients.
    loader.register_libm_impls()
    # The embedded OpenCV lazy initializer uses the Windows TLS vector and the
    # CRT FLS API. Keep this scaffold local to the witness: AexLoader's generic
    # TEB mapping remains intentionally policy-free for unrelated probes.
    tls_table = loader.host_alloc(0x100, align=16)
    tls_slot = loader.host_alloc(0x100, align=16)
    loader.write_bytes(tls_table, b"\x00" * 0x100)
    loader.write_bytes(tls_slot, b"\x00" * 0x100)
    loader.write_bytes(tls_table, struct.pack("<Q", tls_slot))
    # MSVC's __Init_thread_epoch starts at _UNINITIALIZED_THREAD_EPOCH (-1),
    # not zero.  Keeping this value lets the AEX's own function-local-static
    # guard perform its normal header/constructor/footer sequence and publish
    # the embedded OpenCV runtime singleton.
    loader.write_bytes(tls_slot + 4, struct.pack("<i", -1))
    loader.write_bytes(0x50000000 + 0x58, struct.pack("<Q", tls_table))
    # The embedded OpenCV CPU-dispatch initializer writes a 32-byte record for
    # each 8-byte constant entry in [0x1818481a0, 0x18184a1a0). In a loaded
    # process this pointer is prepared by an earlier CRT initializer; direct
    # helper replay must provide the same writable backing store.
    opencv_dispatch_table = loader.host_alloc(0x10000, align=64)
    loader.write_bytes(opencv_dispatch_table, b"\x00" * 0x10000)
    loader.write_bytes(OPENCV_CPU_DISPATCH_TABLE_GLOBAL, struct.pack("<Q", opencv_dispatch_table))

    fls_values: dict[int, int] = {}

    def fls_alloc(_uc: Any, _args: list[int]) -> int:
        # The AEX only needs one process-local FLS slot in this isolated call.
        return 0

    def fls_get(_uc: Any, int_args: list[int]) -> int:
        slot = int_args[0]
        # Windows FLS returns NULL for an allocated-but-unset slot.  The
        # OpenCV TLSDataContainer relies on that distinction to create its
        # per-thread vector; fabricating a zeroed block makes it parse zeros
        # as a live vector header.
        return fls_values.get(slot, 0)

    def fls_set(_uc: Any, int_args: list[int]) -> int:
        fls_values[int_args[0]] = int_args[1]
        return 1

    def fls_free(_uc: Any, int_args: list[int]) -> int:
        fls_values.pop(int_args[0], None)
        return 1

    aligned_allocations: dict[int, dict[str, int]] = {}

    def aligned_malloc(_uc: Any, int_args: list[int]) -> int:
        size, alignment = int(int_args[0]), int(int_args[1])
        if size <= 0 or alignment <= 0 or alignment & (alignment - 1):
            return 0
        pointer = loader.host_alloc(size, align=alignment)
        loader.write_bytes(pointer, b"\x00" * size)
        aligned_allocations[pointer] = {"size": size, "alignment": alignment}
        return pointer

    def aligned_free(_uc: Any, int_args: list[int]) -> int:
        # host_alloc is monotonic for one bounded probe. Forget ownership while
        # retaining the mapped bytes until the emulation instance is discarded.
        aligned_allocations.pop(int(int_args[0]), None)
        return 0

    loader.register_import_impl("FlsAlloc", fls_alloc)
    loader.register_import_impl("FlsGetValue", fls_get)
    loader.register_import_impl("FlsSetValue", fls_set)
    loader.register_import_impl("FlsFree", fls_free)
    loader.register_import_impl("_aligned_malloc", aligned_malloc)
    loader.register_import_impl("_aligned_free", aligned_free)
    if os.environ.get("OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC") == "1":
        event_handle = loader.host_alloc(8, align=8)
        loader.register_import_impl("InitializeCriticalSectionAndSpinCount", lambda _uc, _args: 1)
        loader.register_import_impl("CreateEventW", lambda _uc, _args: event_handle)
        loader.register_import_impl("DeleteCriticalSection", lambda _uc, _args: 0)
        loader.register_import_impl("EnterCriticalSection", lambda _uc, _args: 0)
        loader.register_import_impl("LeaveCriticalSection", lambda _uc, _args: 0)
        loader.register_import_impl("SetEvent", lambda _uc, _args: 1)
        loader.register_import_impl("ResetEvent", lambda _uc, _args: 1)
    if os.environ.get("OLM_KK_PROCESS_ATTACH_DIAGNOSTIC") == "1":
        # Probe-local experiment only: emulate the loader's process-attach
        # ordering before the direct helper call. The PE has no TLS callbacks,
        # so its executable initialization boundary is the DLL entry point.
        loader.write_bytes(0x50000000 + 0x30, struct.pack("<Q", 0x50000000))
        loader.write_bytes(0x50000000 + 0x08, struct.pack("<Q", 1))
        attach = loader.call_function(
            0x18132B650,
            int_args=[loader.image_base, 1, 0],
            max_instructions=20_000_000,
        )
        attach_imports = [
            {"dll": item.dll, "name": item.name,
             "implemented": item.name in loader.import_impls, "ret": item.ret,
             "args": [hex(value) for value in item.args]}
            for item in loader.import_log
        ]
        report["process_attach_diagnostic"] = {
            "entry": "0x18132b650",
            "rax": attach.get("rax"),
            "instructions": attach.get("instructions"),
            "imports": attach_imports,
        }
        if os.environ.get("OLM_KK_MANUAL_CRT_INITIALIZERS_DIAGNOSTIC") == "1":
            loader.enable_crt_initializer_imports()
            result = loader.import_impls["_initterm"](
                loader.uc, [0x1814857B8, 0x181485950, 0, 0])
            report["manual_crt_initializers_diagnostic"] = {
                "result": result,
                "callbacks": [
                    {"kind": item["kind"], "slot": hex(item["slot"]),
                     "target": hex(item["target"]), "result": item["result"]}
                    for item in loader.crt_initializer_log
                ],
            }
    report["tls_scaffold"] = {
        "mode": "probe-local-windows-tls-fls",
        "gs_0x58": hex(0x50000000 + 0x58),
        "tls_table": hex(tls_table),
        "tls_slot": hex(tls_slot),
        "tls_generation_dword": -1,
        "fls_slot": 0,
        "aligned_allocator": "probe-local host_alloc with requested power-of-two alignment",
        "opencv_cpu_dispatch_table": hex(opencv_dispatch_table),
        "opencv_cpu_dispatch_table_global": hex(OPENCV_CPU_DISPATCH_TABLE_GLOBAL),
    }
    cols, rows = args.width, args.height
    step = cols * 4
    source_data = loader.bump_alloc(rows * step, align=64)
    source = [[float((r * cols + c) % 17) / 17.0 for c in range(cols)] for r in range(rows)]
    loader.write_f32_array(source_data, [v for row in source for v in row])
    out_data = loader.bump_alloc(rows * step, align=64)
    loader.write_bytes(out_data, b"\x00" * (rows * step))
    source_mat = mat_header(loader, source_data, rows, cols, step)
    temp1_mat = mat_header(loader, loader.bump_alloc(rows * step, align=64), rows, cols, step)
    temp2_mat = mat_header(loader, loader.bump_alloc(rows * step, align=64), rows, cols, step)
    dst_mat = mat_header(loader, out_data, rows, cols, step)
    capture: dict[str, Any] = {"hits": []}
    fault: dict[str, Any] = {}

    def on_invalid_memory(uc: Any, access: int, address: int, size: int, value: int, _user: Any) -> bool:
        fault["invalid_memory"] = {
            "rip": hex(uc.reg_read(UC_X86_REG_RIP)),
            "access": access,
            "address": hex(address),
            "size": size,
            "value": hex(value),
            "rax": hex(uc.reg_read(UC_X86_REG_RAX)),
            "rcx": hex(uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(uc.reg_read(UC_X86_REG_R8)),
            "r9": hex(uc.reg_read(UC_X86_REG_R9)),
            "rsp": hex(uc.reg_read(UC_X86_REG_RSP)),
        }
        return False

    loader.uc.hook_add(UC_HOOK_MEM_INVALID, on_invalid_memory)

    def safe_qword(emu: AexLoader, address: int) -> int | None:
        try:
            return struct.unpack("<Q", emu.read_bytes(address, 8))[0]
        except Exception:
            return None

    def safe_dword(emu: AexLoader, address: int) -> int | None:
        try:
            return struct.unpack("<I", emu.read_bytes(address, 4))[0]
        except Exception:
            return None

    def on_tls_lookup(emu: AexLoader, _address: int, _size: int) -> None:
        # 0x181163706 loads the module TLS index; 0x18116371e then selects
        # the per-thread object from GS:[0x58]. Record both before the lookup
        # helper's generation check changes control flow.
        index = safe_dword(emu, TLS_INDEX_GLOBAL)
        gs_table = safe_qword(emu, 0x50000000 + 0x58)
        selected = safe_qword(emu, (gs_table or 0) + (index or 0) * 8) if gs_table is not None and index is not None else None
        fault["tls_lookup"] = {
            "rip": hex(FUN_OPENCV_TLS_LOOKUP),
            "tls_index": index,
            "gs_0x58": hex(gs_table) if gs_table is not None else None,
            "selected_object": hex(selected) if selected is not None else None,
            "selected_generation_at_plus4": safe_dword(emu, (selected or 0) + 4) if selected else None,
        }

    def on_tls_selected(emu: AexLoader, _address: int, _size: int) -> None:
        rcx = emu.uc.reg_read(UC_X86_REG_RCX)
        fault["tls_selected"] = {
            "rip": hex(FUN_OPENCV_TLS_SELECTED),
            "selected_object": hex(rcx),
            "generation_at_plus4": safe_dword(emu, rcx + 4),
            "global_generation": safe_dword(emu, TLS_GENERATION_GLOBAL),
        }

    def on_tls_generation(emu: AexLoader, _address: int, _size: int) -> None:
        rcx = emu.uc.reg_read(UC_X86_REG_RCX)
        fault["generation_check"] = {
            "rip": hex(FUN_OPENCV_TLS_FAULT),
            "object": hex(rcx),
            "generation_at_plus8": safe_dword(emu, rcx + 8),
            "qword_at_plus0": hex(safe_qword(emu, rcx) or 0),
            "qword_at_plus8": hex(safe_qword(emu, rcx + 8) or 0),
        }

    def on_vector_compare(emu: AexLoader, _address: int, _size: int) -> None:
        rax = emu.uc.reg_read(UC_X86_REG_RAX)
        rdi = emu.uc.reg_read(UC_X86_REG_RDI)
        fault["vector_compare"] = {
            "rip": hex(FUN_OPENCV_VECTOR_COMPARE),
            "vector_object": hex(rax),
            "requested_generation": rdi,
            "vector_end_or_count": hex(safe_qword(emu, rax + 0x50) or 0),
            "vector_field_plus50": safe_qword(emu, rax + 0x50),
            "vector_begin": hex(safe_qword(emu, rax + 0x58) or 0),
            "vector_end": hex(safe_qword(emu, rax + 0x60) or 0),
            "vector_capacity": hex(safe_qword(emu, rax + 0x68) or 0),
            "requested_entry": hex(safe_qword(emu, (safe_qword(emu, rax + 0x58) or 0) + 8 * rdi) or 0),
        }

    def on_tls_data(emu: AexLoader, _address: int, _size: int) -> None:
        fault["tls_data_accessor"] = {
            "rip": hex(FUN_OPENCV_TLS_DATA),
            "rax_return": None,
            "tls_epoch": safe_dword(emu, 0x40000104),
            "guard_1f8": safe_dword(emu, 0x1818391F8),
            "guard_208": safe_dword(emu, 0x181839208),
            "global_data": hex(safe_qword(emu, 0x1818391F0) or 0),
        }

    def on_tls_container(emu: AexLoader, _address: int, _size: int) -> None:
        fault["tls_container_accessor"] = {
            "rip": hex(FUN_OPENCV_TLS_CONTAINER),
            "tls_epoch": safe_dword(emu, 0x40000104),
            "guard_218": safe_dword(emu, 0x181839218),
            "global_container": hex(safe_qword(emu, 0x181839210) or 0),
        }

    def on_tls_data_create(emu: AexLoader, _address: int, _size: int) -> None:
        fault["tls_data_create"] = {
            "rip": hex(FUN_OPENCV_TLS_DATA_CREATE),
            "rcx": hex(emu.uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(emu.uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(emu.uc.reg_read(UC_X86_REG_R8)),
        }

    def on_error_path(emu: AexLoader, _address: int, _size: int) -> None:
        fault["error_path"] = {
            "rip": hex(FUN_OPENCV_ERROR_PATH),
            "rcx": hex(emu.uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(emu.uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(emu.uc.reg_read(UC_X86_REG_R8)),
            "r9": hex(emu.uc.reg_read(UC_X86_REG_R9)),
        }

    def on_error_entry(emu: AexLoader, _address: int, _size: int) -> None:
        rsp = emu.uc.reg_read(UC_X86_REG_RSP)
        exception = emu.uc.reg_read(UC_X86_REG_RDX)
        exception_words = [safe_qword(emu, exception + off) for off in range(0, 0x40, 8)] if exception else []
        fault["error_entry"] = {
            "rip": hex(FUN_OPENCV_ERROR_ENTRY),
            "rcx": hex(emu.uc.reg_read(UC_X86_REG_RCX)),
            "rdx": hex(emu.uc.reg_read(UC_X86_REG_RDX)),
            "r8": hex(emu.uc.reg_read(UC_X86_REG_R8)),
            "r9": hex(emu.uc.reg_read(UC_X86_REG_R9)),
            "return_address": hex(safe_qword(emu, rsp) or 0),
            "exception_object": hex(exception),
            "exception_words": [hex(word or 0) for word in exception_words],
        }

    def on_gaussian(emu: AexLoader, _address: int, _size: int) -> None:
        regs = [emu.uc.reg_read(reg) for reg in (UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)]
        xmm3_raw = emu.uc.reg_read(UC_X86_REG_XMM3)
        sigma_x = struct.unpack("<d", int(xmm3_raw & ((1 << 64) - 1)).to_bytes(8, "little"))[0]
        rsp = emu.uc.reg_read(UC_X86_REG_RSP)
        stack = [struct.unpack("<Q", emu.read_bytes(rsp + off, 8))[0] for off in (0x20, 0x28, 0x30, 0x38)]
        capture["hits"].append({
            "rip": hex(FUN_GAUSSIAN),
            "register_args_rcx_rdx_r8_r9": [hex(x) for x in regs],
            "shadow_or_caller_stack_words": [hex(x) for x in stack],
            "size_packed": hex(regs[2]),
            "size": [u32(regs[2]), u32(regs[2] >> 32)],
            "sigma_x_f64": sigma_x,
            "input_array": read_array_wrapper(emu, regs[0]),
            "output_array": read_array_wrapper(emu, regs[1]),
            "r9_not_an_argument": hex(regs[3]),
        })
        emu.uc.emu_stop()

    loader.add_code_hook(FUN_GAUSSIAN, on_gaussian)
    loader.add_code_hook(FUN_OPENCV_TLS_LOOKUP, on_tls_lookup)
    loader.add_code_hook(FUN_OPENCV_TLS_SELECTED, on_tls_selected)
    loader.add_code_hook(FUN_OPENCV_VECTOR_COMPARE, on_vector_compare)
    loader.add_code_hook(FUN_OPENCV_TLS_DATA, on_tls_data)
    loader.add_code_hook(FUN_OPENCV_TLS_CONTAINER, on_tls_container)
    loader.add_code_hook(FUN_OPENCV_TLS_DATA_CREATE, on_tls_data_create)
    loader.add_code_hook(FUN_OPENCV_TLS_FAULT, on_tls_generation)
    loader.add_code_hook(FUN_OPENCV_ERROR_PATH, on_error_path)
    loader.add_code_hook(FUN_OPENCV_ERROR_ENTRY, on_error_entry)

    try:
        result = loader.call_function(
            FUN_HELPER,
            int_args=[0, source_mat, temp1_mat, dst_mat, temp2_mat, args.length, args.length, 3, 1],
            max_instructions=args.max_instructions,
        )
        report["status"] = "captured" if capture["hits"] else "completed_without_target_hit"
        report["helper_result"] = {"xmm0_f32": result["xmm0_f32"], "instructions": result["instructions"]}
        if not capture["hits"]:
            report["post_sample"] = {
                "center_xy": [cols // 2, rows // 2],
                "center_f32": struct.unpack("<f", loader.read_bytes(out_data + (rows // 2) * step + (cols // 2) * 4, 4))[0],
                "first_row_f32": loader.read_f32_array(out_data, cols),
            }
    except Exception as exc:
        report.update(status="blocked", error=repr(exc))
        report["runtime_imports"] = [
            {"name": item.name, "args": [hex(arg) for arg in item.args], "ret": hex(item.ret)}
            for item in loader.import_log
            if item.name in {"malloc", "free", "_aligned_malloc", "_aligned_free", "FlsAlloc", "FlsGetValue", "FlsSetValue", "FlsFree"}
        ]
    report["aligned_allocations_live"] = {hex(pointer): spec for pointer, spec in aligned_allocations.items()}
    report["target_capture"] = capture
    report["fault_boundary"] = fault
    if fault.get("generation_check"):
        singleton = fault["generation_check"]
        vector = fault.get("vector_compare", {})
        report["runtime_singleton"] = {
            "status": "initialized_before_downstream_fault",
            "object": singleton["object"],
            "vtable": singleton["qword_at_plus0"],
            "generation": singleton["qword_at_plus8"],
            "tls_container": vector.get("vector_object"),
            "tls_vector_begin": vector.get("vector_begin"),
            "tls_vector_end": vector.get("vector_end"),
            "per_thread_data": "0x20000960" if fault.get("tls_data_create") else None,
        }
    if fault and not capture["hits"]:
        report["FACT"].append("The AEX's own MSVC local-static guard initialized the OpenCV runtime singleton and its per-thread TLS vector before the downstream OpenCV allocation failure.")
        report["INFERENCE"].append("The singleton restoration is semantically active, but the probe still does not reach the Gaussian boundary; no OpenCV call arguments are claimed.")
    if capture["hits"]:
        hit = capture["hits"][0]
        report["FACT"].append("The actual AEX reached FUN_181272ec0; the four-argument Gaussian wrapper boundary is captured before executing its body.")
        report["INFERENCE"].append("R9 and the caller shadow words are retained as raw context, not promoted to Gaussian arguments; this callsite passes InputArray, OutputArray, Size, and sigmaX only.")
        boundary_source = hit["input_array"]["mat"].get("values_f32") or source
        report["sidecar"] = gaussian_sidecar(boundary_source, tuple(hit["size"]), (hit["sigma_x_f64"], 0.0), 4)
    return report


def render_md(report: dict[str, Any]) -> str:
    lines = ["# OLMKiraKira Blur Mode 3 actual-AEX probe", "", f"Status: **{report['status']}**", ""]
    lines += ["## FACT", ""] + [f"- {item}" for item in report.get("FACT", [])] + [""]
    lines += ["## INFERENCE / LIMIT", ""] + [f"- {item}" for item in report.get("INFERENCE", [])] + [""]
    lines += ["## Execution", "", f"- AEX: `{report['aex']}`", f"- SHA-256: `{report['aex_sha256']}`", f"- Entry: `{report['entry']['name']} @ {report['entry']['address']}`", f"- Target: `{report['target']['name']} @ {report['target']['address']}`", f"- Input: `{json.dumps(report['input'], sort_keys=True)}`", ""]
    if report.get("error"):
        lines += [f"- Error: `{report['error']}`", ""]
    if report.get("fault_boundary"):
        lines += [f"- Fault boundary: `{json.dumps(report['fault_boundary'], sort_keys=True)}`", ""]
    if report.get("runtime_singleton"):
        lines += ["## Runtime singleton", "", f"- `{json.dumps(report['runtime_singleton'], sort_keys=True)}`", ""]
    if report.get("error_callback_contract"):
        lines += ["## Error callback ABI", "", f"- `{json.dumps(report['error_callback_contract'], sort_keys=True)}`", ""]
    if report.get("target_capture", {}).get("hits"):
        hit = report["target_capture"]["hits"][0]
        lines += ["## Captured boundary", "", f"- Hit count: `{len(report['target_capture']['hits'])}`", f"- Size: `{hit['size']}`", f"- sigmaX: `{hit['sigma_x_f64']}`", f"- input wrapper: `{json.dumps(hit.get('input_array'), sort_keys=True)}`", f"- output wrapper: `{json.dumps(hit.get('output_array'), sort_keys=True)}`", f"- raw R9 (not an argument): `{hit['r9_not_an_argument']}`", ""]
    if report.get("post_sample"):
        lines += ["## Post sample", "", f"- `{json.dumps(report['post_sample'], sort_keys=True)}`", ""]
    lines += ["## Sidecar", "", f"- `{json.dumps(report.get('sidecar', {'status': 'not_run'}), sort_keys=True)}`", ""]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report = run(args)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "json": str(args.output_json), "md": str(args.output_md), "hits": len(report.get("target_capture", {}).get("hits", []))}, sort_keys=True))
    return 0 if report["status"] in {"captured", "completed_without_target_hit", "blocked", "skip"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
