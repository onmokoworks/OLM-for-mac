#!/usr/bin/env python3
"""Validate the recoverable Radial Type-1 incremental install identity.

The default invocation is read-only and validates the checked-in report against
the live build/install/backup state.  Report materialization is intentionally
restricted to the explicit ``--write`` mode.
"""
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
HANDOFF = ROOT / "handoff/mac_plugin_backups/mediacore_20260812_radial_type1_before_install"
SOURCE_BUNDLE = ROOT / "mac/OLMRadialBlur/Mac/build/Debug/OLMRadialBlur.plugin"
STAGED_BUNDLE = HANDOFF / "staged/OLMRadialBlur.plugin"
INSTALLED_BUNDLE = (
    Path.home()
    / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin"
)
BACKUP_BUNDLE = HANDOFF / "OLMRadialBlur.plugin"
MOVED_OLD_BUNDLE = HANDOFF / "pre_swap_original/OLMRadialBlur.plugin"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_20260806.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
CORE_HEADER = ROOT / "core/dblur_noise.h"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_incremental_install_identity_20260812.json"
DOC = REPORT.with_suffix(".md")

SOURCE_SHA = "184fb4e70913622b29f5b627d1eaae1f70b8dedfe6d8b78b8f644058e6121fec"
CORE_HEADER_SHA = "f0600bb4bb208ed8fba92cc6586eb66ac8f767299c8928ec88fc4635c1cfb591"
OLD_SHA = "dee346586c21d9dbf04d89c6bac8a4f61f1e475b647f1df1fcb77a1eba536e97"
NEW_SHA = "03e837e8a9ccebbc3e03479b4d8a66f65aa85cce1ac0be616b14dac82284d548"
PRE_IDENTITY_SHA = "f54d5f8b3d4ed950c1d0e7220b7f81ea17e1d87adbe73d6a3020a2a01fc3fcc7"
POST_IDENTITY_SHA = "44e1dca88bb9413ca28e86792fcf9b7d5b48f71a6b770f35bd414897f5bc0061"
PLUGIN = "OLMRadialBlur"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
BUNDLE_PATHS = (
    ("source", SOURCE_BUNDLE),
    ("staged", STAGED_BUNDLE),
    ("installed", INSTALLED_BUNDLE),
    ("backup", BACKUP_BUNDLE),
    ("pre_swap_original", MOVED_OLD_BUNDLE),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_or_absolute(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def binary(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMRadialBlur"


def bundle_manifest(bundle: Path) -> list[dict[str, object]]:
    assert bundle.is_dir(), bundle
    rows: list[dict[str, object]] = []
    paths = sorted(
        [bundle, *bundle.rglob("*")],
        key=lambda item: item.relative_to(bundle).as_posix(),
    )
    for path in paths:
        info = path.lstat()
        name = "." if path == bundle else path.relative_to(bundle).as_posix()
        row: dict[str, object] = {"path": name, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update({"type": "symlink", "target": os.readlink(path)})
        elif path.is_dir():
            row["type"] = "directory"
        elif path.is_file():
            row.update({"type": "file", "bytes": info.st_size, "sha256": sha(path)})
        else:
            raise AssertionError(f"unsupported bundle entry: {path}")
        rows.append(row)
    return rows


def live_bundle(bundle: Path) -> dict[str, object]:
    executable = binary(bundle)
    assert executable.is_file(), executable
    archs = run("lipo", "-archs", str(executable)).stdout.split()
    signature = run("codesign", "--verify", "--deep", "--strict", str(bundle))
    return {
        "path": rel_or_absolute(bundle),
        "binary_sha256": sha(executable),
        "architectures": archs,
        "universal_exact": set(archs) == {"arm64", "x86_64"},
        "strict_codesign": signature.returncode == 0,
        "manifest": bundle_manifest(bundle),
    }


def installed_bundle_count() -> int:
    media_core = INSTALLED_BUNDLE.parent
    return len([path for path in media_core.rglob("OLMRadialBlur.plugin") if path.is_dir()])


def ae_pids() -> list[int]:
    result = run(
        "pgrep", "-f",
        r"^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects( |$)",
    )
    assert result.returncode in (0, 1)
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def identity_transition() -> dict[str, object]:
    pre = json.loads(PRE_IDENTITY.read_text(encoding="utf-8"))
    post = json.loads(IDENTITY.read_text(encoding="utf-8"))
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    assert set(pre_rows) == set(post_rows) == PLUGINS

    changed: dict[str, list[str]] = {}
    for name in sorted(PLUGINS):
        fields = sorted(
            key for key in set(pre_rows[name]) | set(post_rows[name])
            if pre_rows[name].get(key) != post_rows[name].get(key)
        )
        if fields:
            changed[name] = fields
    top_level_changed = sorted(
        key for key in set(pre) | set(post)
        if key != "plugins" and pre.get(key) != post.get(key)
    )
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "top_level_changed_fields": top_level_changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "old_executable_sha256": pre_rows[PLUGIN]["sha256"],
        "new_executable_sha256": post_rows[PLUGIN]["sha256"],
    }


def validate(report: dict[str, object]) -> None:
    assert report["schema"] == "olmradialblur.type1-incremental-install-identity/1"
    assert report["status"] == "PASS_RECOVERABLE_RADIAL_ONLY_INSTALL_IDENTITY"
    assert report["claim_boundary"] == (
        "Recoverable build-to-MediaCore identity transition for only OLMRadialBlur; "
        "no AE load/render or numerical-host claim"
    )
    assert report["production_source_sha256"] == sha(SOURCE) == SOURCE_SHA
    assert report["core_header_sha256"] == sha(CORE_HEADER) == CORE_HEADER_SHA
    assert report["pre_identity_manifest_sha256"] == sha(PRE_IDENTITY) == PRE_IDENTITY_SHA
    assert report["accepted_identity_manifest_sha256"] == sha(IDENTITY) == POST_IDENTITY_SHA
    assert report["after_effects_processes"] == ae_pids() == []
    assert report["installed_bundle_count"] == installed_bundle_count() == 1

    live = {name: live_bundle(path) for name, path in BUNDLE_PATHS}
    assert report["bundles"] == live
    assert live["source"]["binary_sha256"] == NEW_SHA
    assert live["staged"]["binary_sha256"] == NEW_SHA
    assert live["installed"]["binary_sha256"] == NEW_SHA
    assert live["source"]["manifest"] == live["staged"]["manifest"] == live["installed"]["manifest"]
    assert live["backup"]["binary_sha256"] == OLD_SHA
    assert live["pre_swap_original"]["binary_sha256"] == OLD_SHA
    assert live["backup"]["manifest"] == live["pre_swap_original"]["manifest"]
    assert all(row["universal_exact"] and row["strict_codesign"] for row in live.values())

    transition = identity_transition()
    assert report["identity_transition"] == transition
    assert transition == {
        "changed_plugins": [PLUGIN],
        "changed_fields": {PLUGIN: ["sha256", "source_sha256"]},
        "top_level_changed_fields": [],
        "unchanged_plugins": sorted(PLUGINS - {PLUGIN}),
        "old_executable_sha256": OLD_SHA,
        "new_executable_sha256": NEW_SHA,
    }
    assert report["transaction"] == {
        "backup_before_install": True,
        "backup_method": "ditto",
        "candidate_staged_and_verified_before_swap": True,
        "full_bundle_inventory_exact": True,
        "installed_bundle_count": 1,
        "rollback_bundle_retained": True,
        "source_staged_installed_full_bundle_exact": True,
    }


def generate() -> dict[str, object]:
    report: dict[str, object] = {
        "schema": "olmradialblur.type1-incremental-install-identity/1",
        "status": "PASS_RECOVERABLE_RADIAL_ONLY_INSTALL_IDENTITY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": (
            "Recoverable build-to-MediaCore identity transition for only OLMRadialBlur; "
            "no AE load/render or numerical-host claim"
        ),
        "production_source_sha256": sha(SOURCE),
        "core_header_sha256": sha(CORE_HEADER),
        "pre_identity_manifest_sha256": sha(PRE_IDENTITY),
        "accepted_identity_manifest_sha256": sha(IDENTITY),
        "after_effects_processes": ae_pids(),
        "installed_bundle_count": installed_bundle_count(),
        "bundles": {name: live_bundle(path) for name, path in BUNDLE_PATHS},
        "identity_transition": identity_transition(),
        "transaction": {
            "backup_before_install": True,
            "backup_method": "ditto",
            "candidate_staged_and_verified_before_swap": True,
            "full_bundle_inventory_exact": True,
            "installed_bundle_count": 1,
            "rollback_bundle_retained": True,
            "source_staged_installed_full_bundle_exact": True,
        },
    }
    validate(report)
    return report


def write(report: dict[str, object]) -> None:
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    DOC.write_text(
        "# OLMRadialBlur Type 1 incremental install identity\n\n"
        "Status: **PASS_RECOVERABLE_RADIAL_ONLY_INSTALL_IDENTITY**. The signed "
        f"Universal canonical build and sole MediaCore bundle are full-bundle exact at `{NEW_SHA}`. "
        f"Both retained pre-install bundles are full-bundle exact at `{OLD_SHA}`, and the backed-up "
        "accepted manifest differs from the current manifest only in OLMRadialBlur `sha256` and "
        "`source_sha256`. The production source and shared noise header are hash-bound. This is a "
        "recoverable install-identity claim only; it makes no AE load, render, or numerical-host claim.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write", action="store_true",
        help="Explicitly regenerate the checked-in JSON and Markdown reports.",
    )
    args = parser.parse_args()
    if args.write:
        write(generate())
    else:
        validate(json.loads(REPORT.read_text(encoding="utf-8")))
    print("PASS_OLMRADIALBLUR_TYPE1_INCREMENTAL_INSTALL_IDENTITY_20260812")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
