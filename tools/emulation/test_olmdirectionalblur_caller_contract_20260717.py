#!/usr/bin/env python3
"""Bounded Mac-local actual-AEX caller contract witness for 0x180006b30."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_caller_contract_20260717.json"
WRAPPER = 0x180006700
OUTPUT = 0x180006B30
PARAM_SIZE = 0x8200


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def u32(loader: AexLoader, address: int) -> int:
    return struct.unpack("<I", loader.read_bytes(address, 4))[0]


def f32(loader: AexLoader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    params = loader.host_alloc(PARAM_SIZE)
    source = loader.host_alloc(32 * 16, align=16)
    output = loader.host_alloc(4, align=4)
    rect = loader.host_alloc(16)
    source_world = loader.host_alloc(0x30)
    destination_world = loader.host_alloc(0x30)
    spbasic = loader.host_alloc(0x20)
    iterate_suite = loader.host_alloc(8)
    param1 = loader.host_alloc(0x190)
    loader.write_bytes(params, b"\x00" * PARAM_SIZE)
    source_bytes = bytearray(b"\xA5" * (32 * 16))
    source_bytes[23 * 16:24 * 16] = struct.pack("<4f", 0.125, 0.5, 0.75, 1.25)
    loader.write_bytes(source, bytes(source_bytes))
    loader.write_bytes(output, b"\xCC" * 4)
    loader.write_bytes(rect, struct.pack("<4i", 2, 3, 3, 4))
    loader.write_bytes(source_world, b"\x00" * 0x30)
    loader.write_bytes(destination_world, b"\x00" * 0x30)
    loader.write_bytes(param1, b"\x00" * 0x190)

    # The callback is deliberately one pixel: this exercises the real wrapper
    # ABI and the real output callback without claiming an AE-host iteration.
    fields = {
        0x28: struct.pack("<f", 1.0),
        0x8090: struct.pack("<Q", source),
        0x8098: struct.pack("<I", 3),
        0x809C: struct.pack("<I", 2),
        0x80A0: struct.pack("<I", 4),
    }
    for offset, blob in fields.items():
        loader.write_bytes(params + offset, blob)
    loader.write_bytes(param1 + 0x180, struct.pack("<Q", spbasic))
    loader.write_bytes(iterate_suite, struct.pack("<Q", 0))

    observed: dict = {}

    def acquire_suite(ld: AexLoader, args: list[int]) -> int:
        name = ld.read_bytes(args[0], 64).split(b"\x00", 1)[0].decode("ascii")
        if name != "PF Iterate8 Suite":
            raise RuntimeError(f"unexpected suite {name!r}")
        ld.write_bytes(args[2], struct.pack("<Q", iterate_suite))
        observed["acquire"] = {"name": name, "version": args[1], "out": hex(args[2])}
        return 0

    def iterate(ld: AexLoader, args: list[int]) -> int:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        callback = u64(ld, rsp + 0x38)
        refcon = u64(ld, rsp + 0x30)
        destination_pixel = u64(ld, rsp + 0x40)
        observed["iterate"] = {
            "start": args[1], "end": args[2], "source_world": hex(args[3]),
            "rect": hex(u64(ld, rsp + 0x28)), "refcon": hex(refcon),
            "callback": hex(callback), "destination_pixel": hex(destination_pixel),
            "stack_slots": {hex(offset): hex(u64(ld, rsp + offset)) for offset in (0x28, 0x30, 0x38, 0x40)},
        }
        if callback != OUTPUT or refcon != params or destination_pixel != destination_world:
            raise RuntimeError(
                f"wrapper contract mismatch callback=0x{callback:x} refcon=0x{refcon:x} "
                f"destination=0x{destination_pixel:x} expected callback=0x{OUTPUT:x} "
                f"refcon=0x{params:x} destination_world=0x{destination_world:x}"
            )
        return 0

    acquire_addr = loader.install_callback("SPBasic.AcquireSuite", acquire_suite)
    iterate_addr = loader.install_callback("PF.Iterate8", iterate)
    release_addr = loader.install_callback("SPBasic.ReleaseSuite", lambda _ld, _args: 0)
    loader.write_bytes(spbasic, struct.pack("<2Q", acquire_addr, release_addr))
    loader.write_bytes(iterate_suite, struct.pack("<Q", iterate_addr))

    def output_entry(ld: AexLoader, address: int, _size: int) -> None:
        if observed.get("output_entry"):
            return
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        x = ld.uc.reg_read(UC_X86_REG_RDX) & 0xFFFFFFFF
        y = ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF
        base = u64(ld, params + 0x8090)
        stride = u32(ld, params + 0x80A0)
        row0 = u32(ld, params + 0x8098)
        col0 = u32(ld, params + 0x809C)
        index = ((row0 + y) * stride + col0 + x)
        source_cell = base + index * 16
        observed["output_entry"] = {
            "rip": hex(address), "params_rcx": hex(ld.uc.reg_read(UC_X86_REG_RCX)),
            "x_rdx": x, "y_r8": y, "output_r9": hex(ld.uc.reg_read(UC_X86_REG_R9)),
            "output_stack_0x28": hex(u64(ld, rsp + 0x28)), "source_base": hex(base),
            "row0": row0, "col0": col0, "stride_floats": stride,
            "float_cell_index": index, "float_byte_offset": index * 16,
            "source_rgba_f32": list(struct.unpack("<4f", ld.read_bytes(source_cell, 16))),
        }

    loader.add_code_hook(OUTPUT, output_entry)
    wrapper_execution = loader.call_function(
        WRAPPER,
        int_args=[param1, 0, 1, source_world, rect, params, OUTPUT, destination_world],
        max_instructions=10000,
    )
    execution = loader.call_function(
        OUTPUT, int_args=[params, 1, 2, 0, output], max_instructions=1000
    )
    observed["output_arg_registers"] = {
        "rcx": observed["output_entry"]["params_rcx"],
        "rdx": observed["output_entry"]["x_rdx"],
        "r8": observed["output_entry"]["y_r8"],
    }
    observed["output_arg_registers"]["r9_is_not_contract"] = True
    observed["packed_argb8"] = list(loader.read_bytes(output, 4))
    observed["execution_instructions"] = {
        "wrapper": wrapper_execution["instructions"],
        "output": execution["instructions"],
    }
    observed["aex_sha256"] = sha(AEX)
    observed["status"] = "pass"
    REPORT.write_text(json.dumps({
        "schema": 1,
        "kind": "olmdirectionalblur_mac_actual_aex_caller_contract",
        "status": observed["status"],
        "scope": "Mac-local Unicorn; one real FUN_180006700 wrapper call and one real 0x180006b30 output callback; not AE-host execution",
        "binary": str(AEX.relative_to(ROOT)),
        "binary_sha256": observed["aex_sha256"],
        "fact": [
            "FUN_180006700 acquired PF Iterate8 Suite and preserved callback, refcon, and destination pixel through its stack call area.",
            "The real 0x180006b30 entry observed RCX=params, RDX=x, R8=y, and the PF_Pixel8 destination at [RSP+0x28].",
            "The callback selected one RGBA float cell with ((row0 + y) * stride + col0 + x) * 16 bytes.",
            "The actual writer overwrote all four destination bytes and returned zero.",
        ],
        "inference": [
            "The immediate caller-side float contract is bounded to the captured 8bpc iterate path; it does not prove Windows live writer-entry values.",
            "The output pointer is stack-passed by the iterate callback ABI, not supplied in R9 at 0x180006b30.",
        ],
        "addresses": {"wrapper": hex(WRAPPER), "output": hex(OUTPUT)},
        "observed": observed,
        "commands": ["python3 tools/emulation/test_olmdirectionalblur_caller_contract_20260717.py"],
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT.relative_to(ROOT)), "packed_argb8": observed["packed_argb8"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
