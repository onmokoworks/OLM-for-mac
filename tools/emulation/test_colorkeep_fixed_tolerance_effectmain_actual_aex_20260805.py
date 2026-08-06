#!/usr/bin/env python3
"""Fixed PF32 tolerance and exact PF8/PF16 equality boundaries through EffectMain."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_fixed_tolerance_effectmain_actual_aex_20260805.json"
COLOR = (0.75, 0.0, 0.5, 0.25)
TOLERANCE_BITS = 0x38D1B717


def f32_from_bits(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def main() -> int:
    below, tie, above = (f32_from_bits(TOLERANCE_BITS + delta) for delta in (-1, 0, 1))
    oracle.COLORS = (COLOR,)
    pixels = {
        "PF8": ((191, 0, 128, 64), (191, 1, 128, 64), (191, 255, 128, 64), (190, 0, 128, 64)),
        "PF16": ((24576, 0, 16384, 8192), (24576, 1, 16384, 8192), (24576, 65535, 16384, 8192), (24575, 0, 16384, 8192)),
        "PF32": ((0.75, below, 0.5, 0.25), (0.75, tie, 0.5, 0.25), (0.75, above, 0.5, 0.25), (0.7500001, 0.0, 0.5, 0.25)),
    }
    oracle.DEPTHS = {
        "PF8": (0x180001580, "<4B", pixels["PF8"]),
        "PF16": (0x180001280, "<4H", pixels["PF16"]),
        "PF32": (0x180001850, "<4f", pixels["PF32"]),
    }
    inputs, expected = {}, {}
    for depth, (entry, fmt, values) in oracle.DEPTHS.items():
        rows = [b"".join(struct.pack(fmt, *values[(y * 4 + x) % 4]) for x in range(4)) + b"\xcc" * 8 for y in range(3)]
        inputs[depth] = b"".join(rows)
        expected[depth] = oracle.actual_frame(entry, fmt, values)
    # PF8/PF16: exact first pixel only. PF32: below, tie, and independent
    # alpha-below all match; one ULP above the fixed tolerance rejects.
    for depth, fmt in (("PF8", "<4B"), ("PF16", "<4H")):
        ps, rb = struct.calcsize(fmt), 4 * struct.calcsize(fmt) + 8
        alphas = [struct.unpack(fmt, expected[depth][x * ps:(x + 1) * ps])[0] for x in range(4)]
        assert alphas == [pixels[depth][0][0], 0, 0, 0]
        assert expected[depth][4 * ps:rb] == b"\xee" * 8
    pf32_alphas = [struct.unpack_from("<f", expected["PF32"], x * 16)[0] for x in range(4)]
    assert pf32_alphas == [0.75, 0.75, 0.0, struct.unpack("<f", struct.pack("<f", 0.7500001))[0]]
    observed = adapter.compile_and_run(inputs)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    report = {
        "status": "exact",
        "parameter_surface_fact": "ColorKeep has no tolerance or softness parameter; Enabled Color Num and Color[100] are the complete setup surface",
        "boundary_under_test": {"PF32_fixed_tolerance_bits": f"0x{TOLERANCE_BITS:08x}", "cases": ["one ULP below", "tie", "one ULP above"], "PF8_PF16": "exact typed equality and +/- one unit"},
        "actual_aex_sha256": oracle.AEX_SHA256,
        "dynamic_effectmain_paths": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "smart_parameter_dependencies": {"checkout_count": 101, "ordered_indices": list(range(1, 102))},
        "fixture": "4x3, one enabled color, 8-byte input/output row padding",
        "depth_oracle_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in expected.items()},
        "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "not_proven": ["After Effects host execution/export", "configurable softness/tolerance because no such parameter exists", "other frames or colors"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
