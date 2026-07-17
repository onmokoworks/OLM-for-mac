#!/usr/bin/env python3
"""Mac-local actual-AEX callback boundary witness; no render or PNG path."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_callback_boundary_20260717.json"
POPULATE = 0x180006980
WRITER = 0x180006B30
PARAM_SIZE = 0x8200


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def words(loader: AexLoader, address: int, count: int) -> list[str]:
    return [f"0x{value:08x}" for value in struct.unpack(
        "<" + "I" * count, loader.read_bytes(address, count * 4)
    )]


def main() -> int:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    params = loader.host_alloc(PARAM_SIZE)
    source_plane = loader.host_alloc(16 * 16, align=16)
    writer_plane = loader.host_alloc(16 * 16, align=16)
    pixel = loader.host_alloc(4, align=4)
    output = loader.host_alloc(4, align=4)
    loader.write_bytes(params, b"\x00" * PARAM_SIZE)
    loader.write_bytes(source_plane, b"\x00" * (16 * 16))
    loader.write_bytes(writer_plane, b"\x00" * (16 * 16))
    loader.write_bytes(output, b"\xCC" * 4)

    # The callback addresses a cell using +0x8098/+0x809c/+0x80a0.
    loader.write_bytes(params + 0x8078, struct.pack("<Q", source_plane))
    loader.write_bytes(params + 0x8090, struct.pack("<Q", writer_plane))
    loader.write_bytes(params + 0x8098, struct.pack("<I", 2))
    loader.write_bytes(params + 0x809C, struct.pack("<I", 3))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", 4))
    loader.write_bytes(params + 0x28, struct.pack("<f", 1.0))

    populate_cases = [
        [0, 0, 0, 0], [255, 0, 0, 0], [0, 255, 0, 0],
        [127, 128, 1, 254], [255, 255, 255, 255],
    ]
    populate = []
    for argb in populate_cases:
        loader.write_bytes(source_plane, b"\x00" * (16 * 16))
        loader.write_bytes(pixel, bytes(argb))
        loader.call_function(POPULATE, int_args=[params, 1, 2, pixel], max_instructions=10000)
        cell = source_plane + ((2 + 2) * 4 + 3 + 1) * 16
        expected = list(struct.unpack(
            "<4f", struct.pack("<4f", *(value / 255.0 for value in (argb[1], argb[2], argb[3], argb[0])))
        ))
        actual = list(struct.unpack("<4f", loader.read_bytes(cell, 16)))
        actual_bits = words(loader, cell, 4)
        if actual != expected:
            raise AssertionError(f"populate mismatch for {argb}: {actual} != {expected}")
        populate.append({"argb8": argb, "rgba_f32": actual, "rgba_f32_bits": actual_bits})

    writer_cases = [
        [0.0, 0.0, 0.0, 0.0],
        [0.25, 0.5, 0.75, 1.0],
        [1.25, -0.25, 0.5, 1.25],
    ]
    writer = []
    cell = writer_plane + ((2 + 2) * 4 + 3 + 1) * 16
    for rgba in writer_cases:
        loader.write_bytes(cell, struct.pack("<4f", *rgba))
        loader.write_bytes(output, b"\xCC" * 4)
        loader.call_function(WRITER, int_args=[params, 1, 2, 0, output], max_instructions=10000)
        packed = list(loader.read_bytes(output, 4))
        # RGB clamps at 1.0 before truncation; alpha is an un-clamped byte cast.
        expected = [int(rgba[3] * 255.0) & 0xFF,
                    int(min(1.0, rgba[0]) * 255.0) & 0xFF,
                    int(min(1.0, rgba[1]) * 255.0) & 0xFF,
                    int(min(1.0, rgba[2]) * 255.0) & 0xFF]
        if packed != expected:
            raise AssertionError(f"writer mismatch for {rgba}: {packed} != {expected}")
        writer.append({"rgba_f32": rgba, "argb8": packed, "argb8_word_le": f"0x{int.from_bytes(bytes(packed), 'little'):08x}"})

    report = {
        "schema": 1,
        "kind": "olmdirectionalblur_callback_boundary_actual_aex",
        "status": "pass",
        "scope": "Mac-local Unicorn direct actual-AEX callback boundary; in-memory ARGB matrix",
        "claim_scope": "Populate channel normalization and writer packing only; no render, Windows, or AE-exact claim",
        "provenance": {"aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX)},
        "callbacks": {
            "populate": {"entry": hex(POPULATE), "abi": "(params, x=RDX, y=R8, source_pixel=R9)", "cases": populate},
            "writer": {"entry": hex(WRITER), "abi": "(params, x=RDX, y=R8, ignored=R9, output=stack)", "cases": writer},
        },
        "plane_contract": {"source_base": hex(source_plane), "writer_base": hex(writer_plane), "row0": 2, "col0": 3, "stride": 4, "cell_xy": [1, 2]},
        "fail_closed": {"png_read": False, "host_render": False, "production_source_edited": False, "ledger_edited": False, "windows_values_fabricated": False, "ae_exact_claim": False},
        "command": "python3 tools/emulation/test_olmdirectionalblur_callback_boundary_20260717.py",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "pass", "report": str(REPORT.relative_to(ROOT)), "populate_cases": len(populate), "writer_cases": len(writer)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
