#!/usr/bin/env python3
"""Byte-exact replay of OLMDirectionalBlur FUN_180001ec0.

The expected planes are produced by the actual Windows AEX under Unicorn.
The candidate is compiled locally with floating-point contraction disabled and
called through its small C ABI.  Fixtures intentionally poison destinations,
so invalid strict-border samples are compared byte-for-byte as well.
"""

from __future__ import annotations

import argparse
import atexit
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

ROTATE = 0x180001EC0
AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
FIXTURES = ROOT / "replay" / "fixtures" / "dblur_rotate"
_candidate_tmp: tempfile.TemporaryDirectory[str] | None = None
LIB: Path | None = None


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def plane(case: int, width: int, height: int) -> bytes:
    values = []
    for y in range(height):
        for x in range(width):
            # Distinct channels, non-integral values, and alpha edge cases.
            values.extend([
                0.03125 + 0.071 * x + 0.113 * y + case * 0.007,
                -0.17 + 0.043 * x - 0.059 * y + case * 0.011,
                0.9 - 0.037 * x + 0.081 * y - case * 0.013,
                0.0 if (x + 2 * y + case) % 7 == 0 else (0.25 + 0.11 * ((x + y) % 5)),
            ])
    return struct.pack("<%df" % len(values), *values)


def cases() -> list[dict]:
    return [
        {"id": "even_angle0", "width": 6, "height": 4, "angle": 0.0},
        {"id": "odd_positive", "width": 5, "height": 3, "angle": 0.37},
        {"id": "odd_negative", "width": 3, "height": 5, "angle": -0.61},
        {"id": "alpha_boundary", "width": 7, "height": 6, "angle": 1.0},
        {"id": "thin_even", "width": 4, "height": 2, "angle": -0.25},
        {"id": "thin_odd", "width": 3, "height": 3, "angle": 0.125},
    ]


def build_candidate() -> None:
    global _candidate_tmp, LIB
    FIXTURES.mkdir(parents=True, exist_ok=True)
    _candidate_tmp = tempfile.TemporaryDirectory(prefix="olm_dblur_rotate_")
    LIB = Path(_candidate_tmp.name) / "libdblur_rotate.so"
    subprocess.run([
        "c++", "-std=c++17", "-O0", "-fno-fast-math", "-ffp-contract=off",
        "-fPIC", "-shared", str(ROOT / "core/dblur_rotate.cpp"), "-o", str(LIB),
    ], cwd=ROOT, check=True)


def run_candidate(source: bytes, destination: bytes, width: int, height: int, angle: float) -> bytes:
    if LIB is None:
        raise RuntimeError("candidate has not been compiled")
    lib = ctypes.CDLL(str(LIB))
    fn = lib.olm_dblur_rotate_rgba_f32
    fn.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int, ctypes.c_float]
    src = (ctypes.c_float * (width * height * 4)).from_buffer_copy(source)
    dst = (ctypes.c_float * (width * height * 4)).from_buffer_copy(destination)
    fn(src, dst, width, height, ctypes.c_float(angle))
    return bytes(ctypes.string_at(ctypes.addressof(dst), len(destination)))


def run_aex(source: bytes, destination: bytes, width: int, height: int, angle: float) -> bytes:
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    loader.register_libm_impls(max_threads=1)
    # This AEX imports the single-precision names; the shared loader only
    # supplies the double-precision cos/sin aliases.
    def f1(fn):
        def impl(_uc, _args):
            loader.write_xmm_f32(0, fn(loader.read_xmm_f32(0)))
            return 0
        return impl
    loader.import_impls.update({"cosf": f1(math.cos), "sinf": f1(math.sin)})
    src_addr = loader.bump_alloc(len(source), align=16)
    dst_addr = loader.bump_alloc(len(destination), align=16)
    loader.write_bytes(src_addr, source)
    loader.write_bytes(dst_addr, destination)
    loader.call_function(ROTATE, int_args=[src_addr, dst_addr, width, height, fbits(angle)], max_instructions=2_000_000)
    return loader.read_bytes(dst_addr, len(destination))


def fixture_paths(item: dict) -> tuple[Path, Path, Path]:
    stem = FIXTURES / item["id"]
    return stem.with_suffix(".src.bin"), stem.with_suffix(".dst.bin"), stem.with_suffix(".json")


def alpha_order_stress_source() -> bytes:
    values = []
    alphas = {(3, 1): 0.1, (3, 2): 0.2, (4, 1): 0.3, (4, 2): 0.4}
    for y in range(6):
        for x in range(6):
            values.extend([0.0, 0.0, 0.0, alphas.get((x, y), 0.0)])
    return struct.pack("<%df" % len(values), *values)


def f32_sum(values: list[float]) -> float:
    result = values[0]
    for value in values[1:]:
        result = struct.unpack("<f", struct.pack("<f", result + value))[0]
    return result


def verify_alpha_order_stress() -> None:
    source = alpha_order_stress_source()
    destination = bytes([0xAA]) * len(source)
    target_alpha_offset = (1 * 6 + 3) * 16 + 12
    actual = run_candidate(source, destination, 6, 6, 0.37)
    aex = run_aex(source, destination, 6, 6, 0.37)
    candidate_bits = fbits(struct.unpack_from("<f", actual, target_alpha_offset)[0])
    aex_bits = fbits(struct.unpack_from("<f", aex, target_alpha_offset)[0])

    terms = [0.023930974304676056, 0.007491882890462875,
             0.18760348856449127, 0.03915436938405037]
    mac_bits = fbits(f32_sum([terms[index] for index in (2, 0, 1, 3)]))
    stated_aex_bits = fbits(f32_sum([terms[index] for index in (1, 0, 2, 3)]))
    assert mac_bits == 0x3E843044
    assert stated_aex_bits == 0x3E843043
    assert aex_bits == mac_bits, f"actual AEX: 0x{aex_bits:08x}, Mac-order witness: 0x{mac_bits:08x}"
    assert candidate_bits == aex_bits


def materialize() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "primitive": "FUN_180001ec0", "pixel_layout": "float32 RGBA", "cases": []}
    for index, item in enumerate(cases()):
        src_path, dst_path, meta_path = fixture_paths(item)
        src = plane(index + 1, item["width"], item["height"])
        dst = bytes((0xA0 + index, 0xB1, 0xC2, 0xD3)) * (item["width"] * item["height"] * 4)
        expected = run_aex(src, dst, item["width"], item["height"], item["angle"])
        src_path.write_bytes(src)
        dst_path.write_bytes(expected)
        metadata = {**item, "source_sha256": hashlib.sha256(src).hexdigest(), "expected_sha256": hashlib.sha256(expected).hexdigest(), "destination_poison_hex": (bytes((0xA0 + index, 0xB1, 0xC2, 0xD3))).hex()}
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        manifest["cases"].append(metadata)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def verify() -> None:
    build_candidate()
    manifest = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["cases"]:
        src_path, dst_path, _ = fixture_paths(item)
        src = src_path.read_bytes()
        expected = dst_path.read_bytes()
        poison = bytes.fromhex(item["destination_poison_hex"]) * (item["width"] * item["height"] * 4)
        actual = run_candidate(src, poison, item["width"], item["height"], item["angle"])
        if actual != expected:
            for offset, (got, want) in enumerate(zip(actual, expected)):
                if got != want:
                    raise AssertionError(f"{item['id']}: byte {offset}: got 0x{got:02x}, expected 0x{want:02x}")
    verify_alpha_order_stress()
    print(f"[OK] {len(manifest['cases'])} actual-AEX rotate fixtures match byte-for-byte")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-fixtures", action="store_true")
    args = parser.parse_args()
    if args.write_fixtures or not (FIXTURES / "manifest.json").exists():
        materialize()
    verify()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
