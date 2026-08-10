#!/usr/bin/env python3
"""Bounded PF32 Size Variation x Type-1 Noise Variation differential."""
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
REPORT = ROOT / "refs/conformance/olmdirectionalblur_pf32_size_noise_type1_combination_actual_aex_20260810.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_pf32_size_noise_type1_combination_actual_aex_20260810.md"
WIDTH = HEIGHT = 16
ACTIVE_BYTES = WIDTH * HEIGHT * 16
PADDING = 32
CASES = ((0.0, 25.0), (25.0, 25.0), (25.0, 100.0), (100.0, 25.0), (100.0, 100.0))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf32_size_noise1_") as raw:
        temp = Path(raw)
        source_path = temp / "source.png"
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        image.save(source_path)
        packed = b"".join(
            struct.pack("<4f", p[3] / 255.0, p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)
            for p in image.get_flattened_data()
        )
        library = temp / "libdblur_pf32_size_noise1.dylib"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        render = ctypes.CDLL(str(library)).olm_dblur_minimal_argb32
        render.argtypes = [
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
            ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_float,
            ctypes.POINTER(ctypes.c_float), ctypes.c_int,
        ]
        Floats = ctypes.c_float * (ACTIVE_BYTES // 4)
        source = Floats.from_buffer_copy(packed)
        rows = []
        for size, noise in CASES:
            stem = f"size_{size:g}_noise_{noise:g}"
            meta_path = temp / f"{stem}.json"
            raw_path = temp / f"{stem}.argb128"
            command = [
                sys.executable, str(FIXTURE), "--source", str(source_path),
                "--output", str(meta_path), "--host-output-raw", str(raw_path),
                "--bitdepth", "32", "--angle", "45", "--brightness-gain", "1",
                "--downsample-num", "1", "--downsample-den", "1",
                "--front-strength", "8", "--size-variation", str(int(size)),
                "--front-alpha-fade", "0", "--front-sharp-tail", "0",
                "--back-strength", "0", "--back-alpha-fade", "0",
                "--back-sharp-tail", "0", "--noise-variation", str(int(noise)),
                "--noise-type", "1", "--seed", "1", "--noise-offset", "0",
                "--thickness", "3", "--world-area", "0", "0", "16", "16",
                "--row-padding", str(PADDING), "--no-detour-rotate",
                "--max-instructions", "20000000",
            ]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(run.stderr)
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            actual = raw_path.read_bytes()
            output = Floats()
            result = render(
                source, output, WIDTH, HEIGHT, 8, 0,
                ctypes.c_float(size), ctypes.c_float(45.0), ctypes.c_float(1.0),
                ctypes.c_float(noise), 1, 1, 0, ctypes.c_float(3.0), None, 0,
            )
            callbacks = [item["callback"] for item in metadata["execution"]["iterate_calls"]]
            production = bytes(output)
            if (result != 0 or metadata["status"] != "ok" or
                    metadata["callback_model_check"]["status"] != "pass" or
                    callbacks != ["0x180006a20", "0x180006bd0"] or
                    len(actual) != ACTIVE_BYTES or production != actual):
                mismatch = sum(a != b for a, b in zip(actual, production))
                raise RuntimeError(f"size={size:g} noise={noise:g} differs ({mismatch} bytes)")
            rows.append({
                "size_variation_percent": size,
                "noise_variation_percent": noise,
                "noise_type": 1,
                "byte_count": len(actual),
                "raw_sha256": hashlib.sha256(actual).hexdigest(),
                "callbacks": callbacks,
            })

    source_text = (ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp").read_text(encoding="utf-8")
    if "size_noise_type1_combination_exact" not in source_text:
        raise RuntimeError("production bounded Size x Noise predicate is absent")
    report = {
        "schema_version": 1,
        "status": "exact_bounded_combination",
        "plugin": "OLMDirectionalBlur",
        "depth": "PF32",
        "combination": "Size Variation x Noise Variation (Type 1)",
        "fixed_route": {
            "geometry": "16x16 padded ARGB128",
            "angle": 45,
            "brightness_gain": 1,
            "front_strength": 8,
            "back_strength": 0,
            "fade_tail": 0,
            "noise_type": 1,
            "seed": 1,
            "noise_offset": 0,
            "thickness": 3,
            "render_scale": [1, 1],
        },
        "representatives": rows,
        "admitted_rule": "The fixed 16x16 PF32 Type-1 route admits Noise Variation 25/100 with Size Variation 0/25/100; simultaneous nonzero evidence is the 2x2 Size 25/100 by Noise 25/100 cross.",
        "not_proven": [
            "other geometry or pixel depth",
            "Noise Type 2/3 combinations",
            "other Size or Noise Variation values",
            "combinations with fade, sharp tail, back blur/fade, other angle/strength, seed/offset/thickness, or downsample",
            "native After Effects render/export",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur PF32 Size × Type-1 Noise — 2026-08-10\n\n"
        "On the pinned 16×16 PF32 route, actual Windows AEX and the production worker are raw-byte exact for "
        "the Noise 25 control and Size 25/100 crossed with Noise 25/100. Admission remains limited to the five "
        "witnessed tuples and fixed Type-1 noise state.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_size_noise_type1_combination_actual_aex_20260810.py`\n",
        encoding="utf-8",
    )
    print("PASS_OLMDIRECTIONALBLUR_PF32_SIZE_NOISE1_COMBINATION cases=5 raw=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
