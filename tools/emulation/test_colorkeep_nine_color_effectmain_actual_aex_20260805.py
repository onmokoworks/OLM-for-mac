#!/usr/bin/env python3
"""Nine-color second-unrolled-group proof through dynamic EffectMain paths."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import DEPTHS as INTEGER_SPECS, quantize

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_nine_color_effectmain_actual_aex_20260805.json"
COLORS = (
    (1.0, 0.0, 0.25, 0.5), (0.75, 0.25, 0.5, 0.75),
    (0.5, 0.5, 0.75, 1.0), (0.25, 0.75, 1.0, 0.0),
    (1.0, 1.0, 0.0, 0.25), (0.875, 0.125, 0.375, 0.625),
    (0.625, 0.375, 0.625, 0.875), (0.375, 0.625, 0.875, 0.125),
    (0.125, 0.875, 0.125, 0.375),
)


def inputs_and_expected():
    oracle.COLORS = COLORS
    selected = (0, 3, 4, 7, 8)
    depth_specs = {}
    for depth, (entry, fmt, _) in oracle.DEPTHS.items():
        if depth == "PF32":
            matches = tuple(COLORS[index] for index in selected)
            pixels = (*matches, (0.55, 0.91, 0.81, 0.71))
        else:
            units = [quantize(color, INTEGER_SPECS[depth]) for color in COLORS]
            matches = tuple(units[index] for index in selected)
            miss = list(units[8]); miss[1] = (miss[1] - 1) & int(INTEGER_SPECS[depth]["mask"])
            pixels = (*matches, tuple(miss))
        depth_specs[depth] = (entry, fmt, pixels)
    oracle.DEPTHS = depth_specs
    inputs, expected = {}, {}
    for depth, (entry, fmt, pixels) in depth_specs.items():
        pixel_size = struct.calcsize(fmt)
        rows = []
        for y in range(oracle.HEIGHT):
            rows.append(b"".join(struct.pack(fmt, *pixels[(y * oracle.WIDTH + x) % len(pixels)]) for x in range(oracle.WIDTH)) + b"\xcc" * oracle.PADDING)
        inputs[depth] = b"".join(rows)
        expected[depth] = oracle.actual_frame(entry, fmt, pixels)
    return inputs, expected


def main() -> int:
    inputs, expected = inputs_and_expected()
    observed = adapter.compile_and_run(inputs)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    report = {
        "status": "exact",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "enabled_colors": 9,
        "paths_covered": ["first unrolled group indices 0/3", "second unrolled group indices 4/7", "scalar tail index 8", "no-match"],
        "dynamic_effectmain_paths": ["legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8", "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32"],
        "parameter_dependencies": {"checkout_count": 10, "indices": list(range(1, 11))},
        "fixture": "4x3 with 8-byte input/output row padding",
        "combined_output_sha256": hashlib.sha256(observed).hexdigest(),
        "depth_oracle_sha256": {depth: hashlib.sha256(value).hexdigest() for depth, value in expected.items()},
        "not_proven": ["After Effects host execution/export", "more than nine colors", "other frames or parameter ranges"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
