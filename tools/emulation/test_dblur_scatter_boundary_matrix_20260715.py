#!/usr/bin/env python3
"""Mac-only AEX scatter boundary matrix for the pending row755 witness.

This is helper-contract evidence, not a complete DirectionalBlur result.  It
keeps the inputs synthetic so the touched destination set is observable.
"""

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
WIDTH = 7
HEIGHT = 3
ROW_BASE = WIDTH
SOURCE_X = 3
SOURCE_PIXEL = ROW_BASE + SOURCE_X
WEIGHTS = [0.03125 + 0.03125 * index for index in range(16)]


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def pack(values: list[float]) -> bytes:
    return struct.pack("<%df" % len(values), *values)


def unpack(data: bytes) -> list[float]:
    return list(struct.unpack("<%df" % (len(data) // 4), data))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def fixture() -> dict[str, bytes]:
    pixels = WIDTH * HEIGHT
    source = [0.0] * (pixels * 4)
    source[SOURCE_PIXEL * 4:SOURCE_PIXEL * 4 + 4] = [2.0, 3.0, 4.0, 0.95]
    destination = [0.1, 0.2, 0.3, 0.4] * pixels
    denominator = [0.5] * pixels
    alpha_max = [0.8] * pixels
    return {
        "source": pack(source),
        "destination": pack(destination),
        "denominator": pack(denominator),
        "alpha_max": pack(alpha_max),
        "weights": pack(WEIGHTS),
    }


CASES = (
    {"name": "forward_row_end_clip", "start": 3, "backward": 0, "count": 5, "end": 7, "coefficient": 1.0},
    {"name": "backward_left_clip", "start": 3, "backward": 1, "count": 5, "end": 7, "coefficient": 1.0},
    {"name": "fractional_forward_one_step", "start": 3, "backward": 0, "count": 5, "end": 7, "coefficient": 0.5},
    {"name": "zero_length_noop", "start": 3, "backward": 0, "count": 5, "end": 7, "coefficient": 0.0},
)


def expected(data: dict[str, bytes], case: dict[str, float | int]) -> tuple[dict[str, bytes], list[int]]:
    result = {name: bytearray(blob) for name, blob in data.items() if name != "source" and name != "weights"}
    source = unpack(data["source"])
    destination = unpack(bytes(result["destination"]))
    denominator = unpack(bytes(result["denominator"]))
    alpha_max = unpack(bytes(result["alpha_max"]))
    coefficient = float(case["coefficient"])
    length = int(float(case["count"]) * coefficient)
    direction = -1 if int(case["backward"]) else 1
    if length <= 0:
        return {name: bytes(blob) for name, blob in result.items()}, []
    start = int(case["start"])
    end = int(case["end"])
    if not int(case["backward"]) and end <= start + length:
        length = end - start
    elif int(case["backward"]) and start - length < 0:
        length = start
    if length <= 1:
        return {name: bytes(blob) for name, blob in result.items()}, []
    scale = f32(1.0 / coefficient) if coefficient > 0.0 else 1.0
    targets: list[int] = []
    for offset in range(1, length):
        target = SOURCE_PIXEL + direction * offset
        targets.append(target)
        weight_index = int(f32(float(offset) * scale))
        contribution = f32(alpha_max[SOURCE_PIXEL] * WEIGHTS[weight_index])
        for channel in range(3):
            product = f32(contribution * source[SOURCE_PIXEL * 4 + channel])
            destination[target * 4 + channel] = f32(destination[target * 4 + channel] + product)
        denominator[target] = f32(denominator[target] + contribution)
        destination[target * 4 + 3] = max(destination[target * 4 + 3], contribution)
    result["destination"][:] = pack(destination)
    result["denominator"][:] = pack(denominator)
    result["alpha_max"][:] = pack(alpha_max)
    return {name: bytes(blob) for name, blob in result.items()}, targets


def call_aex(data: dict[str, bytes], case: dict[str, float | int]) -> dict[str, bytes]:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    addresses = {name: loader.bump_alloc(len(blob), align=16) for name, blob in data.items()}
    for name, blob in data.items():
        loader.write_bytes(addresses[name], blob)
    args = [int(case["start"]), ROW_BASE, int(case["backward"]), addresses["source"],
            addresses["destination"], addresses["denominator"], addresses["alpha_max"],
            addresses["weights"], int(case["count"]), int(case["end"]),
            struct.unpack("<I", struct.pack("<f", float(case["coefficient"]))) [0]]
    loader.call_function(SCATTER, int_args=args, max_instructions=2_000_000)
    return {name: loader.read_bytes(addresses[name], len(blob)) for name, blob in data.items()
            if name not in ("source", "weights")}


def build_current(directory: Path) -> Path:
    library = directory / "libdblur_rowdriver.so"
    subprocess.run([
        "c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
        "-fPIC", "-shared", str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(library),
    ], cwd=ROOT, check=True)
    return library


def call_current(library: Path, data: dict[str, bytes], case: dict[str, float | int]) -> dict[str, bytes]:
    lib = ctypes.CDLL(str(library))
    fn = lib.olm_dblur_scatter_f32
    fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char, ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int,
                   ctypes.c_int, ctypes.c_float]
    arrays = {name: (ctypes.c_float * (len(blob) // 4)).from_buffer_copy(blob)
              for name, blob in data.items()}
    fn(int(case["start"]), ROW_BASE, int(case["backward"]), arrays["source"], arrays["destination"],
       arrays["denominator"], arrays["alpha_max"], arrays["weights"], int(case["count"]),
       int(case["end"]), ctypes.c_float(float(case["coefficient"])))
    return {name: bytes(ctypes.string_at(ctypes.addressof(array), len(data[name])))
            for name, array in arrays.items() if name not in ("source", "weights")}


def assert_result(actual: dict[str, bytes], reference: dict[str, bytes], label: str) -> None:
    for name in reference:
        if actual[name] != reference[name]:
            raise AssertionError(f"{label} {name}: got {sha(actual[name])}, expected {sha(reference[name])}")


def main() -> int:
    data = fixture()
    with tempfile.TemporaryDirectory(prefix="dblur_boundary_") as temp:
        current_library = build_current(Path(temp))
        for case in CASES:
            model, targets = expected(data, case)
            aex = call_aex(data, case)
            current = call_current(current_library, data, case)
            assert_result(aex, model, f"AEX/{case['name']}")
            assert_result(current, model, f"current/{case['name']}")
            assert_result(aex, current, f"AEX-current/{case['name']}")
            print(f"PASS {case['name']}: targets={targets} center_untouched=1 cross_row_untouched=1")
    print("FACT helper contract: forward writes are exclusive of source and row end; backward writes clip at x=0.")
    print("FACT helper contract: coefficient 0 is a no-op; coefficient 0.5 uses table index trunc(i / coefficient).")
    print("INFERENCE pending Windows witness: typed destination/denominator/alpha captures can be checked against this write-set without using PNG bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
