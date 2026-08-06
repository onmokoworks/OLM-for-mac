#!/usr/bin/env python3
"""PF8/PF16 five-color unrolled/tail fixtures from the actual ColorKeep AEX."""

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
REPORT = ROOT / "refs/conformance/colorkeep_pf8_pf16_multicolor_actual_aex_20260805.json"
COLORS = (
    (1.00, 0.00, 0.25, 0.50),
    (0.75, 0.25, 0.50, 0.75),
    (0.50, 0.50, 0.75, 1.00),
    (0.25, 0.75, 1.00, 0.00),
    (1.00, 1.00, 0.00, 0.25),
)
DEPTHS = {
    "PF8": {"entry": 0x180001580, "format": "<4B", "bias": 0.00196078442968428125, "scale": 255.0, "mask": 0xFF},
    "PF16": {"entry": 0x180001280, "format": "<4H", "bias": 0.0000152587890625, "scale": 32768.0, "mask": 0xFFFF},
}


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def quantize(color: tuple[float, float, float, float], spec: dict[str, object]) -> tuple[int, int, int, int]:
    bias, scale, mask = f32(float(spec["bias"])), f32(float(spec["scale"])), int(spec["mask"])
    return tuple(int(f32(f32(f32(value) + bias) * scale)) & mask for value in color)  # type: ignore[return-value]


def invoke(depth: str, source: tuple[int, int, int, int]) -> dict[str, object]:
    spec = DEPTHS[depth]
    fmt = str(spec["format"])
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    refcon = loader.host_alloc(0x28 + len(COLORS) * 16)
    src = loader.host_alloc(struct.calcsize(fmt))
    dst = loader.host_alloc(struct.calcsize(fmt))
    loader.write_bytes(refcon + 0x24, struct.pack("<i", len(COLORS)))
    for index, color in enumerate(COLORS):
        loader.write_bytes(refcon + 0x28 + index * 16, struct.pack("<4f", *color))
    loader.write_bytes(src, struct.pack(fmt, *source))
    loader.write_bytes(dst, b"\xa5" * struct.calcsize(fmt))
    result = loader.call_function(int(spec["entry"]), int_args=[refcon, 0, 0, src, dst], max_instructions=10_000)
    return {
        "source_argb_units": list(source),
        "observed_argb_units": list(struct.unpack(fmt, loader.read_bytes(dst, struct.calcsize(fmt)))),
        "instructions": result["instructions"],
    }


def main() -> int:
    digest = hashlib.sha256(AEX.read_bytes()).hexdigest()
    assert digest == AEX_SHA256
    cases: dict[str, object] = {}
    for depth, spec in DEPTHS.items():
        units = [quantize(color, spec) for color in COLORS]
        no_match = list(units[4])
        no_match[1] = (no_match[1] - 1) & int(spec["mask"])
        depth_cases = {
            "first_unrolled_match": invoke(depth, units[0]),
            "fourth_unrolled_match": invoke(depth, units[3]),
            "fifth_tail_match": invoke(depth, units[4]),
            "no_match": invoke(depth, tuple(no_match)),
        }
        for key, index in (("first_unrolled_match", 0), ("fourth_unrolled_match", 3), ("fifth_tail_match", 4)):
            assert depth_cases[key]["observed_argb_units"] == list(units[index])
        assert depth_cases["no_match"]["observed_argb_units"] == [0, *no_match[1:]]
        cases[depth] = {"enabled_color_argb_units": [list(row) for row in units], "cases": depth_cases}
    report = {
        "status": "exact",
        "aex_sha256": digest,
        "scope": {
            "artifact": "Windows ColorKeep 2025 AEX",
            "entries": {depth: f"0x{spec['entry']:x}" for depth, spec in DEPTHS.items()},
            "depths": ["PF8", "PF16"],
            "shape": "four direct one-pixel calls per depth, five enabled colors",
            "paths": ["four-color unrolled group", "one-color scalar tail"],
            "host": "none; actual PE code under local Unicorn",
        },
        "colors_argb_f32_bits": [[f"0x{v:08x}" for v in struct.unpack("<4I", struct.pack("<4f", *c))] for c in COLORS],
        "depth_results": cases,
        "not_proven": ["After Effects host/export equivalence", "full-frame iteration", "more than five enabled colors"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
