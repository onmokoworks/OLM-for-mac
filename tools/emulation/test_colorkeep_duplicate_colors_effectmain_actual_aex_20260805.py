#!/usr/bin/env python3
"""Duplicate enabled-color semantics across unrolled/tail boundaries."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import DEPTHS as INTEGER_SPECS, quantize

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_duplicate_colors_effectmain_actual_aex_20260805.json"
A = (1.0, 0.125, 0.375, 0.625)
B = (0.75, 0.25, 0.5, 0.75)
COLORS = (A, B, (0.5, 0.5, 0.75, 1.0), (0.25, 0.75, 1.0, 0.0), A, B)


def main() -> int:
    oracle.COLORS = COLORS
    pixels = {}
    for depth in ("PF8", "PF16", "PF32"):
        if depth == "PF32":
            pixels[depth] = (A, B, COLORS[2], COLORS[3], (0.6, 0.9, 0.8, 0.7))
        else:
            units = [quantize(color, INTEGER_SPECS[depth]) for color in COLORS]
            assert units[0] == units[4] and units[1] == units[5]
            miss = list(units[0]); miss[1] = (miss[1] + 1) & int(INTEGER_SPECS[depth]["mask"])
            pixels[depth] = (units[0], units[1], units[2], units[3], tuple(miss))
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
    report = {
        "status": "exact",
        "boundary": "six enabled colors with duplicates crossing the four-color group and scalar tail",
        "duplicate_pairs": [[0, 4], [1, 5]],
        "actual_aex_sha256": oracle.AEX_SHA256,
        "dynamic_effectmain_paths": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "smart_parameter_dependencies": {"checkout_count": 101, "ordered_indices": list(range(1, 102)), "note": "actual Smart preparation depends on the full Color[0..99] surface even when six are enabled"},
        "fixture": "4x3, 8-byte input/output padding, duplicate matches plus distinct matches and no-match",
        "semantics": "duplicate entries do not alter typed output; matching retains source alpha and no-match zeros alpha while preserving RGB bytes",
        "depth_oracle_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in expected.items()},
        "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "not_proven": ["After Effects host execution/export", "NaN/Inf full-frame behavior", "other duplicate layouts or frame sizes"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
