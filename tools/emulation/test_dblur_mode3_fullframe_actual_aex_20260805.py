#!/usr/bin/env python3
"""Full-frame actual-AEX versus portable mode-3 rowdriver differential."""

from __future__ import annotations

import hashlib
import ctypes
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png"
FIXTURE = ROOT / "tools/emulation/dblur_fullrender_host_fixture_20260711.py"
REPORT = ROOT / "refs/conformance/dblur_mode3_fullframe_actual_aex_20260805.json"
EXPECTED_RAW_SHA256 = {
    1: "b7edf1fe473004a79933d44e82cdf5c1b8b17201e3062ec093d5c6fe9a8cc882",
    2: "f83594c779d3aafb8e0a24ccc06fb7cdc482248861753af693f77ada6b4e674e",
}
EXPECTED_NOISE_SHA256 = "15d8e87d57380c0296ec8fe5ca84e6db0d0fb1e06cd1a16a6e57975c3c3929de"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(source: Path, output: Path, raw: Path, detour: bool, noise_type: int) -> dict:
    command = [
        "python3", str(FIXTURE), "--source", str(source),
        "--front-strength", "48", "--front-alpha-fade", "0",
        "--front-sharp-tail", "0", "--back-strength", "0",
        "--size-variation", "0", "--noise-variation", "100",
        "--noise-type", str(noise_type), "--seed", "7", "--noise-offset", "13",
        "--thickness", "10", "--downsample-num", "1",
        "--downsample-den", "2", "--max-instructions", "400000000",
        "--output", str(output), "--host-output-raw", str(raw),
    ]
    if not detour:
        command.append("--no-detour-rowdriver")
    subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(output.read_text(encoding="utf-8"))


def run_portable_core(directory: Path, source: bytes, noise_type: int) -> tuple[int, bytes]:
    library_path = directory / "dblur_mode3.dylib"
    subprocess.run(
        ["c++", "-std=c++17", "-dynamiclib", "-O2", "-fno-fast-math",
         "-ffp-contract=off", str(ROOT / "core/dblur_frontonly.cpp"),
         str(ROOT / "core/dblur_rotate.cpp"), str(ROOT / "core/dblur_rowdriver.cpp"),
         str(ROOT / "core/dblur_field.cpp"),
         "-o", str(library_path)],
        cwd=ROOT,
        check=True,
    )
    library = ctypes.CDLL(str(library_path))
    function = library.olm_dblur_noise_mode3_rgba8
    function.argtypes = [
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float,
        ctypes.c_int, ctypes.c_int, ctypes.c_float,
        ctypes.c_int, ctypes.c_int, ctypes.c_float,
        ctypes.c_float, ctypes.c_float, ctypes.c_int, ctypes.c_uint32,
        ctypes.c_int, ctypes.c_float, ctypes.c_float,
    ]
    input_buffer = (ctypes.c_uint8 * len(source)).from_buffer_copy(source)
    output_buffer = (ctypes.c_uint8 * len(source))()
    result = function(
        input_buffer, output_buffer, 64, 64,
        ctypes.c_float(0.0), ctypes.c_float(1.0),
        48, 0, ctypes.c_float(0.0), 0, 0, ctypes.c_float(0.0),
        ctypes.c_float(0.0), ctypes.c_float(100.0), noise_type, 7, 13,
        ctypes.c_float(10.0), ctypes.c_float(0.5),
    )
    return result, bytes(output_buffer)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="dblur_mode3_fullframe_") as name:
        directory = Path(name)
        source = directory / "source64.png"
        with Image.open(SOURCE) as image:
            left = 462
            top = 137
            cropped = image.convert("RGBA").crop((left, top, left + 64, top + 64))
            cropped.save(source)
            source_rgba = cropped.tobytes()
        runs = {}
        for noise_type in (1, 2):
            actual_raw = directory / f"actual_type{noise_type}.argb"
            detour_raw = directory / f"detour_type{noise_type}.argb"
            actual = run(source, directory / f"actual_type{noise_type}.json",
                         actual_raw, False, noise_type)
            detour = run(source, directory / f"detour_type{noise_type}.json",
                         detour_raw, True, noise_type)
            portable_return, portable_rgba = run_portable_core(
                directory, source_rgba, noise_type)
            portable_argb = bytes(
                channel
                for offset in range(0, len(portable_rgba), 4)
                for channel in (portable_rgba[offset + 3], portable_rgba[offset],
                                portable_rgba[offset + 1], portable_rgba[offset + 2])
            )
            runs[noise_type] = {
                "actual": actual,
                "detour": detour,
                "actual_bytes": actual_raw.read_bytes(),
                "detour_bytes": detour_raw.read_bytes(),
                "actual_hash": sha256(actual_raw),
                "detour_hash": sha256(detour_raw),
                "portable_return": portable_return,
                "portable_argb": portable_argb,
                "portable_hash": hashlib.sha256(portable_argb).hexdigest(),
            }

    checks = {}
    case_reports = {}
    for noise_type, run_data in runs.items():
        actual = run_data["actual"]
        detour = run_data["detour"]
        actual_noise = actual["execution"]["noise_plane_probe"]
        detour_noise = detour["execution"]["noise_plane_probe"]
        prefix = "smooth" if noise_type == 1 else "block"
        checks.update({
            f"{prefix}_actual_complete": actual["status"] == "ok" and actual["output"]["complete"],
            f"{prefix}_detour_complete": detour["status"] == "ok" and detour["output"]["complete"],
            f"{prefix}_raw_byte_exact": run_data["actual_bytes"] == run_data["detour_bytes"],
            f"{prefix}_pinned_raw_hash": run_data["actual_hash"] == run_data["detour_hash"] == EXPECTED_RAW_SHA256[noise_type],
            f"{prefix}_noise_plane_exact": actual_noise["sha256"] == detour_noise["sha256"] == EXPECTED_NOISE_SHA256,
            f"{prefix}_mode3_worker": detour["execution"]["rowdriver_state"]["mode"] == 3,
            f"{prefix}_portable_core_return_zero": run_data["portable_return"] == 0,
            f"{prefix}_portable_core_raw_exact": run_data["portable_argb"] == run_data["actual_bytes"],
        })
        case_reports[prefix] = {
            "noise_type": noise_type,
            "actual_aex_raw_sha256": run_data["actual_hash"],
            "portable_detour_raw_sha256": run_data["detour_hash"],
            "portable_core_raw_sha256": run_data["portable_hash"],
        }
    checks["smooth_and_block_distinct"] = (
        runs[1]["actual_bytes"] != runs[2]["actual_bytes"]
    )
    report = {
        "schema": 1,
        "kind": "dblur_mode3_fullframe_actual_aex_20260805",
        "status": "pass" if all(checks.values()) else "fail_closed",
        "scope": "64x64 witness crop, 8bpc mode 3 Smooth/Block, actual-AEX versus portable",
        "source": {
            "canonical": str(SOURCE.relative_to(ROOT)),
            "construction": "decoded RGBA crop (462,137)..(526,201)",
        },
        "parameters": {
            "front_strength_ui": 48,
            "front_strength_worker": 24,
            "noise_variation": 100,
            "noise_types": {"smooth": 1, "block": 2},
            "seed": 7,
            "noise_offset_ui": 13,
            "noise_offset_worker": 0.3611111044883728,
            "thickness_ui": 10,
            "noise_cell_size_worker": 5,
            "downsample": [1, 2],
        },
        "cases": case_reports,
        "noise_plane_sha256": EXPECTED_NOISE_SHA256,
        "work_dimensions": runs[1]["detour"]["execution"]["rowdriver_state"]["dimensions"],
        "noise_plane_dimensions": runs[1]["actual"]["execution"]["noise_plane_probe"]["dimensions"],
        "checks": checks,
        "claim_boundary": {
            "actual_aex_raw_exact": all(
                checks[f"{prefix}_raw_byte_exact"] and
                checks[f"{prefix}_portable_core_raw_exact"]
                for prefix in ("smooth", "block")
            ),
            "windows_ae_pixel_exact": False,
            "mac_ae_pixel_exact": False,
            "mode2_layer_field": False,
            "full_size_mode3_raw_exact": False,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": checks, "report": str(REPORT.relative_to(ROOT))}))
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
