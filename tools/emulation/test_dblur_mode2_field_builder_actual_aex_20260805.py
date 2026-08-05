#!/usr/bin/env python3
"""Natural actual-AEX differential for DirectionalBlur's 8-bpc Layer field."""

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
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
REPORT = ROOT / "refs/conformance/dblur_mode2_field_builder_actual_aex_20260805.json"
EXPECTED = {
    "source_field": "4454dcba4f929451fba2f76912810c6326bf3d50c878c38f9bd84ccec6256663",
    "rotated_field": "896271211a16fd87192f5c57cafc6b0dbc30c6f739b5234fbc2605b7eee41a7b",
    "output": "c41939b0ddc6faa3aba839c22029f4a9ce73d5ea15a3438418264e20fee64a76",
}


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def run_fixture(directory: Path, source: Path, detour: bool, stem: str) -> dict:
    report_path = directory / f"{stem}.json"
    command = [
        "python3", str(FIXTURE), "--source", str(source),
        "--front-strength", "16", "--noise-variation", "100",
        "--noise-type", "3", "--downsample-num", "1",
        "--downsample-den", "1", "--max-instructions", "250000000",
        "--output", str(report_path),
        "--host-output-raw", str(directory / f"{stem}.argb"),
        "--field-source-raw", str(directory / f"{stem}.source.f32"),
        "--field-rotated-raw", str(directory / f"{stem}.rotated.f32"),
    ]
    if not detour:
        command.append("--no-detour-rowdriver")
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(report_path.read_text(encoding="utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dblur_mode2_field_builder_") as name:
        directory = Path(name)
        cropped_path = directory / "source.png"
        with Image.open(SOURCE) as image:
            cropped = image.convert("RGBA").crop((450, 150, 514, 214))
            cropped.save(cropped_path)
            rgba = cropped.tobytes()
        argb = bytes(
            channel
            for offset in range(0, len(rgba), 4)
            for channel in (rgba[offset + 3], rgba[offset], rgba[offset + 1], rgba[offset + 2])
        )
        actual = run_fixture(directory, cropped_path, False, "actual")
        detour = run_fixture(directory, cropped_path, True, "detour")
        actual_source = (directory / "actual.source.f32").read_bytes()
        actual_rotated = (directory / "actual.rotated.f32").read_bytes()
        actual_output = (directory / "actual.argb").read_bytes()
        detour_output = (directory / "detour.argb").read_bytes()

        library_path = directory / "libdblur_field.dylib"
        subprocess.run(
            ["c++", "-std=c++17", "-O2", "-fno-fast-math",
             "-ffp-contract=off", "-dynamiclib",
             str(ROOT / "core/dblur_field.cpp"), str(ROOT / "core/dblur_rotate.cpp"),
             str(ROOT / "core/dblur_rowdriver.cpp"),
             str(ROOT / "core/dblur_frontonly.cpp"),
             "-o", str(library_path)], cwd=ROOT, check=True,
        )
        library = ctypes.CDLL(str(library_path))
        build_field = library.olm_dblur_layer_field_argb8
        build_field.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int]
        build_field.restype = ctypes.c_float
        rotate = library.olm_dblur_rotate_scalar_f32
        rotate.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                           ctypes.c_int, ctypes.c_float]
        width, height = actual["execution"]["noise_field_source_probe"]["dimensions"]
        placement = actual["execution"]["noise_field_source_probe"]["placement"]
        source_buffer = (ctypes.c_uint8 * len(argb)).from_buffer_copy(argb)
        field_buffer = (ctypes.c_float * (width * height))()
        maximum = build_field(
            source_buffer, 64, 64, 64 * 4, 0, 0, field_buffer,
            width, height, placement["col0"], placement["row0"],
            64, 64, 0, 0,
        )
        portable_source = ctypes.string_at(ctypes.addressof(field_buffer), len(actual_source))
        rotated_buffer = (ctypes.c_float * (width * height))()
        internal_angle = actual["execution"]["param_context"]["angle_radians"]
        rotate(field_buffer, rotated_buffer, width, height, ctypes.c_float(internal_angle))
        portable_rotated = ctypes.string_at(ctypes.addressof(rotated_buffer), len(actual_rotated))
        render = library.olm_dblur_layer_mode2_rgba8
        render.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                           ctypes.c_int, ctypes.c_float, ctypes.c_float,
                           ctypes.c_int, ctypes.c_int, ctypes.c_float,
                           ctypes.c_int, ctypes.c_int, ctypes.c_float,
                           ctypes.c_float, ctypes.c_float, ctypes.c_void_p,
                           ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, ctypes.c_float]
        input_buffer = (ctypes.c_uint8 * len(rgba)).from_buffer_copy(rgba)
        output_buffer = (ctypes.c_uint8 * len(rgba))()
        render_return = render(
            input_buffer, output_buffer, 64, 64, ctypes.c_float(0.0),
            ctypes.c_float(1.0), 16, 0, ctypes.c_float(45.0), 0, 0,
            ctypes.c_float(0.0), ctypes.c_float(92.0), ctypes.c_float(100.0),
            source_buffer, 64, 64, 64 * 4, 0, 0, 0, 0,
            ctypes.c_float(1.0),
        )
        portable_rgba = bytes(output_buffer)
        portable_output = bytes(
            channel
            for offset in range(0, len(portable_rgba), 4)
            for channel in (portable_rgba[offset + 3], portable_rgba[offset],
                            portable_rgba[offset + 1], portable_rgba[offset + 2])
        )

    checks = {
        "actual_complete": actual["status"] == "ok" and actual["output"]["complete"],
        "detour_complete": detour["status"] == "ok" and detour["output"]["complete"],
        "source_field_byte_exact": portable_source == actual_source,
        "rotated_field_byte_exact": portable_rotated == actual_rotated,
        "rowdriver_detour_output_byte_exact": detour_output == actual_output,
        "portable_core_return_zero": render_return == 0,
        "portable_core_output_byte_exact": portable_output == actual_output,
        "source_field_pinned": digest(actual_source) == EXPECTED["source_field"],
        "rotated_field_pinned": digest(actual_rotated) == EXPECTED["rotated_field"],
        "output_pinned": digest(actual_output) == EXPECTED["output"],
        "maximum_exact": maximum == actual["execution"]["noise_field_source_probe"]["maximum"],
        "nonzero_field": maximum > 0.0,
    }
    report = {
        "schema": 1,
        "kind": "dblur_mode2_field_builder_actual_aex_20260805",
        "status": "pass" if all(checks.values()) else "fail_closed",
        "scope": "64x64 decoded RGBA crop (450,150)..(514,214), 8-bpc Layer mode",
        "work_dimensions": [width, height],
        "placement": placement,
        "internal_angle": internal_angle,
        "hashes": {
            "actual_aex_source_field": digest(actual_source),
            "portable_source_field": digest(portable_source),
            "actual_aex_rotated_field": digest(actual_rotated),
            "portable_rotated_field": digest(portable_rotated),
            "actual_aex_output": digest(actual_output),
            "portable_rowdriver_detour_output": digest(detour_output),
            "portable_core_output": digest(portable_output),
        },
        "checks": checks,
        "claim_boundary": {
            "actual_aex_field_builder_byte_exact": checks["source_field_byte_exact"],
            "actual_aex_scalar_rotate_byte_exact": checks["rotated_field_byte_exact"],
            "actual_aex_full_render_detour_byte_exact": checks["rowdriver_detour_output_byte_exact"],
            "actual_aex_portable_core_byte_exact": checks["portable_core_output_byte_exact"],
            "mac_ae_pixel_exact": False,
            "windows_ae_pixel_exact": False,
            "16_32_bpc": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks,
                      "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
