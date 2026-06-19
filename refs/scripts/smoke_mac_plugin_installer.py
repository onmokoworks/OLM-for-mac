#!/usr/bin/env python3
"""Smoke-test the MediaCore installer in dry-run mode."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


PLUGINS = [
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


def make_bundle(root: Path, plugin: str) -> None:
    binary = root / f"{plugin}.plugin" / "Contents" / "MacOS" / plugin
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    binary.chmod(0o755)


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    installer = repo / "scripts" / "install_mac_plugins_to_mediacore.sh"
    with tempfile.TemporaryDirectory(prefix="olm_installer_smoke_") as tmp:
        tmp_path = Path(tmp)
        source = tmp_path / "OLM_Mac_Plugins_Debug"
        media_core = tmp_path / "MediaCore"
        nested_backup = media_core / "old_backup"
        for plugin in PLUGINS:
            make_bundle(source, plugin)
            make_bundle(media_core, plugin)
        make_bundle(nested_backup, "OLMBlur")

        proc = subprocess.run(
            [
                str(installer),
                "--source-dir",
                str(source),
                "--media-core",
                str(media_core),
                "--backup-root",
                str(tmp_path / "backups"),
                "--dry-run",
                "--allow-ae-running",
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
        if proc.returncode != 0:
            return proc.returncode
        for plugin in PLUGINS:
            if f"[INSTALL] {source / (plugin + '.plugin')}" not in proc.stdout:
                print(f"[FAIL] missing install line for {plugin}")
                return 1
        if str(nested_backup / "OLMBlur.plugin") not in proc.stdout:
            print("[FAIL] nested duplicate bundle was not detected in dry-run")
            return 1
        if "[OK] dry run complete" not in proc.stdout:
            print("[FAIL] dry-run completion marker missing")
            return 1

        audit = subprocess.run(
            [
                str(installer),
                "--media-core",
                str(media_core),
                "--audit-only",
            ],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        print(audit.stdout, end="" if audit.stdout.endswith("\n") else "\n")
        if audit.returncode == 0:
            print("[FAIL] audit-only did not fail on duplicate MediaCore bundles")
            return 1
        if "[DUPLICATE] OLMBlur.plugin count=2" not in audit.stdout:
            print("[FAIL] audit-only did not report the nested OLMBlur duplicate")
            return 1
    print("[OK] mac plugin installer smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
