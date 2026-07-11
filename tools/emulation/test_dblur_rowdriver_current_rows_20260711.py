#!/usr/bin/env python3
"""Compare current-case DirectionalBlur rows against the actual AEX rowdriver."""

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

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
SOURCE = ROOT / (
    "refs/win_references/olm_reference_return_windows_20260611/"
    "OLMDirectionalBlur/directionalblur_context_scale_20260606__software__fr24__"
    "db_angle0_strength_sweep_small_before_effects.png"
)
REPORT = ROOT / "refs/conformance/dblur_rowdriver_current_rows_20260711.json"

ROWDRIVER = 0x1800038D0
WORK_WIDTH = 2206
WORK_HEIGHT = 2206
INPUT_X = 143
INPUT_Y = 563
FRONT_COUNT = 48
PARAM_SIZE = 0x8200
ROWS = (2063, 1802, 1563, 404, 144)
EXPECTED_STAGED_SHA256 = "91537ff463613533427af34deb4960a3aacd88000db6ad7ca70aea30ab11112e"
EXPECTED_ROTATED_SHA256 = "03c7e9bd8ee92bf10ff621378bcf540b883ebeb532bc875f11665b47de518c0d"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_f32(values: list[float]) -> bytes:
    return struct.pack(f"<{len(values)}f", *values)


def f32_at(data: bytes, index: int) -> float:
    return struct.unpack_from("<f", data, index * 4)[0]


def u32_at(data: bytes, index: int) -> int:
    return struct.unpack_from("<I", data, index * 4)[0]


def ordered_float(bits: int) -> int:
    return 0x80000000 - (bits & 0x7FFFFFFF) if bits & 0x80000000 else 0x80000000 + bits


def ulp_distance(left: int, right: int) -> int:
    return abs(ordered_float(left) - ordered_float(right))


def build_libraries(directory: Path) -> tuple[ctypes.CDLL, ctypes.CDLL]:
    rotate_path = directory / "libdblur_rotate.dylib"
    rowdriver_path = directory / "libdblur_rowdriver.dylib"
    subprocess.run(
        [
            "c++", "-std=c++17", "-O0", "-fno-fast-math", "-ffp-contract=off",
            "-dynamiclib", str(ROOT / "core/dblur_rotate.cpp"), "-o", str(rotate_path),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-dynamiclib", str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(rowdriver_path),
        ],
        cwd=ROOT,
        check=True,
    )
    return ctypes.CDLL(str(rotate_path)), ctypes.CDLL(str(rowdriver_path))


def rotated_current_source(rotate_lib: ctypes.CDLL) -> np.ndarray:
    rgba = np.asarray(Image.open(SOURCE).convert("RGBA"), dtype=np.uint8)
    staged = np.zeros((WORK_HEIGHT, WORK_WIDTH, 4), dtype=np.float32)
    staged[INPUT_Y:INPUT_Y + rgba.shape[0], INPUT_X:INPUT_X + rgba.shape[1]] = (
        rgba.astype(np.float32) / np.float32(255.0)
    )
    staged_hash = sha(staged.tobytes())
    if staged_hash != EXPECTED_STAGED_SHA256:
        raise RuntimeError(f"staged source hash mismatch: {staged_hash}")

    rotated = np.zeros_like(staged)
    fn = rotate_lib.olm_dblur_rotate_rgba_f32
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.c_int, ctypes.c_int, ctypes.c_float,
    ]
    fn(
        staged.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        rotated.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        WORK_WIDTH,
        WORK_HEIGHT,
        ctypes.c_float(struct.unpack("<f", bytes.fromhex("db0fc93f"))[0]),
    )
    rotated_hash = sha(rotated.tobytes())
    if rotated_hash != EXPECTED_ROTATED_SHA256:
        raise RuntimeError(f"rotated source hash mismatch: {rotated_hash}")
    return rotated


def gaussian_table() -> bytes:
    ratio = np.float32(FRONT_COUNT) / np.float32(3.0)
    denominator = np.float32(
        np.float64(2.0) * np.float64(ratio) * np.float64(ratio) + np.float64(1.0e-5)
    )
    weights = []
    for index in range(FRONT_COUNT):
        numerator = np.float32(index * index)
        exponent = np.float32(-numerator / denominator)
        weights.append(np.float32(math.exp(float(exponent))).item())
    return pack_f32(weights)


def compact_inputs(rotated: np.ndarray, row: int) -> dict[str, bytes]:
    source = rotated[row].tobytes()
    pixels = WORK_WIDTH
    # In the current mode-1, exponent-0, no-tail case these component fields
    # reduce to coefficient 1.0 and do not encode row-specific geometry.
    comp = np.empty((pixels, 4), dtype=np.float32)
    comp[:, 0] = 1.0
    comp[:, 1] = 0.0
    comp[:, 2] = 0.0
    comp[:, 3] = 1.0
    return {
        "source": source,
        "destination": source,
        "denominator": bytes(pixels * 4),
        "alpha": bytes(pixels * 4),
        "comp": comp.tobytes(),
    }


def run_actual(inputs: dict[str, bytes], weights: bytes) -> tuple[dict[str, bytes], int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def import_powf(_uc, _args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("powf", import_powf)
    addresses = {}
    for name, blob in inputs.items():
        address = loader.host_alloc(max(16, len(blob)))
        loader.write_bytes(address, blob)
        addresses[name] = address

    params = loader.host_alloc(PARAM_SIZE)
    loader.write_bytes(params, bytes(PARAM_SIZE))
    for offset, value in (
        (0x20, struct.pack("<I", 1)),
        (0x2C, struct.pack("<f", 1.0)),
        (0x30, struct.pack("<f", 0.0)),
        (0x38, struct.pack("<f", 1.0)),
        (0x40, struct.pack("<f", 0.0)),
        (0x44, struct.pack("<f", 0.0)),
        (0x48, struct.pack("<I", FRONT_COUNT)),
        (0x4C, struct.pack("<I", 0)),
        (0x50, struct.pack("<I", 0)),
        (0x54, struct.pack("<I", 0)),
        (0x58, weights),
        (0x8080, struct.pack("<Q", addresses["denominator"])),
        (0x8088, struct.pack("<Q", addresses["alpha"])),
        (0x8118, struct.pack("<Q", addresses["comp"])),
    ):
        loader.write_bytes(params + offset, value)

    source_slot = loader.host_alloc(8)
    destination_slot = loader.host_alloc(8)
    loader.write_bytes(source_slot, struct.pack("<Q", addresses["source"]))
    loader.write_bytes(destination_slot, struct.pack("<Q", addresses["destination"]))
    execution = loader.call_function(
        ROWDRIVER,
        int_args=[0, 1, source_slot, destination_slot, WORK_WIDTH, 1, params],
        max_instructions=30_000_000,
    )
    outputs = {
        name: loader.read_bytes(addresses[name], len(inputs[name]))
        for name in ("destination", "denominator", "alpha")
    }
    return outputs, execution["instructions"]


class FloatBuffer:
    def __init__(self, data: bytes):
        self.data = bytearray(data)
        self.array = (ctypes.c_ubyte * len(self.data)).from_buffer(self.data)
        self.pointer = ctypes.cast(self.array, ctypes.POINTER(ctypes.c_float))

    def bytes(self) -> bytes:
        return bytes(self.data)


def run_candidate(lib: ctypes.CDLL, inputs: dict[str, bytes], weights: bytes) -> dict[str, bytes]:
    buffers = {name: FloatBuffer(blob) for name, blob in inputs.items()}
    front = FloatBuffer(weights)
    empty = FloatBuffer(bytes(4))
    fn = lib.olm_dblur_rowdriver_f32
    fn.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int,
    ]
    fn(
        0, 1, buffers["source"].pointer, buffers["destination"].pointer,
        WORK_WIDTH, 1, ctypes.c_float(1.0), ctypes.c_float(0.0),
        ctypes.c_float(1.0), ctypes.c_float(0.0), ctypes.c_float(0.0),
        front.pointer, empty.pointer, empty.pointer, empty.pointer,
        buffers["denominator"].pointer, buffers["alpha"].pointer,
        buffers["comp"].pointer, FRONT_COUNT, 0, 0, 0,
    )
    return {name: buffers[name].bytes() for name in ("destination", "denominator", "alpha")}


def compare(left: bytes, right: bytes) -> dict:
    mismatches = []
    for index in range(len(left) // 4):
        left_bits = u32_at(left, index)
        right_bits = u32_at(right, index)
        if left_bits != right_bits:
            mismatches.append({
                "float_index": index,
                "pixel": index // 4 if len(left) == WORK_WIDTH * 16 else index,
                "channel": index % 4 if len(left) == WORK_WIDTH * 16 else None,
                "actual_bits": f"0x{left_bits:08x}",
                "candidate_bits": f"0x{right_bits:08x}",
                "actual": f32_at(left, index),
                "candidate": f32_at(right, index),
                "ulp": ulp_distance(left_bits, right_bits),
            })
            if len(mismatches) == 16:
                break
    count = sum(
        u32_at(left, index) != u32_at(right, index)
        for index in range(len(left) // 4)
    )
    return {
        "exact": count == 0,
        "differing_floats": count,
        "actual_sha256": sha(left),
        "candidate_sha256": sha(right),
        "first_mismatches": mismatches,
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_current_rows_") as temp:
        rotate_lib, rowdriver_lib = build_libraries(Path(temp))
        rotated = rotated_current_source(rotate_lib)
        weights = gaussian_table()
        cases = []
        for row in ROWS:
            inputs = compact_inputs(rotated, row)
            actual, instructions = run_actual(inputs, weights)
            candidate = run_candidate(rowdriver_lib, inputs, weights)
            comparisons = {
                name: compare(actual[name], candidate[name])
                for name in ("destination", "denominator", "alpha")
            }
            cases.append({
                "source_row": row,
                "source_row_sha256": sha(inputs["source"]),
                "actual_aex_instructions": instructions,
                "comparisons": comparisons,
                "exact": all(item["exact"] for item in comparisons.values()),
            })

    result = {
        "schema": 1,
        "kind": "dblur_rowdriver_current_rows_actual_aex_gate",
        "status": "pass" if all(case["exact"] for case in cases) else "known-red",
        "comparison": "byte equality of float32 rowdriver outputs; no tolerance",
        "aex": str(AEX.relative_to(ROOT)),
        "aex_sha256": sha(AEX.read_bytes()),
        "source": str(SOURCE.relative_to(ROOT)),
        "work_dimensions": [WORK_WIDTH, WORK_HEIGHT],
        "front_count": FRONT_COUNT,
        "rows": list(ROWS),
        "cases": cases,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
