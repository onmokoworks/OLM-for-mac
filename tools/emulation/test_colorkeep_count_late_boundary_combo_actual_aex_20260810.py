#!/usr/bin/env python3
"""ColorKeep enabled-count/late-key/comparison-boundary combination proof."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

import test_colorkeep_effectmain_padded_frame_20260805 as adapter
import test_colorkeep_typed_padded_frame_actual_aex_20260805 as oracle
from test_colorkeep_pf8_pf16_multicolor_actual_aex_20260805 import (
    DEPTHS as INTEGER_SPECS,
    quantize,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/colorkeep_count_late_boundary_combo_actual_aex_20260810.json"
TOLERANCE_BITS = 0x38D1B717


def f32_bits(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def make_palette() -> tuple[tuple[float, float, float, float], ...]:
    colors = [
        (0.5, ((i * 29 + 11) % 251) / 255.0,
         ((i * 47 + 17) % 251) / 255.0,
         ((i * 71 + 23) % 251) / 255.0)
        for i in range(100)
    ]
    # ARGB tuples.  Both late keys use a zero green component so the exact
    # binary32 tolerance constant can be exercised without addition rounding.
    colors[4] = (0.25, 0.75, 0.0, 0.5)
    colors[5] = (0.75, 0.125, 0.875, 0.375)
    colors[98] = (0.625, 0.875, 0.25, 0.125)
    colors[99] = (0.25, 0.625, 0.0, 0.375)
    assert len(set(colors)) == 100
    return tuple(colors)


PALETTE = make_palette()


def integer_pixels(depth: str, count: int):
    units = tuple(quantize(color, INTEGER_SPECS[depth]) for color in PALETTE)
    late = list(units[count - 1])
    alpha_plus = list(late); alpha_plus[0] += 1
    red_plus = list(late); red_plus[1] += 1
    miss = list(late); miss[2] = 127 if depth == "PF8" else 12345
    assert tuple(miss) not in units[:count]
    cases = [
        ("last_enabled_exact", tuple(late), True),
        ("last_enabled_alpha_plus_one", tuple(alpha_plus), False),
        ("last_enabled_red_plus_one", tuple(red_plus), False),
        ("independent_no_match", tuple(miss), False),
    ]
    if count == 5:
        cases.insert(1, ("first_disabled_exact", units[5], False))
    else:
        cases.insert(1, ("penultimate_enabled_exact", units[98], True))
    return cases


def float_pixels(count: int):
    key = PALETTE[count - 1]
    tolerance = f32_bits(TOLERANCE_BITS)
    alpha_inside = f32_bits(0x3E800D1B)  # abs(x - 0.25) < fixed tolerance
    alpha_outside = f32_bits(0x3E800D1C) # next f32; abs(x - 0.25) > tolerance
    green_above = f32_bits(TOLERANCE_BITS + 1)
    cases = [
        ("last_enabled_exact", key, True),
        ("last_enabled_alpha_inside", (alpha_inside, key[1], key[2], key[3]), True),
        ("last_enabled_alpha_outside", (alpha_outside, key[1], key[2], key[3]), False),
        ("last_enabled_green_tie", (key[0], key[1], tolerance, key[3]), True),
        ("last_enabled_green_above", (key[0], key[1], green_above, key[3]), False),
        ("independent_no_match", (0.9, 0.91, 0.92, 0.93), False),
    ]
    if count == 5:
        cases.insert(1, ("first_disabled_exact", PALETTE[5], False))
    else:
        cases.insert(1, ("penultimate_enabled_exact", PALETTE[98], True))
    return cases


def frame_blob(fmt: str, cases) -> bytes:
    rows = []
    for y in range(oracle.HEIGHT):
        rows.append(b"".join(
            struct.pack(fmt, *cases[(y * oracle.WIDTH + x) % len(cases)][1])
            for x in range(oracle.WIDTH)
        ) + b"\xcc" * oracle.PADDING)
    return b"".join(rows)


def assert_semantics(depth: str, fmt: str, cases, expected: bytes) -> dict:
    pixel_size = struct.calcsize(fmt)
    rowbytes = oracle.WIDTH * pixel_size + oracle.PADDING
    seen = {name: 0 for name, _, _ in cases}
    changed_alpha = 0
    retained_rgb_rejects = 0
    for index in range(oracle.WIDTH * oracle.HEIGHT):
        y, x = divmod(index, oracle.WIDTH)
        name, source, match = cases[index % len(cases)]
        output = struct.unpack_from(fmt, expected, y * rowbytes + x * pixel_size)
        seen[name] += 1
        rgb_fmt = "<3" + fmt[-1]
        assert struct.pack(rgb_fmt, *output[1:]) == struct.pack(rgb_fmt, *source[1:])
        if match:
            assert struct.pack(fmt[-1], output[0]) == struct.pack(fmt[-1], source[0])
        else:
            assert output[0] == 0
            changed_alpha += int(source[0] != 0)
            retained_rgb_rejects += 1
    assert all(value > 0 for value in seen.values())
    assert changed_alpha > 0 and retained_rgb_rejects > 0
    assert all(expected[y * rowbytes + oracle.WIDTH * pixel_size:(y + 1) * rowbytes] == b"\xee" * oracle.PADDING for y in range(oracle.HEIGHT))
    return {"cases_seen": seen, "nonzero_rejected_alpha_clears": changed_alpha,
            "reject_rgb_retention_assertions": retained_rgb_rejects}


def run_count(count: int):
    oracle.COLORS = PALETTE[:count]
    cases = {
        "PF8": integer_pixels("PF8", count),
        "PF16": integer_pixels("PF16", count),
        "PF32": float_pixels(count),
    }
    specs = {
        "PF8": (0x180001580, "<4B"),
        "PF16": (0x180001280, "<4H"),
        "PF32": (0x180001850, "<4f"),
    }
    inputs, expected, assertions = {}, {}, {}
    for depth, (entry, fmt) in specs.items():
        inputs[depth] = frame_blob(fmt, cases[depth])
        values = tuple(case[1] for case in cases[depth])
        expected[depth] = oracle.actual_frame(entry, fmt, values)
        assertions[depth] = assert_semantics(depth, fmt, cases[depth], expected[depth])
    observed = adapter.compile_and_run(inputs, enabled_count=count)
    target = expected["PF8"] + expected["PF16"] + expected["PF8"] + expected["PF16"] + expected["PF32"]
    assert observed == target
    return observed, {
        "enabled_count": count,
        "case_names": {depth: [case[0] for case in depth_cases] for depth, depth_cases in cases.items()},
        "semantic_assertions": assertions,
        "depth_oracle_sha256": {depth: hashlib.sha256(blob).hexdigest() for depth, blob in expected.items()},
        "effectmain_output_sha256": hashlib.sha256(observed).hexdigest(),
    }


def main() -> int:
    outputs, fixtures = [], []
    for count in (5, 100):
        observed, fixture = run_count(count)
        outputs.append(observed); fixtures.append(fixture)
    combined = b"".join(outputs)
    report = {
        "status": "exact",
        "actual_aex_sha256": oracle.AEX_SHA256,
        "production_source": "mac/ColorKeep/ColorKeep.cpp",
        "family": "enabled count 5/100 x late palette index x typed equality/PF32 fixed tolerance x alpha",
        "fixtures": fixtures,
        "dynamic_effectmain_paths_per_fixture": [
            "legacy PF8", "legacy PF16", "SmartPreRender->SmartRender PF8",
            "SmartPreRender->SmartRender PF16", "SmartPreRender->SmartRender PF32",
        ],
        "nonzero_contracts": [
            "the first disabled exact key is rejected at count 5",
            "the last enabled key is retained at counts 5 and 100",
            "integer alpha/RGB +1 mismatches reject",
            "PF32 alpha just inside tolerance retains and the next f32 rejects",
            "PF32 exact tolerance tie retains and one-ULP-above rejects",
            "every rejection preserves all source RGB component bits and clears alpha",
            "all output row padding remains untouched",
        ],
        "combined_output_sha256": hashlib.sha256(combined).hexdigest(),
        "not_proven": ["After Effects host execution/export", "other palettes, frames, or parameter combinations"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
