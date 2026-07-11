#!/usr/bin/env python3
"""Check current-case rotate-back target pixels against the actual x86 AEX."""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
from unicorn.x86_const import (
    UC_X86_REG_R8,
    UC_X86_REG_R9,
    UC_X86_REG_R10,
    UC_X86_REG_RBP,
)

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader
import test_dblur_rowdriver_current_rows_20260711 as current


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/dblur_rotateback_current_targets_20260711.json"
ROTATE = 0x180001EC0
NORMALIZED_SHA256 = "f9383f94079457719921600a132a2e8281c137c00defb90f6089d821156a6bcd"
ROTATEBACK_SHA256 = "263644ba0c30c65b6007dacf76d6f4e514256a1057a95887ef5f4188af5a3df7"
OUTPUT_X = (0, 261, 262, 500, 1658, 1659, 1919)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized_plane(rowdriver_lib: ctypes.CDLL, rotated: np.ndarray) -> np.ndarray:
    width = current.WORK_WIDTH
    height = current.WORK_HEIGHT
    destination = rotated.copy()
    denominator = np.zeros((height, width), dtype=np.float32)
    alpha = np.zeros((height, width), dtype=np.float32)
    component = np.empty((height, width, 4), dtype=np.float32)
    component[:, :] = (1.0, 0.0, 0.0, 1.0)
    front = np.frombuffer(current.gaussian_table(), dtype="<f4").copy()
    empty = np.zeros(1, dtype=np.float32)
    pointer = ctypes.POINTER(ctypes.c_float)
    fn = rowdriver_lib.olm_dblur_rowdriver_f32
    fn.argtypes = [
        ctypes.c_int, ctypes.c_int, pointer, pointer, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, pointer, pointer, pointer, pointer, pointer, pointer,
        pointer, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ]
    fn(
        0, 2176,
        rotated.ctypes.data_as(pointer),
        destination.ctypes.data_as(pointer),
        width, 1, ctypes.c_float(1.0), ctypes.c_float(0.0),
        ctypes.c_float(1.0), ctypes.c_float(0.0), ctypes.c_float(0.0),
        front.ctypes.data_as(pointer), empty.ctypes.data_as(pointer),
        empty.ctypes.data_as(pointer), empty.ctypes.data_as(pointer),
        denominator.ctypes.data_as(pointer), alpha.ctypes.data_as(pointer),
        component.ctypes.data_as(pointer), current.FRONT_COUNT, 0, 0, 0,
    )
    valid = denominator > 0.0
    for channel in range(3):
        destination[:, :, channel][valid] = (
            destination[:, :, channel][valid] / denominator[valid]
        )
    actual_hash = sha(destination.tobytes())
    if actual_hash != NORMALIZED_SHA256:
        raise RuntimeError(f"normalized plane hash mismatch: {actual_hash}")
    return destination


def candidate_rotateback(rotate_lib: ctypes.CDLL, source: np.ndarray) -> np.ndarray:
    destination = np.zeros_like(source)
    pointer = ctypes.POINTER(ctypes.c_float)
    fn = rotate_lib.olm_dblur_rotate_rgba_f32
    fn.argtypes = [pointer, pointer, ctypes.c_int, ctypes.c_int, ctypes.c_float]
    angle = struct.unpack("<f", bytes.fromhex("db0fc9bf"))[0]
    fn(
        source.ctypes.data_as(pointer),
        destination.ctypes.data_as(pointer),
        current.WORK_WIDTH,
        current.WORK_HEIGHT,
        ctypes.c_float(angle),
    )
    actual_hash = sha(destination.tobytes())
    if actual_hash != ROTATEBACK_SHA256:
        raise RuntimeError(f"rotate-back plane hash mismatch: {actual_hash}")
    return destination


def run_actual_targets(source: np.ndarray, candidate: np.ndarray) -> list[dict]:
    width = current.WORK_WIDTH
    height = current.WORK_HEIGHT
    plane_bytes = source.nbytes
    loader = AexLoader(str(current.AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def import_f1(function):
        def impl(_uc, _args):
            loader.write_xmm_f32(0, function(loader.read_xmm_f32(0)))
            return 0
        return impl

    loader.import_impls.update({"cosf": import_f1(math.cos), "sinf": import_f1(math.sin)})
    source_address = loader.bump_alloc(plane_bytes, align=16)
    destination_address = loader.bump_alloc(plane_bytes, align=16)
    loader.write_bytes(source_address, source.tobytes())
    loader.write_bytes(destination_address, bytes(plane_bytes))

    state = {"target": (0, 0), "row_skipped": False, "pixel_skipped": False}

    def skip_to_row(ld: AexLoader, _address: int, _size: int) -> None:
        if state["row_skipped"]:
            return
        x, y = state["target"]
        ld.uc.reg_write(UC_X86_REG_R10, y)
        ld.uc.reg_write(UC_X86_REG_RBP, destination_address + 8 + y * width * 16)
        state["row_skipped"] = True

    def skip_to_pixel(ld: AexLoader, _address: int, _size: int) -> None:
        if state["pixel_skipped"]:
            return
        x, y = state["target"]
        ld.uc.reg_write(UC_X86_REG_R8, x)
        ld.uc.reg_write(UC_X86_REG_R9, destination_address + 8 + (y * width + x) * 16)
        state["pixel_skipped"] = True

    def finish_pixel(ld: AexLoader, _address: int, _size: int) -> None:
        ld.uc.reg_write(UC_X86_REG_R8, width - 1)

    def finish_row(ld: AexLoader, _address: int, _size: int) -> None:
        ld.uc.reg_write(UC_X86_REG_R10, height - 1)

    # These hooks preserve global dimensions and coordinates while executing
    # only the selected output pixel through the unmodified AEX math body.
    loader.add_code_hook(0x180001F91, skip_to_row)
    loader.add_code_hook(0x180001FE0, skip_to_pixel)
    loader.add_code_hook(0x1800021BD, finish_pixel)
    loader.add_code_hook(0x1800021DC, finish_row)

    angle = struct.unpack("<f", bytes.fromhex("db0fc9bf"))[0]
    angle_bits = struct.unpack("<I", struct.pack("<f", angle))[0]
    results = []
    for output_x in OUTPUT_X:
        x = current.INPUT_X + output_x
        y = current.INPUT_Y
        state.update(target=(x, y), row_skipped=False, pixel_skipped=False)
        execution = loader.call_function(
            ROTATE,
            int_args=[source_address, destination_address, width, height, angle_bits],
            max_instructions=100_000,
        )
        address = destination_address + (y * width + x) * 16
        actual = loader.read_bytes(address, 16)
        expected = candidate[y, x].tobytes()
        results.append({
            "output_xy": [output_x, 0],
            "work_xy": [x, y],
            "actual_aex_instructions": execution["instructions"],
            "actual_bits": [f"0x{value:08x}" for value in struct.unpack("<4I", actual)],
            "candidate_bits": [f"0x{value:08x}" for value in struct.unpack("<4I", expected)],
            "exact": actual == expected,
        })
    return results


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_rotateback_targets_") as temp:
        rotate_lib, rowdriver_lib = current.build_libraries(Path(temp))
        rotated = current.rotated_current_source(rotate_lib)
        normalized = normalized_plane(rowdriver_lib, rotated)
        candidate = candidate_rotateback(rotate_lib, normalized)
        targets = run_actual_targets(normalized, candidate)

    report = {
        "schema": 1,
        "kind": "dblur_rotateback_current_targets_actual_aex_gate",
        "status": "pass" if all(item["exact"] for item in targets) else "known-red",
        "comparison": "float32 RGBA byte equality; no tolerance",
        "aex": str(current.AEX.relative_to(ROOT)),
        "aex_sha256": sha(current.AEX.read_bytes()),
        "source": str(current.SOURCE.relative_to(ROOT)),
        "normalized_plane_sha256": NORMALIZED_SHA256,
        "candidate_rotateback_sha256": ROTATEBACK_SHA256,
        "targets": targets,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
