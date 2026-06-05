#!/usr/bin/env python3
"""Smoke-test scripts/verify_ae_validation_result.py with synthetic results."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


EXPECTED_PLUGINS = [
    "ColorKeep",
    "OLMBlur",
    "OLMColorKey",
    "OLMDirectionalBlur",
    "OLMRadialBlur",
    "OLMKiraKira",
    "OLMToonDilate",
    "OLMDistanceGradation",
    "OLMSmoother",
    "OLMSmoother2",
]


def base_result() -> dict:
    return {
        "kind": "olm_ae_host_validation_result",
        "package_configuration": "Debug",
        "ae_version": "25.2x131",
        "macos_version": "15.0",
        "machine": "Apple Silicon",
        "project_gpu_accel_type": {"current_name": "SOFTWARE", "raw": 1816},
        "clean_ae_launch_after_install": True,
        "install_path": "~/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/",
        "notes": "",
        "plugins": [
            {
                "name": name,
                "loaded": True,
                "applied": True,
                "render_succeeded": True,
                "effect_menu_name": name,
                "error": "",
                "returned_artifacts": [],
            }
            for name in EXPECTED_PLUGINS
        ],
    }


def template_result() -> dict:
    data = base_result()
    data.update(
        {
            "ae_version": "",
            "macos_version": "",
            "machine": "",
            "project_gpu_accel_type": {"current_name": "", "raw": None},
            "clean_ae_launch_after_install": None,
            "notes": "",
        }
    )
    for entry in data["plugins"]:
        entry["loaded"] = None
        entry["applied"] = None
        entry["render_succeeded"] = None
        entry["effect_menu_name"] = ""
    return data


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print("$", " ".join(cmd))
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc


def write_json(path: Path, data: dict) -> Path:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def expect(proc: subprocess.CompletedProcess[str], want_success: bool, label: str) -> int:
    if (proc.returncode == 0) == want_success:
        return 0
    state = "pass" if want_success else "fail"
    print(f"[FAIL] {label}: expected {state}, got exit={proc.returncode}")
    return 1


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    verifier = root / "scripts" / "verify_ae_validation_result.py"

    with tempfile.TemporaryDirectory(prefix="olm_ae_validation_smoke_") as tmp:
        tmp_path = Path(tmp)
        all_pass = write_json(tmp_path / "all_pass.json", base_result())
        template = write_json(tmp_path / "template.json", template_result())

        failed_data = base_result()
        failed_data["plugins"][2]["render_succeeded"] = False
        failed_data["plugins"][2]["error"] = "render failed in AE host"
        failed = write_json(tmp_path / "failed_but_actionable.json", failed_data)

        bad_data = copy.deepcopy(base_result())
        bad_data["project_gpu_accel_type"]["current_name"] = ""
        bad = write_json(tmp_path / "bad_metadata.json", bad_data)

        checks = [
            (run([sys.executable, str(verifier), "--allow-incomplete", str(template)]), True, "template"),
            (run([sys.executable, str(verifier), str(all_pass)]), True, "all-pass schema"),
            (run([sys.executable, str(verifier), "--require-all-pass", str(all_pass)]), True, "all-pass gate"),
            (run([sys.executable, str(verifier), str(failed)]), True, "actionable failure schema"),
            (run([sys.executable, str(verifier), "--require-all-pass", str(failed)]), False, "all-pass negative"),
            (run([sys.executable, str(verifier), str(bad)]), False, "metadata negative"),
        ]
        for proc, want_success, label in checks:
            rc = expect(proc, want_success, label)
            if rc:
                return rc

    print("[OK] AE validation result verifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
