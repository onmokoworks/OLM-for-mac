#!/usr/bin/env python3
"""Fail-closed actual-AEX/production gate for the first PF16 exact branches."""

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
EXPECTED = "e9312eb08a382321671c3425c32fc028062edc0a5ff88eaeb659b990216faf93"
EXPECTED_GAIN_HALF = "6087391dc9fb2be2fda4eee72145c02dd6fb6ca2690228f5923b0bc12ae458ad"
EXPECTED_ANGLE45 = "07e05693b1fe8fc2516aa67f79b5700ff9a9c99a417e8e90228cd6d9bec5fa11"
EXPECTED_BACK_ANGLE45 = "2545772bed5562452123c265cc52abd8a7c3ff5c8bf9f920f72270447bec7ec7"
EXPECTED_FRONT2_BACK1_ANGLE45 = "07e05693b1fe8fc2516aa67f79b5700ff9a9c99a417e8e90228cd6d9bec5fa11"
EXPECTED_FRONT8_BACK1_ANGLE45 = "3b71a8e7c929b102d74142d778218db8ade316bdc2da60e9e204db5c9be7393c"
EXPECTED_BACK2_ANGLE45 = "097f9257b33a92a078826f24026a8afc294ef2db0f40f3e1966af0e910f40609"
EXPECTED_BACK8_ANGLE45 = "0a2059d3b76dcb7908bfeda0a14bdec7630414ac33c31f2284f76b1c08be85e6"
EXPECTED_NOISE1 = "967a2daed57313a0a3d9d7684ccce50e4e5ff6995914d05bb2764b5227bddcb8"
EXPECTED_NOISE2 = "0b91171a30163a15afcb1a47cf149536e2951671ae9d45f4bdc1e3ecc44a2582"
EXPECTED_NOISE_PLANE = "c0dd4dfdf3d35cf0f52c3a9eb75f51d5b0aaa61de3562e345d4213e7737243dc"
WIDTH = HEIGHT = 16
PACKED_BYTES = WIDTH * HEIGHT * 8
ROW_PADDING = 16


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    production_text = PRODUCTION.read_text(encoding="utf-8")
    for witness in ("olm_dblur_minimal_argb16", "info.front_strength == 2"):
        if witness not in production_text:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: production integration missing {witness}")
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf16_gate_") as name:
        temp = Path(name)
        source = temp / "source.png"
        Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278)).save(source)
        rgba = Image.open(source).convert("RGBA")
        packed_input = b"".join(
            struct.pack("<4H", p[3] * 128, p[0] * 128, p[1] * 128, p[2] * 128)
            for p in rgba.get_flattened_data()
        )
        library = temp / "libdblur_pf16.dylib"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(f"BLOCKED_FAIL_CLOSED: PF16 production core compile failed\n{build.stderr}")
        compiled = ctypes.CDLL(str(library))
        render = compiled.olm_dblur_minimal_argb16
        render.argtypes = [ctypes.POINTER(ctypes.c_uint16), ctypes.POINTER(ctypes.c_uint16),
                           ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_float, ctypes.c_float,
                           ctypes.c_float, ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_float]
        WordArray = ctypes.c_uint16 * (PACKED_BYTES // 2)
        source_words = WordArray.from_buffer_copy(packed_input)
        cases = []
        for strength, back, gain, angle, noise, noise_type, thickness, expected in (
                (1, 0, 1.0, 0, 0, 1, 10, EXPECTED), (2, 0, 1.0, 0, 0, 1, 10, EXPECTED),
                (2, 0, 0.5, 0, 0, 1, 10, EXPECTED_GAIN_HALF),
                (2, 0, 1.0, 45, 0, 1, 10, EXPECTED_ANGLE45),
                (0, 1, 1.0, 45, 0, 1, 10, EXPECTED_BACK_ANGLE45),
                (1, 1, 1.0, 45, 0, 1, 10, EXPECTED_BACK_ANGLE45),
                (2, 1, 1.0, 45, 0, 1, 10, EXPECTED_FRONT2_BACK1_ANGLE45),
                (8, 1, 1.0, 45, 0, 1, 10, EXPECTED_FRONT8_BACK1_ANGLE45),
                (0, 2, 1.0, 45, 0, 1, 10, EXPECTED_BACK2_ANGLE45),
                (0, 8, 1.0, 45, 0, 1, 10, EXPECTED_BACK8_ANGLE45),
                (8, 0, 1.0, 45, 100, 1, 3, EXPECTED_NOISE1),
                (8, 0, 1.0, 45, 100, 2, 3, EXPECTED_NOISE2)):
            report_path = temp / f"actual_{strength}_{back}_{gain}.json"
            actual_path = temp / f"actual_{strength}_{back}_{gain}.argb64"
            command = [sys.executable, str(FIXTURE), "--source", str(source), "--output", str(report_path),
                       "--host-output-raw", str(actual_path), "--bitdepth", "16", "--angle", str(angle),
                       "--brightness-gain", str(gain),
                       "--downsample-num", "1", "--downsample-den", "1", "--front-strength", str(strength),
                       "--size-variation", "0", "--front-alpha-fade", "0", "--front-sharp-tail", "0",
                       "--back-strength", str(back), "--back-alpha-fade", "0", "--back-sharp-tail", "0",
                       "--noise-variation", str(noise), "--noise-type", str(noise_type), "--seed", "1",
                       "--noise-offset", "0", "--thickness", str(thickness),
                       "--world-area", "0", "0", "16", "16",
                       "--row-padding", str(ROW_PADDING), "--no-detour-rotate", "--max-instructions", "20000000"]
            subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            actual = actual_path.read_bytes()
            output_words = WordArray()
            if render(source_words, output_words, WIDTH, HEIGHT, strength, back,
                      ctypes.c_float(gain), ctypes.c_float(angle), ctypes.c_float(noise),
                      noise_type, 1, 0, ctypes.c_float(thickness)) != 0:
                raise RuntimeError("BLOCKED_FAIL_CLOSED: typed production core rejected exact case")
            production = bytes(output_words)
            if (report["status"] != "ok" or report["callback_model_check"]["status"] != "pass" or
                    report["output"]["byte_count"] != PACKED_BYTES or len(actual) != PACKED_BYTES or
                    digest(actual) != expected or production != actual):
                raise RuntimeError(f"BLOCKED_FAIL_CLOSED: PF16 strength {strength} full-byte gate failed")
            if noise and report["execution"]["noise_plane_probe"]["sha256"] != EXPECTED_NOISE_PLANE:
                raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 Noise Type1 plane drifted")
            padded = bytearray((WIDTH * 8 + ROW_PADDING) * HEIGHT)
            padded[:] = b"\xEE" * len(padded)
            for y in range(HEIGHT):
                padded[y * (WIDTH * 8 + ROW_PADDING):y * (WIDTH * 8 + ROW_PADDING) + WIDTH * 8] = \
                    production[y * WIDTH * 8:(y + 1) * WIDTH * 8]
            if any(padded[y * (WIDTH * 8 + ROW_PADDING) + WIDTH * 8:(y + 1) * (WIDTH * 8 + ROW_PADDING)] != b"\xEE" * ROW_PADDING for y in range(HEIGHT)):
                raise RuntimeError("BLOCKED_FAIL_CLOSED: PF16 output padding changed")
            words = struct.unpack("<1024H", production)
            if angle == 0 and (words[239 * 4], words[255 * 4]) != (32639, 32639):
                raise RuntimeError("BLOCKED_FAIL_CLOSED: right-boundary alpha witnesses changed")
            cases.append({"front_strength": strength, "back_strength": back,
                          "brightness_gain": gain, "angle": angle,
                          "noise_variation": noise, "noise_type": noise_type,
                          "sha256": digest(actual), "bytes": len(actual)})
    print(json.dumps({"status": "pass", "format": "ARGB64", "cases": cases,
                      "padding": ROW_PADDING, "witness_alpha": [32639, 32639]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
