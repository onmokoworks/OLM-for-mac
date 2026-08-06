#!/usr/bin/env python3
"""Enabled-colors=0 full typed-frame proof through dynamic EffectMain."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_disabled_effectmain_actual_aex_20260805.json"
PIXELS = {
    "PF8": ((255, 12, 34, 56), (128, 78, 90, 123), (0, 222, 111, 7), (64, 1, 2, 3)),
    "PF16": ((32768, 1234, 5678, 9012), (16384, 22222, 11111, 7), (0, 32768, 1, 2), (8192, 3, 4, 5)),
    "PF32": ((1.0, 0.125, 0.25, 0.5), (0.5, 1.25, -0.25, 0.75), (0.0, 0.9, 0.8, 0.7), (0.25, 0.01, 0.02, 0.03)),
}


def main() -> int:
    oracle.COLORS = ()
    oracle.DEPTHS = {
        "PF8": (0x180001580, "<4B", PIXELS["PF8"]),
        "PF16": (0x180001280, "<4H", PIXELS["PF16"]),
        "PF32": (0x180001850, "<4f", PIXELS["PF32"]),
    }
    inputs, expected = {}, {}
    for depth, (entry, fmt, pixels) in oracle.DEPTHS.items():
        rows = []
        for y in range(oracle.HEIGHT):
            rows.append(b"".join(struct.pack(fmt, *pixels[(y * oracle.WIDTH + x) % len(pixels)]) for x in range(oracle.WIDTH)) + b"\xcc" * oracle.PADDING)
        inputs[depth] = b"".join(rows)
        expected[depth] = oracle.actual_frame(entry, fmt, pixels)
        pixel_size, rowbytes = struct.calcsize(fmt), oracle.WIDTH * struct.calcsize(fmt) + oracle.PADDING
        for y in range(oracle.HEIGHT):
            for x in range(oracle.WIDTH):
                raw = expected[depth][y * rowbytes + x * pixel_size:y * rowbytes + (x + 1) * pixel_size]
                units = struct.unpack(fmt, raw)
                assert units[0] == 0
                source = pixels[(y * oracle.WIDTH + x) % len(pixels)]
                rgb_fmt = f"<3{fmt[-1]}"
                assert struct.pack(rgb_fmt, *units[1:]) == struct.pack(rgb_fmt, *source[1:])
            assert expected[depth][y * rowbytes + oracle.WIDTH * pixel_size:(y + 1) * rowbytes] == b"\xee" * oracle.PADDING
    observed = adapter.compile_and_run(inputs)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    report = {
        "status": "exact",
        "branch": "enabled colors = 0",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "dynamic_effectmain_paths": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "typed_result": "all source RGB component bytes preserved; alpha component is zero",
        "smart_parameter_dependencies": {"checkout_count": 101, "ordered_indices": list(range(1, 102))},
        "fixture": "4x3, 8-byte input/output padding, four source patterns repeated",
        "depth_oracle_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in expected.items()},
        "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "not_proven": ["After Effects host execution/export", "other frames or parameter ranges"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
