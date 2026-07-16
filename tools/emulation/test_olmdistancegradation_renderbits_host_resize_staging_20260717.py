#!/usr/bin/env python3
"""Bounded Mac RenderBits host-world/resize staging audit.

This intentionally compares only row/layout/depth contracts. It does not model
the AE host, the Windows AEX, or the unresolved non-identity resize kernel.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
from dataclasses import dataclass


ROOT = pathlib.Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools/emulation/dg_renderbits_real_harness_20260716.sh"


@dataclass(frozen=True)
class World:
    width: int
    height: int
    rowbytes: int
    pixel_size: int
    data: bytes


def make_world(width: int, height: int, pixel_size: int, padding: int, seed: int) -> World:
    rowbytes = width * pixel_size + padding
    rows = []
    for y in range(height):
        active = bytes((seed + y * 17 + x) & 0xFF for x in range(width * pixel_size))
        rows.append(active + bytes([0xA5]) * padding)
    return World(width, height, rowbytes, pixel_size, b"".join(rows))


def active_rows(world: World) -> list[bytes]:
    active = world.width * world.pixel_size
    return [world.data[y * world.rowbytes : y * world.rowbytes + active]
            for y in range(world.height)]


def stage_same_shape(source: World, destination: World) -> World:
    """Model the observed active-row copy into a tight internal world."""
    if (source.width, source.height, source.pixel_size) != (
        destination.width, destination.height, destination.pixel_size
    ):
        raise ValueError("non-identity resize/depth conversion is outside this audit")
    tight_rowbytes = source.width * source.pixel_size
    tight = b"".join(active_rows(source))
    return World(destination.width, destination.height, tight_rowbytes,
                 destination.pixel_size, tight)


def write_back(internal: World, destination: World) -> bytes:
    if (internal.width, internal.height, internal.pixel_size) != (
        destination.width, destination.height, destination.pixel_size
    ):
        raise ValueError("write-back requires same-shape, same-depth staging")
    active = destination.width * destination.pixel_size
    rows = []
    for y in range(destination.height):
        row = bytearray(destination.data[y * destination.rowbytes : (y + 1) * destination.rowbytes])
        row[:active] = internal.data[y * internal.rowbytes : (y + 1) * internal.rowbytes]
        rows.append(bytes(row))
    return b"".join(rows)


def depth_scale(pixel_size: int) -> int:
    return {4: 255, 8: 32768, 16: 1}[pixel_size]


def run() -> None:
    cases = []
    for pixel_size in (4, 8, 16):
        source = make_world(5, 3, pixel_size, pixel_size, seed=pixel_size)
        destination = make_world(5, 3, pixel_size, pixel_size * 2, seed=0xE0)
        internal = stage_same_shape(source, destination)
        written = write_back(internal, destination)
        active = destination.width * pixel_size
        assert internal.rowbytes == active
        assert active_rows(World(destination.width, destination.height, destination.rowbytes,
                                 destination.pixel_size, written)) == active_rows(source)
        for y in range(destination.height):
            padding = written[y * destination.rowbytes + active : (y + 1) * destination.rowbytes]
            assert padding == bytes([0xA5]) * (destination.rowbytes - active)
        assert depth_scale(pixel_size) in (255, 32768, 1)
        cases.append({
            "pixel_size": pixel_size,
            "source_rowbytes": source.rowbytes,
            "internal_rowbytes": internal.rowbytes,
            "destination_rowbytes": destination.rowbytes,
            "active_bytes_per_row": active,
            "depth_scale": depth_scale(pixel_size),
            "result": "PASS",
        })

    mismatch = make_world(5, 3, 4, 0, seed=1)
    resized = make_world(4, 3, 4, 0, seed=2)
    try:
        stage_same_shape(mismatch, resized)
    except ValueError:
        cases.append({"non_identity_resize": "rejected", "result": "PASS"})
    else:
        raise AssertionError("non-identity resize must remain unresolved, not silently modeled")

    completed = subprocess.run([str(HARNESS)], cwd=ROOT, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               check=False)
    if completed.returncode != 0:
        raise AssertionError(f"production RenderBits harness failed:\n{completed.stdout}{completed.stderr}")
    harness_lines = [line for line in completed.stdout.splitlines() if line.startswith("PASS ")]
    assert len(harness_lines) == 6, harness_lines
    print("PASS staging-contract cases=4")
    print("PASS production-renderbits harness cases=6")
    print("PASS scope=Mac-local-layout-only no-AEX-exact-claim")


if __name__ == "__main__":
    try:
        run()
    except (AssertionError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
