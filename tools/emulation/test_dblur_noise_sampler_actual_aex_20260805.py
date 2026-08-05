#!/usr/bin/env python3
"""Bit-exact differential for OLMDirectionalBlur FUN_180003370."""

from __future__ import annotations

import ctypes
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aex_loader import AexLoader


ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/dblur_noise_sampler_actual_aex_20260805.json"
FUNCTION = 0x180003370
ACTUAL_AEX_PLANE_SHA256 = "61c28ffa1fb0391f1647a4d4cfd8167307b9e88670103b1477aaef9e7cf492d0"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bits(value: float) -> str:
    return f"0x{struct.unpack('<I', struct.pack('<f', value))[0]:08X}"


def build(directory: Path) -> ctypes.CDLL:
    wrapper = (
        '#include "core/dblur_noise.h"\n'
        'extern "C" float candidate(const float* p,int s,float c,int x,int y,int i){'
        'return olm::dblur::sample_noise_plane({p,s,c},x,y,i!=0);}\n'
        'extern "C" int generate(float* out,int cap,int* w,int* h){'
        'std::vector<float> v;if(!olm::dblur::generate_noise_plane(1104,1104,5.0f,'
        '0.3611111044883728f,7,&v,w,h)||cap<(int)v.size())return -1;'
        'for(int i=0;i<(int)v.size();++i)out[i]=v[i];return (int)v.size();}\n'
    )
    library = directory / "noise_sampler.dylib"
    subprocess.run(
        ["c++", "-std=c++17", "-dynamiclib", "-O2", "-fno-fast-math",
         "-ffp-contract=off", "-I", str(ROOT), "-x", "c++", "-",
         "-o", str(library)],
        check=True,
        cwd=ROOT,
        input=wrapper,
        text=True,
    )
    return ctypes.CDLL(str(library))


def main() -> int:
    stride = 7
    rows = 6
    cell_size = 4.25
    values = [
        struct.unpack("<f", struct.pack("<f", ((index * 37) % 101) / 100.0))[0]
        for index in range(stride * rows)
    ]
    raw = struct.pack(f"<{len(values)}f", *values)
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    samples = loader.host_alloc(len(raw))
    context = loader.host_alloc(0x48)
    loader.write_bytes(samples, raw)
    loader.write_bytes(context, bytes(0x48))
    loader.write_bytes(context + 0x08, struct.pack("<Q", samples))
    loader.write_bytes(context + 0x10, struct.pack("<i", stride))
    loader.write_bytes(context + 0x40, struct.pack("<f", cell_size))

    with tempfile.TemporaryDirectory(prefix="dblur_noise_sampler_") as name:
        library = build(Path(name))
        candidate = library.candidate
        candidate.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int,
                              ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        candidate.restype = ctypes.c_float
        array = (ctypes.c_float * len(values))(*values)
        cases = []
        for interpolate in (0, 1):
            for x, y in ((0, 0), (1, 2), (4, 3), (7, 8), (12, 13), (20, 16)):
                loader.call_function(FUNCTION, int_args=[context, x, y, interpolate],
                                     max_instructions=1000)
                actual = loader.read_xmm_f32(0)
                portable = candidate(array, stride, ctypes.c_float(cell_size),
                                     x, y, interpolate)
                cases.append({
                    "xy": [x, y],
                    "interpolate": bool(interpolate),
                    "actual_bits": bits(actual),
                    "portable_bits": bits(portable),
                    "exact": bits(actual) == bits(portable),
                })
        generate = library.generate
        generate.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int,
                             ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        generate.restype = ctypes.c_int
        plane = (ctypes.c_float * (223 * 223))()
        plane_width = ctypes.c_int()
        plane_height = ctypes.c_int()
        generated_count = generate(plane, len(plane), ctypes.byref(plane_width),
                                   ctypes.byref(plane_height))
        generated_bytes = bytes(plane)
        generated_sha256 = sha256(generated_bytes)

    report = {
        "schema": 1,
        "kind": "dblur_noise_sampler_actual_aex_20260805",
        "status": "pass" if all(case["exact"] for case in cases) and
        generated_count == 223 * 223 and generated_sha256 == ACTUAL_AEX_PLANE_SHA256
        else "fail_closed",
        "scope": "FUN_180003370 sampler plus fixed FUN_1800034e0 generated plane",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX.read_bytes()),
            "function": hex(FUNCTION),
        },
        "fixture": {"stride": stride, "rows": rows, "cell_size": cell_size},
        "cases": cases,
        "generator": {
            "source_dimensions": [1104, 1104],
            "plane_dimensions": [plane_width.value, plane_height.value],
            "cell_size": 5.0,
            "offset": 0.3611111044883728,
            "seed": 7,
            "actual_aex_sha256": ACTUAL_AEX_PLANE_SHA256,
            "portable_sha256": generated_sha256,
            "portable_first_words": [
                f"0x{struct.unpack('<I', generated_bytes[index:index + 4])[0]:08X}"
                for index in range(0, 64, 4)
            ],
            "exact": generated_sha256 == ACTUAL_AEX_PLANE_SHA256,
        },
        "claim_boundary": {
            "sampler_exact": all(case["exact"] for case in cases),
            "noise_plane_generation_exact": generated_sha256 == ACTUAL_AEX_PLANE_SHA256,
            "mode3_rowdriver_exact": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "cases": len(cases), "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
