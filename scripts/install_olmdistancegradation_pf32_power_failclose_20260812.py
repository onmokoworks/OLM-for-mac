#!/usr/bin/env python3
"""Install the reviewed DistanceGradation Power-fail-close candidate recoverably."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "handoffs/olmdistancegradation_pf32_power_failclose_universal_candidate_20260812/product/OLMDistanceGradation.plugin"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin"
HANDOFF = ROOT / "handoffs/olmdistancegradation_pf32_power_failclose_install_20260812"
EXPECTED_OLD = "b9971c6480088329ee77a2b01d8187f29b73b1cc06633d77dc3029a4012bfc7a"
EXPECTED_NEW = "231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605"


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMDistanceGradation"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_bundle(bundle: Path, expected: str) -> None:
    if not bundle.is_dir() or sha(executable(bundle)) != expected:
        raise RuntimeError(f"bundle identity mismatch: {bundle}")
    archs = subprocess.run(
        ["lipo", "-archs", str(executable(bundle))], text=True,
        capture_output=True, check=True,
    ).stdout.split()
    if set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"non-Universal bundle: {bundle}")
    subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", str(bundle)],
        check=True, capture_output=True,
    )


def ae_pids() -> list[int]:
    result = subprocess.run(
        ["pgrep", "-f", "/After Effects|AfterFX|aerender"],
        text=True, capture_output=True,
    )
    return [int(value) for value in result.stdout.split() if value.isdigit()]


def main() -> int:
    if ae_pids():
        raise RuntimeError("After Effects process is running")
    check_bundle(CANDIDATE, EXPECTED_NEW)
    check_bundle(INSTALLED, EXPECTED_OLD)
    if HANDOFF.exists():
        raise RuntimeError(f"handoff already exists: {HANDOFF}")

    HANDOFF.mkdir(parents=True)
    backup_a = HANDOFF / "installed_backup/OLMDistanceGradation.plugin"
    backup_b = HANDOFF / "pre_swap_original/OLMDistanceGradation.plugin"
    moved_old = HANDOFF / "moved_old/OLMDistanceGradation.plugin"
    staged = INSTALLED.with_name("OLMDistanceGradation.plugin.power-failclose-staged")
    if staged.exists():
        raise RuntimeError(f"unexpected staged target: {staged}")

    shutil.copy2(
        ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json",
        HANDOFF / "olm_installed_identity_manifest_before.json",
    )
    subprocess.run(["ditto", str(INSTALLED), str(backup_a)], check=True)
    subprocess.run(["ditto", str(INSTALLED), str(backup_b)], check=True)
    check_bundle(backup_a, EXPECTED_OLD)
    check_bundle(backup_b, EXPECTED_OLD)
    subprocess.run(["ditto", str(CANDIDATE), str(staged)], check=True)
    check_bundle(staged, EXPECTED_NEW)

    moved = False
    installed_new = False
    try:
        moved_old.parent.mkdir(parents=True)
        os.replace(INSTALLED, moved_old)
        moved = True
        os.replace(staged, INSTALLED)
        installed_new = True
        check_bundle(INSTALLED, EXPECTED_NEW)
        check_bundle(moved_old, EXPECTED_OLD)
        if ae_pids():
            raise RuntimeError("After Effects appeared during install")
    except BaseException:
        if installed_new and INSTALLED.exists():
            failed = HANDOFF / "failed_new/OLMDistanceGradation.plugin"
            failed.parent.mkdir(parents=True, exist_ok=True)
            os.replace(INSTALLED, failed)
        if moved and moved_old.exists() and not INSTALLED.exists():
            os.replace(moved_old, INSTALLED)
        raise

    print(f"PASS installed={EXPECTED_NEW} rollback={EXPECTED_OLD} handoff={HANDOFF}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
