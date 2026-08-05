#!/usr/bin/env python3
"""Nonzero mode-2 field actual-AEX versus portable rowdriver differential."""

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

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/dblur_mode2_field_rowdriver_actual_aex_20260805.json"
ROWDRIVER = 0x1800038D0
WIDTH = 16
PARAM_SIZE = 0x8200


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def floats(values: list[float]) -> bytes:
    return struct.pack(f"<{len(values)}f", *values)


def inputs() -> dict[str, bytes]:
    source = []
    comp = []
    field = []
    for x in range(WIDTH):
        source.extend((x / 15.0, (15 - x) / 30.0, (x % 5) / 8.0, 1.0))
        comp.extend((1.0, 0.0, 0.0, 1.0))
        field.append((x + 1) / 16.0)
    return {
        "source": floats(source),
        "destination": floats(source),
        "denominator": bytes(WIDTH * 4),
        "alpha": bytes(WIDTH * 4),
        "comp": floats(comp),
        "field": floats(field),
        "front": floats([1.0, 0.8, 0.5, 0.2]),
    }


def run_actual(data: dict[str, bytes]) -> dict[str, bytes]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def import_powf(_uc, _args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0),
                                        loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("powf", import_powf)
    pointers = {}
    for name, blob in data.items():
        pointers[name] = loader.host_alloc(max(16, len(blob)))
        loader.write_bytes(pointers[name], blob)
    params = loader.host_alloc(PARAM_SIZE)
    loader.write_bytes(params, bytes(PARAM_SIZE))
    for offset, blob in (
        (0x20, struct.pack("<I", 2)),
        (0x2C, struct.pack("<f", 0.75)),
        (0x30, struct.pack("<f", 0.0)),
        (0x38, struct.pack("<f", 1.0)),
        (0x40, struct.pack("<f", 0.0)),
        (0x44, struct.pack("<f", 0.0)),
        (0x48, struct.pack("<I", 4)),
        (0x58, data["front"]),
        (0x8080, struct.pack("<Q", pointers["denominator"])),
        (0x8088, struct.pack("<Q", pointers["alpha"])),
        (0x80B0, struct.pack("<Q", pointers["field"])),
        (0x8118, struct.pack("<Q", pointers["comp"])),
    ):
        loader.write_bytes(params + offset, blob)
    source_slot = loader.host_alloc(8)
    destination_slot = loader.host_alloc(8)
    loader.write_bytes(source_slot, struct.pack("<Q", pointers["source"]))
    loader.write_bytes(destination_slot, struct.pack("<Q", pointers["destination"]))
    loader.call_function(
        ROWDRIVER,
        int_args=[0, 1, source_slot, destination_slot, WIDTH, WIDTH, params],
        max_instructions=500_000,
    )
    return {
        name: loader.read_bytes(pointers[name], len(data[name]))
        for name in ("destination", "denominator", "alpha")
    }


class Buffer:
    def __init__(self, blob: bytes):
        self.data = bytearray(blob)
        self.storage = (ctypes.c_ubyte * len(blob)).from_buffer(self.data)
        self.ptr = ctypes.cast(self.storage, ctypes.POINTER(ctypes.c_float))


def run_portable(data: dict[str, bytes], directory: Path) -> dict[str, bytes]:
    library_path = directory / "rowdriver.dylib"
    subprocess.run(
        ["c++", "-std=c++17", "-dynamiclib", "-O2", "-fno-fast-math",
         "-ffp-contract=off", str(ROOT / "core/dblur_rowdriver.cpp"),
         "-o", str(library_path)], cwd=ROOT, check=True)
    library = ctypes.CDLL(str(library_path))
    function = library.olm_dblur_rowdriver_field_f32
    function.argtypes = [
        ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float),
    ]
    buffers = {name: Buffer(blob) for name, blob in data.items()}
    empty = Buffer(bytes(4))
    function(
        0, 1, buffers["source"].ptr, buffers["destination"].ptr, WIDTH,
        ctypes.c_float(0.75), ctypes.c_float(0.0), ctypes.c_float(1.0),
        ctypes.c_float(0.0), ctypes.c_float(0.0), buffers["front"].ptr,
        empty.ptr, empty.ptr, empty.ptr, buffers["denominator"].ptr,
        buffers["alpha"].ptr, buffers["comp"].ptr, 4, 0, 0, 0,
        buffers["field"].ptr,
    )
    return {
        name: bytes(buffers[name].data)
        for name in ("destination", "denominator", "alpha")
    }


def main() -> int:
    data = inputs()
    actual = run_actual(data)
    with tempfile.TemporaryDirectory(prefix="dblur_mode2_field_") as name:
        portable = run_portable(data, Path(name))
    comparisons = {
        name: {
            "exact": actual[name] == portable[name],
            "actual_sha256": sha256(actual[name]),
            "portable_sha256": sha256(portable[name]),
        }
        for name in actual
    }
    report = {
        "schema": 1,
        "kind": "dblur_mode2_field_rowdriver_actual_aex_20260805",
        "status": "pass" if all(item["exact"] for item in comparisons.values()) else "fail_closed",
        "scope": "single 16-pixel row, nonzero mode-2 field, typed rowdriver only",
        "provenance": {"aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha256(AEX.read_bytes()), "function": hex(ROWDRIVER)},
        "parameters": {"opacity": 0.75, "field_range": [0.0625, 1.0], "front_count": 4},
        "comparisons": comparisons,
        "claim_boundary": {"mode2_rowdriver_exact": all(item["exact"] for item in comparisons.values()), "ae_field_generation_exact": False, "mac_ae_exact": False},
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "comparisons": comparisons, "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
