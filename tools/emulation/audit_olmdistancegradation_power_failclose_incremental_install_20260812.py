#!/usr/bin/env python3
"""Validate the recoverable Distance PF32 Power fail-close install transition."""
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
HANDOFF = ROOT / "handoffs/olmdistancegradation_pf32_power_failclose_install_20260812"
SOURCE_BUNDLE = ROOT / "handoffs/olmdistancegradation_pf32_power_failclose_universal_candidate_20260812/product/OLMDistanceGradation.plugin"
INSTALLED_BUNDLE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMDistanceGradation.plugin"
BACKUP_BUNDLE = HANDOFF / "installed_backup/OLMDistanceGradation.plugin"
PRE_SWAP_BUNDLE = HANDOFF / "pre_swap_original/OLMDistanceGradation.plugin"
MOVED_OLD_BUNDLE = HANDOFF / "moved_old/OLMDistanceGradation.plugin"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SOURCE = ROOT / "mac/OLMDistanceGradation/OLMDistanceGradation.cpp"
INSTALL_SCRIPT = ROOT / "scripts/install_olmdistancegradation_pf32_power_failclose_20260812.py"
CODEGEN = ROOT / "refs/conformance/olmdistancegradation_pf32_mode5_universal_codegen_20260812.json"
PUBLIC = ROOT / "refs/conformance/olmdistancegradation_public_smart_owner_contract_20260812.json"
REPORT = ROOT / "refs/conformance/olmdistancegradation_power_failclose_incremental_install_identity_20260812.json"
DOC = REPORT.with_suffix(".md")

OLD_SHA = "b9971c6480088329ee77a2b01d8187f29b73b1cc06633d77dc3029a4012bfc7a"
NEW_SHA = "231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605"
SOURCE_SHA = "06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5"
PRE_IDENTITY_SHA = "1ad14c2f9c9fe1732ec6155ab49d33a479e8ce6c881c56d626f6a6881f8fefea"
POST_IDENTITY_SHA = "90e37eefd68f990e137d23d46212c7039ec49f03e86bfe076765cc350da3820a"
INSTALL_SCRIPT_SHA = "8378ef365b30bd5f6ef339b592d3c38d828c828b44b03110851f36a36bcc551a"
CODEGEN_SHA = "379ec9dc7ef7f5a499ce4f3079a0f8d5df9c6ba2e6e3fd45af5fc5bce771e646"
PUBLIC_SHA = "963e0f3f594eb3af5bea79159021ce126b5bd38aba749a4ef60b7fa0b0950f75"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
CLAIM = (
    "Observed current/rollback bundle bytes and accepted-manifest transition for only "
    "OLMDistanceGradation after the PF32 Power fail-close install; the retained install "
    "script identity is recorded, but its historical invocation sequence is not independently reconstructed. "
    "No AE load/render or numerical-host claim."
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMDistanceGradation"


def bundle_manifest(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise AssertionError(f"missing bundle: {bundle}")
    rows: list[dict[str, object]] = []
    paths = sorted([bundle, *bundle.rglob("*")], key=lambda item: item.relative_to(bundle).as_posix())
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
    binary = executable(bundle)
    lipo = run("lipo", "-archs", str(binary))
    signature = run("codesign", "--verify", "--deep", "--strict", str(bundle))
    detail = run("codesign", "-dv", "--verbose=4", str(bundle))
    archs = lipo.stdout.split() if lipo.returncode == 0 else []
    detail_text = detail.stderr + detail.stdout
    return {
        "path": rel(bundle) if bundle.is_relative_to(ROOT) else str(bundle),
        "binary_sha256": sha(binary),
        "architectures": archs,
        "universal_exact": set(archs) == {"arm64", "x86_64"},
        "strict_codesign": signature.returncode == 0,
        "signing_kind": "ad-hoc" if "Signature=adhoc" in detail_text and "TeamIdentifier=not set" in detail_text else "other",
        "manifest": bundle_manifest(bundle),
    }


def ae_pids() -> list[int]:
    result = run("pgrep", "-f", r"/After Effects|AfterFX|aerender")
    if result.returncode not in (0, 1):
        raise AssertionError("pgrep failed")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def installed_count() -> int:
    media_core = INSTALLED_BUNDLE.parent
    return len(list(media_core.glob("OLMDistanceGradation.plugin")))


def expected_bundles() -> dict[str, dict[str, object]]:
    return {
        name: live_bundle(path) for name, path in (
            ("candidate", SOURCE_BUNDLE),
            ("installed", INSTALLED_BUNDLE),
            ("installed_backup", BACKUP_BUNDLE),
            ("pre_swap_original", PRE_SWAP_BUNDLE),
            ("moved_old", MOVED_OLD_BUNDLE),
        )
    }


def validate(report: dict[str, object]) -> None:
    assert report["schema"] == "olmdistancegradation.power-failclose-incremental-install-identity/1"
    assert report["status"] == "PASS_RECOVERABLE_DISTANCE_POWER_FAILCLOSE_INSTALL_IDENTITY"
    assert report["claim_boundary"] == CLAIM
    assert sha(SOURCE) == report["production_source_sha256"] == SOURCE_SHA
    assert sha(INSTALL_SCRIPT) == report["install_script_sha256"] == INSTALL_SCRIPT_SHA
    assert sha(CODEGEN) == report["universal_codegen_report_sha256"] == CODEGEN_SHA
    assert sha(PUBLIC) == report["public_contract_report_sha256"] == PUBLIC_SHA
    assert sha(PRE_IDENTITY) == report["pre_identity_manifest_sha256"] == PRE_IDENTITY_SHA
    assert sha(IDENTITY) == report["accepted_identity_manifest_sha256"] == POST_IDENTITY_SHA
    assert report["after_effects_processes"] == ae_pids() == []
    assert report["installed_bundle_count"] == installed_count() == 1

    live = expected_bundles()
    assert report["bundles"] == live
    assert live["candidate"]["binary_sha256"] == live["installed"]["binary_sha256"] == NEW_SHA
    assert live["candidate"]["manifest"] == live["installed"]["manifest"]
    rollback_names = ("installed_backup", "pre_swap_original", "moved_old")
    assert all(live[name]["binary_sha256"] == OLD_SHA for name in rollback_names)
    assert all(live[name]["manifest"] == live["installed_backup"]["manifest"] for name in rollback_names)
    assert all(row["universal_exact"] and row["strict_codesign"] and row["signing_kind"] == "ad-hoc" for row in live.values())

    pre = json.loads(PRE_IDENTITY.read_text())
    post = json.loads(IDENTITY.read_text())
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    assert set(pre_rows) == set(post_rows) == PLUGINS
    assert [name for name in sorted(PLUGINS) if pre_rows[name] != post_rows[name]] == ["OLMDistanceGradation"]
    assert all(pre_rows[name] == post_rows[name] for name in PLUGINS - {"OLMDistanceGradation"})
    assert pre_rows["OLMDistanceGradation"]["sha256"] == pre_rows["OLMDistanceGradation"]["source_sha256"] == OLD_SHA
    distance = post_rows["OLMDistanceGradation"]
    assert distance == {
        "architectures": ["x86_64", "arm64"],
        "codesign_exact": True,
        "installed_bundle": str(INSTALLED_BUNDLE),
        "installed_bundle_count": 1,
        "plugin": "OLMDistanceGradation",
        "sha256": NEW_SHA,
        "source_bundle": rel(SOURCE_BUNDLE),
        "source_installed_exact": True,
        "source_sha256": NEW_SHA,
        "universal_exact": True,
    }
    assert pre["accepted_at"] == pre["installed_after"]
    assert post["accepted_at"] == post["installed_after"]
    assert pre["accepted_at"] != post["accepted_at"]
    assert {key for key in pre if pre.get(key) != post.get(key)} == {"accepted_at", "installed_after", "plugins"}
    assert report["identity_transition"] == {
        "changed_plugins": ["OLMDistanceGradation"],
        "unchanged_plugins": sorted(PLUGINS - {"OLMDistanceGradation"}),
        "old_executable_sha256": OLD_SHA,
        "new_executable_sha256": NEW_SHA,
        "pre_accepted_at": pre["accepted_at"],
        "post_accepted_at": post["accepted_at"],
        "distance_row_changed_fields": ["sha256", "source_bundle", "source_sha256"],
        "top_level_changed_fields": ["accepted_at", "installed_after"],
    }
    assert report["observed_recovery"] == {
        "old_bundle_copies": 3,
        "old_bundle_full_manifests_exact": True,
        "new_candidate_installed_full_manifests_exact": True,
        "installed_bundle_count": 1,
        "install_script_identity_retained": True,
        "historical_invocation_sequence_independently_reconstructed": False,
    }


def generate() -> dict[str, object]:
    pre = json.loads(PRE_IDENTITY.read_text())
    post = json.loads(IDENTITY.read_text())
    report: dict[str, object] = {
        "schema": "olmdistancegradation.power-failclose-incremental-install-identity/1",
        "status": "PASS_RECOVERABLE_DISTANCE_POWER_FAILCLOSE_INSTALL_IDENTITY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": CLAIM,
        "production_source_sha256": sha(SOURCE),
        "install_script_sha256": sha(INSTALL_SCRIPT),
        "universal_codegen_report_sha256": sha(CODEGEN),
        "public_contract_report_sha256": sha(PUBLIC),
        "pre_identity_manifest_sha256": sha(PRE_IDENTITY),
        "accepted_identity_manifest_sha256": sha(IDENTITY),
        "after_effects_processes": ae_pids(),
        "installed_bundle_count": installed_count(),
        "bundles": expected_bundles(),
        "identity_transition": {
            "changed_plugins": ["OLMDistanceGradation"],
            "unchanged_plugins": sorted(PLUGINS - {"OLMDistanceGradation"}),
            "old_executable_sha256": OLD_SHA,
            "new_executable_sha256": NEW_SHA,
            "pre_accepted_at": pre["accepted_at"],
            "post_accepted_at": post["accepted_at"],
            "distance_row_changed_fields": ["sha256", "source_bundle", "source_sha256"],
            "top_level_changed_fields": ["accepted_at", "installed_after"],
        },
        "observed_recovery": {
            "old_bundle_copies": 3,
            "old_bundle_full_manifests_exact": True,
            "new_candidate_installed_full_manifests_exact": True,
            "installed_bundle_count": 1,
            "install_script_identity_retained": True,
            "historical_invocation_sequence_independently_reconstructed": False,
        },
    }
    validate(report)
    return report


def write() -> None:
    report = generate()
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    DOC.write_text(
        "# OLMDistanceGradation PF32 Power fail-close incremental install identity\n\n"
        "Status: **PASS_RECOVERABLE_DISTANCE_POWER_FAILCLOSE_INSTALL_IDENTITY**. The current "
        f"candidate and installed executable are `{NEW_SHA}` and their complete scoped bundle "
        f"inventories match. Three retained rollback copies are complete and equal at `{OLD_SHA}`. "
        "Only the Distance row and the two acceptance timestamps changed in the ten-plugin identity "
        "manifest. The retained install script is identity-bound, but this report does not independently "
        "reconstruct its historical invocation sequence. This is install identity only; it makes no AE "
        "load/render or numerical-host claim. Signatures are strict-valid ad-hoc, not Developer ID or "
        "notarization evidence.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        write()
    else:
        validate(json.loads(REPORT.read_text()))
    print("PASS_OLMDISTANCEGRADATION_POWER_FAILCLOSE_INCREMENTAL_INSTALL_IDENTITY_20260812")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
