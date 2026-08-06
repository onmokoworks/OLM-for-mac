#!/usr/bin/env python3
"""Bounded actual-AEX/production gate for PF16 Noise Type 3 Layer."""

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
WIDTH = HEIGHT = 16
ACTIVE = WIDTH * HEIGHT * 8
INPUT_PADDING = 16
LAYER_PADDING = 24
OUTPUT_PADDING = 16
EXPECTED_OUTPUT_SHA256 = "d536acfe42daac18c06ab91b6a78eebec15b68c9cc42540a1592575868391f8a"
EXPECTED_FIELD_SHA256 = "7ba4c0d31dd81cf34b7593862c85f400f0a526e56588d5624f0f566b745f1072"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf16_layer3_") as name:
        temp = Path(name)
        source = temp / "source.png"
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        image.save(source)
        packed = b"".join(struct.pack("<4H", p[3] * 128, p[0] * 128, p[1] * 128, p[2] * 128)
                          for p in image.get_flattened_data())
        report_path = temp / "actual.json"
        actual_path = temp / "actual.argb64"
        command = [sys.executable, str(FIXTURE), "--source", str(source),
                   "--output", str(report_path), "--host-output-raw", str(actual_path),
                   "--bitdepth", "16", "--angle", "45", "--brightness-gain", "1",
                   "--downsample-num", "1", "--downsample-den", "1",
                   "--front-strength", "8", "--size-variation", "0",
                   "--front-alpha-fade", "0", "--front-sharp-tail", "0",
                   "--back-strength", "0", "--back-alpha-fade", "0",
                   "--back-sharp-tail", "0", "--noise-variation", "100",
                   "--noise-type", "3", "--seed", "1", "--noise-offset", "0",
                   "--thickness", "3", "--world-area", "0", "0", "16", "16",
                   "--row-padding", str(INPUT_PADDING), "--noise-layer-row-padding", str(LAYER_PADDING),
                   "--no-detour-rotate", "--max-instructions", "20000000"]
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if run.returncode:
            raise RuntimeError(f"actual AEX fixture failed\n{run.stderr}")
        report = json.loads(report_path.read_text())
        actual = actual_path.read_bytes()
        layer_rowbytes = WIDTH * 8 + LAYER_PADDING
        if (report["status"] != "ok" or report["callback_model_check"]["status"] != "pass" or
                len(actual) != ACTIVE or sha(actual) != EXPECTED_OUTPUT_SHA256 or
                report["execution"]["noise_field_probe"]["sha256"] != EXPECTED_FIELD_SHA256 or
                report["world_layout"]["noise_layer_rowbytes"] != layer_rowbytes):
            raise RuntimeError("actual AEX PF16 Layer contract drifted")

        library = temp / "libdblur_pf16_layer3.dylib"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"production compile failed\n{build.stderr}")
        render = ctypes.CDLL(str(library)).olm_dblur_minimal_layer_argb16
        render.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16),
                           ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_float, ctypes.c_float, ctypes.c_float,
                           ctypes.POINTER(ctypes.c_uint16), ctypes.c_int]
        Words = ctypes.c_uint16 * (ACTIVE // 2)
        input_words = Words.from_buffer_copy(packed)
        layer_storage = bytearray(b"\xA5" * (layer_rowbytes * HEIGHT))
        for y in range(HEIGHT):
            layer_storage[y * layer_rowbytes:y * layer_rowbytes + WIDTH * 8] = \
                packed[y * WIDTH * 8:(y + 1) * WIDTH * 8]
        LayerBytes = ctypes.c_ubyte * len(layer_storage)
        layer_bytes = LayerBytes.from_buffer_copy(layer_storage)
        output_words = Words()
        result = render(input_words, output_words, WIDTH, HEIGHT, 8, 0, 1.0, 45.0, 100.0,
                        ctypes.cast(layer_bytes, ctypes.POINTER(ctypes.c_uint16)), layer_rowbytes)
        production = bytes(output_words)
        if result != 0 or production != actual:
            raise RuntimeError(f"PF16 Noise Type3 differs: actual={sha(actual)} production={sha(production)}")
        padded = bytearray(b"\xEE" * ((WIDTH * 8 + OUTPUT_PADDING) * HEIGHT))
        for y in range(HEIGHT):
            padded[y * (WIDTH * 8 + OUTPUT_PADDING):y * (WIDTH * 8 + OUTPUT_PADDING) + WIDTH * 8] = \
                production[y * WIDTH * 8:(y + 1) * WIDTH * 8]
        if any(padded[y * (WIDTH * 8 + OUTPUT_PADDING) + WIDTH * 8:(y + 1) * (WIDTH * 8 + OUTPUT_PADDING)] !=
               b"\xEE" * OUTPUT_PADDING for y in range(HEIGHT)):
            raise RuntimeError("output padding changed")
        print(json.dumps({"status": "pass", "format": "ARGB64", "dimensions": [16, 16],
                          "noise_type": 3, "noise_variation": 100, "front_strength": 8,
                          "angle": 45, "actual_sha256": sha(actual),
                          "field_sha256": report["execution"]["noise_field_probe"]["sha256"],
                          "input_rowbytes": WIDTH * 8 + INPUT_PADDING,
                          "layer_rowbytes": layer_rowbytes, "output_padding": OUTPUT_PADDING}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
