#!/usr/bin/env python3
"""Synthetic smoke for compare_ae26_3_float_exr_acceptance.py."""

from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPARE = ROOT / "refs/scripts/compare_ae26_3_float_exr_acceptance.py"


def attr(name: str, typ: str, value: bytes) -> bytes:
    return name.encode() + b"\0" + typ.encode() + b"\0" + struct.pack("<I", len(value)) + value


def make_exr(path: Path, delta: int = 0) -> None:
    channels = ["A", "B", "G", "R"]
    entries = b"".join(name.encode() + b"\0" + struct.pack("<iB3xii", 2, 0, 1, 1) for name in channels) + b"\0"
    header = b"".join([
        attr("channels", "chlist", entries), attr("compression", "compression", b"\0"),
        attr("dataWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)), attr("displayWindow", "box2i", struct.pack("<4i", 0, 0, 1, 0)),
        attr("lineOrder", "lineOrder", b"\0"), attr("pixelAspectRatio", "float", struct.pack("<f", 1.0)),
        attr("screenWindowCenter", "v2f", struct.pack("<2f", 0.0, 0.0)), attr("screenWindowWidth", "float", struct.pack("<f", 1.0)),
    ]) + b"\0"
    header_blob = struct.pack("<II", 20000630, 2) + header
    payload = struct.pack("<8I", 0x3f800000, 0x3f000000, 0x3e800000, 0x00000000, 0x3f800000, 0x3f000000, 0x3e800000, delta)
    chunk = struct.pack("<iI", 0, len(payload)) + payload
    offset = len(header_blob) + 8
    path.write_bytes(header_blob + struct.pack("<Q", offset) + chunk)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_ae26_3_float_acceptance_") as tmp_name:
        root = Path(tmp_name)
        for name, delta in (("source.exr", 0), ("windows_control.exr", 0), ("mac_control.exr", 0), ("windows_effect.exr", 9), ("mac_effect.exr", 9)):
            make_exr(root / name, delta)
        aex_hash = "a" * 64
        mac_hash = "b" * 64
        package = {
            "kind": "ae26_3_float_exr_acceptance_package", "ae_version": "26.3",
            "bit_depth": "32bpc", "bits_per_channel": 32, "linear_light": False,
            "windows_host": {"os": "windows", "renderer": "SOFTWARE", "ae_build": "26.3-test"},
            "mac_host": {"os": "macos", "renderer": "SOFTWARE", "ae_build": "26.3-test"},
            "cases": [{"id": "olmcolorkey__case_0001", "plugin": "OLMColorKey", "dimensions": [2, 1], "linear_light": False,
                "case_contract_sha256": "d" * 64,
                "windows_aex_binding": {"sha256": aex_hash}, "mac_plugin_binding": {"sha256": mac_hash},
                "source_input": {"path": "source.exr", "sha256": digest(root / "source.exr")},
                "windows_no_effect_control": {"path": "windows_control.exr", "sha256": digest(root / "windows_control.exr"), "effect_enabled": False},
                "mac_no_effect_control": {"path": "mac_control.exr", "sha256": digest(root / "mac_control.exr"), "effect_enabled": False},
                "windows_effect_output": {"path": "windows_effect.exr", "sha256": digest(root / "windows_effect.exr"), "loaded_aex_sha256": aex_hash},
                "mac_effect_output": {"path": "mac_effect.exr", "sha256": digest(root / "mac_effect.exr"), "loaded_plugin_sha256": mac_hash}}],
        }
        package_path = root / "package.json"
        package_path.write_text(json.dumps(package), encoding="utf-8")
        proc = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root), "--json", "--require-exact"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert proc.returncode == 0, proc.stdout
        result = json.loads(proc.stdout)
        case = result["cases"][0]
        assert case["host_input_conversion"]["mismatched_samples"] == 0
        assert case["mac_effect_delta"]["mismatched_samples"] > 0
        assert case["cross_host_effect_output"]["mismatched_samples"] == 0
        assert case["cross_host_status"] == "raw-float-bits-exact"
        wrong_linear = json.loads(package_path.read_text())
        wrong_linear["linear_light"] = True
        wrong_linear["cases"][0]["linear_light"] = True
        package_path.write_text(json.dumps(wrong_linear), encoding="utf-8")
        rejected_linear = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert rejected_linear.returncode != 0 and "linear_light must be false" in rejected_linear.stdout, rejected_linear.stdout
        package_path.write_text(json.dumps(package), encoding="utf-8")
        broken = json.loads(package_path.read_text())
        del broken["cases"][0]["mac_no_effect_control"]
        package_path.write_text(json.dumps(broken), encoding="utf-8")
        rejected = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert rejected.returncode != 0 and "mac_no_effect_control" in rejected.stdout, rejected.stdout
        package_path.write_text(json.dumps(package), encoding="utf-8")
        missing_windows = json.loads(package_path.read_text())
        del missing_windows["cases"][0]["windows_effect_output"]
        package_path.write_text(json.dumps(missing_windows), encoding="utf-8")
        rejected_windows = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert rejected_windows.returncode != 0 and "windows_effect_output" in rejected_windows.stdout, rejected_windows.stdout
        package_path.write_text(json.dumps(package), encoding="utf-8")
        bad_mac_hash = json.loads(package_path.read_text())
        bad_mac_hash["cases"][0]["mac_effect_output"]["loaded_plugin_sha256"] = "c" * 64
        package_path.write_text(json.dumps(bad_mac_hash), encoding="utf-8")
        rejected_mac_hash = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert rejected_mac_hash.returncode != 0 and "loaded Mac plugin hash" in rejected_mac_hash.stdout, rejected_mac_hash.stdout
        package_path.write_text(json.dumps(package), encoding="utf-8")
        make_exr(root / "mac_effect.exr", 10)
        nonexact = json.loads(package_path.read_text())
        nonexact["cases"][0]["mac_effect_output"]["sha256"] = digest(root / "mac_effect.exr")
        package_path.write_text(json.dumps(nonexact), encoding="utf-8")
        rejected_nonexact = subprocess.run([sys.executable, str(COMPARE), str(package_path), "--artifact-root", str(root), "--require-exact"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert rejected_nonexact.returncode != 0 and "not attributable raw-float-bit exact" in rejected_nonexact.stdout, rejected_nonexact.stdout
    print("[OK] AE 26.3 FLOAT EXR comparator requires cross-host outputs, binary hashes, linear-light off, and no-effect control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
