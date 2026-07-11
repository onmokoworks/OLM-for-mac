"""Typed AEX fixtures for the helpers called by FUN_180005f20.

The fixtures deliberately call FUN_1800014f0 and FUN_180001ea0 directly.
They are not full-entry renders and do not reuse the older 0x1000/0x1980
helper fixture family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
FIXTURES = Path(__file__).parent / "fixtures" / "olmblur_fullworker_helper"
HORIZONTAL = 0x1800014F0
VERTICAL = 0x180001EA0


CASES = [
    {"id": "horizontal_basic", "direction": "horizontal", "width": 7, "height": 4, "columns": 5, "rows": 2, "offset": 1, "radius": 3, "breaks": []},
    {"id": "horizontal_flag_break", "direction": "horizontal", "width": 9, "height": 5, "columns": 7, "rows": 3, "offset": 1, "radius": 2, "breaks": [11, 13, 31]},
    {"id": "horizontal_large_radius", "direction": "horizontal", "width": 13, "height": 7, "columns": 10, "rows": 3, "offset": 2, "radius": 5, "breaks": [28, 31, 45, 72]},
    {"id": "horizontal_all_same_center_copy", "direction": "horizontal", "width": 4, "height": 2, "columns": 4, "rows": 2, "offset": 0, "radius": 1, "breaks": [], "witness": [0, 1], "carry_rgb": [37.25, 83.5, 129.75], "center_rgb": [211.5, 17.25, 64.75]},
    {"id": "vertical_basic", "direction": "vertical", "width": 6, "height": 8, "columns": 3, "rows": 6, "offset": 1, "radius": 2, "breaks": []},
    {"id": "vertical_flag_break", "direction": "vertical", "width": 8, "height": 9, "columns": 5, "rows": 7, "offset": 2, "radius": 3, "breaks": [18, 26, 51]},
    {"id": "vertical_large_radius", "direction": "vertical", "width": 11, "height": 14, "columns": 6, "rows": 10, "offset": 2, "radius": 5, "breaks": [24, 35, 69, 112]},
    {"id": "vertical_all_same_center_copy", "direction": "vertical", "width": 3, "height": 3, "columns": 2, "rows": 3, "offset": 0, "radius": 1, "breaks": [], "witness": [1, 0], "carry_rgb": [37.25, 83.5, 129.75], "center_rgb": [211.5, 17.25, 64.75]},
]


def alloc(loader: AexLoader, data: bytes) -> int:
    addr = loader.bump_alloc(len(data), align=16)
    loader.write_bytes(addr, data)
    return addr


def run_case(case: dict) -> bytes:
    width = case["width"]
    height = case["height"]
    count = width * height
    flags_data = bytearray([1] * count)
    for index in case["breaks"]:
        flags_data[index] = 0
    src_values = [float((index * 17 + channel * 3) % 251) / 7.0 for index in range(count) for channel in range(3)]
    if "witness" in case:
        carry = case["carry_rgb"]
        center = case["center_rgb"]
        src_values = list(carry) * count
        witness_x, witness_y = case["witness"]
        witness_index = witness_y * width + witness_x
        src_values[witness_index * 3:witness_index * 3 + 3] = center
    weights_values = [0.375 + (index * 0.625) for index in range(case["radius"] * 2 + 1)]
    dst_values = [-777.0] * (count * 3)

    loader = AexLoader(str(AEX), verbose=False, fast=True)
    flags = alloc(loader, bytes(flags_data))
    src = alloc(loader, struct.pack(f"<{len(src_values)}f", *src_values))
    dst = alloc(loader, struct.pack(f"<{len(dst_values)}f", *dst_values))
    weights = alloc(loader, struct.pack(f"<{len(weights_values)}f", *weights_values))
    args = [flags, src, dst, weights, width]
    if case["direction"] == "horizontal":
        args += [0, case["columns"], case["rows"], case["offset"], case["radius"]]
        address = HORIZONTAL
    else:
        args += [height, case["columns"], case["rows"], case["offset"], case["radius"]]
        address = VERTICAL
    result = loader.call_function(address, int_args=args, max_instructions=2_000_000)
    return loader.read_bytes(dst, len(dst_values) * 4), result["instructions"]


def export() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "olm.aex.cpu-fixture/2", "plugin": "OLMBlur", "binary_sha256": hashlib.sha256(AEX.read_bytes()).hexdigest(), "functions": {"horizontal": hex(HORIZONTAL), "vertical": hex(VERTICAL)}, "cases": []}
    for case in CASES:
        output, instructions = run_case(case)
        directory = FIXTURES / case["id"]
        directory.mkdir(exist_ok=True)
        width = case["width"]
        height = case["height"]
        count = width * height
        flags = bytes(0 if index in case["breaks"] else 1 for index in range(count))
        src_values = [float((index * 17 + channel * 3) % 251) / 7.0 for index in range(count) for channel in range(3)]
        if "witness" in case:
            src_values = list(case["carry_rgb"]) * count
            witness_x, witness_y = case["witness"]
            witness_index = witness_y * width + witness_x
            src_values[witness_index * 3:witness_index * 3 + 3] = case["center_rgb"]
        src = struct.pack(f"<{count * 3}f", *src_values)
        weights = struct.pack(f"<{case['radius'] * 2 + 1}f", *[0.375 + (index * 0.625) for index in range(case["radius"] * 2 + 1)])
        for name, data in (("flags.bin", flags), ("src.bin", src), ("weights.bin", weights), ("expected.bin", output)):
            (directory / name).write_bytes(data)
        manifest_case = {key: case[key] for key in ("id", "direction", "width", "height", "columns", "rows", "offset", "radius", "breaks")}
        for key in ("witness", "carry_rgb", "center_rgb"):
            if key in case:
                manifest_case[key] = case[key]
        manifest_case["instructions"] = instructions
        manifest_case["expected_sha256"] = hashlib.sha256(output).hexdigest()
        manifest["cases"].append(manifest_case)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    if not args.export:
        parser.error("use --export to execute the actual AEX helpers and materialize fixtures")
    export()
