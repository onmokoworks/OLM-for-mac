#!/usr/bin/env python3
"""Narrow AEX/current-core contract check for rowdriver scatter."""

from __future__ import annotations

import ctypes
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
SCATTER = 0x1800013E0
WIDTH = 5
HEIGHT = 3
ROW_BASE = WIDTH
START = 2
END = WIDTH
SOURCE_PIXEL = ROW_BASE + START
TARGETS = (ROW_BASE + 3, ROW_BASE + 4)


def floats(values: list[float]) -> bytes:
    return struct.pack("<%df" % len(values), *values)


def unpack(data: bytes) -> list[float]:
    return list(struct.unpack("<%df" % (len(data) // 4), data))


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs() -> dict[str, bytes]:
    pixels = WIDTH * HEIGHT
    source = [0.0] * (pixels * 4)
    source[SOURCE_PIXEL * 4:SOURCE_PIXEL * 4 + 4] = [2.0, 3.0, 4.0, 0.95]
    destination = [0.1, 0.2, 0.3, 0.4] * pixels
    denominator = [0.5] * pixels
    alpha_max = [0.1] * pixels
    alpha_max[SOURCE_PIXEL] = 0.8
    weights = [1.0, 0.5, 0.25, 0.125] + [0.0] * 4
    return {"source": floats(source), "destination": floats(destination),
            "denominator": floats(denominator), "alpha_max": floats(alpha_max),
            "weights": floats(weights)}


def call_aex(data: dict[str, bytes]) -> dict[str, bytes]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    addresses = {}
    for name, blob in data.items():
        addresses[name] = loader.bump_alloc(len(blob), align=16)
        loader.write_bytes(addresses[name], blob)
    args = [START, ROW_BASE, 0, addresses["source"], addresses["destination"],
            addresses["denominator"], addresses["alpha_max"], addresses["weights"],
            4, END, struct.unpack("<I", struct.pack("<f", 1.0))[0]]
    loader.call_function(SCATTER, int_args=args, max_instructions=2_000_000)
    return {name: loader.read_bytes(addresses[name], len(blob))
            for name, blob in data.items() if name != "source" and name != "weights"}


def build_current() -> Path:
    directory = Path(tempfile.mkdtemp(prefix="dblur_contract_"))
    library = directory / "libdblur_rowdriver.so"
    subprocess.run([
        "c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
        "-fPIC", "-shared", str(ROOT / "core/dblur_rowdriver.cpp"),
        "-o", str(library),
    ], cwd=ROOT, check=True)
    return library


def call_current(library: Path, data: dict[str, bytes]) -> dict[str, bytes]:
    lib = ctypes.CDLL(str(library))
    fn = lib.olm_dblur_scatter_f32
    fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char,
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int,
                   ctypes.c_float]
    arrays = {
        name: (ctypes.c_float * (len(blob) // 4)).from_buffer_copy(blob)
        for name, blob in data.items()
    }
    fn(START, ROW_BASE, 0, arrays["source"], arrays["destination"],
       arrays["denominator"], arrays["alpha_max"], arrays["weights"],
       4, END, ctypes.c_float(1.0))
    return {name: bytes(ctypes.string_at(ctypes.addressof(array), len(data[name])))
            for name, array in arrays.items()
            if name != "source" and name != "weights"}


def expected(data: dict[str, bytes]) -> dict[str, bytes]:
    result = {name: bytearray(blob) for name, blob in data.items()
              if name != "source" and name != "weights"}
    source = unpack(data["source"])
    for target, weight in zip(TARGETS, (0.5, 0.25)):
        contribution = 0.8 * weight
        for channel in range(3):
            offset = target * 4 + channel
            value = unpack(bytes(result["destination"]))[offset]
            product = f32(f32(contribution) * f32(source[SOURCE_PIXEL * 4 + channel]))
            struct.pack_into("<f", result["destination"], offset * 4,
                             f32(value + product))
        struct.pack_into("<f", result["destination"], target * 16 + 12,
                         max(0.4, contribution))
        struct.pack_into("<f", result["denominator"], target * 4,
                         f32(0.5 + contribution))
    return {name: bytes(blob) for name, blob in result.items()}


def assert_contract(actual: dict[str, bytes], reference: dict[str, bytes], label: str) -> None:
    for name in reference:
        if actual[name] != reference[name]:
            raise AssertionError(f"{label} {name}: got {sha(actual[name])}, expected {sha(reference[name])}")
    for name in ("destination", "denominator", "alpha_max"):
        values = unpack(actual[name])
        touched = {target for target in TARGETS}
        if name == "destination":
            indices = [i for i in range(WIDTH * HEIGHT * 4)
                       if i // 4 not in touched]
        else:
            indices = [i for i in range(WIDTH * HEIGHT) if i not in touched]
        initial = unpack(inputs()[name])
        if any(values[index] != initial[index] for index in indices):
            raise AssertionError(f"{label} {name}: write crossed row-end/stride boundary")


def main() -> int:
    data = inputs()
    model = expected(data)
    aex = call_aex(data)
    current = call_current(build_current(), data)
    assert_contract(aex, model, "AEX")
    assert_contract(current, model, "current")
    if aex != current:
        raise AssertionError("current scatter helper diverges from AEX contract")
    print("PASS dblur rowdriver contract: exclusive row-end, width stride, denominator add, max alpha")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
