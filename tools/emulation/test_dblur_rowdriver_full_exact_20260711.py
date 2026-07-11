#!/usr/bin/env python3
"""Full-entry mode-0 rowdriver gate against the actual OLMDirectionalBlur AEX."""

from __future__ import annotations

import argparse
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
FIXTURES = ROOT / "replay/fixtures/dblur_rowdriver_full"
REPORT_JSON = ROOT / "refs/conformance/dblur_rowdriver_full_exact_20260711.json"

ROWDRIVER = 0x1800038D0
PARAM_SIZE = 0x8200
CANARY = bytes.fromhex("a5 5a c3 3c 96 69 f0 0f")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack(values: list[float]) -> bytes:
    return struct.pack("<%df" % len(values), *values)


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def f32(data: bytes, offset: int) -> float:
    return struct.unpack_from("<f", data, offset)[0]


def cases() -> list[dict]:
    return [
        {"id": "plane3_rows01_w5", "width": 5, "height": 3, "row_start": 0,
         "row_end": 2, "zero_alpha": [1], "front_count": 4, "back_count": 3,
         "pre_front_count": 3, "pre_back_count": 4, "exponent": 1.25,
         "scale": 1.7, "edge_x": 0.35, "edge_y": 0.85, "map_row": 0.4,
         "extent": 2.3},
        {"id": "plane4_rows12_w7", "width": 7, "height": 4, "row_start": 1,
         "row_end": 3, "zero_alpha": [], "front_count": 6, "back_count": 5,
         "pre_front_count": 5, "pre_back_count": 6, "exponent": 0.75,
         "scale": 0.9, "edge_x": 1.15, "edge_y": 0.42, "map_row": 1.6,
         "extent": 3.1},
        {"id": "plane5_rows24_w9_mode1", "width": 9, "height": 5, "row_start": 2,
         "row_end": 5, "zero_alpha": [0, 8], "front_count": 5, "back_count": 7,
         "pre_front_count": 7, "pre_back_count": 5, "exponent": 1.6,
         "scale": 2.2, "edge_x": 0.63, "edge_y": 1.4, "map_row": 2.25,
         "extent": 4.7, "mode": 1},
    ]


def source_blob(item: dict, case_index: int) -> bytes:
    values: list[float] = []
    for y in range(item["height"]):
        for x in range(item["width"]):
            alpha = 0.17 + 0.041 * x + 0.023 * y + case_index * 0.013
            if x in item["zero_alpha"] and item["row_start"] <= y < item["row_end"]:
                alpha = 0.0
            values += [0.07 + 0.031 * x + 0.017 * y,
                       -0.19 + 0.027 * x - 0.011 * y,
                       0.43 - 0.019 * x + 0.029 * y,
                       alpha]
    return pack(values)


def initial_blobs(item: dict, case_index: int) -> dict[str, bytes]:
    pixels = item["width"] * item["height"]
    source = source_blob(item, case_index)
    destination = pack([0.013 + case_index * 0.007 + i * 0.0003
                        for i in range(pixels * 4)])
    denominator = pack([0.21 + 0.017 * (i % item["width"]) for i in range(pixels)])
    alpha_max = pack([0.08 + 0.013 * (i % item["width"]) for i in range(pixels)])
    return {"source.bin": source, "destination.bin": destination,
            "denominator.bin": denominator, "alpha.bin": alpha_max}


def table(base: float, count: int, step: float) -> bytes:
    return pack([1.0] + [base + step * i for i in range(1, max(8, count))])


def comp_map(item: dict, case_index: int) -> bytes:
    values: list[float] = []
    for y in range(item["height"]):
        for x in range(item["width"]):
            values += [0.72 + 0.11 * x + 0.07 * case_index,
                       0.0, item["map_row"] + 0.17 * ((x + y) % 3), item["extent"]]
    return pack(values)


def protected_write(ld: AexLoader, data: bytes) -> tuple[int, int, int]:
    total = len(CANARY) + len(data) + len(CANARY)
    base = ld.bump_alloc(total, align=16)
    ld.write_bytes(base, CANARY + data + CANARY)
    return base + len(CANARY), len(data), base


def canary_ok(ld: AexLoader, base: int, size: int) -> bool:
    return ld.read_bytes(base, len(CANARY)) == CANARY and ld.read_bytes(
        base + len(CANARY) + size, len(CANARY)) == CANARY


def build_params(ld: AexLoader, item: dict, inputs: dict[str, bytes], index: int):
    width = item["width"]
    height = item["height"]
    params = ld.host_alloc(PARAM_SIZE)
    ld.write_bytes(params, b"\x00" * PARAM_SIZE)
    front = table(0.76 - index * 0.03, item["front_count"], -0.13)
    back = table(0.68 - index * 0.02, item["back_count"], -0.11)
    pre_front = table(0.84 - index * 0.025, item["pre_front_count"], -0.15)
    pre_back = table(0.61 - index * 0.018, item["pre_back_count"], -0.09)
    comp_addr, comp_size, comp_base = protected_write(ld, inputs["comp_map.bin"])
    denom_addr, denom_size, denom_base = protected_write(ld, inputs["denominator.bin"])
    alpha_addr, alpha_size, alpha_base = protected_write(ld, inputs["alpha.bin"])
    for off, value in ((0x20, item.get("mode", 0)), (0x2c, 0.73 + index * 0.04),
                       (0x30, item["exponent"]), (0x38, item["scale"]),
                       (0x40, item["edge_x"]), (0x44, item["edge_y"]),
                       (0x48, item["front_count"]), (0x4c, item["pre_front_count"]),
                       (0x50, item["back_count"]), (0x54, item["pre_back_count"])):
        blob = struct.pack("<I", value) if isinstance(value, int) else struct.pack("<f", value)
        ld.write_bytes(params + off, blob)
    for off, data in ((0x58, front), (0x4068, back),
                      (0x3ed8, pre_front), (0x7ee8, pre_back)):
        ld.write_bytes(params + off, data)
    for off, address in ((0x8080, denom_addr), (0x8088, alpha_addr),
                         (0x8118, comp_addr)):
        ld.write_bytes(params + off, struct.pack("<Q", address))
    return params, {"denom": (denom_addr, denom_size, denom_base),
                     "alpha": (alpha_addr, alpha_size, alpha_base),
                     "comp": (comp_addr, comp_size, comp_base)}


def run_actual(item: dict, inputs: dict[str, bytes], index: int) -> tuple[dict[str, bytes], dict]:
    ld = AexLoader(str(AEX), verbose=False, fast=True)
    ld.register_libm_impls(max_threads=1)

    def import_powf(_uc, _args):
        ld.write_xmm_f32(0, math.pow(ld.read_xmm_f32(0), ld.read_xmm_f32(1)))
        return 0

    ld.register_import_impl("powf", import_powf)
    addresses = {}
    guards = {}
    for name in ("source.bin", "destination.bin"):
        ptr, size, base = protected_write(ld, inputs[name])
        addresses[name] = ptr
        guards[name] = (base, size)
    for name in ("denominator.bin", "alpha.bin", "comp_map.bin"):
        inputs[name] = inputs[name]
    params, param_guards = build_params(ld, item, inputs, index)
    source_slot = ld.host_alloc(8)
    destination_slot = ld.host_alloc(8)
    ld.write_bytes(source_slot, struct.pack("<Q", addresses["source.bin"]))
    ld.write_bytes(destination_slot, struct.pack("<Q", addresses["destination.bin"]))
    result = ld.call_function(ROWDRIVER, int_args=[item["row_start"], item["row_end"],
                                                    source_slot, destination_slot,
                                                    item["width"], item.get("mode", 0), params],
                              max_instructions=20_000_000)
    outputs = {"destination.bin": ld.read_bytes(addresses["destination.bin"], len(inputs["destination.bin"])),
               "denominator.bin": ld.read_bytes(param_guards["denom"][0], param_guards["denom"][1]),
               "alpha.bin": ld.read_bytes(param_guards["alpha"][0], param_guards["alpha"][1])}
    bad = [name for name, (base, size) in {**guards,
           "denominator.bin": (param_guards["denom"][2], param_guards["denom"][1]),
           "alpha.bin": (param_guards["alpha"][2], param_guards["alpha"][1]),
           "comp_map.bin": (param_guards["comp"][2], param_guards["comp"][1])}.items()
        if not canary_ok(ld, base, size)]
    unimplemented = sorted({entry.name for entry in ld.import_log if entry.name not in ld.import_impls})
    return outputs, {"instructions": result["instructions"], "canary_failures": bad,
                     "unimplemented_imports": unimplemented}


def materialize() -> dict:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "kind": "dblur_rowdriver_full_actual_aex_fixture",
                "aex": str(AEX.relative_to(ROOT)), "aex_sha256": sha(AEX.read_bytes()),
                "comparison": "byte equality only; no tolerance", "cases": []}
    for index, item in enumerate(cases()):
        directory = FIXTURES / item["id"]
        directory.mkdir(parents=True, exist_ok=True)
        inputs = initial_blobs(item, index)
        inputs["comp_map.bin"] = comp_map(item, index)
        actual, execution = run_actual(item, dict(inputs), index)
        for name, data in {**inputs, **{"actual_" + k: v for k, v in actual.items()}}.items():
            (directory / name).write_bytes(data)
        record = {**item, "input_sha256": {k: sha(v) for k, v in inputs.items()},
                  "actual_sha256": {k: sha(v) for k, v in actual.items()}, "execution": execution}
        (directory / "case.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest["cases"].append(record)
    (FIXTURES / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


class Guarded:
    def __init__(self, data: bytes):
        self.raw = bytearray(CANARY + data + CANARY)
        self.size = len(data)
        self.array = (ctypes.c_ubyte * len(self.raw)).from_buffer(self.raw)
        self.ptr = ctypes.cast(ctypes.byref(self.array, len(CANARY)), ctypes.POINTER(ctypes.c_float))

    def bytes(self) -> bytes:
        return bytes(self.raw[len(CANARY):len(CANARY) + self.size])

    def canary_ok(self) -> bool:
        return bytes(self.raw[:len(CANARY)]) == CANARY and bytes(self.raw[-len(CANARY):]) == CANARY


def build_candidate() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="olm_dblur_rowdriver_full_"))
    lib = temp / "libdblur_rowdriver.so"
    subprocess.run(["c++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
                    "-fPIC", "-shared", str(ROOT / "core/dblur_rowdriver.cpp"), "-o", str(lib)],
                   cwd=ROOT, check=True)
    return lib


def run_candidate(lib_path: Path, item: dict, inputs: dict[str, bytes], index: int) -> tuple[dict[str, bytes], list[str]]:
    lib = ctypes.CDLL(str(lib_path))
    fn = lib.olm_dblur_rowdriver_f32
    fn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float, ctypes.c_float,
                   ctypes.c_float, ctypes.c_float, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                   ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_int,
                   ctypes.c_int, ctypes.c_int]
    guarded = {name: Guarded(inputs[name]) for name in ("source.bin", "destination.bin", "denominator.bin", "alpha.bin", "comp_map.bin")}
    front = Guarded(table(0.76 - index * 0.03, item["front_count"], -0.13))
    back = Guarded(table(0.68 - index * 0.02, item["back_count"], -0.11))
    pre_front = Guarded(table(0.84 - index * 0.025, item["pre_front_count"], -0.15))
    pre_back = Guarded(table(0.61 - index * 0.018, item["pre_back_count"], -0.09))
    fn(item["row_start"], item["row_end"], guarded["source.bin"].ptr, guarded["destination.bin"].ptr,
       item["width"], item.get("mode", 0), ctypes.c_float(0.73 + index * 0.04), ctypes.c_float(item["exponent"]),
       ctypes.c_float(item["scale"]), ctypes.c_float(item["edge_x"]), ctypes.c_float(item["edge_y"]),
       front.ptr, back.ptr, pre_front.ptr, pre_back.ptr, guarded["denominator.bin"].ptr,
       guarded["alpha.bin"].ptr, guarded["comp_map.bin"].ptr, item["front_count"], item["back_count"],
       item["pre_front_count"], item["pre_back_count"])
    outputs = {name: guarded[name].bytes() for name in ("destination.bin", "denominator.bin", "alpha.bin")}
    failures = [name for name, value in {**guarded, "front": front, "back": back,
                                          "pre_front": pre_front, "pre_back": pre_back}.items()
                if not value.canary_ok()]
    return outputs, failures


def first_difference(got: bytes, expected: bytes) -> tuple[int, float | None, float | None] | None:
    for offset, (a, b) in enumerate(zip(got, expected)):
        if a != b:
            base = offset - offset % 4
            return offset, (f32(got, base) if base + 4 <= len(got) else None), (f32(expected, base) if base + 4 <= len(expected) else None)
    return (len(got), None, None) if len(got) != len(expected) else None


def verify(manifest: dict) -> dict:
    lib = build_candidate()
    failures = []
    for index, item in enumerate(manifest["cases"]):
        directory = FIXTURES / item["id"]
        inputs = {name: (directory / name).read_bytes() for name in
                  ("source.bin", "destination.bin", "denominator.bin", "alpha.bin", "comp_map.bin")}
        got, canaries = run_candidate(lib, item, inputs, index)
        if canaries:
            failures.append({"case": item["id"], "kind": "canary", "buffers": canaries})
        for name, value in got.items():
            expected = (directory / ("actual_" + name)).read_bytes()
            diff = first_difference(value, expected)
            if diff:
                offset, got_float, expected_float = diff
                failures.append({"case": item["id"], "file": name, "byte_offset": offset,
                                 "candidate_float": got_float, "actual_aex_float": expected_float})
    return {"status": "pass" if not failures else "known-red", "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-fixtures", action="store_true")
    args = parser.parse_args()
    manifest_path = FIXTURES / "manifest.json"
    manifest = materialize() if args.write_fixtures or not manifest_path.exists() else json.loads(manifest_path.read_text())
    result = verify(manifest)
    report = {"schema": 1, "kind": "dblur_rowdriver_full_exact_gate", "status": result["status"],
              "harness": str(Path(__file__).relative_to(ROOT)), "fixture_dir": str(FIXTURES.relative_to(ROOT)),
              "aex_sha256": manifest["aex_sha256"], "comparison": "byte equality only; no tolerance",
              "cases": len(manifest["cases"]), **result}
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
