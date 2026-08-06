#!/usr/bin/env python3
"""ColorKeep public maximum (100) plus nearest upper tail (99) proof."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import DEPTHS as INTEGER_SPECS, quantize

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_max100_effectmain_actual_aex_20260805.json"
COLORS100 = tuple((1.0, i / 255.0, ((i * 37) % 256) / 255.0, ((i * 73) % 256) / 255.0) for i in range(100))
REQUIRED = (0, 3, 4, 15, 16, 31, 32, 63, 64, 95, 96, 99)


def depth_pixels(colors, selected):
    result = {}
    for depth in ("PF8", "PF16", "PF32"):
        if depth == "PF32":
            result[depth] = tuple(colors[i] for i in selected) + ((1.0, 0.9, 0.91, 0.92),)
        else:
            units = [quantize(color, INTEGER_SPECS[depth]) for color in colors]
            miss = (units[0][0], 200 if depth == "PF8" else 30000, 17, 29)
            assert miss not in units
            result[depth] = tuple(units[i] for i in selected) + (miss,)
    return result


def run_fixture(colors, selected):
    oracle.COLORS = tuple(colors)
    pixels = depth_pixels(colors, selected)
    oracle.DEPTHS = {
        "PF8": (0x180001580, "<4B", pixels["PF8"]),
        "PF16": (0x180001280, "<4H", pixels["PF16"]),
        "PF32": (0x180001850, "<4f", pixels["PF32"]),
    }
    inputs, expected = {}, {}
    for depth, (entry, fmt, values) in oracle.DEPTHS.items():
        rows = [b"".join(struct.pack(fmt, *values[(y * 4 + x) % len(values)]) for x in range(4)) + b"\xcc" * 8 for y in range(3)]
        inputs[depth] = b"".join(rows)
        expected[depth] = oracle.actual_frame(entry, fmt, values)
    observed = adapter.compile_and_run(inputs)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    return observed, expected


def main() -> int:
    # Thirteen requested outcomes need two 4x3 frames at count=100.
    first, first_expected = run_fixture(COLORS100, REQUIRED[:7])
    second, second_expected = run_fixture(COLORS100, REQUIRED[7:])
    # 100 is exactly 25 groups of four and has no scalar tail. Count=99 is
    # the nearest upper-bound state with a three-color scalar tail (96..98).
    tail, tail_expected = run_fixture(COLORS100[:99], (96, 98))
    combined = first + second + tail
    report = {
        "status": "exact",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "public_maximum": 100,
        "maximum_dispatch": "25 complete four-color unrolled groups; mathematically no scalar tail at count 100",
        "nearest_upper_tail": "count 99: 24 complete groups plus scalar tail indices 96..98",
        "required_match_indices_at_100": list(REQUIRED),
        "no_match_at_100": True,
        "fixtures": ["count100 frame A: 4x3 padded", "count100 frame B: 4x3 padded", "count99 tail frame: 4x3 padded"],
        "dynamic_effectmain_paths_per_fixture": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "smart_dependencies": {"count100": {"checkout_count": 101, "ordered_indices": list(range(1, 102))}, "count99": {"checkout_count": 101, "ordered_indices": list(range(1, 102))}},
        "padding": "8 input bytes and 8 output bytes per row, preserved",
        "combined_output_sha256": hashlib.sha256(combined).hexdigest(),
        "count100_frame_depth_sha256": [{depth: hashlib.sha256(value).hexdigest() for depth, value in frame.items()} for frame in (first_expected, second_expected)],
        "count99_tail_depth_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in tail_expected.items()},
        "not_proven": ["After Effects host execution/export", "parameter values above the declared maximum", "other frames or color sets"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
