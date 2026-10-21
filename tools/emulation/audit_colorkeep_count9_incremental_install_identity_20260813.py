#!/usr/bin/env python3
"""Audit the ColorKeep count9 single-plugin incremental install (read-only by default)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import plistlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/colorkeep_count9_incremental_install_20260813"
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
PROJECT = ROOT / "mac/ColorKeep/Mac/ColorKeep.xcodeproj/project.pbxproj"
INSTALL_SCRIPT = ROOT / "scripts/install_colorkeep_count9_incremental_20260813.py"
BUILD_LOG = HANDOFF / "xcodebuild_macos11.log"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
REPORT = ROOT / "refs/conformance/colorkeep_count9_incremental_install_identity_20260813.json"
DOC = REPORT.with_suffix(".md")
PREFLIGHT = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"
SOURCE_SHA = "3ff3a4d4319f5b3b5519e517fcf591be417c97e4e9dd62117fe4e42f66ebdfd3"
OLD_SHA = "262b73e656d4363dce0de6f0fe819fabf461e157ca7cedd98cad107c8db87fe8"
NEW_SHA = "fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77"
PRE_IDENTITY_SHA = "90e37eefd68f990e137d23d46212c7039ec49f03e86bfe076765cc350da3820a"
POST_IDENTITY_SHA = "869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90"
PREINSTALL_SHA = "bcb6779f3780ac4d0226aad05c0df4b85de853ea26c06c6b0e49a812b7a924d2"
TRANSACTION_SHA = "fa51e4297b153964a47cc4fc931689268ef7ee88a2155fe63922dc6dbb330c37"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
BUNDLES = {
    "source": HANDOFF / "candidate/Product/ColorKeep.plugin",
    "staged": HANDOFF / "staged/ColorKeep.plugin",
    "installed": Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin",
    "installed_backup": HANDOFF / "installed_backup/ColorKeep.plugin",
    "pre_swap_original": HANDOFF / "pre_swap_original/ColorKeep.plugin",
    "moved_old": HANDOFF / "moved_old/ColorKeep.plugin",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("colorkeep_install", INSTALL_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def identity_transition() -> dict[str, object]:
    pre = json.loads(PRE_IDENTITY.read_text(encoding="utf-8"))
    post = json.loads(POST_IDENTITY.read_text(encoding="utf-8"))
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    assert set(pre_rows) == set(post_rows) == PLUGINS
    changed: dict[str, list[str]] = {}
    for name in sorted(PLUGINS):
        fields = sorted(key for key in set(pre_rows[name]) | set(post_rows[name])
                        if pre_rows[name].get(key) != post_rows[name].get(key))
        if fields:
            changed[name] = fields
    top = sorted(key for key in set(pre) | set(post)
                 if key != "plugins" and pre.get(key) != post.get(key))
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "top_level_changed_fields": top,
        "old_executable_sha256": pre_rows["ColorKeep"]["sha256"],
        "new_executable_sha256": post_rows["ColorKeep"]["sha256"],
        "other_nine_rows_exact": all(pre_rows[name] == post_rows[name]
                                     for name in PLUGINS - {"ColorKeep"}),
    }


def build_evidence() -> dict[str, object]:
    text = BUILD_LOG.read_text(encoding="utf-8")
    compiled = sorted(set(re.findall(
        r"^CompileC .*?/ColorKeep\.o .*?/ColorKeep\.cpp normal (arm64|x86_64) ",
        text, re.MULTILINE,
    )))
    linked = sorted(set(re.findall(
        r"^Ld .*?/Binary/ColorKeep normal (arm64|x86_64) ", text, re.MULTILINE,
    )))
    return {
        "configuration": "Debug",
        "command_deployment_target": "11.0",
        "path": relative(BUILD_LOG),
        "sha256": sha(BUILD_LOG),
        "compiled_architectures": compiled,
        "linked_architectures": linked,
        "build_succeeded_marker": "** BUILD SUCCEEDED **" in text,
        "warning_marker_line_count": sum("warning:" in line for line in text.splitlines()),
        "error_marker_line_count": sum("error:" in line for line in text.splitlines()),
    }


def preflight_collection() -> dict[str, object]:
    result = subprocess.run([sys.executable, str(PREFLIGHT)], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 2, (result.returncode, result.stderr)
    payload = json.loads(result.stdout)
    assert payload["status"] == "ae_not_running" and payload["after_effects"] == []
    assert len(payload["bundles"]) == 10
    assert all(row["bundle_count"] == 1 and row["sha256_exact"]
               and row["universal_exact"] and row["codesign_exact"]
               for row in payload["bundles"])
    return payload


def generate() -> dict[str, object]:
    installer = load_installer()
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(PRE_IDENTITY) == PRE_IDENTITY_SHA
    assert sha(POST_IDENTITY) == sha(POST_IDENTITY_COPY) == POST_IDENTITY_SHA
    assert sha(PREINSTALL) == PREINSTALL_SHA and sha(TRANSACTION) == TRANSACTION_SHA
    assert installer.ae_pids() == []
    bundles: dict[str, object] = {}
    for name, path in BUNDLES.items():
        current = name in {"source", "staged", "installed"}
        bundles[name] = {
            "path": relative(path),
            **installer.verify_bundle(path, NEW_SHA if current else OLD_SHA, current),
        }
    new_manifests = [bundles[name]["manifest"] for name in ("source", "staged", "installed")]
    old_manifests = [bundles[name]["manifest"] for name in
                     ("installed_backup", "pre_swap_original", "moved_old")]
    assert new_manifests[0] == new_manifests[1] == new_manifests[2]
    assert old_manifests[0] == old_manifests[1] == old_manifests[2]
    transition = identity_transition()
    assert transition == {
        "changed_plugins": ["ColorKeep"],
        "changed_fields": {"ColorKeep": ["sha256", "source_bundle", "source_sha256"]},
        "unchanged_plugins": sorted(PLUGINS - {"ColorKeep"}),
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "old_executable_sha256": OLD_SHA,
        "new_executable_sha256": NEW_SHA,
        "other_nine_rows_exact": True,
    }
    with (BUNDLES["installed"] / "Contents/Info.plist").open("rb") as stream:
        plist = plistlib.load(stream)
    assert plist["CFBundleExecutable"] == "ColorKeep"
    preflight = [preflight_collection(), preflight_collection()]
    transaction = json.loads(TRANSACTION.read_text(encoding="utf-8"))
    assert transaction["same_volume_atomic_bundle_exchange"] is True
    assert transaction["atomic_exchange_api"] == "renameatx_np(RENAME_SWAP)"
    return {
        "schema": "colorkeep.count9-incremental-install-identity/1",
        "status": "installed_identity_exact_no_ae_execution",
        "generated_at": json.loads(POST_IDENTITY.read_text())["accepted_at"],
        "claim_boundary": "ColorKeep-only atomic bundle exchange and accepted installed identity; no AE launch, load, UI, render, fresh smoke, release gate, Developer ID, notarization, or distribution claim.",
        "production_source_sha256": SOURCE_SHA,
        "project_sha256": sha(PROJECT),
        "install_script_sha256": sha(INSTALL_SCRIPT),
        "generator_sha256": sha(Path(__file__)),
        "preinstall_manifest_sha256": PREINSTALL_SHA,
        "transaction_sha256": TRANSACTION_SHA,
        "pre_identity_manifest_sha256": PRE_IDENTITY_SHA,
        "accepted_identity_manifest_sha256": POST_IDENTITY_SHA,
        "after_effects_processes_at_audit": [],
        "installed_bundle_count": 1,
        "product_identity": {
            "bundle_executable": plist["CFBundleExecutable"],
            "bundle_identifier": plist["CFBundleIdentifier"],
            "bundle_package_type": plist["CFBundlePackageType"],
        },
        "inventory_scope": {
            "claimed": ["relative path", "entry type", "POSIX mode", "file byte size", "file SHA-256", "symlink target"],
            "not_claimed": ["mtime preservation", "extended attributes", "ACL semantic equality", "Finder metadata", "transaction timing beyond recorded observations"],
        },
        "build_evidence": build_evidence(),
        "bundles": bundles,
        "identity_transition": transition,
        "transaction": transaction,
        "stable_all10_preflight_collections": preflight,
        "boundaries": {
            "rollback_original_retained": True,
            "candidate_staged_and_verified_before_atomic_exchange": True,
            "source_staged_installed_full_inventory_exact": True,
            "old_backup_pre_swap_moved_full_inventory_exact": True,
            "same_volume_namespace_atomic_bundle_exchange": True,
            "manifest_update_atomic_file_replace": True,
            "manifest_and_bundle_single_atomic_transaction": False,
            "developer_id_signed": False,
            "notarized": False,
            "ae_operation_performed": False,
        },
    }


def markdown(report: dict[str, object]) -> str:
    return (
        "# ColorKeep count9 incremental install identity — 2026-08-13\n\n"
        f"ColorKeep source `{SOURCE_SHA}` was unchanged while the isolated Debug Universal "
        f"candidate `{NEW_SHA}` was built with deployment target 11.0, ad-hoc signed, staged, "
        "and atomically exchanged into MediaCore with `renameatx_np(RENAME_SWAP)`. Both Mach-O "
        "slices and Info.plist declare 11.0; both slices export EffectMain.\n\n"
        f"The accepted identity manifest is `{POST_IDENTITY_SHA}`. Only the ColorKeep row fields "
        "`sha256`, `source_bundle`, and `source_sha256`, plus `accepted_at` and `installed_after`, "
        "changed; the other nine plugin rows are exact. The old executable "
        f"`{OLD_SHA}` remains in three full-inventory durable copies. Two post-install all-ten "
        "preflight collections found one Universal, strict-signature-valid, identity-exact bundle "
        "per plugin and zero After Effects processes.\n\n"
        "The inventory claim covers path, type, POSIX mode, size, file SHA-256, and symlink target. "
        "It does not claim mtime, xattr, ACL semantics, Developer ID, notarization, AE load/render, "
        "fresh AE smoke, or release readiness.\n"
    )


def validate(report: dict[str, object]) -> None:
    expected = generate()
    assert report == expected
    assert DOC.read_text(encoding="utf-8") == markdown(expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = generate()
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        DOC.write_text(markdown(report), encoding="utf-8")
        validate(report)
        print("PASS_COLORKEEP_COUNT9_INCREMENTAL_INSTALL_IDENTITY_WRITE")
        return 0
    validate(json.loads(REPORT.read_text(encoding="utf-8")))
    print("PASS_COLORKEEP_COUNT9_INCREMENTAL_INSTALL_IDENTITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
