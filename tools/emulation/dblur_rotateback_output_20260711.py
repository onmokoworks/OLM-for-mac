#!/usr/bin/env python3
"""Bounded rotate-back ABI/output witness for OLMDirectionalBlur."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from unicorn.x86_const import (
    UC_X86_REG_RCX,
    UC_X86_REG_RDX,
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_RSP,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROTATE = 0x180001EC0
CALLSITE = 0x180005628
RETURN_SITE = 0x1800057A2
WIDTH = 960
HEIGHT = 540
TARGETS = ((494, 169), (579, 169))


def f32(loader: AexLoader, address: int) -> float:
    return struct.unpack("<f", loader.read_bytes(address, 4))[0]


def vec4(loader: AexLoader, address: int) -> list[float]:
    return [f32(loader, address + 4 * i) for i in range(4)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=ROOT / "plugins_2025/OLMDirectionalBlur.aex")
    parser.add_argument("--output", type=Path, default=ROOT / "refs/conformance/dblur_rotateback_output_20260711.json")
    args = parser.parse_args()

    loader = AexLoader(str(args.aex), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    count = WIDTH * HEIGHT
    source = loader.bump_alloc(count * 16, align=64)
    destination = loader.bump_alloc(count * 16, align=64)
    # Helper-only continuation: opaque zero RGB source and cleared destination.
    src = bytearray(count * 16)
    for i in range(count):
        struct.pack_into("<f", src, i * 16 + 12, 1.0)
    loader.write_bytes(source, bytes(src))
    loader.write_bytes(destination, b"\x00" * (count * 16))

    entry: dict[str, object] = {}

    def on_entry(ld: AexLoader, _address: int, _size: int) -> None:
        rsp = ld.uc.reg_read(UC_X86_REG_RSP)
        entry.update({
            "rip": ROTATE,
            "rsp": rsp,
            "rcx_source": ld.uc.reg_read(UC_X86_REG_RCX),
            "rdx_destination": ld.uc.reg_read(UC_X86_REG_RDX),
            "r8_width": ld.uc.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF,
            "r9_height": ld.uc.reg_read(UC_X86_REG_R9) & 0xFFFFFFFF,
            "stack_arg5_bits_at_entry_rsp_plus_28": struct.unpack("<I", ld.read_bytes(rsp + 0x28, 4))[0],
            "stack_arg5_at_entry_rsp_plus_28": f32(ld, rsp + 0x28),
        })

    loader.add_code_hook(ROTATE, on_entry)
    loader.call_function(
        ROTATE,
        int_args=[source, destination, WIDTH, HEIGHT, struct.unpack("<I", struct.pack("<f", -0.0))[0]],
        max_instructions=8_000_000,
    )

    outputs = {}
    for x, y in TARGETS:
        address = destination + (y * WIDTH + x) * 16
        outputs[f"{x},{y}"] = {
            "address": address,
            "rgba_f32": vec4(loader, address),
            "rgba_bytes_le": loader.read_bytes(address, 16).hex(),
        }

    result = {
        "kind": "dblur_rotateback_output",
        "schema": 1,
        "status": "bounded_helper_only",
        "aex": str(args.aex.resolve().relative_to(ROOT)),
        "static_callsite": {
            "call": "0x180005628 -> FUN_180001ec0",
            "rcx_source": "RSI",
            "rdx_destination": "R15",
            "r8_width": "dword ptr [RBX+0x80a0]",
            "r9_height": "dword ptr [RBX+0x80a4]",
            "angle": "float at [RSP+0x20] before CALL; -[RBX+0x24] at this callsite",
            "after_return": "qword ptr [RBX+0x8090] = R15",
            "return_site": "0x1800057a2",
        },
        "destination_identity": {
            "rotateback_destination": "R15, the RGBA float work buffer A",
            "host_world": "R13 at FUN_180004a20; distinct from R15",
            "host_output_callback_input": "param_6+0x8090 points to R15 after rotate-back",
        },
        "unicorn_entry": entry,
        "targets": outputs,
        "full_render": {
            "status": "blocked",
            "reason": "No bounded fixture currently supplies the FUN_180004a20 host callback/world layout through the 0x180005628 call.",
            "next_fixture_requirements": [
                "8bpc FUN_180004a20 entry with R13 world/context and R12/R14/R15 preserved",
                "param_6 fields at +0x8078/+0x8080/+0x8088/+0x8090 and dimensions +0x80a0/+0x80a4",
                "PF Iterate8 populate/output callbacks that materialize A and consume param_6+0x8090",
                "capture hooks at 0x180005628 and 0x1800057a2 in the same render invocation",
            ],
            "target_output_bytes_or_floats": "not captured",
        },
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output.relative_to(ROOT)), "targets": list(outputs)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
