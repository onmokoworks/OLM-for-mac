#!/usr/bin/env python3
"""Actual-AEX differential for DirectionalBlur FUN_1800018c0."""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader  # noqa: E402

AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
ROTATE = 0x1800018C0
REPORT = ROOT / "refs/conformance/dblur_scalar_rotate_actual_aex_20260805.json"


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def source_plane(case_index: int, width: int, height: int) -> bytes:
    values = [
        (x * 0.071 + y * 0.113 + case_index * 0.017)
        if (x + 2 * y + case_index) % 5 else 0.0
        for y in range(height) for x in range(width)
    ]
    return struct.pack(f"<{len(values)}f", *values)


def run_aex(source: bytes, destination: bytes, width: int, height: int,
            angle: float) -> bytes:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def unary(function):
        def callback(_uc, _args):
            loader.write_xmm_f32(0, function(loader.read_xmm_f32(0)))
            return 0
        return callback

    loader.import_impls.update({"cosf": unary(math.cos), "sinf": unary(math.sin)})
    source_pointer = loader.bump_alloc(len(source), align=16)
    destination_pointer = loader.bump_alloc(len(destination), align=16)
    loader.write_bytes(source_pointer, source)
    loader.write_bytes(destination_pointer, destination)
    loader.call_function(
        ROTATE,
        int_args=[source_pointer, destination_pointer, width, height, fbits(angle)],
        max_instructions=2_000_000,
    )
    return loader.read_bytes(destination_pointer, len(destination))


def main() -> int:
    cases = [
        ("even_zero", 6, 4, 0.0),
        ("odd_positive", 7, 5, 0.37),
        ("odd_negative", 5, 7, -0.61),
        ("thin", 3, 3, 1.0),
    ]
    with tempfile.TemporaryDirectory(prefix="dblur_scalar_rotate_") as name:
        library_path = Path(name) / "libdblur_scalar_rotate.dylib"
        subprocess.run(
            ["c++", "-std=c++17", "-O0", "-fno-fast-math",
             "-ffp-contract=off", "-dynamiclib", str(ROOT / "core/dblur_rotate.cpp"),
             "-o", str(library_path)],
            cwd=ROOT, check=True,
        )
        library = ctypes.CDLL(str(library_path))
        function = library.olm_dblur_rotate_scalar_f32
        function.argtypes = [ctypes.POINTER(ctypes.c_float),
                             ctypes.POINTER(ctypes.c_float), ctypes.c_int,
                             ctypes.c_int, ctypes.c_float]
        results = []
        for index, (case_id, width, height, angle) in enumerate(cases, 1):
            source = source_plane(index, width, height)
            destination = bytes((0xA0 + index, 0xB1, 0xC2, 0xD3)) * (width * height)
            expected = run_aex(source, destination, width, height, angle)
            source_array = (ctypes.c_float * (width * height)).from_buffer_copy(source)
            destination_array = (ctypes.c_float * (width * height)).from_buffer_copy(destination)
            function(source_array, destination_array, width, height, ctypes.c_float(angle))
            actual = ctypes.string_at(ctypes.addressof(destination_array), len(destination))
            results.append({
                "id": case_id,
                "dimensions": [width, height],
                "angle": angle,
                "actual_aex_sha256": hashlib.sha256(expected).hexdigest(),
                "portable_sha256": hashlib.sha256(actual).hexdigest(),
                "byte_exact": actual == expected,
            })
    report = {
        "schema": 1,
        "kind": "dblur_scalar_rotate_actual_aex_20260805",
        "status": "pass" if all(item["byte_exact"] for item in results) else "fail_closed",
        "primitive": "FUN_1800018c0",
        "scope": "float32 scalar planes; strict-interior bilinear rotation",
        "cases": results,
        "claim_boundary": {"actual_aex_byte_exact": all(item["byte_exact"] for item in results)},
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": results,
                      "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
