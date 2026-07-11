#!/usr/bin/env python3
"""Byte-exact actual-AEX replay for the DirectionalBlur leaf candidate."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import struct
import subprocess
import tempfile
from pathlib import Path

from aex_loader import AexLoader

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMDirectionalBlur.aex"
FIXTURES = ROOT / "replay/fixtures/dblur_rowdriver_portable"
PREPASS = 0x180001000
SCATTER = 0x1800013E0


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def pack(values: list[float]) -> bytes:
    return struct.pack("<%df" % len(values), *values)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cases() -> list[dict]:
    return [
        {"id": "prepass_wide_coeff125", "kind": "prepass", "width": 9,
         "height": 3, "row": 1, "start": 2, "front_count": 4, "back_count": 3,
         "end": 9, "coefficient": 1.25, "alpha_zero": False},
        {"id": "prepass_zero_alpha", "kind": "prepass", "width": 7,
         "height": 3, "row": 1, "start": 3, "front_count": 6, "back_count": 5,
         "end": 7, "coefficient": 0.75, "alpha_zero": True},
        {"id": "prepass_boundary_coeffhalf", "kind": "prepass", "width": 5,
         "height": 3, "row": 1, "start": 1, "front_count": 5, "back_count": 4,
         "end": 4, "coefficient": 0.5, "alpha_zero": False},
        {"id": "scatter_forward_accumulator", "kind": "scatter", "width": 8,
         "height": 3, "row": 1, "start": 3, "count": 5, "end": 8,
         "coefficient": 1.4, "backward": False},
        {"id": "scatter_backward_boundary", "kind": "scatter", "width": 8,
         "height": 3, "row": 1, "start": 5, "count": 5, "end": 8,
         "coefficient": 0.8, "backward": True},
    ]


def source(width: int, height: int, case: int, alpha_zero_x: int | None = None) -> bytes:
    values: list[float] = []
    for y in range(height):
        for x in range(width):
            alpha = 0.13 + 0.071 * x + 0.019 * y + 0.017 * case
            if alpha_zero_x == x and y == 1:
                alpha = 0.0
            values += [0.11 + 0.083 * x + 0.021 * y + case * 0.009,
                       -0.23 + 0.047 * x - 0.013 * y - case * 0.006,
                       0.67 - 0.031 * x + 0.017 * y + case * 0.012, alpha]
    return pack(values)


def weights(count: int, case: int, reverse: bool = False) -> bytes:
    values = [1.0, 0.83 - case * 0.01, 0.57 + case * 0.013,
              0.29 - case * 0.007, 0.11 + case * 0.005, 0.0, 0.0, 0.0]
    if reverse:
        values = [1.0, 0.71 + case * 0.009, 0.43 - case * 0.011,
                  0.19 + case * 0.006, 0.07, 0.0, 0.0, 0.0]
    return pack(values[:max(8, count)])


def make_inputs(item: dict, index: int) -> dict[str, bytes]:
    width = item["width"]
    height = item["height"]
    pixels = width * height
    src = source(width, height, index + 1, item["start"] if item.get("alpha_zero", False) else None)
    if item["kind"] == "prepass":
        return {"source.bin": src, "destination.bin": pack([0.021 + index] * (pixels * 4)),
                "denominator.bin": pack([0.17 + index * 0.03] * pixels),
                "valid.bin": pack([0.09 + index * 0.02] * pixels),
                "front_weights.bin": weights(item["front_count"], index + 1),
                "back_weights.bin": weights(item["back_count"], index + 1, True)}
    return {"source.bin": src, "destination.bin": pack([0.019 + index * 0.01] * (pixels * 4)),
            "denominator.bin": pack([0.12 + index * 0.02] * pixels),
            "alpha_max.bin": pack([0.08 + index * 0.03] * pixels),
            "weights.bin": weights(item["count"], index + 1)}


def run_aex(item: dict, data: dict[str, bytes]) -> dict[str, bytes]:
    ld = AexLoader(str(AEX), verbose=False, fast=True)
    ld.register_libm_impls(max_threads=1)
    addresses = {}
    for name, blob in data.items():
        addresses[name] = ld.bump_alloc(len(blob), align=16)
        ld.write_bytes(addresses[name], blob)
    i = item
    row_base = i["row"] * i["width"]
    if i["kind"] == "prepass":
        args = [i["start"], row_base, addresses["source.bin"], addresses["destination.bin"],
                addresses["denominator.bin"], addresses["valid.bin"], addresses["front_weights.bin"],
                i["front_count"], addresses["back_weights.bin"], i["back_count"], i["end"],
                fbits(i["coefficient"])]
        ld.call_function(PREPASS, int_args=args, max_instructions=2_000_000)
        names = ["destination.bin", "denominator.bin", "valid.bin"]
    else:
        args = [i["start"], row_base, int(i["backward"]), addresses["source.bin"],
                addresses["destination.bin"], addresses["denominator.bin"], addresses["alpha_max.bin"],
                addresses["weights.bin"], i["count"], i["end"], fbits(i["coefficient"])]
        ld.call_function(SCATTER, int_args=args, max_instructions=2_000_000)
        names = ["destination.bin", "denominator.bin", "alpha_max.bin"]
    return {name: ld.read_bytes(addresses[name], len(data[name])) for name in names}


def materialize() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha(AEX.read_bytes()),
                "exact_policy": "byte equality only; no tolerance", "cases": []}
    for index, item in enumerate(cases()):
        directory = FIXTURES / item["id"]
        directory.mkdir(exist_ok=True)
        inputs = make_inputs(item, index)
        expected = run_aex(item, inputs)
        for name, blob in {**inputs, **{f"expected_{k}": v for k, v in expected.items()}}.items():
            (directory / name).write_bytes(blob)
        record = {**item, "input_sha256": {k: sha(v) for k, v in inputs.items()},
                  "expected_sha256": {k: sha(v) for k, v in expected.items()}}
        (directory / "case.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest["cases"].append(record)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def build_candidate() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="olm_dblur_rowdriver_"))
    lib = tmp / "libdblur_rowdriver.so"
    subprocess.run(["c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                    "-fPIC", "-shared", str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(lib)],
                   cwd=ROOT, check=True)
    return lib


def run_candidate(lib_path: Path, item: dict, data: dict[str, bytes]) -> dict[str, bytes]:
    lib = ctypes.CDLL(str(lib_path))
    width = item["width"]
    row_base = item["row"] * width
    arrays = {k: (ctypes.c_float * (len(v) // 4)).from_buffer_copy(v) for k, v in data.items()}
    if item["kind"] == "prepass":
        fn = lib.olm_dblur_prepass_f32
        fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                       ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int, ctypes.c_float]
        fn(item["start"], row_base, arrays["source.bin"], arrays["destination.bin"], arrays["denominator.bin"],
           arrays["valid.bin"], arrays["front_weights.bin"], item["front_count"], arrays["back_weights.bin"],
           item["back_count"], item["end"], item["coefficient"])
        names = ["destination.bin", "denominator.bin", "valid.bin"]
    else:
        fn = lib.olm_dblur_scatter_f32
        fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                       ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                       ctypes.c_int, ctypes.c_int, ctypes.c_float]
        fn(item["start"], row_base, int(item["backward"]), arrays["source.bin"], arrays["destination.bin"],
           arrays["denominator.bin"], arrays["alpha_max.bin"], arrays["weights.bin"], item["count"], item["end"],
           item["coefficient"])
        names = ["destination.bin", "denominator.bin", "alpha_max.bin"]
    return {name: bytes(ctypes.string_at(ctypes.addressof(arrays[name]), len(data[name]))) for name in names}


def verify() -> None:
    lib = build_candidate()
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    for item in manifest["cases"]:
        directory = FIXTURES / item["id"]
        names = ["source.bin", "destination.bin", "denominator.bin", "valid.bin", "front_weights.bin", "back_weights.bin"] if item["kind"] == "prepass" else ["source.bin", "destination.bin", "denominator.bin", "alpha_max.bin", "weights.bin"]
        data = {name: (directory / name).read_bytes() for name in names}
        actual = run_candidate(lib, item, data)
        for name, got in actual.items():
            expected = (directory / f"expected_{name}").read_bytes()
            if got != expected:
                for pos, (a, b) in enumerate(zip(got, expected)):
                    if a != b:
                        raise AssertionError(f"{item['id']} {name}: byte {pos}: got 0x{a:02x}, expected 0x{b:02x}")
                raise AssertionError(f"{item['id']} {name}: length mismatch")
    print(f"[OK] {len(manifest['cases'])} actual-AEX leaf fixtures match byte-for-byte")


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
