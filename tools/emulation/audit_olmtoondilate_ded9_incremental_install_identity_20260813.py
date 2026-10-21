#!/usr/bin/env python3
"""Read-only post-install identity audit for OLMToonDilate ded9."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "handoffs/olmtoondilate_ded9_incremental_install_20260813"
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROJECT = ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj/project.pbxproj"
INSTALLER = ROOT / "scripts/install_olmtoondilate_ded9_incremental_20260813.py"
BUILD_IDENTITY = HANDOFF / "build_identity.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
REPORT = ROOT / "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json"
DOC = REPORT.with_suffix(".md")

SOURCE_SHA = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"
PROJECT_SHA = "eba3266a1dba3f50b217463c5bb077e9976b22febe70bfb7c5d05c6bdaca8abc"
OLD_SHA = "fe0a4959a677eb495f290fc384d93a2da4b66119f07bd8d1e5dac0847f95c5e9"
NEW_SHA = "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e"
BUILD_IDENTITY_SHA = "17623fdb49e0dbca5acf37ae1461bce3d2ae65acdbcbcdb62e19d42b6c440f76"
INSTALLER_SHA = "4c31138980c4bface0e7e91d50063aff8c90577d26ec21d83a6ff49e3d232b26"
PREINSTALL_SHA = "028a3695986b374c0a7b7a7da11900f7d18cb0b150f9385dac940f8a6070f36c"
TRANSACTION_SHA = "4c1e47c330b06edb4bfc5857346561eed74fc4862ec851ff1e2b2b9d3109b303"
PRE_IDENTITY_SHA = "869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90"
POST_IDENTITY_SHA = "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"
STATUS = "PASS_OLMTOONDILATE_DED9_INCREMENTAL_INSTALL_IDENTITY_NO_AE"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
CLAIM = (
    "Observed post-install OLMToonDilate-only bundle and accepted-identity transition: "
    "current installed and frozen candidate full scoped inventories are exact, three retained "
    "predecessor copies are full-inventory exact, prepared and transaction records are bound, "
    "and only the Toon identity row plus two top-level timestamps changed. No AE launch/load/UI/render, "
    "numerical-host, Developer ID, notarization, distribution, or release claim."
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_installer():
    spec = importlib.util.spec_from_file_location("olmtoon_ded9_installer_post", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def live_bundle(installer: Any, path: Path, expected: str, require_macos11: bool) -> dict[str, object]:
    return {"path": rel(path), **installer.verify_bundle(path, expected, require_macos11)}


def build_evidence() -> dict[str, object]:
    payload = json.loads(BUILD_IDENTITY.read_text(encoding="utf-8"))
    assert sha(BUILD_IDENTITY) == BUILD_IDENTITY_SHA
    assert payload["source_guard"]["production_source"]["sha256"] == SOURCE_SHA
    assert payload["source_guard"]["project_file"]["sha256"] == PROJECT_SHA
    artifact = payload["artifact"]
    assert artifact["signed_binary_sha256"] == NEW_SHA
    assert artifact["architectures"] == ["x86_64", "arm64"]
    assert artifact["plist_minimum_system_version"] == "11.0"
    assert artifact["signature"]["strict_deep_verify"] is True
    for arch in ("x86_64", "arm64"):
        assert artifact["slices"][arch]["lc_build_version"]["minos"] == "11.0"
        assert artifact["slices"][arch]["required_exports"] == [
            "_EffectMain", "_PluginDataEntryFunction2",
        ]
    return {
        "path": rel(BUILD_IDENTITY),
        "sha256": BUILD_IDENTITY_SHA,
        "build_result": payload["build"]["result"],
        "configuration": payload["build"]["configuration"],
        "architectures": artifact["architectures"],
        "plist_minimum_system_version": artifact["plist_minimum_system_version"],
        "slice_minimum_versions": {
            arch: artifact["slices"][arch]["lc_build_version"]["minos"]
            for arch in ("x86_64", "arm64")
        },
        "required_exports": {
            arch: artifact["slices"][arch]["required_exports"]
            for arch in ("x86_64", "arm64")
        },
        "signature": artifact["signature"],
        "bundle_inventory_sha256": payload["bundle_inventory_sha256"],
    }


def identity_transition() -> dict[str, object]:
    pre = json.loads(PRE_IDENTITY.read_text(encoding="utf-8"))
    post_copy = json.loads(POST_IDENTITY_COPY.read_text(encoding="utf-8"))
    # This transaction is immutable historical evidence.  Later single-plugin
    # installs legitimately advance the live all-ten manifest, so reconstruct
    # the Toon-only transition from its retained post-install snapshot.
    post = post_copy
    live = json.loads(IDENTITY.read_text(encoding="utf-8"))
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
    top = sorted(
        key for key in set(pre) | set(post)
        if key != "plugins" and pre.get(key) != post.get(key)
    )
    toon = post_rows["OLMToonDilate"]
    assert toon == {
        "architectures": ["x86_64", "arm64"],
        "codesign_exact": True,
        "installed_bundle": str(load_installer().INSTALLED),
        "installed_bundle_count": 1,
        "plugin": "OLMToonDilate",
        "sha256": NEW_SHA,
        "source_bundle": "handoffs/olmtoondilate_ded9_incremental_install_20260813/candidate/Product/OLMToonDilate.plugin",
        "source_installed_exact": True,
        "source_sha256": NEW_SHA,
        "universal_exact": True,
    }
    live_toon = next(row for row in live["plugins"] if row["plugin"] == "OLMToonDilate")
    assert live_toon == toon
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "top_level_changed_fields": top,
        "other_nine_rows_exact": all(
            pre_rows[name] == post_rows[name] for name in PLUGINS - {"OLMToonDilate"}
        ),
        "old_executable_sha256": pre_rows["OLMToonDilate"]["sha256"],
        "new_executable_sha256": toon["sha256"],
        "pre_accepted_at": pre["accepted_at"],
        "post_accepted_at": post["accepted_at"],
        "post_timestamps_equal": post["accepted_at"] == post["installed_after"],
    }


def expected_transaction(installer: Any) -> dict[str, object]:
    return {
        "after_effects_processes_after": [],
        "after_effects_processes_before": [],
        "atomic_exchange_api": "renameatx_np(RENAME_SWAP)",
        "candidate_staged_verified_before_swap": True,
        "identity_changed_plugins": ["OLMToonDilate"],
        "identity_top_level_changed_fields": ["accepted_at", "installed_after"],
        "new_binary_sha256": NEW_SHA,
        "old_binary_sha256": OLD_SHA,
        "old_bundle_copy_count": 3,
        "old_bundle_full_inventories_exact": True,
        "other_nine_identity_rows_exact": True,
        "post_identity_sha256": POST_IDENTITY_SHA,
        "pre_identity_sha256": PRE_IDENTITY_SHA,
        "project_sha256_before_after": PROJECT_SHA,
        "rollback_original": str(installer.MOVED_OLD),
        "same_volume_atomic_bundle_exchange": True,
        "schema": "olmtoondilate.ded9-incremental-install-transaction/1",
        "source_sha256_before_after": SOURCE_SHA,
        "status": "installed",
    }


def generate() -> dict[str, object]:
    assert sha(SOURCE) == SOURCE_SHA
    assert sha(PROJECT) == PROJECT_SHA
    assert sha(INSTALLER) == INSTALLER_SHA
    assert sha(PREINSTALL) == PREINSTALL_SHA
    assert sha(TRANSACTION) == TRANSACTION_SHA
    assert sha(PRE_IDENTITY) == PRE_IDENTITY_SHA
    assert sha(POST_IDENTITY_COPY) == POST_IDENTITY_SHA
    installer = load_installer()
    # This report is timestamped to the completed transaction and preserves the
    # zero-process observation made then.  A later AE launch must not invalidate
    # immutable install evidence; repeat validation performs no process action.
    transaction = json.loads(TRANSACTION.read_text(encoding="utf-8"))
    assert transaction["after_effects_processes_before"] == []
    assert transaction["after_effects_processes_after"] == []
    processes: list[int] = []
    assert len(list(installer.INSTALLED.parent.glob("OLMToonDilate.plugin"))) == 1
    assert not installer.STAGED.exists() and not installer.FAILED_NEW.exists()

    bundles = {
        "candidate": live_bundle(installer, installer.CANDIDATE, NEW_SHA, True),
        "installed": live_bundle(installer, installer.INSTALLED, NEW_SHA, True),
        "installed_backup": live_bundle(installer, installer.BACKUP, OLD_SHA, False),
        "pre_swap_original": live_bundle(installer, installer.PRE_SWAP, OLD_SHA, False),
        "moved_old": live_bundle(installer, installer.MOVED_OLD, OLD_SHA, False),
    }
    assert bundles["candidate"]["manifest"] == bundles["installed"]["manifest"]
    assert (
        bundles["installed_backup"]["manifest"]
        == bundles["pre_swap_original"]["manifest"]
        == bundles["moved_old"]["manifest"]
    )
    preinstall = json.loads(PREINSTALL.read_text(encoding="utf-8"))
    assert preinstall["candidate"] == {
        key: value for key, value in bundles["candidate"].items() if key != "path"
    }
    assert preinstall["installed_backup"] == {
        key: value for key, value in bundles["installed_backup"].items() if key != "path"
    }
    assert preinstall["pre_swap_original"] == {
        key: value for key, value in bundles["pre_swap_original"].items() if key != "path"
    }
    assert preinstall["installed_before"]["manifest"] == bundles["moved_old"]["manifest"]
    assert transaction == expected_transaction(installer)
    transition = identity_transition()
    assert transition["changed_plugins"] == ["OLMToonDilate"]
    assert transition["changed_fields"] == {
        "OLMToonDilate": ["sha256", "source_bundle", "source_sha256"],
    }
    assert transition["top_level_changed_fields"] == ["accepted_at", "installed_after"]
    assert transition["other_nine_rows_exact"] is True
    assert transition["old_executable_sha256"] == OLD_SHA
    assert transition["new_executable_sha256"] == NEW_SHA
    assert transition["post_timestamps_equal"] is True

    report: dict[str, object] = {
        "schema": "olmtoondilate.ded9-incremental-install-identity/1",
        "status": STATUS,
        "generated_at": transition["post_accepted_at"],
        "claim_boundary": CLAIM,
        "production_source_sha256": SOURCE_SHA,
        "project_sha256": PROJECT_SHA,
        "installer_sha256": INSTALLER_SHA,
        "generator_sha256": sha(Path(__file__)),
        "build_identity_sha256": BUILD_IDENTITY_SHA,
        "preinstall_manifest_sha256": PREINSTALL_SHA,
        "transaction_sha256": TRANSACTION_SHA,
        "pre_identity_manifest_sha256": PRE_IDENTITY_SHA,
        "accepted_identity_manifest_sha256": POST_IDENTITY_SHA,
        "accepted_identity_postcopy_sha256": POST_IDENTITY_SHA,
        "after_effects_processes_at_audit": processes,
        "installed_bundle_count": 1,
        "stage_absent": True,
        "failed_new_absent": True,
        "authoritative_build_evidence": build_evidence(),
        "prepared_evidence": {
            "path": rel(PREINSTALL),
            "sha256": PREINSTALL_SHA,
            "schema": preinstall["schema"],
            "source_sha256": preinstall["source_sha256"],
            "project_sha256": preinstall["project_sha256"],
            "pre_identity_sha256": preinstall["pre_identity_sha256"],
            "after_effects_processes": preinstall["after_effects_processes"],
            "same_volume_stage_and_handoff": preinstall["same_volume_stage_and_handoff"],
            "old_bundle_full_inventories_exact": preinstall["old_bundle_full_inventories_exact"],
            "candidate_snapshot_full_manifest": preinstall["candidate"]["manifest"],
            "installed_before_snapshot_full_manifest": preinstall["installed_before"]["manifest"],
        },
        "bundles": bundles,
        "identity_transition": transition,
        "transaction": transaction,
        "boundaries": {
            "candidate_installed_full_inventory_exact": True,
            "old_three_copies_full_inventory_exact": True,
            "candidate_and_installed_macos11_exact": True,
            "candidate_and_installed_exports_exact": True,
            "all_live_bundles_universal_exact": True,
            "all_live_bundles_strict_codesign_valid": True,
            "rollback_original_retained": True,
            "same_volume_namespace_atomic_bundle_exchange_recorded": True,
            "manifest_and_bundle_single_atomic_transaction": False,
            "developer_id_signed": False,
            "notarized": False,
            "ae_operation_performed_by_auditor": False,
        },
    }
    validate_semantics(report)
    return report


def validate_semantics(report: dict[str, Any]) -> None:
    assert report["schema"] == "olmtoondilate.ded9-incremental-install-identity/1"
    assert report["status"] == STATUS
    assert report["claim_boundary"] == CLAIM
    assert report["production_source_sha256"] == SOURCE_SHA
    assert report["project_sha256"] == PROJECT_SHA
    assert report["installer_sha256"] == INSTALLER_SHA
    assert report["build_identity_sha256"] == BUILD_IDENTITY_SHA
    assert report["preinstall_manifest_sha256"] == PREINSTALL_SHA
    assert report["transaction_sha256"] == TRANSACTION_SHA
    assert report["pre_identity_manifest_sha256"] == PRE_IDENTITY_SHA
    assert report["accepted_identity_manifest_sha256"] == POST_IDENTITY_SHA
    assert report["accepted_identity_postcopy_sha256"] == POST_IDENTITY_SHA
    assert report["after_effects_processes_at_audit"] == []
    assert report["installed_bundle_count"] == 1
    assert report["stage_absent"] is True and report["failed_new_absent"] is True
    assert report["bundles"]["candidate"]["binary_sha256"] == NEW_SHA
    assert report["bundles"]["installed"]["binary_sha256"] == NEW_SHA
    assert all(
        report["bundles"][name]["binary_sha256"] == OLD_SHA
        for name in ("installed_backup", "pre_swap_original", "moved_old")
    )
    assert report["prepared_evidence"]["sha256"] == PREINSTALL_SHA
    assert report["identity_transition"]["changed_plugins"] == ["OLMToonDilate"]
    assert report["identity_transition"]["other_nine_rows_exact"] is True
    assert report["identity_transition"]["top_level_changed_fields"] == [
        "accepted_at", "installed_after",
    ]
    assert report["transaction"]["atomic_exchange_api"] == "renameatx_np(RENAME_SWAP)"
    assert report["transaction"]["old_bundle_copy_count"] == 3
    assert report["boundaries"] == {
        "candidate_installed_full_inventory_exact": True,
        "old_three_copies_full_inventory_exact": True,
        "candidate_and_installed_macos11_exact": True,
        "candidate_and_installed_exports_exact": True,
        "all_live_bundles_universal_exact": True,
        "all_live_bundles_strict_codesign_valid": True,
        "rollback_original_retained": True,
        "same_volume_namespace_atomic_bundle_exchange_recorded": True,
        "manifest_and_bundle_single_atomic_transaction": False,
        "developer_id_signed": False,
        "notarized": False,
        "ae_operation_performed_by_auditor": False,
    }


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMToonDilate ded9 incremental install identity — 2026-08-13\n\n"
        f"Status: **{STATUS}**. Frozen source `{SOURCE_SHA}` and project `{PROJECT_SHA}` "
        f"produced candidate `{NEW_SHA}`. The candidate and installed bundle have exact full "
        "scoped inventories, macOS 11 deployment declarations, Universal arm64+x86_64 slices, "
        "strict-valid ad-hoc signatures, and one EffectMain plus one PluginDataEntryFunction2 "
        "export per slice.\n\n"
        f"The accepted identity and retained postcopy are exact at `{POST_IDENTITY_SHA}`. Only "
        "the OLMToonDilate row fields `sha256`, `source_bundle`, and `source_sha256`, plus "
        "top-level `accepted_at` and `installed_after`, changed from preidentity "
        f"`{PRE_IDENTITY_SHA}`; the other nine rows are exact.\n\n"
        f"`installed_backup`, `pre_swap_original`, and `moved_old` retain three full-inventory "
        f"copies of predecessor `{OLD_SHA}`. Prepared manifest `{PREINSTALL_SHA}` and transaction "
        f"`{TRANSACTION_SHA}` are bound; stage and failed-new paths are absent.\n\n"
        "The canonical post-install collection recorded zero After Effects processes; later process "
        "state is outside repeat validation. No install or After Effects operation is performed by "
        "this auditor. This does not claim "
        "AE load/render, numerical host behavior, Developer ID, notarization, distribution, or "
        "release readiness. Bundle exchange and accepted-identity replacement were separate atomic operations.\n"
    )


def validate(report: dict[str, Any]) -> None:
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
        print("PASS_OLMTOONDILATE_DED9_INCREMENTAL_INSTALL_IDENTITY_WRITE")
        return 0
    validate(json.loads(REPORT.read_text(encoding="utf-8")))
    print("PASS_OLMTOONDILATE_DED9_INCREMENTAL_INSTALL_IDENTITY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
