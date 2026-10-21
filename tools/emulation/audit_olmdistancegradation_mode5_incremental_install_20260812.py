#!/usr/bin/env python3
"""Validate the recoverable Distance Mode 5 build/install identity transition."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmdistancegradation_mode5_install_20260812T185828JST"
SOURCE_BUNDLE = ROOT / "mac/OLMDistanceGradation/Mac/build/Debug/OLMDistanceGradation.plugin"
INSTALLED_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin"
BACKUP_BUNDLE = HANDOFF / "pre_install/OLMDistanceGradation.plugin"
MOVED_OLD_BUNDLE = HANDOFF / "pre_swap_original/OLMDistanceGradation.plugin"
PRE_IDENTITY = HANDOFF / "pre_install/olm_installed_identity_manifest_20260806.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
CODEGEN = ROOT / "refs/conformance/olmdistancegradation_pf32_mode5_universal_codegen_20260812.json"
REPORT = ROOT / "refs/conformance/olmdistancegradation_mode5_incremental_install_identity_20260812.json"
DOC = REPORT.with_suffix(".md")

OLD_SHA = "0caf728ce871feefd606cdedd2054f17bce09c80639722748ebecd9ed5440093"
NEW_SHA = "b9971c6480088329ee77a2b01d8187f29b73b1cc06633d77dc3029a4012bfc7a"
SOURCE_SHA = "1fcfd2c1e748f86807883282f431797ccb733f09b207e844cee086bff9c42ef8"
PRE_IDENTITY_SHA = "70db3215ff4125dcfcf072b3b29ea7b0422ec7fc00c23e1646af79e005cf0954"
POST_IDENTITY_SHA = "f54d5f8b3d4ed950c1d0e7220b7f81ea17e1d87adbe73d6a3020a2a01fc3fcc7"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def binary(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMDistanceGradation"


def bundle_manifest(bundle: Path) -> list[dict[str, object]]:
    assert bundle.is_dir()
    rows: list[dict[str, object]] = []
    for path in sorted([bundle, *bundle.rglob("*")], key=lambda item: item.relative_to(bundle).as_posix()):
        info = path.lstat()
        name = "." if path == bundle else path.relative_to(bundle).as_posix()
        row: dict[str, object] = {"path": name, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update({"type": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            row.update({"type": "directory"})
        elif path.is_file():
            row.update({"type": "file", "bytes": info.st_size, "sha256": sha(path)})
        else:
            raise AssertionError(f"unsupported bundle entry: {path}")
        rows.append(row)
    return rows


def live_bundle(bundle: Path) -> dict[str, object]:
    archs = run("lipo", "-archs", str(binary(bundle))).stdout.split()
    signature = run("codesign", "--verify", "--deep", "--strict", str(bundle))
    return {
        "path": str(bundle) if bundle.is_absolute() and not bundle.is_relative_to(ROOT) else rel(bundle),
        "binary_sha256": sha(binary(bundle)),
        "architectures": archs,
        "universal_exact": set(archs) == {"arm64", "x86_64"},
        "strict_codesign": signature.returncode == 0,
        "manifest": bundle_manifest(bundle),
    }


def ae_pids() -> list[int]:
    result = run("pgrep", "-f", r"^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects( |$)")
    assert result.returncode in (0, 1)
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def validate(report: dict[str, object]) -> None:
    assert report["schema"] == "olmdistancegradation.mode5-incremental-install-identity/1"
    assert report["status"] == "PASS_RECOVERABLE_DISTANCE_ONLY_INSTALL_IDENTITY"
    assert report["claim_boundary"] == (
        "Recoverable build-to-MediaCore identity transition for only OLMDistanceGradation; "
        "no AE load/render or numerical-host claim"
    )
    assert sha(SOURCE) == report["production_source_sha256"] == SOURCE_SHA
    assert sha(CODEGEN) == report["universal_codegen_report_sha256"]
    assert sha(PRE_IDENTITY) == report["pre_identity_manifest_sha256"] == PRE_IDENTITY_SHA
    assert sha(IDENTITY) == report["accepted_identity_manifest_sha256"] == POST_IDENTITY_SHA
    assert report["after_effects_processes"] == ae_pids() == []

    live = {name: live_bundle(path) for name, path in (
        ("source", SOURCE_BUNDLE), ("backup", BACKUP_BUNDLE),
        ("pre_swap_original", MOVED_OLD_BUNDLE), ("installed", INSTALLED_BUNDLE),
    )}
    assert report["bundles"] == live
    assert live["source"]["binary_sha256"] == live["installed"]["binary_sha256"] == NEW_SHA
    assert live["source"]["manifest"] == live["installed"]["manifest"]
    assert live["backup"]["binary_sha256"] == live["pre_swap_original"]["binary_sha256"] == OLD_SHA
    assert live["backup"]["manifest"] == live["pre_swap_original"]["manifest"]
    assert all(row["universal_exact"] and row["strict_codesign"] for row in live.values())

    pre = json.loads(PRE_IDENTITY.read_text())
    post = json.loads(IDENTITY.read_text())
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    assert set(pre_rows) == set(post_rows) == PLUGINS
    assert [name for name in sorted(PLUGINS) if pre_rows[name] != post_rows[name]] == ["OLMDistanceGradation"]
    assert all(pre_rows[name] == post_rows[name] for name in PLUGINS - {"OLMDistanceGradation"})
    assert pre_rows["OLMDistanceGradation"]["sha256"] == OLD_SHA
    distance = post_rows["OLMDistanceGradation"]
    assert distance["sha256"] == distance["source_sha256"] == NEW_SHA
    assert distance["installed_bundle_count"] == 1
    assert distance["source_installed_exact"] and distance["universal_exact"] and distance["codesign_exact"]
    assert report["identity_transition"] == {
        "changed_plugins": ["OLMDistanceGradation"],
        "unchanged_plugins": sorted(PLUGINS - {"OLMDistanceGradation"}),
        "old_executable_sha256": OLD_SHA,
        "new_executable_sha256": NEW_SHA,
        "accepted_at": post["accepted_at"],
    }
    assert report["transaction"] == {
        "backup_before_install": True,
        "backup_method": "ditto",
        "candidate_staged_and_verified_before_swap": True,
        "installed_bundle_count": 1,
        "rollback_bundle_retained": True,
        "source_installed_full_bundle_exact": True,
    }


def generate() -> dict[str, object]:
    post = json.loads(IDENTITY.read_text())
    report: dict[str, object] = {
        "schema": "olmdistancegradation.mode5-incremental-install-identity/1",
        "status": "PASS_RECOVERABLE_DISTANCE_ONLY_INSTALL_IDENTITY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Recoverable build-to-MediaCore identity transition for only OLMDistanceGradation; "
            "no AE load/render or numerical-host claim"
        ),
        "production_source_sha256": sha(SOURCE),
        "universal_codegen_report_sha256": sha(CODEGEN),
        "pre_identity_manifest_sha256": sha(PRE_IDENTITY),
        "accepted_identity_manifest_sha256": sha(IDENTITY),
        "after_effects_processes": ae_pids(),
        "bundles": {name: live_bundle(path) for name, path in (
            ("source", SOURCE_BUNDLE), ("backup", BACKUP_BUNDLE),
            ("pre_swap_original", MOVED_OLD_BUNDLE), ("installed", INSTALLED_BUNDLE),
        )},
        "identity_transition": {
            "changed_plugins": ["OLMDistanceGradation"],
            "unchanged_plugins": sorted(PLUGINS - {"OLMDistanceGradation"}),
            "old_executable_sha256": OLD_SHA,
            "new_executable_sha256": NEW_SHA,
            "accepted_at": post["accepted_at"],
        },
        "transaction": {
            "backup_before_install": True,
            "backup_method": "ditto",
            "candidate_staged_and_verified_before_swap": True,
            "installed_bundle_count": 1,
            "rollback_bundle_retained": True,
            "source_installed_full_bundle_exact": True,
        },
    }
    validate(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        validate(json.loads(REPORT.read_text()))
    else:
        report = generate()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        DOC.write_text(
            "# OLMDistanceGradation Mode 5 incremental install identity\n\n"
            "Status: **PASS_RECOVERABLE_DISTANCE_ONLY_INSTALL_IDENTITY**. The previous full bundle "
            "and identity manifest are retained under the named handoff. Only Distance changed from "
            f"`{OLD_SHA}` to `{NEW_SHA}`; the other nine accepted rows are byte-identical. The "
            "canonical repo build, installed bundle, Universal slices and strict signature are exact. "
            "This is install identity only, not an AE numerical claim.\n"
        )
    print("PASS_OLMDISTANCEGRADATION_MODE5_INCREMENTAL_INSTALL_IDENTITY_20260812")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
