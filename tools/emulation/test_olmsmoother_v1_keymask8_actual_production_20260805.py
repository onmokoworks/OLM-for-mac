#!/usr/bin/env python3
"""Compare the PF8 Color Key callback with the pinned Windows AEX."""

import ctypes
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/emulation"))
from aex_loader import AexLoader


AEX = ROOT / "plugins_2025/OLMSmoother.aex"
AEX_SHA256 = "6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82"
ENTRY = 0x1800026E0
HARNESS = ROOT / "tools/emulation/olmsmoother_v1_mainkernel8_production_harness_20260805.cpp"
OUT = ROOT / "refs/conformance/olmsmoother_v1_pf8_keymask_actual_production_20260805.json"
KEY = (202, 187, 230)
VECTORS = (
    ("transparent_exact", (0, 202, 187, 230), (17, 18, 19, 20)),
    ("opaque_exact_rgb", (255, 202, 187, 230), (21, 22, 23, 24)),
    ("alpha_one_exact_rgb", (1, 202, 187, 230), (25, 26, 27, 28)),
    ("red_mismatch", (0, 201, 187, 230), (29, 30, 31, 32)),
    ("green_mismatch", (0, 202, 188, 230), (33, 34, 35, 36)),
    ("blue_mismatch", (0, 202, 187, 231), (37, 38, 39, 40)),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert sha256(AEX) == AEX_SHA256
    loader = AexLoader(str(AEX), verbose=False, fast=True)
    state = loader.host_alloc(0x40, align=16)
    input_pixel = loader.host_alloc(4, align=4)
    output_pixel = loader.host_alloc(4, align=4)
    loader.write_bytes(state, b"\0" * 0x40)
    loader.write_bytes(state + 1, bytes((0, *KEY)))

    with tempfile.TemporaryDirectory(prefix="olmsmoother-v1-keymask8-") as temp_name:
        library_path = Path(temp_name) / "libolmsmoother_keymask8.dylib"
        subprocess.run([
            "clang++", "-std=c++17", "-O2", "-shared", "-fPIC",
            "-I" + str(ROOT / "cli/OLMSmoother/shim"), str(HARNESS),
            "-o", str(library_path),
        ], cwd=ROOT, check=True, capture_output=True, text=True)
        library = ctypes.CDLL(str(library_path))
        production = library.olmsmoother_run_keymask8_production
        production.argtypes = [ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8,
                               ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8)]

        results = []
        mismatches = []
        for name, input_argb, preseed_argb in VECTORS:
            loader.write_bytes(input_pixel, bytes(input_argb))
            loader.write_bytes(output_pixel, bytes(preseed_argb))
            loader.call_function(ENTRY, [state, 0, 0, input_pixel, output_pixel],
                                 max_instructions=1000)
            actual = loader.read_bytes(output_pixel, 4)

            production_input = (ctypes.c_uint8 * 4)(*input_argb)
            production_output = (ctypes.c_uint8 * 4)(*preseed_argb)
            production(*KEY, production_input, production_output)
            portable = bytes(production_output)
            item = {
                "name": name,
                "input_argb": bytes(input_argb).hex(),
                "preseed_argb": bytes(preseed_argb).hex(),
                "actual_argb": actual.hex(),
                "production_argb": portable.hex(),
            }
            results.append(item)
            if actual != portable:
                mismatches.append(item)

    report = {
        "schema_version": 1,
        "status": "exact" if not mismatches else "fail",
        "scope": "OLMSmoother v1 PF8 Color Key callback at Windows RVA 0x26e0",
        "actual_aex_sha256": AEX_SHA256,
        "key_rgb": list(KEY),
        "vectors": results,
        "mismatches": mismatches,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    assert report["status"] == "exact"


if __name__ == "__main__":
    main()
