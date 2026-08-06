#!/usr/bin/env python3
"""Fail closed on the accepted DistanceGradation installed identity."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.emulation.olm_installed_identity import MANIFEST
from tools.emulation.olm_installed_identity import verified_binary

INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin"


def fail(message: str) -> None:
    raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {message}")


def main() -> int:
    binary, row = verified_binary("OLMDistanceGradation")
    if Path(row["installed_bundle"]) != INSTALLED or row.get("installed_bundle_count") != 1:
        fail("manifest selects an unexpected DistanceGradation installation")
    actual = row["sha256"]
    archs = subprocess.run(["lipo", "-archs", str(binary)], capture_output=True, text=True, check=True).stdout.split()
    signature = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(INSTALLED)], capture_output=True)
    active = list(INSTALLED.parent.glob("OLMDistanceGradation.plugin"))
    if set(archs) != {"arm64", "x86_64"} or signature.returncode or len(active) != 1:
        fail("installed identity does not match the accepted external manifest")

    print(json.dumps({
        "status": "pass",
        "plugin": "OLMDistanceGradation",
        "sha256": actual,
        "architectures": archs,
        "codesign": "valid",
        "active_bundle_count": len(active),
        "identity_manifest": str(MANIFEST.relative_to(ROOT)),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
