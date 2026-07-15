#!/usr/bin/env python3
"""Probe checked-in OLMColorKey edge leaves and emit FACT/INFERENCE evidence."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aex_loader import AexLoader  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AEX = ROOT / "aex" / "OLMColorKey" / "Plugins" / "64" / "2025" / "OLMColorKey.aex"
BOUNDARY = 0x180008C90
WEIGHT = 0x1800049A0


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
    return alloc(loader, bytes(header), align=16)


def first_channel(loader: AexLoader, payload: int, width: int, height: int, pixel_size: int) -> list[list[int]]:
    raw = loader.read_bytes(payload, width * height * pixel_size)
    return [[raw[(y * width + x) * pixel_size] for x in range(width)] for y in range(height)]


def f32_grid(loader: AexLoader, payload: int, width: int, height: int) -> list[list[float]]:
    values = struct.unpack("<%df" % (width * height), loader.read_bytes(payload, width * height * 4))
    return [list(values[y * width:(y + 1) * width]) for y in range(height)]


def run(aex_path: Path) -> dict:
    loader = AexLoader(str(aex_path), verbose=False, fast=True)
    width, height = 7, 5
    # 255 is the kept/keyed side. Fixtures isolate diagonal, frame-edge, and
    # single-pixel adjacency behavior without using a rendered PNG.
    cases = {
        "isolated_center": [(3, 2)],
        "frame_corner": [(0, 0)],
        "diagonal_pair": [(2, 1), (3, 2)],
        "horizontal_run": [(1, 2), (2, 2), (3, 2)],
    }
    boundary_results = {}
    for name, points in cases.items():
        source = bytearray(width * height * 4)
        for x, y in points:
            source[(y * width + x) * 4] = 255
        source_plane = plane(loader, width, height, 4, bytes(source))
        output_data = bytearray(width * height * 4)
        output_payload = alloc(loader, bytes(output_data))
        output_plane = plane(loader, width, height, 4, bytes(output_data))
        # Redirect the output plane's data pointer to the separately allocated
        # zero buffer so the returned address can be read without ambiguity.
        loader.write_bytes(output_plane + 0x18, struct.pack("<Q", output_payload))
        result = loader.call_function(BOUNDARY, int_args=[source_plane, output_plane, 8], max_instructions=200_000)
        boundary_results[name] = {
            "source_points": [[x, y] for x, y in points],
            "output_first_channel": first_channel(loader, output_payload, width, height, 4),
            "rax": hex(result["rax"]),
        }

    # Weight leaf: boundary byte plane and float distance plane are independent
    # inputs, making the seed/distance/weight boundary observable separately.
    boundary = bytearray(width * height * 4)
    distances = []
    for y in range(height):
        for x in range(width):
            index = y * width + x
            boundary[index * 4] = 255 if x in (0, 3, 6) else 0
            distances.append(float(x))
    boundary_plane = plane(loader, width, height, 4, bytes(boundary))
    distance_plane = plane(loader, width, height, 16, struct.pack("<%df" % (width * height * 4), *[v for v in distances for _ in range(4)]))
    weights_payload = alloc(loader, bytes(width * height * 4 * 4))
    weights_plane = plane(loader, width, height, 16, bytes(width * height * 16))
    loader.write_bytes(weights_plane + 0x18, struct.pack("<Q", weights_payload))
    # The float occupies argument slot 0 (XMM0), so the GP argument list has
    # an explicit placeholder before the three pointer arguments.
    weight_result = loader.call_function(WEIGHT, float_args={0: 4.0}, int_args=[0, boundary_plane, distance_plane, weights_payload], max_instructions=200_000)
    weights = f32_grid(loader, weights_payload, width, height)

    report = {
        "kind": "olmcolorkey_edge_thin_blur_actual_aex_decomp_probe",
        "schema": 1,
        "classification": "Mac-local Unicorn execution of checked-in Windows PE leaves; not AE-host execution and not AE-exact output",
        "aex": str(aex_path.relative_to(ROOT)),
        "functions": {
            "boundary_seed": {"va": hex(BOUNDARY), "name": "FUN_180008c90", "bit_depth_arg": 8},
            "edge_blur_weight": {"va": hex(WEIGHT), "name": "FUN_1800049a0", "amount": 4.0},
        },
        "facts": {
            "boundary_seed_fixtures": boundary_results,
            "weight_grid_first_float": weights,
            "weight_rax": hex(weight_result["rax"]),
            "imports": [entry.name for entry in loader.import_log],
            "instructions": loader.instructions_executed,
        },
        "inferences": [
            "FUN_180008c90 seeds every nonzero source pixel to the bit-depth maximum, then clears the output seed when an in-frame 8-neighbor is zero; its edge checks do not treat out-of-frame neighbors as zero.",
            "FUN_1800049a0 consumes an already-built byte boundary plane and an independent float distance plane; it is therefore downstream of seed construction and distance calculation.",
            "For direction/type 1, a nonzero boundary receives full weight at distance >= amount and a sine-ramp weight below amount; a zero boundary receives zero weight.",
            "The probe does not establish the distance-transform metric, the full apply/composite semantics, or AE host behavior.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aex", type=Path, default=DEFAULT_AEX)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.aex)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass_leaf_probe", "json": str(args.json), "instructions": report["facts"]["instructions"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
