#!/usr/bin/env python3
"""Gate the portable mode-1 case_0001 path against the actual-AEX frame."""

from __future__ import annotations

import ctypes
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
WINDOWS = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001.png"
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/dblur_mode1_case0001_portable_20260805.json"
ACTUAL_AEX_ARGB_SHA256 = "e6465cd9994e88abef18f6ca8f62c6d1c9b3ec100efff1d5de4ec16b3e4de1b9"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rgba_to_argb(value: bytes) -> bytes:
    return bytes(
        channel
        for offset in range(0, len(value), 4)
        for channel in (value[offset + 3], value[offset], value[offset + 1], value[offset + 2])
    )


def build(directory: Path) -> Path:
    library = directory / "libdblur_mode1.dylib"
    subprocess.run(
        [
            "c++", "-std=c++17", "-dynamiclib", "-O2", "-fno-fast-math",
            "-ffp-contract=off", str(ROOT / "core/dblur_frontonly.cpp"),
            str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
            str(ROOT / "core/dblur_field.cpp"),
            "-o", str(library),
        ],
        cwd=ROOT,
        check=True,
    )
    return library


def main() -> int:
    image = Image.open(SOURCE).convert("RGBA")
    source = image.tobytes()
    with tempfile.TemporaryDirectory(prefix="dblur_mode1_case0001_") as raw:
        library = ctypes.CDLL(str(build(Path(raw))))
        function = library.olm_dblur_frontonly_mode1_rgba8
        function.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_int,
            ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ]
        input_buffer = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
        output_buffer = (ctypes.c_uint8 * len(source))()
        return_code = function(
            input_buffer, output_buffer, image.width, image.height,
            ctypes.c_float(0.0), ctypes.c_float(1.0), 1690, 0,
            ctypes.c_float(92.0), ctypes.c_float(45.0), ctypes.c_float(0.5),
        )
        output = bytes(output_buffer)

    expected = Image.open(WINDOWS).convert("RGBA").tobytes()
    differences = [abs(actual - reference) for actual, reference in zip(output, expected)]
    differing_bytes = sum(value != 0 for value in differences)
    differing_pixels = sum(
        any(differences[offset:offset + 4]) for offset in range(0, len(differences), 4)
    )
    output_argb_sha256 = sha256(rgba_to_argb(output))
    checks = {
        "return_code_zero": return_code == 0,
        "actual_aex_raw_exact": output_argb_sha256 == ACTUAL_AEX_ARGB_SHA256,
        "windows_residual_bounded": differing_bytes == 1639 and differing_pixels == 1639 and max(differences) == 1,
    }
    report = {
        "schema": 1,
        "kind": "dblur_mode1_case0001_portable_20260805",
        "status": "pass" if all(checks.values()) else "fail_closed",
        "scope": "portable mode-1 8bpc case_0001 raw callback; Windows AE residual remains explicit",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX.read_bytes()),
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE.read_bytes()),
            "windows_reference": str(WINDOWS.relative_to(ROOT)),
            "windows_reference_sha256": sha256(WINDOWS.read_bytes()),
        },
        "parameters": {
            "angle": 0, "brightness_gain": 1, "size_variation": 92,
            "front_strength_ui": 1690, "front_strength_worker": 845,
            "front_alpha_fade": 0, "front_sharp_tail": 45,
            "render_scale": 0.5,
        },
        "actual_aex_raw_argb_sha256": ACTUAL_AEX_ARGB_SHA256,
        "portable_raw_argb_sha256": output_argb_sha256,
        "windows_decoded_rgba_sha256": sha256(expected),
        "portable_decoded_rgba_sha256": sha256(output),
        "windows_residual": {
            "differing_bytes": differing_bytes,
            "differing_pixels": differing_pixels,
            "max_absolute_byte_delta": max(differences),
        },
        "checks": checks,
        "claim_boundary": {
            "actual_aex_raw_exact": checks["actual_aex_raw_exact"],
            "windows_ae_pixel_exact": False,
            "remaining": "1639 one-byte Windows-AE-versus-emulated-callback deltas",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
