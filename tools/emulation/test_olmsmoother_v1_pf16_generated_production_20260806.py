#!/usr/bin/env python3
"""Compare generated PF16 EdgeWalker/SubHandler with the pinned actual AEX."""
import ctypes
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader

AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
EDGEWALKER16 = 0x180009960
SUBHANDLER16 = 0x180002740
LIB = Path("/tmp/olmsmoother_pf16_generated_20260806.dylib")
WIDTH = HEIGHT = 7
X = Y = 3
DIRECTIONS = (1, 3, 5, 7)


def build() -> None:
    subprocess.run([
        "clang++", "-std=c++17", "-fPIC", "-shared",
        "-I" + str(ROOT / "cli/OLMSmoother/shim"),
        str(ROOT / "tools/emulation/olmsmoother_v1_pf16_control_ctypes_harness_20260806.cpp"),
        "-o", str(LIB),
    ], check=True)


def fixtures():
    yield "flat", [(32768, 12000, 18000, 24000)] * (WIDTH * HEIGHT)
    yield "impulse", [
        (32768, 32768 if x == X and y == Y else 0,
         8192 if x == X and y == Y else 0,
         24576 if x == X and y == Y else 0)
        for y in range(HEIGHT) for x in range(WIDTH)
    ]
    yield "checker", [
        (32768, 32768 if (x + y) & 1 else 0,
         2048 + x * 3072, 4096 + y * 2560)
        for y in range(HEIGHT) for x in range(WIDTH)
    ]
    yield "boundary", [
        (32768, (x * 5003 + y * 7001) & 0x7FFF,
         (x * 8191 + y) & 0x7FFF, (y * 8191 + x) & 0x7FFF)
        for y in range(HEIGHT) for x in range(WIDTH)
    ]


def raw_bytes(pixels) -> bytes:
    return b"".join(struct.pack("<4H", *pixel) for pixel in pixels)


def actual_fixture(loader, raw):
    pixel_base = loader.host_alloc(len(raw), align=16)
    loader.write_bytes(pixel_base, raw)
    world = loader.host_alloc(0x40, align=16)
    loader.write_bytes(world, b"\0" * 0x40)
    loader.write_bytes(world + 4, struct.pack("<iii", WIDTH, HEIGHT, WIDTH * 8))
    loader.write_bytes(world + 0x10, struct.pack("<Q", pixel_base))
    loader.write_bytes(world + 0x18, struct.pack("<Qiii", pixel_base, WIDTH * 8, WIDTH, HEIGHT))
    state = loader.host_alloc(0x80, align=16)
    loader.write_bytes(state, b"\0" * 0x80)
    loader.write_bytes(state + 8, struct.pack("<iii", 6, 6, 6))
    loader.write_bytes(state + 0x18, struct.pack("<Q", world))
    pointers = [pixel_base + ((Y + dy) * WIDTH + X + dx) * 8
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
    neighbors = loader.host_alloc(72, align=16)
    loader.write_bytes(neighbors, struct.pack("<9Q", *pointers))
    return pixel_base, state, neighbors


def main() -> None:
    assert hashlib.sha256(AEX.read_bytes()).hexdigest() == AEX_SHA256
    build()
    dll = ctypes.CDLL(str(LIB))
    edge = dll.olmsmoother_edgewalker16_generated
    edge.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.c_int, ctypes.c_int,
                     ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32,
                     ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    edge.restype = ctypes.c_int64
    sub = dll.olmsmoother_subhandler16_generated
    sub.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.c_int, ctypes.c_int,
                    ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_int,
                    ctypes.c_int, ctypes.POINTER(ctypes.c_uint32)]
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    mismatches = []
    calls = 0
    for name, pixels in fixtures():
        raw = raw_bytes(pixels)
        for direction in DIRECTIONS:
            pixel_base, state, neighbors = actual_fixture(loader, raw)
            out_x = loader.host_alloc(4, align=4)
            out_y = loader.host_alloc(4, align=4)
            loader.write_bytes(out_x, struct.pack("<i", -99))
            loader.write_bytes(out_y, struct.pack("<i", -99))
            actual_ptr = loader.call_function(
                EDGEWALKER16, [state, X, Y, direction, direction, out_x, out_y, 6],
                max_instructions=500000)["rax"]
            actual_edge = (
                actual_ptr & 0xFFFFFFFF,
                struct.unpack("<i", loader.read_bytes(out_x, 4))[0],
                struct.unpack("<i", loader.read_bytes(out_y, 4))[0],
            )
            buf = (ctypes.c_uint16 * (len(raw) // 2)).from_buffer_copy(raw)
            got_x, got_y = ctypes.c_int(-99), ctypes.c_int(-99)
            portable_edge = (edge(buf, WIDTH, HEIGHT, X, Y, direction, direction,
                                  6, ctypes.byref(got_x), ctypes.byref(got_y)),
                             got_x.value, got_y.value)
            calls += 1
            if actual_edge != portable_edge:
                mismatches.append((name, direction, "edge", actual_edge, portable_edge))

            outs = [loader.host_alloc(4, align=4) for _ in range(9)]
            for pointer in outs:
                loader.write_bytes(pointer, b"\0" * 4)
            loader.call_function(SUBHANDLER16,
                                 [state, neighbors, X, Y, direction, *outs],
                                 max_instructions=1000000)
            actual_sub = [struct.unpack("<I", loader.read_bytes(p, 4))[0] for p in outs]
            got = (ctypes.c_uint32 * 9)()
            sub(buf, WIDTH, HEIGHT, X, Y, direction, 6, 6, got)
            portable_sub = list(got)
            calls += 1
            if actual_sub != portable_sub:
                mismatches.append((name, direction, "sub", actual_sub, portable_sub))
    report = {
        "status": "exact" if not mismatches else "fail",
        "aex_sha256": AEX_SHA256,
        "scope": ["EdgeWalker16 0x180009960..0x180009e30",
                  "SubHandler16 0x180002740..0x1800033c4"],
        "fixtures": 4,
        "directions": list(DIRECTIONS),
        "calls": calls,
        "mismatch_count": len(mismatches),
        "first_mismatches": mismatches[:3],
    }
    print(json.dumps(report, indent=2))
    assert not mismatches


if __name__ == "__main__":
    main()
