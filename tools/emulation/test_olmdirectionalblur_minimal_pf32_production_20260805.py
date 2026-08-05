#!/usr/bin/env python3
"""Argument-free actual-AEX to production PF32 minimal exact gate."""

from __future__ import annotations

import ctypes
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
PRODUCTION = ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp"
EXPECTED_SHA256 = "49cd0976b5e056824e447104f5737d8bdd9a3d98896d91645f042844eeda96ac"
EXPECTED_ANGLE45_SHA256 = "a53550f8e1ed323a96bc887a5d0e0249c09e6fb25fad20f3051315e9130e978f"
EXPECTED_BACK_ANGLE45_SHA256 = "132b84402145a1c426a04df92b66d3c865b23886c614c4029712bb86f5617b18"
EXPECTED_SIZE50_SHA256 = "a0f5e1deee28cce8362fcf078c62ef0bfb8ec23ed296f88089015de35bab6d25"
EXPECTED_NOISE1_SHA256 = "a2ebf3f1ea54fc0c44d3f8321f92e4f15b35733707691e7e6029d3083e735cf0"
EXPECTED_NOISE2_SHA256 = "ed3ac62ee2da22b7a2f68c4de7449db155a14ddcbe6e25e0f75eae05f04fd928"
EXPECTED_LAYER3_SHA256 = "f773f5cef5898a59f5a1bc68ff6cba5532b206c628b609d02749a7faa106d640"
EXPECTED_LAYER3_ROTATED_SHA256 = "94c1bddf9744a71c8c14be7616fef78311f0e762828bfb0f83675b88c769559f"
EXPECTED_GAIN_HALF_SHA256 = "f5892e697ea97eb4768bb2608bf4c69c7e3573722bc4a6ab6c4e9fa40e1b25aa"
EXPECTED_NOISE1_PLANE_SHA256 = "c0dd4dfdf3d35cf0f52c3a9eb75f51d5b0aaa61de3562e345d4213e7737243dc"
WIDTH = HEIGHT = 16
ACTIVE_BYTES = WIDTH * HEIGHT * 16
PADDING = 32


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    text = PRODUCTION.read_text(encoding="utf-8")
    if "olm_dblur_minimal_argb32" not in text or "info.front_strength == 2" not in text:
        raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 production exact dispatch is absent")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf32_exact_") as name:
        temp = Path(name)
        source = temp / "source.png"
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        image.save(source)
        packed_input = b"".join(
            struct.pack("<4f", p[3] / 255.0, p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)
            for p in image.get_flattened_data()
        )
        library = temp / "libdblur_pf32.dylib"
        compile_result = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if compile_result.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: production core compile failed\n{compile_result.stderr}")
        dylib = ctypes.CDLL(str(library))
        render = dylib.olm_dblur_minimal_argb32
        render.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
                           ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
                           ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_float,
                           ctypes.POINTER(ctypes.c_float), ctypes.c_int]
        Floats = ctypes.c_float * (ACTIVE_BYTES // 4)
        input_floats = Floats.from_buffer_copy(packed_input)
        layer_rowbytes = WIDTH * 16 + 48
        layer_padded = bytearray(layer_rowbytes * HEIGHT)
        for y in range(HEIGHT):
            layer_padded[y * layer_rowbytes:y * layer_rowbytes + WIDTH * 16] = \
                packed_input[y * WIDTH * 16:(y + 1) * WIDTH * 16]
        LayerBytes = ctypes.c_ubyte * len(layer_padded)
        layer_storage = LayerBytes.from_buffer_copy(layer_padded)
        layer_pointer = ctypes.cast(layer_storage, ctypes.POINTER(ctypes.c_float))
        cases = []
        for strength, back, size, angle, gain, noise, noise_type, thickness, expected_sha in (
                (1, 0, 0, 0, 1, 0, 1, 10, EXPECTED_SHA256), (2, 0, 0, 0, 1, 0, 1, 10, EXPECTED_SHA256),
                (2, 0, 0, 45, 1, 0, 1, 10, EXPECTED_ANGLE45_SHA256),
                (0, 1, 0, 45, 1, 0, 1, 10, EXPECTED_BACK_ANGLE45_SHA256),
                (8, 0, 50, 45, 1, 0, 1, 10, EXPECTED_SIZE50_SHA256),
                (8, 0, 0, 45, 1, 100, 1, 3, EXPECTED_NOISE1_SHA256),
                (8, 0, 0, 45, 1, 100, 2, 3, EXPECTED_NOISE2_SHA256),
                (8, 0, 0, 45, 1, 100, 3, 3, EXPECTED_LAYER3_SHA256),
                (8, 0, 0, 45, 0.5, 0, 1, 10, EXPECTED_GAIN_HALF_SHA256)):
            report_path = temp / f"actual_{strength}_{back}_{size}_{angle}.json"
            raw_path = temp / f"actual_{strength}_{back}_{size}_{angle}.argb128"
            command = [sys.executable, str(FIXTURE), "--source", str(source),
                       "--output", str(report_path), "--host-output-raw", str(raw_path),
                       "--bitdepth", "32", "--angle", str(angle), "--brightness-gain", str(gain),
                       "--downsample-num", "1",
                       "--downsample-den", "1", "--front-strength", str(strength),
                       "--size-variation", str(size), "--front-alpha-fade", "0",
                       "--front-sharp-tail", "0", "--back-strength", str(back),
                       "--back-alpha-fade", "0", "--back-sharp-tail", "0",
                       "--noise-variation", str(noise), "--noise-type", str(noise_type), "--seed", "1",
                       "--noise-offset", "0", "--thickness", str(thickness),
                       "--world-area", "0", "0", "16", "16",
                       "--row-padding", str(PADDING), "--no-detour-rotate",
                       "--max-instructions", "20000000"]
            if noise_type == 3:
                command.extend(["--noise-layer-row-padding", "48",
                                "--noise-layer-origin", "2", "1"])
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f"BLOCKED_FAIL_CLOSED: actual fixture failed\n{run.stderr}")
            report = json.loads(report_path.read_text(encoding="utf-8"))
            actual = raw_path.read_bytes()
            callbacks = [item["callback"] for item in report["execution"]["iterate_calls"]]
            if (report["status"] != "ok" or report["callback_model_check"]["status"] != "pass" or
                    callbacks != ["0x180006a20", "0x180006bd0"] or
                    report["world_layout"]["input_rowbytes"] != WIDTH * 16 + PADDING or
                    len(actual) != ACTIVE_BYTES or sha256(actual) != expected_sha):
                raise RuntimeError(f"BLOCKED_FAIL_CLOSED: PF32 actual strength {strength} angle {angle} contract drifted")
            if (noise and noise_type != 3 and
                    report["execution"]["noise_plane_probe"]["sha256"] != EXPECTED_NOISE1_PLANE_SHA256):
                raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 generated noise plane state drifted")
            if noise_type == 3 and (report["execution"]["noise_field_probe"]["sha256"] != EXPECTED_LAYER3_ROTATED_SHA256 or
                                    report["world_layout"]["noise_layer_rowbytes"] != layer_rowbytes or
                                    report["world_layout"]["noise_layer_extent_hint"] != [2, 1, 18, 17]):
                raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 Layer field/world contract drifted")
            output_floats = Floats()
            if render(input_floats, output_floats, WIDTH, HEIGHT, strength, back,
                      ctypes.c_float(size), ctypes.c_float(angle), ctypes.c_float(gain),
                      ctypes.c_float(noise), noise_type, 1, 0, ctypes.c_float(thickness),
                      layer_pointer if noise_type == 3 else None,
                      layer_rowbytes if noise_type == 3 else 0) != 0:
                raise RuntimeError("BLOCKED_FAIL_CLOSED: production PF32 core rejected fixture")
            production = bytes(output_floats)
            if production != actual:
                raise RuntimeError(f"BLOCKED_FAIL_CLOSED: PF32 strength {strength} angle {angle} raw words differ")
            rowbytes = WIDTH * 16 + PADDING
            padded = bytearray(b"\xEE" * (rowbytes * HEIGHT))
            for y in range(HEIGHT):
                padded[y * rowbytes:y * rowbytes + WIDTH * 16] = production[y * WIDTH * 16:(y + 1) * WIDTH * 16]
            if any(padded[y * rowbytes + WIDTH * 16:(y + 1) * rowbytes] != b"\xEE" * PADDING for y in range(HEIGHT)):
                raise RuntimeError("BLOCKED_FAIL_CLOSED: PF32 padding changed")
            cases.append({"front_strength": strength, "back_strength": back,
                          "size_variation": size, "angle": angle,
                          "noise_variation": noise, "noise_type": noise_type,
                          "bytes": len(actual), "sha256": sha256(actual)})
    print(json.dumps({"status": "pass", "format": "ARGB128", "callbacks": ["0x180006a20", "0x180006bd0"],
                      "rowbytes": WIDTH * 16 + PADDING, "padding": PADDING, "cases": cases}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
