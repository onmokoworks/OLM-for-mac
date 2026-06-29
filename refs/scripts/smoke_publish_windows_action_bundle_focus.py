#!/usr/bin/env python3
"""Smoke-test scripts/publish_windows_action_bundle_focus.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
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


def main() -> int:
    root = repo_root()
    script = root / "scripts" / "publish_windows_action_bundle_focus.py"

    with tempfile.TemporaryDirectory(prefix="olm_publish_bundle_focus_") as tmp:
        share_root = Path(tmp) / "olm_pr"
        (share_root / "new").mkdir(parents=True)
        (share_root / "old").mkdir(parents=True)

        dry = run(
            [
                sys.executable,
                str(script),
                "--focus",
                "secondary-runtime",
                "--share-root",
                str(share_root),
                "--dry-run",
            ],
            root,
        )
        if "[OK] Windows action bundle:" not in dry.stdout:
            print("[FAIL] helper did not package a bundle in dry-run")
            return 1
        if "[DRY-RUN] publish command:" not in dry.stdout:
            print("[FAIL] helper did not print publish command in dry-run")
            return 1

        proc = run(
            [
                sys.executable,
                str(script),
                "--focus",
                "secondary-runtime",
                "--share-root",
                str(share_root),
            ],
            root,
        )
        if "[OK] published:" not in proc.stdout:
            print("[FAIL] helper did not publish bundle to share")
            return 1
        new_files = sorted(path.name for path in (share_root / "new").iterdir() if path.is_file())
        if len(new_files) != 1 or not new_files[0].endswith("_secondary_runtime.zip"):
            print("[FAIL] unexpected share/new contents:", new_files)
            return 1

    print("[OK] publish Windows action bundle focus smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
