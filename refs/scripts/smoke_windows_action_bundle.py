#!/usr/bin/env python3
"""Smoke-test scripts/package_windows_action_bundle.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run(cmd: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def nested_zip_kind(archive: zipfile.ZipFile, name: str) -> str:
    with archive.open(name) as handle:
        with zipfile.ZipFile(handle) as nested:
            for nested_name in nested.namelist():
                if nested_name.endswith("runtime_trace_package_manifest.json"):
                    data = json.loads(nested.read(nested_name).decode("utf-8"))
                    if data.get("kind") == "olm_runtime_trace_request_package":
                        return "runtime-trace-request-package"
                if nested_name.endswith("request_manifest.json"):
                    data = json.loads(nested.read(nested_name).decode("utf-8"))
                    if data.get("kind") == "olm_ae_pixel_validation_request":
                        return "ae-pixel-validation-request"
    return "unknown"


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "package_windows_action_bundle.py"
    with tempfile.TemporaryDirectory(prefix="olm_windows_action_bundle_smoke_") as tmp:
        output = Path(tmp) / "windows_action_bundle.zip"
        proc = run([sys.executable, str(script), "--output", str(output)], root)
        assert "[OK] Windows action bundle:" in proc.stdout
        assert output.exists()

        with zipfile.ZipFile(output) as archive:
            names = set(archive.namelist())
            assert "README_WINDOWS_ACTION_BUNDLE.md" in names
            assert "windows_action_bundle_manifest.json" in names
            manifest = json.loads(archive.read("windows_action_bundle_manifest.json").decode("utf-8"))
            assert manifest["kind"] == "olm_windows_action_bundle"
            assert manifest["priority"] == "smoother-priority"
            runtime_rows = manifest["runtime_trace_packages"]
            ae_rows = manifest["ae_pixel_validation_packages"]
            assert len(runtime_rows) == 5
            assert len(ae_rows) == 9
            assert "olmsmoother2_legacy_key_gamma" in runtime_rows[0]["source"]
            assert "olmsmoother2_no_key_grid" in runtime_rows[1]["source"]
            for row in runtime_rows:
                assert row["bundle_path"] in names
                assert row["kind"] == "runtime-trace-request-package"
                assert nested_zip_kind(archive, row["bundle_path"]) == row["kind"]
            for row in ae_rows:
                assert row["bundle_path"] in names
                assert row["kind"] == "ae-pixel-validation-request"
                assert nested_zip_kind(archive, row["bundle_path"]) == row["kind"]
            assert "notes/CONFORMANCE_LEDGER.md" in names

        runtime_only = Path(tmp) / "runtime_only_bundle.zip"
        run([sys.executable, str(script), "--runtime-only", "--output", str(runtime_only)], root)
        with zipfile.ZipFile(runtime_only) as archive:
            manifest = json.loads(archive.read("windows_action_bundle_manifest.json").decode("utf-8"))
            assert len(manifest["runtime_trace_packages"]) == 5
            assert manifest["ae_pixel_validation_packages"] == []

        blur_kirakira = Path(tmp) / "blur_kirakira_bundle.zip"
        run(
            [
                sys.executable,
                str(script),
                "--focus",
                "blur-kirakira",
                "--runtime-only",
                "--output",
                str(blur_kirakira),
            ],
            root,
        )
        with zipfile.ZipFile(blur_kirakira) as archive:
            names = set(archive.namelist())
            manifest = json.loads(archive.read("windows_action_bundle_manifest.json").decode("utf-8"))
            assert manifest["priority"] == "blur-kirakira"
            runtime_rows = manifest["runtime_trace_packages"]
            assert len(runtime_rows) == 2
            assert manifest["ae_pixel_validation_packages"] == []
            assert "olmblur_repeat_threshold" in runtime_rows[0]["source"]
            assert "kirakira_stage_values" in runtime_rows[1]["source"]
            for row in runtime_rows:
                assert row["bundle_path"] in names
                assert nested_zip_kind(archive, row["bundle_path"]) == "runtime-trace-request-package"

    print("[OK] Windows action bundle smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
