#!/usr/bin/env python3
"""Lock the checked-in AEX boundary for PF32 Mode5's unresolved IPP result."""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/DistanceGradation.aex"
IMAGE_BASE = 0x180000000


def sections(blob: bytes):
    pe = struct.unpack_from("<I", blob, 0x3C)[0]
    count = struct.unpack_from("<H", blob, pe + 6)[0]
    optional_size = struct.unpack_from("<H", blob, pe + 20)[0]
    cursor = pe + 24 + optional_size
    result = []
    for _ in range(count):
        row = blob[cursor:cursor + 40]
        name = row[:8].rstrip(b"\0").decode("ascii")
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from("<IIII", row, 8)
        result.append((name, rva, max(virtual_size, raw_size), raw_offset))
        cursor += 40
    return result


blob = AEX.read_bytes()
table = sections(blob)


def at_rva(rva: int, size: int) -> bytes:
    for _, base, span, raw in table:
        if base <= rva and rva + size <= base + span:
            return blob[raw + rva - base:raw + rva - base + size]
    raise AssertionError(f"unmapped RVA 0x{rva:x}")


# The CV_32F bilateral invoker vtable used by the exported path points its
# ParallelLoopBody::operator() slot at the IPP invoker body.
vtable = struct.unpack("<4Q", at_rva(0x15553C8, 32))
assert vtable[1] == IMAGE_BASE + 0x12C9430

# Its body calls the checked-in OpenCV/IPP backend wrapper.
call_rva = 0x12C94F1
call = at_rva(call_rva, 5)
assert call[0] == 0xE8
target = call_rva + 5 + struct.unpack_from("<i", call, 1)[0]
assert target == 0x1399760

# The opaque/no-background compose boundary only multiplies the field value
# by source alpha and stores that alpha. It cannot create the preceding ULPs.
assert at_rva(0x1170F8B, 4) == bytes.fromhex("f30f59f2")  # mulss xmm6,xmm2
assert at_rva(0x1170FB2, 4) == bytes.fromhex("f30f1137")  # movss [rdi],xmm6

print("PASS_OLMDISTANCEGRADATION_PF32_MODE5_IPP_PRODUCER_BOUNDARY_20260811")
