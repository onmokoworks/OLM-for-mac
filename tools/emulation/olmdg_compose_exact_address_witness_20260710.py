#!/usr/bin/env python3
"""Bounded actual-AEX witness for DG 0010/0011 compose addresses.

This calls only FUN_181170480 twice per witness.  The worlds are harness-built
so their addresses are local facts, not Windows address captures.  The address
formula and field read offset come from the AEX disassembly; no CLI output is
used as an oracle.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from test_dg_compose import (  # noqa: E402
    FUN_181170480,
    REFCON_SIZE,
    WORLD_DATA_PTR,
    WORLD_HEIGHT,
    WORLD_ROWBYTES,
    WORLD_WIDTH,
    alloc_refcon,
    build_world,
    make_loader,
)


WIDTH = 1920
HEIGHT = 1080
ROWBYTES = WIDTH * 8
PIXEL_SIZE = 8
FIELD_WORD_OFFSET = 2
POINTS = ((6, 40), (901, 394))

# Accepted Windows same-run values from the pointer-map return.  They are
# targets for comparison, not values used to drive the AEX's address math.
WINDOWS = {
    (6, 40): {"field_word": 29500, "store_a": 3268},
    (901, 394): {"field_word": 22892, "store_a": 9876},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_u64(loader, address: int) -> int:
    return struct.unpack("<Q", loader.read_bytes(address, 8))[0]


def read_u32(loader, address: int) -> int:
    return struct.unpack("<I", loader.read_bytes(address, 4))[0]


def make_case0010_refcon(loader, source_world: int, field_world: int) -> int:
    refcon = alloc_refcon(loader)
    loader.write_bytes(refcon, struct.pack("<QQ", source_world, field_world))
    # Static refcon offsets used by FUN_181170480. Case 0010 is gradation,
    # constant interpolation, no background, invert off, Both mode.
    loader.write_bytes(refcon + 0x90, b"\x00")
    loader.write_bytes(refcon + 0x94, struct.pack("<i", 3))
    loader.write_bytes(refcon + 0x9C, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + 0xA0, struct.pack("<f", 1.0))
    loader.write_bytes(refcon + 0xA4, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + 0xAC, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + 0xB0, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + 0xB4, struct.pack("<f", 0.0))
    loader.write_bytes(refcon + 0xC0, b"\x00")
    loader.write_bytes(refcon + 0xC1, b"\x00")
    loader.write_bytes(refcon + 0xC8, struct.pack("<i", 1))
    loader.write_bytes(refcon + 0xCC, struct.pack("<i", 2))
    loader.write_bytes(refcon + 0xD0, struct.pack("<f", 1.0))
    return refcon


def call_actual_aex(loader, refcon: int, x: int, y: int, out: int) -> int:
    regs = loader.call_function(
        FUN_181170480,
        int_args=[refcon, x, y, 0, out],
        max_instructions=200_000,
    )
    return int(regs["instructions"])


def witness() -> dict[str, object]:
    loader = make_loader()
    field_pixels = {xy: (0, WINDOWS[xy]["field_word"], 0, 0) for xy in POINTS}
    source_world = build_world(loader, WIDTH, HEIGHT, {})
    field_world = build_world(loader, WIDTH, HEIGHT, field_pixels)
    refcon = make_case0010_refcon(loader, source_world, field_world)

    source_base = read_u64(loader, source_world + WORLD_DATA_PTR)
    field_base = read_u64(loader, field_world + WORLD_DATA_PTR)
    output_base = loader.bump_alloc(len(POINTS) * PIXEL_SIZE, align=16)
    loader.write_bytes(output_base, b"\xEE" * (len(POINTS) * PIXEL_SIZE))

    result_points = []
    instructions = 0
    for index, (x, y) in enumerate(POINTS):
        output_addr = output_base + index * PIXEL_SIZE
        field_addr = field_base + y * ROWBYTES + x * PIXEL_SIZE
        source_addr = source_base + y * ROWBYTES + x * PIXEL_SIZE
        instructions += call_actual_aex(loader, refcon, x, y, output_addr)
        field_words = struct.unpack("<4H", loader.read_bytes(field_addr, 8))
        source_words = struct.unpack("<4H", loader.read_bytes(source_addr, 8))
        output_words = struct.unpack("<4H", loader.read_bytes(output_addr, 8))
        field_word = field_words[1]
        result_points.append({
            "xy": [x, y],
            "field_addr": hex(field_addr),
            "source_addr": hex(source_addr),
            "output_addr": hex(output_addr),
            "field_words_agrb": list(field_words),
            "source_words_agrb": list(source_words),
            "field_read_word_at_rcx_plus_2": field_word,
            "field_scalar_x": field_word / 32768.0,
            "compose_alpha_xmm2_model": 1.0 - field_word / 32768.0,
            "aex_output_words_agrb": list(output_words),
            "windows_store_a": WINDOWS[(x, y)]["store_a"],
            "aex_matches_windows_store_a": output_words[0] == WINDOWS[(x, y)]["store_a"],
        })

    return {
        "kind": "olmdg_compose_exact_address_witness",
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "local_actual_aex_bounded_witness",
        "binary": {
            "path": "plugins_2025/DistanceGradation.aex",
            "sha256": sha256_file(ROOT / "plugins_2025/DistanceGradation.aex"),
            "function": hex(FUN_181170480),
            "max_instructions_per_call": 200000,
            "calls": len(POINTS),
        },
        "address_formula": {
            "field": "field_base + y * field_rowbytes + x * field_pixel_size",
            "source": "source_base + y * source_rowbytes + x * source_pixel_size",
            "output": "output_base + output_index * output_pixel_size (local two-point output); Windows full-frame form is output_base + y * 0x3c00 + x * 8",
            "field_read": "field_addr + 0x2 (FUN_181170480 reads [RCX+2])",
            "rowbytes": ROWBYTES,
            "pixel_size": PIXEL_SIZE,
            "dimensions": [WIDTH, HEIGHT],
            "channel_layout": "A,G,R,B words in this harness, with compose read at +0x2",
        },
        "local_bases": {
            "field_base": hex(field_base),
            "source_base": hex(source_base),
            "output_base": hex(output_base),
            "note": "Unicorn heap addresses; not Windows address evidence.",
        },
        "windows_reference": {
            "source_output_rowbytes": "0x3c00",
            "pixel_size": 8,
            "output_formula": "output_base + y * 0x3c00 + x * 8",
            "field_base": "not returned",
            "field_world_layout": "not returned",
        },
        "instructions_total": instructions,
        "points": result_points,
    }


def main() -> int:
    report = witness()
    out = ROOT / "refs/conformance/olmdg_compose_exact_address_witness_20260710.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"wrote={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
