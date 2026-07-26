#!/usr/bin/env python3
"""Smoke the PF32 ARGB-entry to semantic FLOAT EXR comparator."""

from __future__ import annotations

import gzip
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_pf32_entry_to_exr import compare_pf32_entry


def make_exr(path: Path, pixels: list[tuple[float, float, float, float]]) -> None:
    width = len(pixels)
    channels = bytearray()
    for name in ("A", "B", "G", "R"):
        channels += name.encode() + b"\0"
        channels += struct.pack("<iB3xii", 2, 0, 1, 1)
    channels += b"\0"

    def attr(name: str, kind: str, value: bytes) -> bytes:
        return (
            name.encode()
            + b"\0"
            + kind.encode()
            + b"\0"
            + struct.pack("<I", len(value))
            + value
        )

    header = (
        struct.pack("<II", 20000630, 2)
        + attr("channels", "chlist", bytes(channels))
        + attr("compression", "compression", b"\0")
        + attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, width - 1, 0))
        + b"\0"
    )
    offset = len(header) + 8
    payload = bytearray()
    for index in (0, 3, 2, 1):
        payload += b"".join(struct.pack("<f", pixel[index]) for pixel in pixels)
    path.write_bytes(
        header
        + struct.pack("<Q", offset)
        + struct.pack("<iI", 0, len(payload))
        + payload
    )


def main() -> int:
    pixels = [(1.0, 0.25, 0.5, 0.75), (0.5, 0.125, 0.25, 1.0)]
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        exr = root / "fixture.exr"
        raw = root / "entry.bin.gz"
        make_exr(exr, pixels)
        interleaved = b"".join(
            struct.pack("<4f", pixel[0], pixel[1], pixel[2], pixel[3])
            for pixel in pixels
        )
        with gzip.open(raw, "wb") as stream:
            stream.write(interleaved)
        exact = compare_pf32_entry(raw, exr)
        assert exact["mismatched_words"] == 0
        assert exact["max_raw_u32_delta"] == 0
        assert exact["channel_order"] == ["A", "R", "G", "B"]

        changed = bytearray(interleaved)
        changed[4:8] = struct.pack("<f", 0.375)
        with gzip.open(raw, "wb") as stream:
            stream.write(changed)
        mismatch = compare_pf32_entry(raw, exr)
        assert mismatch["mismatched_words"] == 1
        assert mismatch["first_mismatches"][0]["channel"] == "R"
    print("[OK] PF32 entry comparator smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
