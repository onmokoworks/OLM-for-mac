#!/usr/bin/env python3
"""Static, no-launch readiness audit for the current OLMBlur Mac AE runner."""

from __future__ import annotations

import hashlib
import json
import plistlib
import subprocess
from pathlib import Path

import run_olmblur_case0001_pf32_current_mac_20260805 as runner

ROOT = Path(__file__).resolve().parents[1]
AE_APP = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app")
AE_INFO = AE_APP / "Contents/Info.plist"
DELEGATE_SHA256 = "085aca8b5ae9304f148135e9a4fcb20e4c457173815e1601a1948d25c235cb08"
PROJECT_RUNNER = ROOT / "scripts/run_olmblur_32bpc_mac_validation_20260715.py"
PROJECT_RUNNER_SHA256 = "1828610901bf61673b4b8a8779116ee1d53c1bf5a6eb22505169ac97bb3032b8"
RUNNER_SHA256 = "0260d9d68283aeaf3a4d8d2a1297d5c4722e7b96b09eedeeb51045f00e731e7e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    plugin = runner.DEFAULT_PLUGIN
    binary = plugin / "Contents/MacOS/OLMBlur"
    plist = plistlib.loads(AE_INFO.read_bytes()) if AE_INFO.is_file() else {}
    lipo = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True,
                          text=True, check=False) if binary.is_file() else None
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(plugin)],
                          capture_output=True, text=True, check=False) if plugin.is_dir() else None
    authoritative_artifacts = runner.locate_authoritative_artifacts()
    checks = {
        "ae_app_present": AE_APP.is_dir(),
        "ae_version": plist.get("CFBundleShortVersionString") == "26.3.0" and
                      plist.get("CFBundleVersion") == "26.3.0.87",
        "runner_hash": sha256(Path(runner.__file__)) == RUNNER_SHA256,
        "delegate_hash": sha256(runner.DELEGATE) == DELEGATE_SHA256,
        "project_jsx_runner_hash": sha256(PROJECT_RUNNER) == PROJECT_RUNNER_SHA256,
        "installed_binary_hash": binary.is_file() and sha256(binary) == runner.PINNED_BINARY_SHA256,
        "installed_architectures": bool(lipo and lipo.returncode == 0 and
                                        set(lipo.stdout.split()) == {"arm64", "x86_64"}),
        "installed_codesign": bool(sign and sign.returncode == 0),
        "request_hash": sha256(runner.REQUEST) == runner.PINNED_REQUEST_SHA256,
        "input_hash": sha256(runner.INPUT) == runner.PINNED_INPUT_SHA256,
        "formal_matrix_hash": sha256(runner.FORMAL_MATRIX) == runner.PINNED_FORMAL_MATRIX_SHA256,
        "install_identity_hash": sha256(runner.INSTALL_IDENTITY) == runner.PINNED_INSTALL_IDENTITY_SHA256,
        "authoritative_record_hash": sha256(runner.AUTHORITATIVE_RECORD) == runner.PINNED_AUTHORITATIVE_RECORD_SHA256,
        "authoritative_record_exact": runner.authoritative_record_exact(),
        "authoritative_artifacts_complete": len(authoritative_artifacts) == 4,
        "parameter_contract": runner.parameter_contract_exact(),
    }
    ready = all(checks.values())
    report = {
        "schema": "olmblur.mac-ae-host-phase-readiness/1",
        "status": "ready_for_runner" if ready else "authoritative_recapture_required",
        "ae_was_launched_or_operated": False,
        "target": {
            "application": str(AE_APP), "version": "26.3.0.87",
            "renderer": "SOFTWARE", "bit_depth": 32,
            "working_space": "None", "linear_blending": False,
            "case": "olmblur__case_0001", "dimensions": [1920, 1080], "frame": 0,
            "params": {"Blur Amount": 129.4, "Blur Smoothness": 100,
                       "Number of Repeat": 1, "Bias Direction": 1, "Legacy": 0},
        },
        "installed_plugin": {"bundle": str(plugin), "binary_sha256": runner.PINNED_BINARY_SHA256,
                             "architectures": ["arm64", "x86_64"]},
        "expected_outputs": {
            "authoritative_record": str(runner.AUTHORITATIVE_RECORD.relative_to(ROOT)),
            "mac_no_effect_sha256": runner.AUTHORITATIVE_MAC_CONTROL_SHA256,
            "mac_effect_on_sha256": runner.AUTHORITATIVE_MAC_EFFECT_SHA256,
            "windows_no_effect_sha256": runner.AUTHORITATIVE_WINDOWS_CONTROL_SHA256,
            "windows_effect_on_sha256": runner.AUTHORITATIVE_WINDOWS_EFFECT_SHA256,
            "artifacts_present": {key: str(path.relative_to(ROOT)) for key, path in authoritative_artifacts.items()},
            "comparison": "raw FLOAT32 A,B,G,R words; mismatched_values=0 and max_raw_u32_delta=0",
        },
        "runner": str(Path(runner.__file__).relative_to(ROOT)),
        "runner_sha256": RUNNER_SHA256,
        "project_generation": {
            "runner": str(PROJECT_RUNNER.relative_to(ROOT)),
            "runner_sha256": PROJECT_RUNNER_SHA256,
            "mode": "creates a fresh unsaved 32bpc project and closes without saving",
        },
        "checks": checks,
        "next_gate": "Restore the four 20260727 authoritative EXRs or recapture the exact hash-bound contract. The runner will not render against the superseded 20260710 reference or self-adopt a current Mac output.",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
