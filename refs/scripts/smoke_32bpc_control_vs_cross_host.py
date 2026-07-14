#!/usr/bin/env python3
"""Regression smoke for the two independent FLOAT EXR exactness gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPARE = ROOT / "refs/scripts/compare_ae26_3_float_exr_acceptance.py"
sys.path.insert(0, str(ROOT / "refs/scripts"))
from smoke_verify_32bpc_float_return import make_exr


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package(root: Path, mac_control: Path, mac_effect: Path, win_effect: Path) -> Path:
    files = {
        "source_input": root / "source.exr",
        "windows_no_effect_control": root / "windows-control.exr",
        "mac_no_effect_control": mac_control,
        "windows_effect_output": win_effect,
        "mac_effect_output": mac_effect,
    }
    artifacts = {key: {"path": path.name, "sha256": digest(path)} for key, path in files.items()}
    artifacts["windows_no_effect_control"]["effect_enabled"] = False
    artifacts["mac_no_effect_control"]["effect_enabled"] = False
    artifacts["windows_effect_output"]["loaded_aex_sha256"] = "1" * 64
    artifacts["mac_effect_output"]["loaded_plugin_sha256"] = "2" * 64
    case = {
        "id": "synthetic__case_0001",
        "plugin": "Synthetic",
        "dimensions": [2, 2],
        "linear_light": False,
        "case_contract_sha256": "3" * 64,
        "windows_aex_binding": {"sha256": "1" * 64},
        "mac_plugin_binding": {"sha256": "2" * 64},
        **artifacts,
    }
    path = root / "package.json"
    path.write_text(json.dumps({
        "kind": "ae26_3_float_exr_acceptance_package",
        "ae_version": "26.3",
        "bit_depth": "32bpc",
        "bits_per_channel": 32,
        "linear_light": False,
        "windows_host": {"os": "windows", "renderer": "SOFTWARE", "ae_build": "26.3x87"},
        "mac_host": {"os": "macos", "renderer": "SOFTWARE", "ae_build": "26.3x87"},
        "cases": [case],
    }), encoding="utf-8")
    return path


def run(path: Path, require_exact: bool = False) -> tuple[int, dict]:
    command = [sys.executable, str(COMPARE), str(path), "--artifact-root", str(path.parent), "--json"]
    if require_exact:
        command.append("--require-exact")
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if require_exact:
        return result.returncode, {}
    return result.returncode, json.loads(result.stdout)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="32bpc_control_vs_cross_host_") as tmp:
        root = Path(tmp)
        for name in ("source.exr", "windows-control.exr", "mac-control.exr", "windows-effect.exr", "mac-effect.exr"):
            make_exr(root / name)
        effect = bytearray((root / "windows-effect.exr").read_bytes())
        effect[-1] ^= 1
        (root / "windows-effect.exr").write_bytes(effect)
        (root / "mac-effect.exr").write_bytes(effect)

        exact_package = package(root, root / "mac-control.exr", root / "mac-effect.exr", root / "windows-effect.exr")
        code, report = run(exact_package)
        strict_code, _ = run(exact_package, require_exact=True)
        case = report["cases"][0]
        assert code == 0 and strict_code == 0
        assert case["attribution"] == "eligible"
        assert case["cross_host_status"] == "raw-float-bits-exact"
        assert case["host_input_conversion"]["mismatched_samples"] == 0
        assert case["cross_host_effect_output"]["mismatched_samples"] == 0
        assert case["mac_effect_delta"]["mismatched_samples"] == 1

        changed = bytearray((root / "mac-control.exr").read_bytes())
        changed[-1] ^= 1
        (root / "mac-control.exr").write_bytes(changed)
        blocked_package = package(root, root / "mac-control.exr", root / "windows-effect.exr", root / "windows-effect.exr")
        code, report = run(blocked_package)
        case = report["cases"][0]
        strict_code, _ = run(blocked_package, require_exact=True)
        assert code == 0 and strict_code != 0
        assert case["attribution"] == "blocked-by-host-input-conversion"
        assert case["cross_host_status"] == "not-exact-or-not-attributable"
        assert case["host_input_conversion"]["mismatched_samples"] == 1
        assert case["cross_host_effect_output"]["mismatched_samples"] == 0

    print("[OK] Mac control parity and cross-host AE exactness stay separate and fail closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
