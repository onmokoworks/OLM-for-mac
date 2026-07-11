"""
aex_witness.py — reusable primitives for driving OLM (and other AE) .aex
functions under the AexLoader emulator and reading typed witnesses.

Every per-plugin test_*.py in this directory re-implemented the same steps:
build a pixel world, marshal params, drive a function, read back a float cell.
This module collects the hard-won, cross-plugin pieces so the next plugin (OLM
or not) starts from a checklist instead of rediscovering them. See GOTCHAS.md
for *why* each of these is the way it is.

Nothing here changes AexLoader; it only wraps its public API
(build_pf_world/read_* use loader.host_alloc/bump_alloc/read_bytes/write_bytes).
Existing tests keep working; opt in when convenient.
"""
from __future__ import annotations

import struct
from typing import List, Tuple

# --- AE PF world header offsets --------------------------------------------
# Empirically confirmed on the OLM 2025 x64 builds (RadialBlur/DistanceGradation).
# These match the AE SDK PF_EffectWorld/PF_LayerDef shape. VERIFY per new plugin
# by sentinel-probing which offsets the callee reads (see GOTCHAS.md #5).
WORLD_DATA_OFF = 0x18      # qword: pointer to pixel data
WORLD_ROWBYTES_OFF = 0x20  # u32: row stride in BYTES
WORLD_WIDTH_OFF = 0x24     # u32
WORLD_HEIGHT_OFF = 0x28    # u32
WORLD_BPC_OFF = 0x2C       # u16: bits-per-channel tag (e.g. 8)
WORLD_STRUCT_SIZE = 0x80


def rgba_to_argb_bytes(rgba: bytes) -> bytes:
    """PIL/RGBA byte order -> AE PF_Pixel ARGB (alpha-first) byte order.

    AE PF_Pixel8 is {alpha, red, green, blue} in memory. Feeding raw RGBA makes
    the plugin's source-world unpack read alpha into blue and blue into alpha
    (the classic [x,x,y,y] vs [z,z,z,1.0] signature). See GOTCHAS.md #2.
    """
    if len(rgba) % 4 != 0:
        raise ValueError("rgba length must be a multiple of 4")
    mv = memoryview(rgba)
    out = bytearray(len(rgba))
    out[0::4] = mv[3::4]  # A
    out[1::4] = mv[0::4]  # R
    out[2::4] = mv[1::4]  # G
    out[3::4] = mv[2::4]  # B
    return bytes(out)


def promote_ae16(half_word: int) -> int:
    """AE internal 16-bit (PF_MAX_CHAN16 == 32768, 1.0==0x8000) -> full 0..65535.

    trunc(half / 32768 * 65535). NOT half*2 (that gives +1 errors: 0x8000*2 =
    65536 != 65535). Verified on DistanceGradation case_0023. See GOTCHAS.md #3.
    """
    return int(half_word / 32768.0 * 65535.0)


def build_pf_world(loader, width: int, height: int, argb_bytes: bytes,
                   bpc: int = 8) -> int:
    """Allocate a PF world header + data and return the header pointer.

    `argb_bytes` must already be in AE ARGB order (use rgba_to_argb_bytes()).
    Uses the host_alloc region for the header and bump_alloc for the pixels,
    matching the split every existing test uses.
    """
    data = loader.bump_alloc(len(argb_bytes), align=64)
    loader.write_bytes(data, argb_bytes)
    world = loader.host_alloc(WORLD_STRUCT_SIZE)
    loader.write_bytes(world, b"\x00" * WORLD_STRUCT_SIZE)
    loader.write_bytes(world + WORLD_DATA_OFF, struct.pack("<Q", data))
    loader.write_bytes(world + WORLD_ROWBYTES_OFF, struct.pack("<I", width * 4))
    loader.write_bytes(world + WORLD_WIDTH_OFF, struct.pack("<I", width))
    loader.write_bytes(world + WORLD_HEIGHT_OFF, struct.pack("<I", height))
    loader.write_bytes(world + WORLD_BPC_OFF, struct.pack("<H", bpc))
    return world


def read_plane_cell_f32(loader, plane_ptr: int, cols: int, row: int, col: int
                        ) -> Tuple[float, float, float, float]:
    """Read a 4-float RGBA cell from a row-major float plane.

    Note the internal working plane is RGBA (alpha LAST), even though the input
    world is ARGB — the plugin reorders on unpack. See GOTCHAS.md #2.
    """
    base = plane_ptr + (row * cols + col) * 16
    return struct.unpack("<4f", loader.read_bytes(base, 16))


def read_plane_cell_bits(loader, plane_ptr: int, cols: int, row: int, col: int
                         ) -> Tuple[int, int, int, int]:
    """Same as read_plane_cell_f32 but returns raw u32 bit patterns (for exact
    bit / ULP comparison against Windows CDB typed cells)."""
    base = plane_ptr + (row * cols + col) * 16
    return struct.unpack("<4I", loader.read_bytes(base, 16))


def ulp_u32(a: int, b: int) -> int:
    """ULP-ish distance between two float bit patterns (monotone-ordered floats
    only; fine for the small same-sign deltas seen in these witnesses)."""
    return abs((a & 0xFFFFFFFF) - (b & 0xFFFFFFFF))


def f32_bits(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def bits_f32(b: int) -> float:
    return struct.unpack("<f", struct.pack("<I", b))[0]


def leaf_check(loader, addr: int, int_args: List[int], expected_ret: int = None,
               max_instructions: int = 2_000_000):
    """Drive a small import-free leaf and return its result dict. Use to sanity
    -check ABI/stack-arg placement before trusting a real witness run — the
    fastest detector of a mis-placed 5th (stack) argument. See GOTCHAS.md #4."""
    res = loader.call_function(addr, int_args=int_args, max_instructions=max_instructions)
    if expected_ret is not None and res.get("rax") != expected_ret:
        raise AssertionError(f"leaf_check {hex(addr)}: rax={res.get('rax'):#x} != {expected_ret:#x}")
    return res
