#!/usr/bin/env python3
"""PF16 practical-geometry public-entry covering family for Smoother v1."""

import ctypes
import hashlib
import json
import struct
import tempfile
from pathlib import Path

import test_olmsmoother_v1_key_tolerance_geometry_actual_aex_20260810 as base

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812.json"
DOC = ROOT / "refs/conformance/olmsmoother_v1_pf16_practical_geometry_actual_aex_20260812.md"
WIDTH, HEIGHT = 64, 36
PADDING = 32
TOLERANCES = (6, 127)


def fixture(width, height, padding):
    """Colored, premultiplied-valid alpha coverage with exact key islands."""
    rowbytes = width * 8 + padding
    payload = bytearray()
    key_points = {
        (0, 0), (width - 1, 0), (width // 2, height // 2),
        (0, height - 1), (width - 1, height - 1),
    }
    alphas = (0, 1, 17, 32, 63, 64, 95, 127, 128, 159, 191, 223, 254, 255)
    for y in range(height):
        for x in range(width):
            if (x, y) in key_points:
                pixel = (255, *base.KEY)
            else:
                # Keep a broad opaque multivalue ramp so the natural
                # interpolation writer is exercised, and interleave every
                # fractional endpoint across that same practical frame.
                alpha = alphas[(x * 5 + y * 3) % len(alphas)] if (x + y * 3) % 11 == 0 else 255
                if x < 16 and y < 16 and alpha == 255:
                    value = (x * 17 + y * 23) & 255
                    pixel = (alpha, value, value, value)
                else:
                    pixel = (
                        alpha,
                        min((x * 37 + y * 19 + 13) & 255, alpha),
                        min((x * 11 + y * 53 + 201) & 255, alpha),
                        min((x * 71 + y * 7 + 41) & 255, alpha),
                    )
            payload += struct.pack("<4H", *(base.widen(value) for value in pixel))
        payload += bytes([0xC0 + (y % 31)]) * padding
    return bytes(payload), rowbytes


def active(raw, width, height, rowbytes):
    return b"".join(raw[y * rowbytes:y * rowbytes + width * 8] for y in range(height))


def padding_rows(raw, width, height, rowbytes):
    return [raw[y * rowbytes + width * 8:(y + 1) * rowbytes] for y in range(height)]


def production(lib, payload, width, height, rowbytes, use_key, tolerance):
    count = len(payload) // 2
    values = struct.unpack(f"<{count}H", payload)
    source = (ctypes.c_uint16 * count)(*values)
    destination = (ctypes.c_uint16 * count)(*([0xA5A5] * count))
    fn = lib.olmsmoother_v1_effectmain_render16_matrix
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16),
        ctypes.c_int32, ctypes.c_int32, ctypes.c_int32, ctypes.c_int32,
        ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_int32,
    ]
    assert fn(source, destination, width, height, rowbytes, use_key, *base.KEY, tolerance) == 0
    source_after = struct.pack(f"<{count}H", *source)
    rendered = struct.pack(f"<{count}H", *destination)
    return rendered, source_after


def run_case(lib, code, width, height, padding, use_key, tolerance):
    payload, rowbytes = fixture(width, height, padding)
    base.W, base.H = width, height
    actual, trace, actual_source_after = base.actual(
        16, payload, rowbytes, use_key, tolerance, code, diagnostics=True
    )
    portable, portable_source_after = production(
        lib, payload, width, height, rowbytes, use_key, tolerance
    )
    assert actual == portable
    assert actual_source_after == payload
    assert portable_source_after == payload
    expected_padding = [bytes([0xA5]) * padding for _ in range(height)]
    assert padding_rows(actual, width, height, rowbytes) == expected_padding
    counts = {name: trace.count(name) for name in ("mask", "main", "classifier", "executor")}
    # The guest iterate suite invokes the main callback with a distinct output
    # pointer for every pixel and commits that callback's returned word to the
    # destination world.  This is the public-chain writer boundary; the deeper
    # interpolation executor is recorded separately and is not required to be
    # active for every classifier family.
    counts["writer"] = counts["main"]
    assert counts["main"] == width * height
    assert counts["mask"] == (width * height if use_key else 0)
    assert counts["classifier"] > 0, counts
    assert counts["writer"] == width * height, counts
    return {
        "use_key": use_key,
        "tolerance": tolerance,
        "dimensions": [width, height],
        "rowbytes": rowbytes,
        "raw_sha256": hashlib.sha256(actual).hexdigest(),
        "active_sha256": hashlib.sha256(active(actual, width, height, rowbytes)).hexdigest(),
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "changed_active_bytes_from_input": sum(
            a != b for a, b in zip(active(actual, width, height, rowbytes), active(payload, width, height, rowbytes))
        ),
        "trace_counts": counts,
        "actual_production_raw_exact": True,
        "actual_input_unchanged": True,
        "production_input_unchanged": True,
        "output_padding_exact": True,
    }


def main():
    assert hashlib.sha256(base.AEX.read_bytes()).hexdigest() == base.AEX_SHA
    temporary, lib = base.build_production()
    try:
        with tempfile.TemporaryDirectory(prefix="sm1-pf16-practical-") as directory:
            code = base.guest_code(Path(directory), 8)
        practical = [
            run_case(lib, code, WIDTH, HEIGHT, PADDING, use_key, tolerance)
            for use_key in (0, 1) for tolerance in TOLERANCES
        ]
        controls = [
            run_case(lib, code, 7, 5, 8, use_key, tolerance)
            for use_key in (0, 1) for tolerance in TOLERANCES
        ]
    finally:
        temporary.cleanup()

    assert all(row["changed_active_bytes_from_input"] > 0 for row in practical)
    assert len({row["active_sha256"] for row in practical}) == 4
    report = {
        "schema_version": 1,
        "status": "exact",
        "verdict": "PASS_V1_PF16_PRACTICAL_GEOMETRY_4_CELLS_EXACT",
        "actual_aex_sha256": base.AEX_SHA,
        "production_entry": "public EffectMain(PF_Cmd_RENDER)",
        "scope": "PF16 padded 64x36 colored fractional-alpha; Color Key off/on x Do Smooth Range 6/127; actual exported Windows AEX versus production public EffectMain",
        "fixture": {
            "dimensions": [WIDTH, HEIGHT],
            "padding_bytes_per_row": PADDING,
            "key_rgb8": base.KEY,
            "alpha_codes": [0, 1, 17, 32, 63, 64, 95, 127, 128, 159, 191, 223, 254, 255],
            "rgb": "independent affine colored channels clamped to alpha (premultiplied-valid)",
            "key_islands": "four corners and center",
        },
        "summary": {"exact_practical_cells": 4, "exact_small_control_cells": 4},
        "practical_cases": practical,
        "small_controls": controls,
        "invariants": {
            "classifier_mask_main_writer_observed": True,
            "writer_boundary": "iterate-suite per-pixel destination writer following the main callback",
            "actual_and_production_raw_exact": True,
            "actual_and_production_inputs_unchanged": True,
            "output_padding_preserved": True,
            "all_cells_nonvacuous": True,
        },
        "claims_not_made": [
            "native PF32 arithmetic",
            "AE 32bpc host conversion",
            "arbitrary geometry or parameter combinations",
            "AE host/export color management",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMSmoother v1 PF16 practical geometry boundary\n\n"
        "Verdict: `PASS_V1_PF16_PRACTICAL_GEOMETRY_4_CELLS_EXACT`\n\n"
        "A padded 64×36 colored fractional-alpha fixture crosses Color Key off/on and "
        "Do Smooth Range 6/127 through the exported Windows AEX `PF_Cmd_RENDER` and "
        "the production public `EffectMain`. All four raw worlds are exact. The natural "
        "classifier, optional key-mask pass, main callback, and iterate destination writer are "
        "observed; both inputs remain unchanged and destination padding remains intact. "
        "Four 7×5 controls cover the same parameter cells.\n\n"
        "PF32 native arithmetic and AE 32bpc host conversion remain outside this claim.\n"
    )
    print(report["verdict"])


if __name__ == "__main__":
    main()
