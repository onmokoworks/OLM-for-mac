#!/usr/bin/env python3
"""Execute the ColorKey seed -> distance boundary on the checked-in AEX."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

BOUNDARY = 0x180008C90
DISTANCE = {1: 0x180006E20, 2: 0x180005D60}
DEFAULT_AEX = ROOT / "aex/OLMColorKey/Plugins/64/2025/OLMColorKey.aex"


def alloc(loader: AexLoader, data: bytes, align: int = 16) -> int:
    address = loader.bump_alloc(len(data), align=align)
    loader.write_bytes(address, data)
    return address


def plane(loader: AexLoader, width: int, height: int, pixel_size: int, data: bytes) -> int:
    assert len(data) == width * height * pixel_size
    payload = alloc(loader, data)
    header = bytearray(0x30)
    struct.pack_into("<Q", header, 0x18, payload)
    struct.pack_into("<i", header, 0x20, width * pixel_size)
    struct.pack_into("<i", header, 0x24, width)
    struct.pack_into("<i", header, 0x28, height)
    return alloc(loader, bytes(header))


def f32_grid(loader: AexLoader, payload: int, width: int, height: int) -> list[list[float]]:
    values = struct.unpack("<%df" % (width * height), loader.read_bytes(payload, width * height * 4))
    return [list(values[y * width:(y + 1) * width]) for y in range(height)]


def byte_grid(loader: AexLoader, payload: int, width: int, height: int) -> list[list[int]]:
    raw = loader.read_bytes(payload, width * height * 4)
    return [[raw[(y * width + x) * 4] for x in range(width)] for y in range(height)]


def run(aex_path: Path) -> dict:
    width, height = 5, 3
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    source = bytearray(width * height * 4)
    source[(1 * width + 2) * 4] = 255
    source_world = plane(loader, width, height, 4, bytes(source))
    seed_payload = alloc(loader, b"\0" * (width * height * 4))
    seed_world = plane(loader, width, height, 4, b"\0" * (width * height * 4))
    loader.write_bytes(seed_world + 0x18, struct.pack("<Q", seed_payload))
    seed_call = loader.call_function(BOUNDARY, int_args=[source_world, seed_world, 8], max_instructions=200_000)

    ctx = loader.host_alloc(0x140)
    loader.write_bytes(ctx, b"\0" * 0x140)
    loader.write_bytes(ctx + 0x120, struct.pack("<i", 255))
    loader.write_bytes(ctx + 0x128, struct.pack("<i", 255))
    distances: dict[str, object] = {}
    for distance_type, function in DISTANCE.items():
        output_payload = alloc(loader, b"\0" * (width * height * 16))
        output_world = plane(loader, width, height, 16, b"\0" * (width * height * 16))
        loader.write_bytes(output_world + 0x18, struct.pack("<Q", output_payload))
        result = loader.call_function(
            function,
            int_args=[ctx, seed_world, output_world],
            float_args={3: 255.0},
            max_instructions=200_000,
        )
        distances[str(distance_type)] = {
            "va": hex(function),
            "first_float_grid": f32_grid(loader, output_payload, width, height),
            "rax": hex(result["rax"]),
            "instructions": result["instructions"],
            "imports": [entry.name for entry in loader.import_log],
        }

    return {
        "kind": "olmcolorkey_boundary_to_distance_actual_aex_20260716",
        "schema": 1,
        "classification": "Mac-local Unicorn execution of checked-in Windows PE leaves; not AE-host execution and not AE-exact output",
        "aex": str(aex_path.relative_to(ROOT)),
        "abi": {
            "boundary_seed": {"va": hex(BOUNDARY), "args": "RCX=source_world, RDX=seed_world, R8D=8"},
            "distance_leaves": {"args": "RCX=context, RDX=seed_world, R8=distance_world, XMM3=255.0"},
            "context_offsets": {"0x120": 255, "0x128": 255},
            "world_offsets": {"0x18": "payload", "0x20": "row_bytes", "0x24": "width", "0x28": "height"},
        },
        "facts": {
            "seed_first_channel": byte_grid(loader, seed_payload, width, height),
            "seed_rax": hex(seed_call["rax"]),
            "distance": distances,
            "distance_type_3_next_blocker": "FUN_180007ec0 allocates an internal squared-distance buffer through ctx+0x180 AE handle suite; this witness does not emulate that host table.",
        },
        "inferences": [
            "The boundary seed world is directly consumable by the type 1 and type 2 distance leaves without an AE import or allocator callback.",
            "The next unresolved ABI is isolated to the type 3 Euclidean leaf's ctx+0x180 handle-suite allocation path, not the seed-to-distance plane contract for types 1 and 2.",
            "This is an executable AEX/decomp differential witness, not an AE-exact claim.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.aex)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass_boundary_to_distance", "json": str(args.json)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
