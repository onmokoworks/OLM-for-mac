#!/usr/bin/env python3
"""ColorKeep PF32 five-color SIMD/tail fixtures from the actual 2025 AEX."""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "aex/OLMColorKeep/Plugins/64/2025/ColorKeep.aex"
AEX_SHA256 = "6d3718868c6c876c3bb370b19cb2bb3c4f89a3a479c29f03ae0d032a5d043b86"
ENTRY = 0x180001850
REPORT = ROOT / "refs/conformance/colorkeep_pf32_multicolor_actual_aex_20260805.json"

COLORS = (
    (1.0, 0.10, 0.20, 0.30),
    (0.9, 0.15, 0.25, 0.35),
    (0.8, 0.40, 0.50, 0.60),
    (0.7, 0.65, 0.75, 0.85),
    (0.6, 0.123456, 0.234567, 0.345678),
)


def f32_tuple(values: tuple[float, ...]) -> tuple[float, ...]:
    return struct.unpack(f"<{len(values)}f", struct.pack(f"<{len(values)}f", *values))


def words(values: tuple[float, ...]) -> list[str]:
    raw = struct.pack(f"<{len(values)}f", *values)
    return [f"0x{word:08x}" for word in struct.unpack(f"<{len(values)}I", raw)]


def invoke(source: tuple[float, float, float, float]) -> dict[str, object]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x28 + len(COLORS) * 16)
    src = loader.host_alloc(16)
    dst = loader.host_alloc(16)
    loader.write_bytes(refcon + 0x24, struct.pack("<i", len(COLORS)))
    for index, color in enumerate(COLORS):
        loader.write_bytes(refcon + 0x28 + index * 16, struct.pack("<4f", *color))
    loader.write_bytes(src, struct.pack("<4f", *source))
    loader.write_bytes(dst, b"\xa5" * 16)
    result = loader.call_function(ENTRY, int_args=[refcon, 0, 0, src, dst], max_instructions=10_000)
    raw = loader.read_bytes(dst, 16)
    return {
        "source_argb_bits": words(source),
        "observed_argb_bits": [f"0x{word:08x}" for word in struct.unpack("<4I", raw)],
        "instructions": result["instructions"],
    }


def main() -> int:
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    assert digest == AEX_SHA256
    colors = tuple(f32_tuple(color) for color in COLORS)
    outside = f32_tuple((0.55, 0.91, 0.81, 0.71))
    cases = {
        "first_unrolled_match": invoke(colors[0]),
        "fourth_unrolled_match": invoke(colors[3]),
        "fifth_tail_match": invoke(colors[4]),
        "no_match": invoke(outside),
    }
    assert cases["first_unrolled_match"]["observed_argb_bits"] == words(colors[0])
    assert cases["fourth_unrolled_match"]["observed_argb_bits"] == words(colors[3])
    assert cases["fifth_tail_match"]["observed_argb_bits"] == words(colors[4])
    assert cases["no_match"]["observed_argb_bits"] == ["0x00000000", *words(outside)[1:]]
    report = {
        "status": "exact",
        "aex_sha256": digest,
        "scope": {
            "artifact": "Windows ColorKeep 2025 AEX",
            "entry": f"0x{ENTRY:x}",
            "depth": "PF32",
            "shape": "four direct one-pixel worker calls, five enabled colors",
            "paths": ["four-color unrolled group", "one-color scalar tail"],
            "host": "none; actual PE code under local Unicorn",
        },
        "enabled_color_argb_bits": [words(color) for color in colors],
        "cases": cases,
        "not_proven": [
            "After Effects host dispatch or export equivalence",
            "PF8/PF16 equivalence",
            "full-frame iteration or more than five enabled colors",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
