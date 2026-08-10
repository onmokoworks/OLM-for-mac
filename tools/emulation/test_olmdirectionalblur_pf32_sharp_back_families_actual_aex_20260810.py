#!/usr/bin/env python3
"""PF32 Front Sharp Tail and back-control bounded actual-AEX families."""
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
REPORT = ROOT / "refs/conformance/olmdirectionalblur_pf32_sharp_back_families_actual_aex_20260810.json"
NOTE = ROOT / "refs/conformance/olmdirectionalblur_pf32_sharp_back_families_actual_aex_20260810.md"
W = H = 16
ACTIVE = W * H * 16
PAD = 32
CASES = (
    ("front_sharp", 8, 0, 0, 0, 0),
    ("front_sharp", 8, 50, 0, 0, 0),
    ("front_sharp", 8, 100, 0, 0, 0),
    ("back_alpha_fade", 0, 0, 8, 0, 0),
    ("back_alpha_fade", 0, 0, 8, 50, 0),
    ("back_alpha_fade", 0, 0, 8, 100, 0),
    ("back_sharp", 0, 0, 8, 0, 50),
    ("back_sharp", 0, 0, 8, 0, 100),
    ("back_fade_sharp_cross", 0, 0, 8, 50, 50),
)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_dblur_pf32_sharp_back_") as raw:
        temp = Path(raw)
        source_path = temp / "source.png"
        image = Image.open(SOURCE).convert("RGBA").crop((472, 262, 488, 278))
        image.save(source_path)
        packed = b"".join(
            struct.pack("<4f", p[3] / 255.0, p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)
            for p in image.get_flattened_data()
        )
        library = temp / "libdblur_pf32_sharp_back.dylib"
        build = subprocess.run([
            "clang++", "-std=c++17", "-O2", "-fno-fast-math", "-ffp-contract=off",
            "-shared", "-fPIC", "core/dblur_frontonly.cpp", "core/dblur_rotate.cpp",
            "core/dblur_rowdriver.cpp", "core/dblur_field.cpp", "-o", str(library),
        ], cwd=ROOT, capture_output=True, text=True)
        if build.returncode:
            raise RuntimeError(build.stderr)
        render = ctypes.CDLL(str(library)).olm_dblur_full_argb32
        render.argtypes = [
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_float,
            ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_float,
            ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_int,
            ctypes.c_uint32, ctypes.c_int, ctypes.c_float,
            ctypes.POINTER(ctypes.c_float), ctypes.c_int,
        ]
        Floats = ctypes.c_float * (ACTIVE // 4)
        source = Floats.from_buffer_copy(packed)
        rows = []
        for index, (family, front, front_sharp, back, back_fade, back_sharp) in enumerate(CASES):
            meta_path = temp / f"case_{index}.json"
            raw_path = temp / f"case_{index}.argb128"
            command = [
                sys.executable, str(FIXTURE), "--source", str(source_path),
                "--output", str(meta_path), "--host-output-raw", str(raw_path),
                "--bitdepth", "32", "--angle", "45", "--brightness-gain", "1",
                "--downsample-num", "1", "--downsample-den", "1",
                "--front-strength", str(front), "--size-variation", "0",
                "--front-alpha-fade", "0", "--front-sharp-tail", str(front_sharp),
                "--back-strength", str(back), "--back-alpha-fade", str(back_fade),
                "--back-sharp-tail", str(back_sharp), "--noise-variation", "0",
                "--noise-type", "1", "--seed", "1", "--noise-offset", "0",
                "--thickness", "10", "--world-area", "0", "0", "16", "16",
                "--row-padding", str(PAD), "--no-detour-rotate", "--max-instructions", "20000000",
            ]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            if run.returncode:
                raise RuntimeError(f"{family} fixture failed: {run.stderr}")
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            actual = raw_path.read_bytes()
            output = Floats()
            result = render(
                source, output, W, H, front, 0, ctypes.c_float(front_sharp),
                back, back_fade, ctypes.c_float(back_sharp), ctypes.c_float(0),
                ctypes.c_float(45), ctypes.c_float(1), ctypes.c_float(0), 1, 1, 0,
                ctypes.c_float(10), None, 0,
            )
            callbacks = [item["callback"] for item in metadata["execution"]["iterate_calls"]]
            production = bytes(output)
            if (result != 0 or metadata["status"] != "ok" or
                    metadata["callback_model_check"]["status"] != "pass" or
                    callbacks != ["0x180006a20", "0x180006bd0"] or
                    len(actual) != ACTIVE or production != actual):
                mismatches = sum(a != b for a, b in zip(actual, production))
                raise RuntimeError(f"{family} index={index} differs ({mismatches} bytes)")
            rows.append({
                "family": family,
                "front_strength": front,
                "front_sharp_tail": front_sharp,
                "back_strength": back,
                "back_alpha_fade": back_fade,
                "back_sharp_tail": back_sharp,
                "byte_count": len(actual),
                "raw_sha256": hashlib.sha256(actual).hexdigest(),
                "callbacks": callbacks,
            })

    source_text = (ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp").read_text(encoding="utf-8")
    for token in ("sharp_back_family_exact", "olm_dblur_full_argb32"):
        if token not in source_text:
            raise RuntimeError(f"production token absent: {token}")
    report = {
        "schema_version": 1,
        "status": "exact_bounded_families",
        "plugin": "OLMDirectionalBlur",
        "depth": "PF32",
        "fixed_route": {
            "geometry": "16x16 padded ARGB128", "angle": 45, "brightness_gain": 1,
            "size_variation": 0, "noise_variation": 0, "render_scale": [1, 1],
        },
        "representatives": rows,
        "families": {
            "Front Sharp Tail": [0, 50, 100],
            "Back Alpha Fade": [0, 50, 100],
            "Back Sharp Tail": [0, 50, 100],
            "natural_cross": {"back_alpha_fade": 50, "back_sharp_tail": 50},
        },
        "admission": "Only the listed fixed-route representatives are admitted; neighboring values and cross-families remain fail-closed.",
        "not_proven": ["PF16", "other geometry", "other values", "front/back simultaneous blur", "size/noise/fade/tail combinations", "native AE export"],
    }
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    NOTE.write_text(
        "# OLMDirectionalBlur PF32 Sharp/Back families — 2026-08-10\n\n"
        "Actual Windows AEX and the production full PF32 worker are raw-byte exact on the pinned 16×16 route for "
        "Front Sharp Tail 0/50/100, Back Alpha Fade 0/50/100, Back Sharp Tail 0/50/100, and the natural Back Fade 50 × Back Sharp 50 cross. Admission is enumeration-bounded.\n\n"
        "Reproduction: `python3 tools/emulation/test_olmdirectionalblur_pf32_sharp_back_families_actual_aex_20260810.py`\n",
        encoding="utf-8",
    )
    print("PASS_OLMDIRECTIONALBLUR_PF32_SHARP_BACK_FAMILIES cases=9 raw=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
