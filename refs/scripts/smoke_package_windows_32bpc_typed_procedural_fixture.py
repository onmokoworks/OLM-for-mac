#!/usr/bin/env python3
"""Smoke the Windows 32bpc typed-procedural fixture package."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "package_windows_32bpc_typed_procedural_fixture_20260713.py"
PACKAGE_STEM = "olm_windows_32bpc_typed_procedural_fixture_20260713"


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_exr(path: Path, delta: int = 0, width: int = 64, height: int = 64) -> None:
    channels = ["A", "B", "G", "R"]
    entries = b"".join(
        name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) for name in channels
    ) + b"\0"
    header = b"".join(
        [
            attr("channels", "chlist", entries),
            attr("compression", "compression", b"\0"),
            attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, width - 1, height - 1)),
            attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, width - 1, height - 1)),
            attr("lineOrder", "lineOrder", b"\0"),
            attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
            attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)),
            attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
        ]
    ) + b"\0"
    header_blob = struct.pack("<II", 20000630, 2) + header
    base_pixel = (0x3F800000, 0x3F000000, 0x3E800000, 0x00000000)
    rows = []
    offsets = []
    row_payload_size = width * len(channels) * 4
    cursor = len(header_blob) + height * 8
    for y in range(height):
        values = list(base_pixel * width)
        if y == height - 1:
            values[-1] = delta
        payload = struct.pack("<" + "I" * len(values), *values)
        rows.append(struct.pack("<iI", y, len(payload)) + payload)
        offsets.append(cursor)
        cursor += 8 + len(payload)
    table = struct.pack("<" + "Q" * len(offsets), *offsets)
    path.write_bytes(header_blob + table + b"".join(rows))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_record(root: Path, platform: str, delta: int = 0) -> Path:
    cases = []
    fixture_contract = {
        "manifest_kind": "olm_32bpc_typed_procedural_fixture",
        "project_bits_per_channel": 32,
        "working_space": "None",
        "linear_blending": False,
        "dimensions": [64, 64],
        "frame": 0,
        "source_policy": "AE-generated solids only; no footage imported",
        "render_policy": "same comp, only branch enabled state changes",
        "source_layers": [
            {"name": "solid_background", "kind": "solid", "bounds": [0, 0, 64, 64], "rgb": [0, 0, 0], "alpha": 1.0},
            {"name": "rect_integer_a25", "kind": "solid", "bounds": [4, 4, 20, 16], "rgb": [1, 0, 0], "alpha": 0.25},
            {"name": "rect_integer_a50", "kind": "solid", "bounds": [28, 4, 20, 16], "rgb": [0, 1, 0], "alpha": 0.5},
            {"name": "rect_integer_a75", "kind": "solid", "bounds": [4, 28, 20, 16], "rgb": [0, 0, 1], "alpha": 0.75},
            {"name": "rect_integer_a100", "kind": "solid", "bounds": [28, 28, 20, 16], "rgb": [1, 1, 1], "alpha": 1.0},
        ],
        "output_names": {
            "no_effect": "effect_no_effect_00000.exr",
            "effect_on": "effect_effect_on_00000.exr",
        },
    }
    fixture_sha = "f" * 64
    for case_id, effect in (
        ("olmcolorkey_typed_procedural_64x64", "OLM Color Key"),
        ("olmtoondilate_typed_procedural_64x64", "OLM Toon Dilate"),
    ):
        case_root = root / case_id
        case_root.mkdir(parents=True, exist_ok=True)
        no_effect = case_root / "effect_no_effect_00000.exr"
        effect_on = case_root / "effect_effect_on_00000.exr"
        make_exr(no_effect, 0)
        make_exr(effect_on, delta)
        cases.append(
            {
                "id": case_id,
                "effect": effect,
                "plugin": {"name": effect.replace(" ", "") + (".aex" if platform == "windows" else ".plugin"), "path": "", "sha256": "a" * 64},
                "fixture_contract": fixture_contract,
                "outputs": {
                    "no_effect": {"path": f"{case_id}/effect_no_effect_00000.exr", "sha256": digest(no_effect)},
                    "effect_on": {"path": f"{case_id}/effect_effect_on_00000.exr", "sha256": digest(effect_on)},
                },
            }
        )
    record = {
        "kind": "olm_32bpc_typed_procedural_render_record",
        "schema": 1,
        "platform": platform,
        "record_role": "reference" if platform == "macos" else "return",
        "required_ae_major_minor": "26.3",
        "ae_version": "26.3-test",
        "output_template": "OLM EXR 32 Float",
        "fixture_jsx_sha256": fixture_sha,
        "cases": cases,
    }
    path = root / ("reference_manifest.json" if platform == "macos" else "return_manifest.json")
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="typed_proc_pkg_smoke_") as tmp_name:
        tmp = Path(tmp_name)
        support = tmp / "support"
        archive = tmp / "package.zip"
        subprocess.run(
            [sys.executable, str(SCRIPT), "--support-dir", str(support), "--output", str(archive)],
            cwd=ROOT,
            check=True,
        )
        assert archive.is_file() and zipfile.is_zipfile(archive)
        expected = {
            PACKAGE_STEM + "/README.md",
            PACKAGE_STEM + "/CONTRACT.md",
            PACKAGE_STEM + "/manifest.json",
            PACKAGE_STEM + "/RETURN_MANIFEST_TEMPLATE.json",
            PACKAGE_STEM + "/MAC_REFERENCE_RECORD_TEMPLATE.json",
            PACKAGE_STEM + "/compare_cross_host_typed_procedural_fixture.py",
            PACKAGE_STEM + "/run_windows_typed_procedural_fixture_20260713.ps1",
            PACKAGE_STEM + "/fixture/ae_generate_32bpc_typed_procedural_fixture.jsx",
            PACKAGE_STEM + "/fixture/compare_float_exr.py",
            PACKAGE_STEM + "/fixture/verify_32bpc_float_return.py",
        }
        with zipfile.ZipFile(archive) as zipped:
            names = set(zipped.namelist())
            assert expected <= names
            runner = zipped.read(PACKAGE_STEM + "/run_windows_typed_procedural_fixture_20260713.ps1").decode("utf-8")
            for token in (
                "afterfx_running",
                "Stop-AfterFX",
                "fixture_result.json",
                "plugin_hash_mismatch",
                "OLM Color Key",
                "OLM Toon Dilate",
                "effect_no_effect_00000.exr",
                "effect_effect_on_00000.exr",
            ):
                assert token in runner
        manifest = json.loads((support / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["fixture_contract"]["dimensions"] == [64, 64]
        assert manifest["fixture_jsx"]["path"] == "fixture/ae_generate_32bpc_typed_procedural_fixture.jsx"
        compare_script = support / "compare_cross_host_typed_procedural_fixture.py"

        mac_root = tmp / "mac_record"
        win_root = tmp / "win_record"
        mac_root.mkdir()
        win_root.mkdir()
        build_record(mac_root, "macos", delta=9)
        build_record(win_root, "windows", delta=9)
        proc = subprocess.run(
            [sys.executable, str(compare_script), str(mac_root), str(win_root), "--json"],
            cwd=support,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        result = json.loads(proc.stdout)
        assert result["status"] == "pass"
        assert all(row["no_effect_cross_host"]["mismatched_values"] == 0 for row in result["cases"])
        assert all(row["effect_on_cross_host"]["mismatched_values"] == 0 for row in result["cases"])

        broken_root = tmp / "win_broken"
        broken_root.mkdir()
        build_record(broken_root, "windows", delta=10)
        rejected = subprocess.run(
            [sys.executable, str(compare_script), str(mac_root), str(broken_root)],
            cwd=support,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert rejected.returncode != 0
        assert "effect_on is not raw-float-bit exact across hosts" in rejected.stdout

        same_platform = subprocess.run(
            [sys.executable, str(compare_script), str(win_root), str(broken_root)],
            cwd=support,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert same_platform.returncode != 0
        assert "two different platforms" in same_platform.stdout

    print("[OK] Windows 32bpc typed procedural package smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
