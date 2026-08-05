#!/usr/bin/env python3
"""Gate the portable mode-1 back-only path against a pinned actual-AEX frame."""

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
AEX = ROOT / "plugins_2025/OLMDirectionalBlur.aex"
REPORT = ROOT / "refs/conformance/dblur_mode1_backonly_portable_20260805.json"
ACTUAL_AEX_ARGB_SHA256 = "1a25fefa174c7a69f1004ce42f116e9633967587bccc3278b0d2418d99084695"
ACTUAL_AEX_BACKFULL_ARGB_SHA256 = "6136b2c1c4c7ebe5d030e6f5933d393a991ced79607409f44a2f3ba2fff93b0e"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def rgba_to_argb(value: bytes) -> bytes:
    return bytes(
        channel
        for offset in range(0, len(value), 4)
        for channel in (value[offset + 3], value[offset], value[offset + 1], value[offset + 2])
    )


def build(directory: Path) -> Path:
    library = directory / "libdblur_mode1_back.dylib"
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
    with tempfile.TemporaryDirectory(prefix="dblur_mode1_backonly_") as raw:
        library = ctypes.CDLL(str(build(Path(raw))))
        function = library.olm_dblur_mode1_rgba8
        function.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.c_float, ctypes.c_float,
            ctypes.c_int, ctypes.c_int, ctypes.c_float,
            ctypes.c_int, ctypes.c_int, ctypes.c_float,
            ctypes.c_float, ctypes.c_float,
        ]
        input_buffer = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
        output_buffer = (ctypes.c_uint8 * len(source))()
        return_code = function(
            input_buffer, output_buffer, image.width, image.height,
            ctypes.c_float(0.0), ctypes.c_float(1.0),
            0, 0, ctypes.c_float(0.0),
            240, 0, ctypes.c_float(0.0),
            ctypes.c_float(0.0), ctypes.c_float(0.5),
        )
        output = bytes(output_buffer)
        full_output_buffer = (ctypes.c_uint8 * len(source))()
        full_return_code = function(
            input_buffer, full_output_buffer, image.width, image.height,
            ctypes.c_float(0.0), ctypes.c_float(1.0),
            0, 0, ctypes.c_float(0.0),
            240, 96, ctypes.c_float(25.0),
            ctypes.c_float(50.0), ctypes.c_float(0.5),
        )
        full_output = bytes(full_output_buffer)

    portable_hash = sha256(rgba_to_argb(output))
    portable_full_hash = sha256(rgba_to_argb(full_output))
    checks = {
        "return_code_zero": return_code == 0,
        "actual_aex_raw_exact": portable_hash == ACTUAL_AEX_ARGB_SHA256,
        "back_fade_tail_return_code_zero": full_return_code == 0,
        "back_fade_tail_actual_aex_raw_exact": portable_full_hash == ACTUAL_AEX_BACKFULL_ARGB_SHA256,
    }
    report = {
        "schema": 1,
        "kind": "dblur_mode1_backonly_portable_20260805",
        "status": "pass" if all(checks.values()) else "fail_closed",
        "scope": "portable mode-1 8bpc back-only raw callback",
        "provenance": {
            "aex": str(AEX.relative_to(ROOT)),
            "aex_sha256": sha256(AEX.read_bytes()),
            "source": str(SOURCE.relative_to(ROOT)),
            "source_sha256": sha256(SOURCE.read_bytes()),
            "oracle_command": "python3 tools/emulation/dblur_fullrender_host_fixture_20260711.py --front-strength 0 --front-alpha-fade 0 --front-sharp-tail 0 --back-strength 240 --back-alpha-fade 0 --back-sharp-tail 0 --size-variation 0 --noise-variation 0 --downsample-num 1 --downsample-den 2",
            "back_fade_tail_oracle_command": "python3 tools/emulation/dblur_fullrender_host_fixture_20260711.py --front-strength 0 --front-alpha-fade 0 --front-sharp-tail 0 --back-strength 240 --back-alpha-fade 96 --back-sharp-tail 25 --size-variation 50 --noise-variation 0 --downsample-num 1 --downsample-den 2",
        },
        "parameters": {
            "angle": 0,
            "brightness_gain": 1,
            "size_variation": 0,
            "front_strength_worker": 0,
            "back_strength_ui": 240,
            "back_strength_worker": 120,
            "render_scale": 0.5,
        },
        "back_fade_tail_parameters": {
            "angle": 0,
            "brightness_gain": 1,
            "size_variation": 50,
            "front_strength_worker": 0,
            "back_strength_ui": 240,
            "back_strength_worker": 120,
            "back_alpha_fade_ui": 96,
            "back_alpha_fade_worker": 48,
            "back_sharp_tail": 25,
            "component_divisor": 518530,
            "render_scale": 0.5,
        },
        "actual_aex_worker": {
            "mode": 1,
            "work_dimensions": [1104, 1104],
            "scatter_front": 0,
            "scatter_back": 120,
            "prepass_front": 0,
            "prepass_back": 0,
        },
        "actual_aex_raw_argb_sha256": ACTUAL_AEX_ARGB_SHA256,
        "portable_raw_argb_sha256": portable_hash,
        "back_fade_tail_actual_aex_raw_argb_sha256": ACTUAL_AEX_BACKFULL_ARGB_SHA256,
        "back_fade_tail_portable_raw_argb_sha256": portable_full_hash,
        "checks": checks,
        "claim_boundary": {
            "actual_aex_raw_exact": checks["actual_aex_raw_exact"],
            "windows_ae_pixel_exact": False,
            "remaining": "no corresponding Windows AE saved-frame reference for this synthetic back-only parameter set",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
