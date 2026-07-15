#!/usr/bin/env python3
"""Probe the first shared 8bpc DG stage for the 0001/0015/0029 family.

This is a Mac-side probe of the actual current AEX under the repository's
Unicorn loader.  It deliberately uses a one-pixel fixture so field reads,
source reads, the pre-u8 values, and the four output byte stores are all
addressable facts.  It does not claim Windows internals or AE exactness.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.x86_const import UC_X86_REG_RIP, UC_X86_REG_XMM5, UC_X86_REG_XMM6

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402


AEX = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
CALLBACK = 0x181170870
STAGES = {
    0x18117098F: "FIELD_READ_INPUT",
    0x181170A09: "SOURCE_READ",
    0x181170C11: "COMPOSE_PRE_U8_SCALE",
    0x181170C20: "U8_PRE_STORE",
    0x181170C40: "POST_STORE",
}
STORE_RIPS = {
    0x181170C29: 1,
    0x181170C30: 3,
    0x181170C37: 2,
    0x181170C3E: 0,
}


def read_xmm_f32(loader: AexLoader, register: int) -> float:
    raw = loader.uc.reg_read(register).to_bytes(16, "little")
    return struct.unpack("<f", raw[:4])[0]


def world8(loader: AexLoader, rgba: tuple[int, int, int, int]) -> tuple[int, int]:
    data = loader.bump_alloc(4, align=64)
    loader.write_bytes(data, bytes(rgba))
    world = loader.host_alloc(0x80, align=16)
    loader.write_bytes(world, b"\0" * 0x80)
    loader.write_bytes(world + 0x18, data.to_bytes(8, "little"))
    loader.write_bytes(world + 0x20, (4).to_bytes(4, "little"))
    loader.write_bytes(world + 0x24, (1).to_bytes(4, "little"))
    loader.write_bytes(world + 0x28, (1).to_bytes(4, "little"))
    return world, data


def refcon(loader: AexLoader, field: int, source: int, gradation: int = 1) -> int:
    r = loader.host_alloc(0x100, align=16)
    loader.write_bytes(r, b"\0" * 0x100)
    loader.write_bytes(r + 0x00, source.to_bytes(8, "little"))
    loader.write_bytes(r + 0x08, field.to_bytes(8, "little"))
    loader.write_bytes(r + 0x94, (3).to_bytes(4, "little"))  # Both
    for offset, value in ((0x9C, 0.22), (0xA0, 0.91), (0xA4, 0.08),
                          (0xAC, 0.03), (0xB0, 0.80), (0xB4, 0.12)):
        loader.write_bytes(r + offset, struct.pack("<f", value))
    loader.write_bytes(r + 0xC0, b"\1")  # background enabled
    loader.write_bytes(r + 0xC1, b"\0")  # invert off => 1-X
    loader.write_bytes(r + 0xC8, gradation.to_bytes(4, "little"))  # Gradation
    loader.write_bytes(r + 0xCC, (1).to_bytes(4, "little"))  # Linear
    return r


def run_fixture(loader: AexLoader, field_world: int, field_data: int,
                source_world: int, source_data: int, name: str,
                gradation: int = 1) -> dict[str, object]:
    field_bytes = loader.read_bytes(field_data, 4)
    source_bytes = loader.read_bytes(source_data, 4)
    output = loader.bump_alloc(4, align=16)
    loader.write_bytes(output, b"\xA5\xA6\xA7\xA8")
    target = refcon(loader, field_world, source_world, gradation)
    events: list[dict[str, object]] = []

    def code_hook(ld: AexLoader, rip: int, _size: int) -> None:
        row: dict[str, object] = {"rip": f"0x{rip:x}", "stage": STAGES[rip]}
        if rip == 0x181170C20:
            row["scaled_float_lane_1_3_2_0"] = [
                ld.read_xmm_f32(1), ld.read_xmm_f32(3),
                read_xmm_f32(ld, UC_X86_REG_XMM5),
                read_xmm_f32(ld, UC_X86_REG_XMM6),
            ]
        if rip == 0x181170C40:
            row["post_store_memory"] = list(ld.read_bytes(output, 4))
        events.append(row)

    def memory_hook(uc, access, address, size, value, _user_data) -> None:
        rip = uc.reg_read(UC_X86_REG_RIP)
        kind = "read" if access == 16 else "write"
        if kind == "read" and (field_data <= address < field_data + 4 or source_data <= address < source_data + 4):
            events.append({"memory": kind, "address": f"0x{address:x}", "size": size,
                           "rip": f"0x{rip:x}", "role": "field" if field_data <= address < field_data + 4 else "source"})
        if kind == "write" and output <= address < output + 4:
            events.append({"memory": kind, "address": f"0x{address:x}", "size": size,
                           "rip": f"0x{rip:x}", "byte_offset": address - output,
                           "byte_value": value & 0xFF})

    # Exact code hooks remain active in the loader's fast mode.
    for rip in STAGES:
        loader.add_code_hook(rip, code_hook)
    loader.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, memory_hook)
    loader.call_function(CALLBACK, int_args=[target, 0, 0, 0, output], max_instructions=200_000)
    return {
        "fixture": name,
        "field_rgba_memory": list(field_bytes),
        "source_rgba_memory": list(source_bytes),
        "output_address": f"0x{output:x}",
        "output_rgba_memory": list(loader.read_bytes(output, 4)),
        "events": events,
    }


def main() -> int:
    fixtures = []
    for fixture in (
        ("baseline", (0, 100, 0, 255), (10, 20, 30, 40), 1),
        ("field_green_plus_one", (0, 101, 0, 255), (10, 20, 30, 40), 1),
        ("source_channel_perturbation", (0, 100, 0, 255), (110, 120, 130, 200), 2),
    ):
        name, field_rgba, source_rgba, gradation = fixture
        loader = AexLoader(str(AEX), verbose=False, fast=True)
        field_world, field_data = world8(loader, field_rgba)
        source_world, source_data = world8(loader, source_rgba)
        fixtures.append(run_fixture(loader, field_world, field_data, source_world, source_data, name, gradation))
    print(json.dumps({
        "aex": str(AEX),
        "aex_sha256": "a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae",
        "callback": "0x181170870",
        "abi": {"rcx": "refcon", "rdx": "x", "r8": "y", "stack_5": "[rsp+0xe0]=output_ptr"},
        "fixtures": fixtures,
        "store_rips": {f"0x{k:x}": v for k, v in STORE_RIPS.items()},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
