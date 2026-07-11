"""Bounded full-entry probe for OLMBlur Legacy 16bpc FUN_180005f20.

This is a host-layout probe, not an AE-exact render claim.  The context,
parameter, and world offsets below are copied from the OLMBlur decompilation
and disassembly; PF Handle callbacks follow the existing DG/DirectionalBlur
emulation harnesses.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from unicorn.x86_const import UC_X86_REG_RIP

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = REPO_ROOT / "plugins_2025" / "OLMBlur.aex"
FUN_ENTRY = 0x180005F20
FUN_HORIZONTAL = 0x1800014F0
FUN_LEGACY_OR_VERTICAL = 0x180001EA0


def u64(loader: AexLoader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def build_pf_suites(loader: AexLoader) -> tuple[int, list[tuple[str, int]]]:
    events: list[tuple[str, int]] = []

    def h_new(ld: AexLoader, args: list[int]) -> int:
        size = args[0] & 0xFFFFFFFFFFFFFFFF
        data = ld.bump_alloc(max(size, 1), align=64)
        ld.write_bytes(data, b"\x00" * max(size, 1))
        handle = ld.host_alloc(8)
        ld.write_bytes(handle, struct.pack("<Q", data))
        events.append(("new", size))
        return handle

    def h_lock(ld: AexLoader, args: list[int]) -> int:
        events.append(("lock", args[0]))
        return u64(ld, args[0]) if args[0] else 0

    def h_unlock(ld: AexLoader, args: list[int]) -> int:
        events.append(("unlock", args[0]))
        return 0

    def h_dispose(ld: AexLoader, args: list[int]) -> int:
        events.append(("dispose", args[0]))
        return 0

    suite = loader.host_alloc(0x20)
    loader.write_bytes(
        suite,
        struct.pack(
            "<4Q",
            loader.install_callback("PFHandle.new", h_new),
            loader.install_callback("PFHandle.lock", h_lock),
            loader.install_callback("PFHandle.unlock", h_unlock),
            loader.install_callback("PFHandle.dispose", h_dispose),
        ),
    )

    def acquire(ld: AexLoader, args: list[int]) -> int:
        out_suite = args[2]
        ld.write_bytes(out_suite, struct.pack("<Q", suite))
        events.append(("AcquireSuite", args[1]))
        return 0

    def release(ld: AexLoader, args: list[int]) -> int:
        events.append(("ReleaseSuite", 0))
        return 0

    spbasic = loader.host_alloc(0x10)
    loader.write_bytes(
        spbasic,
        struct.pack(
            "<2Q",
            loader.install_callback("SPBasic.AcquireSuite", acquire),
            loader.install_callback("SPBasic.ReleaseSuite", release),
        ),
    )
    return spbasic, events


def build_context(loader: AexLoader, spbasic: int) -> int:
    ctx = loader.host_alloc(0x200)
    loader.write_bytes(ctx, b"\x00" * 0x200)
    # FUN_180005f20 reads render scale from +0x11c/+0x120 and SPBasic at +0x180.
    loader.write_bytes(ctx + 0x11C, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x120, struct.pack("<I", 1))
    loader.write_bytes(ctx + 0x180, struct.pack("<Q", spbasic))
    return ctx


def build_world(loader: AexLoader, width: int, height: int) -> tuple[int, int]:
    rowbytes = width * 8
    data = loader.bump_alloc(rowbytes * height, align=64)
    pixels = bytearray(rowbytes * height)
    for y in range(height):
        for x in range(width):
            off = y * rowbytes + x * 8
            # A nonzero alpha plus nonuniform RGB makes unpack and writeback visible.
            pixels[off:off + 8] = struct.pack("<4H", 0xFFFF, 100 + x, 200 + y, 300 + x + y)
    loader.write_bytes(data, bytes(pixels))
    world = loader.host_alloc(0x80)
    loader.write_bytes(world, b"\x00" * 0x80)
    # FUN_180005f20's observed 16bpc reads use data + row*rowbytes + x*8.
    loader.write_bytes(world + 0x18, struct.pack("<Q", data))
    loader.write_bytes(world + 0x20, struct.pack("<I", rowbytes))
    loader.write_bytes(world + 0x24, struct.pack("<I", width))
    loader.write_bytes(world + 0x28, struct.pack("<I", height))
    loader.write_bytes(world + 0x2C, struct.pack("<H", 16))
    return world, data


def build_params(loader: AexLoader, radius: float = 1.0, strength: float = 1.0) -> int:
    params = loader.host_alloc(0x40)
    loader.write_bytes(params, b"\x00" * 0x40)
    # Decomp/disasm: +0x18 is bit-depth branch, +0x20/+0x24 feed radius math,
    # and +0x2c selects the horizontal/vertical mode loop.
    loader.write_bytes(params + 0x18, struct.pack("<I", 16))
    loader.write_bytes(params + 0x20, struct.pack("<f", radius))
    loader.write_bytes(params + 0x24, struct.pack("<f", strength))
    loader.write_bytes(params + 0x2C, struct.pack("<I", 1))
    return params


def main() -> int:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=False)
    loader.register_libm_impls(max_threads=1)
    spbasic, events = build_pf_suites(loader)
    ctx = build_context(loader, spbasic)
    width, height = 8, 2
    source, source_data = build_world(loader, width, height)
    output, output_data = build_world(loader, width, height)
    loader.write_bytes(output_data, b"\x00" * (width * height * 8))
    params = build_params(loader)

    hits: list[tuple[str, int]] = []

    def mark(label: str):
        def hook(ld: AexLoader, address: int, size: int) -> None:
            hits.append((label, address))
        return hook

    loader.add_code_hook(FUN_ENTRY, mark("entry"))
    loader.add_code_hook(FUN_HORIZONTAL, mark("horizontal"))
    loader.add_code_hook(FUN_LEGACY_OR_VERTICAL, mark("worker_180001ea0"))

    try:
        result = loader.call_function(FUN_ENTRY, int_args=[ctx, source, output, params], max_instructions=2_000_000)
        status = "return"
        error = None
    except Exception as exc:  # Unicorn reports the precise unmapped access here.
        result = {}
        status = "exception"
        error = f"{type(exc).__name__}: {exc}"

    output_head = loader.read_bytes(output_data, min(32, rowbytes := width * 8)).hex()
    print("FACT entry", hex(FUN_ENTRY))
    print("FACT grounded_context_offsets", {"scale_num": "0x11c", "scale_den": "0x120", "spbasic": "0x180"})
    print("FACT grounded_param_offsets", {"bit_depth": "0x18", "radius": "0x20", "strength": "0x24", "mode": "0x2c"})
    print("FACT grounded_world_offsets", {"data": "0x18", "rowbytes": "0x20", "width": "0x24", "height": "0x28", "bit_depth": "0x2c"})
    print("FACT status", status)
    print("FACT error", error)
    print("FACT result_rax", hex(result.get("rax", 0)) if result else None)
    print("FACT callbacks", events)
    print("FACT code_hits", [(name, hex(address)) for name, address in hits])
    print("FACT output_head_hex", output_head)
    print("INFERENCE final_store_reached", bool(hits and status == "return" and output_head != bytes(width * 8).hex()))
    print("INFERENCE scope: mocked host structs and synthetic 16bpc worlds are layout probes, not AE-exact output evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
