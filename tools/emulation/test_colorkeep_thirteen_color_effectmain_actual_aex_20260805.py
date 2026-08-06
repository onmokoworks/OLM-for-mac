#!/usr/bin/env python3
"""Thirteen-color three-unrolled-group proof through dynamic EffectMain."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import DEPTHS as INTEGER_SPECS, quantize

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_thirteen_color_effectmain_actual_aex_20260805.json"
COLORS = (
    (1.0, 0.0, 0.25, 0.5), (0.75, 0.25, 0.5, 0.75),
    (0.5, 0.5, 0.75, 1.0), (0.25, 0.75, 1.0, 0.0),
    (1.0, 1.0, 0.0, 0.25), (0.875, 0.125, 0.375, 0.625),
    (0.625, 0.375, 0.625, 0.875), (0.375, 0.625, 0.875, 0.125),
    (0.125, 0.875, 0.125, 0.375), (0.9375, 0.0625, 0.3125, 0.5625),
    (0.6875, 0.3125, 0.5625, 0.8125), (0.4375, 0.5625, 0.8125, 0.0625),
    (0.1875, 0.8125, 0.0625, 0.3125),
)
SELECTED = (0, 3, 4, 7, 8, 11, 12)


def materialize():
    oracle.COLORS = COLORS
    specs = {}
    for depth, (entry, fmt, _) in oracle.DEPTHS.items():
        if depth == "PF32":
            pixels = (*(COLORS[index] for index in SELECTED), (0.55, 0.91, 0.81, 0.71))
        else:
            units = [quantize(color, INTEGER_SPECS[depth]) for color in COLORS]
            miss = list(units[-1]); miss[1] = (miss[1] - 1) & int(INTEGER_SPECS[depth]["mask"])
            pixels = (*(units[index] for index in SELECTED), tuple(miss))
        specs[depth] = (entry, fmt, pixels)
    oracle.DEPTHS = specs
    inputs, expected = {}, {}
    for depth, (entry, fmt, pixels) in specs.items():
        rows = []
        for y in range(oracle.HEIGHT):
            rows.append(b"".join(struct.pack(fmt, *pixels[(y * oracle.WIDTH + x) % len(pixels)]) for x in range(oracle.WIDTH)) + b"\xcc" * oracle.PADDING)
        inputs[depth] = b"".join(rows)
        expected[depth] = oracle.actual_frame(entry, fmt, pixels)
    return inputs, expected


def main() -> int:
    inputs, expected = materialize()
    observed = adapter.compile_and_run(inputs)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    report = {
        "status": "exact",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "enabled_colors": len(COLORS),
        "paths_covered": [
            *(f"group{group + 1} indices {group * 4}/{group * 4 + 3}" for group in range(len(COLORS) // 4)),
            f"scalar tail index {len(COLORS) - 1}",
            "no-match",
        ],
        "dynamic_effectmain_paths": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "parameter_dependencies": {"checkout_count": 101, "indices": list(range(1, 102))},
        "fixture": f"4x3 with 8-byte input/output row padding; {len(SELECTED) + 1}-path pixel pattern repeated to 12 pixels",
        "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "depth_oracle_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in expected.items()},
        "not_proven": ["After Effects host execution/export", f"more than {len(COLORS)} colors", "other frames or parameter ranges"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
