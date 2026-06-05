#!/usr/bin/env python3
"""Smoke-test scripts/verify_mac_plugin_package.py with a synthetic package."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from smoke_ae_validation_result_verifier import EXPECTED_PLUGINS, template_result


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    verifier = repo / "scripts" / "verify_mac_plugin_package.py"
    with tempfile.TemporaryDirectory(prefix="olm_mac_pkg_smoke_") as tmp:
        tmp_path = Path(tmp)
        root = tmp_path / "OLM_Mac_Plugins_Debug"
        root.mkdir()
        (root / "INSTALL.txt").write_text("install notes\n", encoding="utf-8")
        (root / "AE_VALIDATION_CHECKLIST.txt").write_text("validation checklist\n", encoding="utf-8")
        (root / "AE_VALIDATION_RESULT.template.json").write_text(
            json.dumps(template_result(), indent=2),
            encoding="utf-8",
        )
        pixel_dir = root / "AE_PIXEL_VALIDATION"
        pixel_dir.mkdir()
        pixel_request = pixel_dir / "olmblur_request.zip"
        proc = subprocess.run(
            [
                sys.executable,
                str(repo / "scripts" / "package_ae_pixel_validation_request.py"),
                "--preset",
                "olmblur",
                "--output",
                str(pixel_request),
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

        plugins = []
        for name in EXPECTED_PLUGINS:
            binary = root / f"{name}.plugin" / "Contents" / "MacOS" / name
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"synthetic-binary")
            plugins.append(
                {
                    "name": name,
                    "bundle": f"{name}.plugin",
                    "binary_sha256": "0" * 64,
                    "architectures": ["arm64", "x86_64"],
                }
            )

        manifest = {
            "kind": "olm_mac_plugin_package",
            "configuration": "Debug",
            "source_root": str(repo),
            "packaged_at": "2026-06-06T00:00:00Z",
            "install_notes": "INSTALL.txt",
            "validation_checklist": "AE_VALIDATION_CHECKLIST.txt",
            "validation_result_template": "AE_VALIDATION_RESULT.template.json",
            "ae_pixel_validation_requests": [
                {
                    "name": "OLMBlur",
                    "request_id": "ae_pixel_olmblur_20260606",
                    "zip": "AE_PIXEL_VALIDATION/olmblur_request.zip",
                }
            ],
            "plugins": plugins,
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        zip_path = tmp_path / "synthetic_mac_plugins.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in root.rglob("*"):
                archive.write(path, path.relative_to(tmp_path))

        proc = subprocess.run(
            [sys.executable, str(verifier), str(zip_path)],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="")
        if proc.returncode != 0:
            return proc.returncode

    print("[OK] mac plugin package verifier smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
