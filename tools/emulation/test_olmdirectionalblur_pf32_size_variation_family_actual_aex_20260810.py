#!/usr/bin/env python3
"""PF32 Size Variation representative family: actual AEX vs production core."""

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
REPORT = ROOT / "refs/conformance/olmdirectionalblur_pf32_size_variation_family_actual_aex_20260810.json"
WIDTH = HEIGHT = 16
ACTIVE_BYTES = WIDTH * HEIGHT * 16
PADDING = 32
CASES = (0.0, 25.0, 50.0, 100.0)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf32_size_family_") as raw:
        temp = Path(raw)
        source = temp / "source.png"
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        image.save(source)
        packed = b"".join(
            struct.pack("<4f", p[3] / 255.0, p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)
            for p in image.get_flattened_data()
        )

        library = temp / "libdblur_pf32_size_family.dylib"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        dylib = ctypes.CDLL(str(library))
        render = dylib.olm_dblur_minimal_argb32
        render.argtypes = [
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
            ctypes.c_int, ctypes.c_uint32, ctypes.c_int, ctypes.c_float,
            ctypes.POINTER(ctypes.c_float), ctypes.c_int,
        ]
        Floats = ctypes.c_float * (ACTIVE_BYTES // 4)
        source_floats = Floats.from_buffer_copy(packed)
        rows = []
        for size in CASES:
            actual_report = temp / f"actual_size_{size:g}.json"
            actual_raw = temp / f"actual_size_{size:g}.argb128"
            command = [
                sys.executable, str(FIXTURE), "--source", str(source),
                "--output", str(actual_report), "--host-output-raw", str(actual_raw),
                "--bitdepth", "32", "--angle", "45", "--brightness-gain", "1",
                "--downsample-num", "1", "--downsample-den", "1",
                "--front-strength", "8", "--size-variation", str(int(size)),
                "--front-alpha-fade", "0", "--front-sharp-tail", "0",
                "--back-strength", "0", "--back-alpha-fade", "0",
                "--back-sharp-tail", "0", "--noise-variation", "0",
                "--noise-type", "1", "--seed", "1", "--noise-offset", "0",
                "--thickness", "10", "--world-area", "0", "0", "16", "16",
                "--row-padding", str(PADDING), "--no-detour-rotate",
                "--max-instructions", "20000000",
            ]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(run.stderr)
            metadata = json.loads(actual_report.read_text(encoding="utf-8"))
            actual = actual_raw.read_bytes()
            output = Floats()
            result = render(
                source_floats, output, WIDTH, HEIGHT, 8, 0,
                ctypes.c_float(size), ctypes.c_float(45.0), ctypes.c_float(1.0),
                ctypes.c_float(0.0), 1, 1, 0, ctypes.c_float(10.0), None, 0,
            )
            production = bytes(output)
            callbacks = [item["callback"] for item in metadata["execution"]["iterate_calls"]]
            if (result != 0 or metadata["status"] != "ok" or
                    metadata["callback_model_check"]["status"] != "pass" or
                    callbacks != ["0x180006a20", "0x180006bd0"] or
                    len(actual) != ACTIVE_BYTES or production != actual):
                raise RuntimeError(f"PF32 Size Variation {size:g} differs")
            rows.append({
                "size_variation_percent": size,
                "raw_sha256": sha(actual),
                "byte_count": len(actual),
                "callbacks": callbacks,
            })

    source_text = (ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp").read_text(encoding="utf-8")
    if not all(token in source_text for token in (
        "info.size_variation >= 0.0", "info.size_variation <= 100.0",
        "olm_dblur_minimal_argb32",
    )):
        raise RuntimeError("production PF32 Size Variation family predicate is absent")
    report = {
        "schema_version": 1,
        "status": "exact_representative_family",
        "plugin": "OLMDirectionalBlur",
        "depth": "PF32",
        "family": "Size Variation public slider 0..100%",
        "fixed_route": {
            "geometry": "16x16 padded ARGB128",
            "angle": 45,
            "brightness_gain": 1,
            "front_strength": 8,
            "back_strength": 0,
            "fade_tail_noise": 0,
            "render_scale": [1, 1],
        },
        "representatives": rows,
        "basis": "0 and 100 are public endpoints, 25 exercises a non-half interior value, and 50 preserves the previous exact gate. All execute the actual AEX typed callbacks and production worker with raw-byte equality.",
        "production_source": "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "not_proven": [
            "PF16 Size Variation",
            "Size Variation combined with noise, fade, tail, back blur, other angle/strength, or downsample",
            "native After Effects render/export",
            "values outside the public 0..100 slider range",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_OLMDIRECTIONALBLUR_PF32_SIZE_VARIATION_FAMILY sizes=0,25,50,100 raw=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
