#!/usr/bin/env python3
"""Bounded actual-AEX rowdriver gate for the Alpha Fade witness column."""

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

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader
from unicorn.x86_const import UC_X86_REG_RBX, UC_X86_REG_RDI, UC_X86_REG_RSI, UC_X86_REG_R15, UC_X86_REG_XMM6


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
INPUT = ROOT / "refs/win_references/20260711_directionalblur_front_alpha_current_2025_aex/raw/input_argb8_tight.bin"
TABLES = ROOT / "refs/reports/dblur_ucrt_expf_return/olm_runtime_trace_olmdirectionalblur_ucrt_expf_gaussian_tables_20260711_return_windows_validated_tables.json"
REPORT = ROOT / "refs/conformance/dblur_alpha_fade_witness_row_20260712.json"
ROWDRIVER = 0x1800038D0
NORMALIZE_LOOP = 0x180005554
NORMALIZE_END = 0x180005610
OUTPUT8 = 0x180006B30
HOST_WIDTH, HOST_HEIGHT = 1920, 1080
WORK_WIDTH = 2206
OFFSET_X, OFFSET_Y = 143, 563
HOST_X = 1308
HOST_Y_FIRST, HOST_Y_LAST = 184, 517
INTERNAL_ROW = 755
INTERNAL_X_FIRST = HOST_Y_FIRST + OFFSET_Y
INTERNAL_X_LAST = HOST_Y_LAST + OFFSET_Y
SCATTER_COUNT, PREPASS_COUNT = 240, 96
PARAM_SIZE = 0x8200


def sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def table_bytes() -> dict[int, bytes]:
    payload = json.loads(TABLES.read_text(encoding="utf-8"))
    result = {}
    for table in payload["tables"]:
        result[table["n"]] = b"".join(struct.pack("<I", int(word, 16)) for word in table["words"])
    if set(result) != {PREPASS_COUNT, SCATTER_COUNT}:
        raise RuntimeError(f"unexpected UCRT table sizes: {sorted(result)}")
    return result


def rotated_witness_row() -> bytes:
    """Materialize only rotate(+pi/2) row 755 from the captured PF world."""
    argb = np.frombuffer(INPUT.read_bytes(), dtype=np.uint8).reshape(HOST_HEIGHT, HOST_WIDTH, 4)
    row = np.zeros((WORK_WIDTH, 4), dtype=np.float32)
    # For internal y=755, rotate(+pi/2) samples staged x=1451 exactly and
    # staged y=internal_x. PF A/R/G/B becomes work R/G/B/A.
    host_column = argb[:, HOST_X]
    row[OFFSET_Y:OFFSET_Y + HOST_HEIGHT, 0] = host_column[:, 1].astype(np.float32) / np.float32(255.0)
    row[OFFSET_Y:OFFSET_Y + HOST_HEIGHT, 1] = host_column[:, 2].astype(np.float32) / np.float32(255.0)
    row[OFFSET_Y:OFFSET_Y + HOST_HEIGHT, 2] = host_column[:, 3].astype(np.float32) / np.float32(255.0)
    row[OFFSET_Y:OFFSET_Y + HOST_HEIGHT, 3] = host_column[:, 0].astype(np.float32) / np.float32(255.0)
    return row.tobytes()


def initial_inputs(source: bytes, logical_row: int = 0) -> dict[str, bytes]:
    comp = np.zeros((WORK_WIDTH, 4), dtype=np.float32)
    comp[:, 0] = np.float32(1.0)
    comp[:, 2] = np.float32(logical_row)
    comp[:, 3] = np.float32(1.0)
    return {
        "source": source,
        "destination": source,
        "denominator": bytes(WORK_WIDTH * 4),
        "alpha": bytes(WORK_WIDTH * 4),
        "comp": comp.tobytes(),
    }


def run_actual(inputs: dict[str, bytes], tables: dict[int, bytes]) -> tuple[dict[str, bytes], int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)

    def import_powf(_uc, _args):
        loader.write_xmm_f32(0, math.pow(loader.read_xmm_f32(0), loader.read_xmm_f32(1)))
        return 0

    loader.register_import_impl("powf", import_powf)
    addresses = {}
    for name, blob in inputs.items():
        addresses[name] = loader.host_alloc(max(16, len(blob)))
        loader.write_bytes(addresses[name], blob)
    params = loader.host_alloc(PARAM_SIZE)
    loader.write_bytes(params, bytes(PARAM_SIZE))
    plane_bias = INTERNAL_ROW * WORK_WIDTH * 16
    scalar_bias = INTERNAL_ROW * WORK_WIDTH * 4
    fields = (
        (0x20, struct.pack("<I", 1)), (0x2C, struct.pack("<f", 1.0)),
        (0x30, struct.pack("<f", 0.0)), (0x38, struct.pack("<f", 1.0)),
        (0x40, struct.pack("<f", 0.0)), (0x44, struct.pack("<f", 0.0)),
        (0x48, struct.pack("<I", SCATTER_COUNT)), (0x4C, struct.pack("<I", PREPASS_COUNT)),
        (0x50, struct.pack("<I", 0)), (0x54, struct.pack("<I", 0)),
        (0x58, tables[SCATTER_COUNT]), (0x3ED8, tables[PREPASS_COUNT]),
        (0x8080, struct.pack("<Q", addresses["denominator"] - scalar_bias)),
        (0x8088, struct.pack("<Q", addresses["alpha"] - scalar_bias)),
        (0x8118, struct.pack("<Q", addresses["comp"] - plane_bias)),
    )
    for offset, blob in fields:
        loader.write_bytes(params + offset, blob)
    source_slot, destination_slot = loader.host_alloc(8), loader.host_alloc(8)
    loader.write_bytes(source_slot, struct.pack("<Q", addresses["source"] - plane_bias))
    loader.write_bytes(destination_slot, struct.pack("<Q", addresses["destination"] - plane_bias))
    execution = loader.call_function(
        ROWDRIVER,
        int_args=[INTERNAL_ROW, INTERNAL_ROW + 1, source_slot, destination_slot,
                  WORK_WIDTH, WORK_WIDTH, params],
        max_instructions=35_000_000,
    )
    return ({name: loader.read_bytes(addresses[name], len(inputs[name]))
             for name in ("destination", "denominator", "alpha")}, execution["instructions"])


def run_actual_normalization(destination: bytes, denominator: bytes) -> tuple[bytes, int]:
    """Enter the AEX normalization loop directly and stop before rotate-back."""
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    destination_ptr = loader.host_alloc(len(destination))
    denominator_ptr = loader.host_alloc(len(denominator))
    cleared_ptr = loader.host_alloc(len(destination))
    params = loader.host_alloc(PARAM_SIZE)
    loader.write_bytes(destination_ptr, destination)
    loader.write_bytes(denominator_ptr, denominator)
    loader.write_bytes(cleared_ptr, b"\xa5" * len(destination))
    loader.write_bytes(params, bytes(PARAM_SIZE))
    loader.write_bytes(params + 0x8080, struct.pack("<Q", denominator_ptr))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", WORK_WIDTH))
    loader.write_bytes(params + 0x80A4, struct.pack("<I", 1))

    def setup(ld: AexLoader, _address: int, _size: int) -> None:
        ld.uc.reg_write(UC_X86_REG_RBX, params)
        ld.uc.reg_write(UC_X86_REG_RSI, destination_ptr)
        ld.uc.reg_write(UC_X86_REG_R15, cleared_ptr)
        ld.uc.reg_write(UC_X86_REG_RDI, 0)
        ld.uc.reg_write(UC_X86_REG_XMM6, 0)

    def stop(ld: AexLoader, _address: int, _size: int) -> None:
        ld.uc.emu_stop()

    loader.add_code_hook(NORMALIZE_LOOP, setup)
    loader.add_code_hook(NORMALIZE_END, stop)
    execution = loader.call_function(NORMALIZE_LOOP, max_instructions=200_000)
    if loader.read_bytes(cleared_ptr, len(destination)) != bytes(len(destination)):
        raise RuntimeError("actual normalization did not clear the destination row")
    return loader.read_bytes(destination_ptr, len(destination)), execution["instructions"]


def run_actual_writer(normalized: bytes) -> tuple[bytes, int]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    source_ptr = loader.host_alloc(len(normalized))
    params = loader.host_alloc(PARAM_SIZE)
    output_ptr = loader.host_alloc(4)
    loader.write_bytes(source_ptr, normalized)
    loader.write_bytes(params, bytes(PARAM_SIZE))
    loader.write_bytes(params + 0x28, struct.pack("<f", 1.0))
    loader.write_bytes(params + 0x8090, struct.pack("<Q", source_ptr))
    loader.write_bytes(params + 0x80A0, struct.pack("<I", WORK_WIDTH))
    packed = bytearray()
    instructions = 0
    for internal_x in range(INTERNAL_X_FIRST, INTERNAL_X_LAST + 1):
        loader.write_bytes(output_ptr, b"\x00" * 4)
        execution = loader.call_function(
            OUTPUT8, int_args=[params, internal_x, 0, 0, output_ptr], max_instructions=1000)
        instructions += execution["instructions"]
        packed.extend(loader.read_bytes(output_ptr, 4))
    return bytes(packed), instructions


def portable_normalization(destination: bytes, denominator: bytes) -> bytes:
    result = np.frombuffer(destination, dtype="<f4").reshape(WORK_WIDTH, 4).copy()
    divisor = np.frombuffer(denominator, dtype="<f4")
    active = divisor > np.float32(0.0)
    result[active, :3] = np.float32(result[active, :3] / divisor[active, None])
    return result.tobytes()


def expected_windows_packed() -> bytes:
    raw = np.frombuffer(
        (INPUT.parent / "output_argb8_tight.bin").read_bytes(), dtype=np.uint8
    ).reshape(HOST_HEIGHT, HOST_WIDTH, 4)
    return raw[HOST_Y_FIRST:HOST_Y_LAST + 1, HOST_X].tobytes()


class Buffer:
    def __init__(self, blob: bytes):
        self.data = bytearray(blob)
        self.storage = (ctypes.c_ubyte * len(blob)).from_buffer(self.data)
        self.ptr = ctypes.cast(self.storage, ctypes.POINTER(ctypes.c_float))


def run_portable(inputs: dict[str, bytes], tables: dict[int, bytes], temp: Path) -> dict[str, bytes]:
    library = temp / "libdblur_rowdriver.dylib"
    subprocess.run([
        "c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
        "-dynamiclib", str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(library),
    ], cwd=ROOT, check=True)
    lib = ctypes.CDLL(str(library))
    fn = lib.olm_dblur_rowdriver_f32
    buffers = {name: Buffer(blob) for name, blob in inputs.items()}
    scatter, prepass, empty = Buffer(tables[SCATTER_COUNT]), Buffer(tables[PREPASS_COUNT]), Buffer(bytes(4))
    fn.argtypes = [ctypes.c_int, ctypes.c_int] + [ctypes.POINTER(ctypes.c_float)] * 2 + [ctypes.c_int, ctypes.c_int] + [ctypes.c_float] * 5 + [ctypes.POINTER(ctypes.c_float)] * 7 + [ctypes.c_int] * 4
    fn(0, 1, buffers["source"].ptr, buffers["destination"].ptr, WORK_WIDTH, 1,
       ctypes.c_float(1.0), ctypes.c_float(0.0), ctypes.c_float(1.0), ctypes.c_float(0.0), ctypes.c_float(0.0),
       scatter.ptr, empty.ptr, prepass.ptr, empty.ptr, buffers["denominator"].ptr,
       buffers["alpha"].ptr, buffers["comp"].ptr, SCATTER_COUNT, 0, PREPASS_COUNT, 0)
    return {name: bytes(buffers[name].data) for name in ("destination", "denominator", "alpha")}


def compare(actual: bytes, portable: bytes, components: int) -> dict:
    actual_words = np.frombuffer(actual, dtype="<u4")
    portable_words = np.frombuffer(portable, dtype="<u4")
    different = np.flatnonzero(actual_words != portable_words)
    focus_first = INTERNAL_X_FIRST * components
    focus_last = (INTERNAL_X_LAST + 1) * components
    focus = different[(different >= focus_first) & (different < focus_last)]
    return {
        "exact": different.size == 0,
        "differing_floats": int(different.size),
        "focus_differing_floats": int(focus.size),
        "actual_sha256": sha(actual),
        "portable_sha256": sha(portable),
        "first_differing_indices": different[:16].tolist(),
        "first_focus_differing_indices": focus[:16].tolist(),
    }


def main() -> int:
    tables = table_bytes()
    source = rotated_witness_row()
    inputs = initial_inputs(source, INTERNAL_ROW)
    portable_inputs = initial_inputs(source, 0)
    with tempfile.TemporaryDirectory(prefix="olm_dblur_alpha_witness_") as name:
        actual, instructions = run_actual(inputs, tables)
        portable = run_portable(portable_inputs, tables, Path(name))
    actual_normalized, normalization_instructions = run_actual_normalization(
        actual["destination"], actual["denominator"])
    portable_normalized = portable_normalization(portable["destination"], portable["denominator"])
    actual_packed, writer_instructions = run_actual_writer(actual_normalized)
    windows_packed = expected_windows_packed()
    comparisons = {
        "destination": compare(actual["destination"], portable["destination"], 4),
        "denominator": compare(actual["denominator"], portable["denominator"], 1),
        "alpha": compare(actual["alpha"], portable["alpha"], 1),
    }
    status = "pass" if all(item["exact"] for item in comparisons.values()) else "mismatch"
    result = {
        "schema": 1,
        "kind": "dblur_alpha_fade_witness_row_actual_aex_gate",
        "status": status,
        "parameters": {"front_strength": 240, "front_alpha_fade": 96, "angle_degrees": 0, "input_alpha": "PREMULTIPLIED"},
        "mapping": {
            "host_witness": [HOST_X, HOST_Y_FIRST],
            "host_residual_extent": [HOST_X, HOST_Y_FIRST, HOST_X, HOST_Y_LAST],
            "work_offset": [OFFSET_X, OFFSET_Y],
            "rotateback_work_destination": [HOST_X + OFFSET_X, HOST_Y_FIRST + OFFSET_Y],
            "internal_witness": [INTERNAL_X_FIRST, INTERNAL_ROW],
            "internal_focus_extent": [INTERNAL_X_FIRST, INTERNAL_ROW, INTERNAL_X_LAST, INTERNAL_ROW],
            "rotateback_fraction": [0.0, 0.0],
        },
        "scope": {"rowdriver_rows": [INTERNAL_ROW, INTERNAL_ROW + 1], "row_width": WORK_WIDTH, "full_entry_rerun": False},
        "aex_sha256": sha(AEX.read_bytes()),
        "input_sha256": sha(INPUT.read_bytes()),
        "rotated_row_sha256": sha(source),
        "ucrt_table_sha256": {str(count): sha(blob) for count, blob in tables.items()},
        "actual_aex_instructions": instructions,
        "comparisons": comparisons,
        "downstream": {
            "normalization": compare(actual_normalized, portable_normalized, 4),
            "normalization_actual_aex_instructions": normalization_instructions,
            "rotateback": {
                "operation": "fx=fy=+0.0 maps each focused normalized pixel to the same host pixel",
                "source_bits_preserved": True,
            },
            "pf_writer": {
                "actual_aex_instructions": writer_instructions,
                "actual_aex_vs_windows": compare(actual_packed, windows_packed, 4),
                "actual_aex_packed_sha256": sha(actual_packed),
                "windows_packed_sha256": sha(windows_packed),
            },
            "first_mismatch_boundary": "captured row state versus full-render state before normalization",
        },
        "production_changed": False,
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
