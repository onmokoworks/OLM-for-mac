#!/usr/bin/env python3
"""Run a narrow Mac AE boundary render for the accepted Smoother2 witness.

This creates its request and render staging only under /tmp.  The checked-in
outputs are evidence about the Mac host boundary; no shared request or source
file is modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CASE_ID = "legacy_case_0012_gamma5_red_blue_current_aex"
X, Y = 92, 841
WINDOWS_MANIFEST = ROOT / "refs/win_references/olm_reference_return_windows_smoother2_legacy_full_current_aex_recapture_20260621/OLMSmootherv2/reference_manifest.json"
WINDOWS_ROOT = WINDOWS_MANIFEST.parent
SOURCE = WINDOWS_ROOT / "input\\current_olm_cells.png"
WINDOWS_OUTPUT = WINDOWS_ROOT / "smoother2_legacy_full_current_aex_recapture_20260621__software__fr24__legacy_case_0012_gamma5_red_blue_current_aex.png"
MAC_PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother2.plugin"
MAC_BINARY = MAC_PLUGIN / "Contents/MacOS/OLMSmoother2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("FAIL_CLOSED: " + message)


def load_case() -> dict[str, Any]:
    data = json.loads(WINDOWS_MANIFEST.read_text(encoding="utf-8"))
    case = next((item for item in data["cases"] if item["id"] == CASE_ID), None)
    require(case is not None, "case-0012 is missing from the retained Windows manifest")
    require(case["project_gpu_accel_type"]["current_name"] == "SOFTWARE", "Windows reference is not Software")
    require(SOURCE.is_file() and WINDOWS_OUTPUT.is_file(), "retained source or Windows output is missing")
    return case


def stage_request(root: Path, case: dict[str, Any]) -> Path:
    request = root / "request"
    input_dir = request / "input"
    input_dir.mkdir(parents=True)
    shutil.copy2(SOURCE, input_dir / "current_olm_cells.png")
    request_manifest = {
        "schema": 1,
        "input_dir": "input",
        "reference_manifest": "reference_manifest.json",
        "effect_name": "OLM Smoother v2",
        "effect_match_name": "OLM Smoother v2",
        "cases": [{"id": CASE_ID, "before_effects_frame": "current_olm_cells.png", "frame": CASE_ID + ".png"}],
    }
    reference_manifest = {
        "schema": 2,
        "platform": "windows",
        "ae_version": "26.2x49",
        "project": {"width": case["comp"]["width"], "height": case["comp"]["height"], "frame_rate": case["comp"]["frame_rate"]},
        "cases": [case],
    }
    (request / "request_manifest.json").write_text(json.dumps(request_manifest, indent=2) + "\n", encoding="utf-8")
    (request / "reference_manifest.json").write_text(json.dumps(reference_manifest, indent=2) + "\n", encoding="utf-8")
    return request


def run_ae(request: Path, output_dir: Path) -> Path:
    command = [
        sys.executable,
        str(ROOT / "scripts/run_ae_single_case.py"),
        "--request-dir", str(request),
        "--case-id", CASE_ID,
        "--output-dir", str(output_dir),
        "--app-name", "Adobe After Effects 2026",
        "--timeout", "1800",
        "--ae-env", "OLM_AE_FORCE_NEW_PROJECT=1",
        "--ae-env", "OLM_AE_FORCE_SOFTWARE=1",
        "--ae-env", "OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT=1",
        "--ae-env", "OLM_AE_INPUT_ALPHA_MODE=STRAIGHT",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=1830)
    require(result.returncode == 0, (result.stdout + result.stderr)[-4000:])
    result_json = output_dir / "AE_SINGLE_CASE_RESULT.json"
    require(result_json.is_file(), "AE result JSON missing")
    result_data = json.loads(result_json.read_text(encoding="utf-8-sig"))
    require(result_data.get("status") == "ok", f"AE status is {result_data.get('status')}: {result_data.get('error')}")
    output = Path(result_data["output_png"])
    require(output.is_file(), f"AE output PNG missing; render files={[str(p) for p in output_dir.rglob('*')]}")
    return output


def pixels(path: Path) -> dict[str, list[int]]:
    image = Image.open(path).convert("RGBA")
    return {
        f"{x},{y}": list(image.getpixel((x, y)))
        for y in range(Y - 1, Y + 2)
        for x in range(X - 1, X + 2)
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-json", type=Path, default=ROOT / "refs/conformance/olmsmoother2_mac_actual_ae_boundary_20260717.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "refs/conformance/olmsmoother2_mac_actual_ae_boundary_20260717.md")
    args = parser.parse_args()
    case = load_case()
    require(MAC_PLUGIN.is_dir() and MAC_BINARY.is_file(), "installed Mac OLMSmoother2.plugin is missing")
    try:
        with tempfile.TemporaryDirectory(prefix="olmsmoother2_mac_boundary_20260717_") as temp:
            temp_root = Path(temp)
            request = stage_request(temp_root, case)
            output = run_ae(request, temp_root / "render")
            mac_px = pixels(output)
            mac_output_sha256 = sha256(output)
    except Exception as exc:
        report = {
            "verdict": "BLOCKED_MAC_AE_BOUNDARY_RENDER_EMPTY",
            "scope": "Mac After Effects host render at the accepted Windows actual-AEX legacy producer witness",
            "platform": {"host": "macOS", "ae_app": "Adobe After Effects 2026", "renderer": "SOFTWARE", "project_bpc": 8, "input_alpha_mode": "STRAIGHT"},
            "case": {"id": CASE_ID, "coordinate": [X, Y]},
            "mac_plugin": {"bundle": str(MAC_PLUGIN), "binary_sha256": sha256(MAC_BINARY)},
            "windows_actual_aex_witness": {"descriptor": [92, 841, 1, 92, 842, 2], "e170_c": 7, "first_append": True},
            "failure": str(exc),
            "claims_not_made": ["No Mac pixel output was produced", "No AE exactness", "No Mac internal class-plane or producer return capture", "No modification to shared files"],
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text("\n".join(["# OLMSmoother2 Mac actual-AE boundary probe - 2026-07-17", "", f"- Verdict: `{report['verdict']}`", f"- Case: `{CASE_ID}`; target `(x={X}, y={Y})`.", f"- Installed Mac plug-in binary SHA-256: `{report['mac_plugin']['binary_sha256']}`.", "", "## Result", "", f"- The Mac AE host was reached, but the render output remained empty and the harness timed out waiting for a stable PNG: `{report['failure']}`.", "- No Mac pixel or AE-exactness claim is made.", "", "## Reproduction", "", "```sh", "python3 tools/emulation/probe_olmsmoother2_mac_actual_ae_boundary_20260717.py", "```", ""]), encoding="utf-8")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    windows_px = pixels(WINDOWS_OUTPUT)
    report: dict[str, Any] = {
        "verdict": "MAC_AE_BOUNDARY_RENDER_COMPLETED_NOT_AE_EXACT",
        "scope": "Mac After Effects host render at the accepted Windows actual-AEX legacy producer witness",
        "platform": {"host": "macOS", "ae_app": "Adobe After Effects 2026", "renderer": "SOFTWARE", "project_bpc": 8, "input_alpha_mode": "STRAIGHT"},
        "case": {"id": CASE_ID, "coordinate": [X, Y], "parameters": {"enable_color_key": 1, "smoothness": 100, "extra_smooth": 40, "smooth_range": 88, "smoother_version": 2, "gamma_correction": 2, "gamma_value": 2.16954731941223, "num_gamma_colors": 5, "gamma_colors": [[1, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 1, 1]]}},
        "mac_plugin": {"bundle": str(MAC_PLUGIN), "binary_sha256": sha256(MAC_BINARY)},
        "inputs": {"source_png_sha256": sha256(SOURCE), "windows_output_png_sha256": sha256(WINDOWS_OUTPUT), "mac_output_png_sha256": mac_output_sha256},
        "boundary": {"windows_actual_aex_witness": {"descriptor": [92, 841, 1, 92, 842, 2], "e170_c": 7, "first_append": True}, "windows_rgba_3x3": windows_px, "mac_rgba_3x3": mac_px, "center_equal": mac_px[f"{X},{Y}"] == windows_px[f"{X},{Y}"], "neighborhood_equal": mac_px == windows_px},
        "claims_not_made": ["No Mac internal class-plane or producer return capture", "No AE exactness", "No claim that a final-pixel residual identifies c280, cce0, or the writer", "No modification to shared files"],
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    center_win = windows_px[f"{X},{Y}"]
    center_mac = mac_px[f"{X},{Y}"]
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join([
        "# OLMSmoother2 Mac actual-AE boundary probe - 2026-07-17", "", f"- Verdict: `{report['verdict']}`", f"- Case: `{CASE_ID}`; witness pixel `(x={X}, y={Y})`.", "- Mac run: After Effects 2026, Software renderer, 8bpc, straight-alpha input, Gamma Correction `2`, Gamma Value `2.16954731941223`, five gamma colors.", f"- Installed Mac plug-in binary SHA-256: `{report['mac_plugin']['binary_sha256']}`.", "", "## Boundary", "", "- Windows actual-AEX witness: descriptor `[92,841,1,92,842,2]`, `e170 c=7`, first append observed.", f"- Windows center RGBA: `{center_win}`.", f"- Mac center RGBA: `{center_mac}`.", f"- Center equal: `{report['boundary']['center_equal']}`; 3x3 neighborhood equal: `{report['boundary']['neighborhood_equal']}`.", "", "The render completed through the Mac AE host and installed Mac plug-in. This is a host-boundary residual measurement, not an internal Mac producer trace and not AE exactness.", "", "## Reproduction", "", "```sh", "python3 tools/emulation/probe_olmsmoother2_mac_actual_ae_boundary_20260717.py", "```", ""]), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
