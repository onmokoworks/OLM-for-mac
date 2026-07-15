#!/usr/bin/env python3
"""Bounded DG residual check using the real AEX callback and portable core.

This is a semantic harness, not an AE render and not a Windows-internals
claim.  It checks the retained 8bpc callback model against the actual AEX
under Unicorn, runs the existing portable field/core regression, and records
which residual shapes are locally explainable without inventing missing
field/source witnesses.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
AEX_PATH = ROOT / "aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex"
CALLBACK = 0x181170870
WORLD_DATA = 0x18
WORLD_ROWBYTES = 0x20
WORLD_WIDTH = 0x24
WORLD_HEIGHT = 0x28
WORLD_SIZE = 0x80
REFCON_SIZE = 0x100

RESIDUALS = {
    "case_0001": {"xy": (17, 0), "mac": [57, 0, 0, 57], "windows": [56, 0, 0, 56]},
    "case_0015": {"xy": (780, 495), "mac": [0, 0, 0, 10], "windows": [10, 0, 0, 10]},
    "case_0029": {"xy": (987, 496), "mac": [7, 0, 60, 64], "windows": [7, 0, 63, 67]},
}


def world8(loader: AexLoader, width: int, height: int, rgba_by_xy: dict[tuple[int, int], tuple[int, int, int, int]]) -> int:
    rowbytes = width * 4
    data = loader.bump_alloc(rowbytes * height, align=64)
    loader.write_bytes(data, b"\0" * (rowbytes * height))
    for (x, y), rgba in rgba_by_xy.items():
        loader.write_bytes(data + y * rowbytes + x * 4, bytes(rgba))
    world = loader.host_alloc(WORLD_SIZE, align=16)
    loader.write_bytes(world, b"\0" * WORLD_SIZE)
    loader.write_bytes(world + WORLD_DATA, int(data).to_bytes(8, "little"))
    loader.write_bytes(world + WORLD_ROWBYTES, rowbytes.to_bytes(4, "little"))
    loader.write_bytes(world + WORLD_WIDTH, width.to_bytes(4, "little"))
    loader.write_bytes(world + WORLD_HEIGHT, height.to_bytes(4, "little"))
    return world


def set_refcon(loader: AexLoader, field_world: int, source_world: int) -> int:
    refcon = loader.host_alloc(REFCON_SIZE, align=16)
    loader.write_bytes(refcon, b"\0" * REFCON_SIZE)
    loader.write_bytes(refcon + 0x00, int(source_world).to_bytes(8, "little"))
    loader.write_bytes(refcon + 0x08, int(field_world).to_bytes(8, "little"))
    loader.write_bytes(refcon + 0x94, (3).to_bytes(4, "little"))  # Both
    loader.write_bytes(refcon + 0x9C, __import__("struct").pack("<f", 0.22))
    loader.write_bytes(refcon + 0xA0, __import__("struct").pack("<f", 0.91))
    loader.write_bytes(refcon + 0xA4, __import__("struct").pack("<f", 0.08))
    loader.write_bytes(refcon + 0xAC, __import__("struct").pack("<f", 0.03))
    loader.write_bytes(refcon + 0xB0, __import__("struct").pack("<f", 0.80))
    loader.write_bytes(refcon + 0xB4, __import__("struct").pack("<f", 0.12))
    loader.write_bytes(refcon + 0xC0, b"\1")  # background enabled
    loader.write_bytes(refcon + 0xC1, b"\0")  # invert off => 1-X
    loader.write_bytes(refcon + 0xC8, (1).to_bytes(4, "little"))  # Gradation
    loader.write_bytes(refcon + 0xCC, (1).to_bytes(4, "little"))  # Linear
    return refcon


def local_aex_model(field_green: int) -> list[int]:
    """FUN_181170870's retained Linear + RGB + background branch."""
    x = 1.0 - field_green / 255.0
    red = 0.80 * (1.0 - x) + 0.91 * x
    green = 0.03 * (1.0 - x) + 0.22 * x
    blue = 0.12 * (1.0 - x) + 0.08 * x
    # Output is memory A,G,R,B (the PNG-facing census values are R,G,B,A); the
    # callback uses truncating casts.
    return [int(max(0.0, min(255.0, value * 255.0))) for value in (1.0, green, red, blue)]


def run_actual_aex_matrix() -> dict[str, object]:
    loader = AexLoader(str(AEX_PATH), verbose=False, fast=True)
    width, height = 8, 1
    fields = { (i, 0): (0, value, 0, 255) for i, value in enumerate((0, 1, 2, 127, 128, 129, 254, 255)) }
    sources = { (i, 0): (255, 12, 34, 56) for i in range(width) }
    field = world8(loader, width, height, fields)
    source = world8(loader, width, height, sources)
    refcon = set_refcon(loader, field, source)
    actual = []
    expected = []
    for x in range(width):
        out = loader.bump_alloc(4, align=16)
        loader.write_bytes(out, b"\xee" * 4)
        loader.call_function(CALLBACK, int_args=[refcon, x, 0, 0, out], max_instructions=200_000)
        actual.append(list(loader.read_bytes(out, 4)))
        expected.append(local_aex_model(fields[(x, 0)][1]))
    return {"field_values": [row[1] for row in fields.values()], "actual": actual, "model": expected, "match": actual == expected}


def run_portable_core() -> dict[str, object]:
    compiler = "clang++"
    output = Path("/tmp/dg_core_distance_stage_20260716")
    command = [compiler, "-std=c++17", "-O2", "-Icore", "core/olmdistancegradation_fieldgen.cpp", "tools/emulation/test_dg_core_distance_stage.cpp", "-o", str(output)]
    build = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if build.returncode:
        return {"status": "build-failed", "stderr": build.stderr[-1200:]}
    run = subprocess.run([str(output)], cwd=ROOT, capture_output=True, text=True)
    return {"status": "pass" if run.returncode == 0 else "fail", "stdout": run.stdout.strip(), "stderr": run.stderr.strip()}


def classify() -> dict[str, dict[str, object]]:
    return {
        "case_0001": {"classification": "semantically_possible_not_proven", "reason": "A one-byte truncation boundary can produce Mac 57 versus Windows 56 for both red and alpha, but the retained census has no field/source/pre-store value at (17,0)."},
        "case_0015": {"classification": "not_reproduced_locally", "reason": "The retained residual changes red only while alpha is equal; without the live field/source/compose values, field ownership, color input, and writeback cannot be separated."},
        "case_0029": {"classification": "not_reproduced_locally", "reason": "The retained residual keeps red/green equal while blue and alpha are both three codes lower on Mac; blur/field or compose inputs could cause it, but no local witness identifies which stage."},
    }


def main() -> int:
    actual = run_actual_aex_matrix()
    core = run_portable_core()
    result = {"actual_aex_emulation": actual, "portable_core": core, "residual_classification": classify()}
    print(json.dumps(result, indent=2))
    return 0 if actual["match"] and core["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
