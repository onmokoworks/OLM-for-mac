#!/usr/bin/env python3
"""Audit the ColorKeep source-bound complete-union install and replay it hostlessly."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_colorkeep_source_bound_complete_union_20260813.py"
UNION = ROOT / "tools/emulation/test_colorkeep_source_bound_complete_union_candidate_20260813.py"
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
HANDOFF = ROOT / "handoffs/colorkeep_source_bound_complete_union_install_20260813"
CANDIDATE = ROOT / "handoffs/colorkeep_source_bound_complete_union_candidate_20260813/Product/ColorKeep.plugin"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
REPORT = ROOT / "refs/conformance/colorkeep_source_bound_complete_union_install_20260813.json"
DOC = REPORT.with_suffix(".md")
NEW_SHA = "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d"
OLD_SHA = "fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77"
PRE_IDENTITY_SHA = "e17dddbd8f26b1ac6caf65b43179689b8fa821f2cd9fe1ff23290afe29023431"
POST_IDENTITY_SHA = "4d0b65792e6ccec43577fac7cde4f78e59180cab72cec36443a7b032fea6a70a"
TRANSACTION_SHA = "87ae1b919366197a68b8f8f4fe0fe4f9c4d60b6fcefc9cb8a62ace63adec0613"
PREINSTALL_SHA = "4cd34d84281591eb05c8391c1d9985d1aff84ad11d1bb8114ef082176757cf52"
STATUS = "PASS_COLORKEEP_SOURCE_BOUND_COMPLETE_UNION_INSTALLED_AE_FREE"
TOP = {"schema", "status", "claim_boundary", "authorities", "bundles", "identity_transition", "installed_replay", "preflight", "scope"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def bundle_rows(installer) -> dict:
    paths = {
        "candidate": CANDIDATE,
        "installed": INSTALLED,
        "installed_backup": HANDOFF / "installed_backup/ColorKeep.plugin",
        "pre_swap_original": HANDOFF / "pre_swap_original/ColorKeep.plugin",
        "moved_old": HANDOFF / "moved_old/ColorKeep.plugin",
    }
    rows = {}
    for name, path in paths.items():
        current = name in {"candidate", "installed"}
        rows[name] = {"path": str(path), **installer.base.verify_bundle(path, NEW_SHA if current else OLD_SHA, current)}
    if rows["candidate"]["manifest"] != rows["installed"]["manifest"]:
        raise RuntimeError("candidate/installed inventory drift")
    if not (rows["installed_backup"]["manifest"] == rows["pre_swap_original"]["manifest"] == rows["moved_old"]["manifest"]):
        raise RuntimeError("old bundle inventory drift")
    return rows


def transition() -> dict:
    pre = json.loads(PRE_IDENTITY.read_text())
    post = json.loads(POST_COPY.read_text())
    current = json.loads(IDENTITY.read_text())
    if sha(PRE_IDENTITY) != PRE_IDENTITY_SHA or sha(POST_COPY) != POST_IDENTITY_SHA:
        raise RuntimeError("historical install identity hash drift")
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    changed = {}
    for name in sorted(pre_rows):
        fields = sorted(key for key in set(pre_rows[name]) | set(post_rows[name]) if pre_rows[name].get(key) != post_rows[name].get(key))
        if fields:
            changed[name] = fields
    top = sorted(key for key in set(pre) | set(post) if key != "plugins" and pre.get(key) != post.get(key))
    expected = {
        "changed_plugins": {"ColorKeep": ["sha256", "source_bundle", "source_sha256"]},
        "unchanged_plugins": sorted(set(pre_rows) - {"ColorKeep"}),
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "old_sha256": OLD_SHA, "new_sha256": NEW_SHA,
    }
    actual = {"changed_plugins": changed, "unchanged_plugins": sorted(set(pre_rows) - set(changed)),
              "top_level_changed_fields": top, "old_sha256": pre_rows["ColorKeep"]["sha256"],
              "new_sha256": post_rows["ColorKeep"]["sha256"]}
    if actual != expected:
        raise RuntimeError(f"identity transition drift: {actual}")
    current_rows = {row["plugin"]: row for row in current["plugins"]}
    if set(current_rows) != set(post_rows) or current_rows["ColorKeep"] != post_rows["ColorKeep"]:
        raise RuntimeError("current accepted identity no longer retains the installed ColorKeep row")
    if current_rows["ColorKeep"]["sha256"] != NEW_SHA:
        raise RuntimeError("current accepted ColorKeep executable drift")
    return actual


def installed_replay() -> dict:
    union = load(UNION, "colorkeep_complete_union")
    union.BINARY = INSTALLED / "Contents/MacOS/ColorKeep"
    return {"legacy_union": union.check_legacy(), "count9_union": union.check_count9()}


def preflight() -> dict:
    script = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"
    result = subprocess.run(["python3", str(script)], cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 2:
        raise RuntimeError(f"preflight return drift: {result.returncode}")
    payload = json.loads(result.stdout)
    if payload.get("status") != "ae_not_running" or payload.get("after_effects") != []:
        raise RuntimeError("preflight AE state drift")
    bundles = payload.get("bundles", [])
    if len(bundles) != 10 or not all(row["bundle_count"] == 1 and row["sha256_exact"] and row["universal_exact"] and row["codesign_exact"] for row in bundles):
        raise RuntimeError("preflight install identity drift")
    return {"returncode": 2, "status": "ae_not_running", "plugin_rows": 10,
            "all_identity_universal_codesign_exact": True,
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest()}


def authorities() -> dict:
    return {"production_source_sha256": sha(SOURCE),
            "installer_sha256": sha(INSTALLER), "union_generator_sha256": sha(UNION),
            "preinstall_sha256": sha(PREINSTALL), "transaction_sha256": sha(TRANSACTION),
            "pre_identity_sha256": sha(PRE_IDENTITY),
            "install_post_identity_sha256": sha(POST_COPY),
            "current_accepted_identity_sha256": sha(IDENTITY)}


def generate() -> dict:
    if sha(PREINSTALL) != PREINSTALL_SHA or sha(TRANSACTION) != TRANSACTION_SHA:
        raise RuntimeError("transaction evidence drift")
    installer = load(INSTALLER, "colorkeep_complete_union_installer")
    if installer.base.ae_pids() != []:
        raise RuntimeError("After Effects is running")
    return {
        "schema": "colorkeep.source-bound-complete-union-install/1", "status": STATUS,
        "claim_boundary": "ColorKeep-only hostless historical install transition, current accepted ColorKeep-row identity, and complete bounded public replay. Later changes to other accepted identity rows are outside this transaction. No AE launch/load/render, Developer ID, notarization, or arbitrary source/tuple claim.",
        "authorities": authorities(), "bundles": bundle_rows(installer),
        "identity_transition": transition(), "installed_replay": installed_replay(),
        "preflight": [preflight(), preflight()],
        "scope": {"installed": True, "arm64": True, "x86_64_rosetta": True,
                  "native_after_effects": False, "after_effects_launched": False, "rollback_copies": 3},
    }


def validate(report: dict) -> None:
    if set(report) != TOP or report["schema"] != "colorkeep.source-bound-complete-union-install/1" or report["status"] != STATUS:
        raise RuntimeError("schema/status drift")
    if report["authorities"] != authorities() or report["identity_transition"] != transition():
        raise RuntimeError("authority/identity drift")
    installer = load(INSTALLER, "colorkeep_complete_union_installer_validate")
    if report["bundles"] != bundle_rows(installer):
        raise RuntimeError("bundle drift")
    if report["scope"] != {"installed": True, "arm64": True, "x86_64_rosetta": True,
                            "native_after_effects": False, "after_effects_launched": False, "rollback_copies": 3}:
        raise RuntimeError("scope drift")
    replay = report["installed_replay"]
    if replay["legacy_union"]["paths_per_slice"] != 10 or replay["legacy_union"]["source_helper_active_mutation_rejects"] != 18:
        raise RuntimeError("legacy replay drift")
    if any(row != {"paths": 5, "padded_output_sha256": "2e68fc7a643641652edb27b6400cbdb2358b10c438893a8c346f8efd1ef7aebe", "rejects": 136, "all_precommit_atomic": True}
           for row in replay["count9_union"]["architectures"].values()):
        raise RuntimeError("count9 replay drift")
    if len(report["preflight"]) != 2 or any(row["returncode"] != 2 or row["plugin_rows"] != 10 or not row["all_identity_universal_codesign_exact"] for row in report["preflight"]):
        raise RuntimeError("preflight drift")


def markdown(report: dict) -> str:
    return (
        "# ColorKeep source-bound complete-union install — 2026-08-13\n\n"
        f"Status: `{STATUS}`\n\n"
        "The candidate and installed bundle inventories are exact at binary `dae59a6…`; three durable old-bundle copies retain `fcd501…`. The retained install-time manifests prove that only the ColorKeep row and two top-level timestamps changed in that transaction. The current accepted manifest still retains that exact ColorKeep row while allowing later transactions for other plug-ins. The installed arm64 and Rosetta x86_64 slices replay all 10 legacy and all 5 count9 paths; count9 retains 136 atomic rejects per slice. Two all-ten preflights report the expected `ae_not_running` state with all identities, Universal slices, and signatures exact.\n\n"
        f"Boundary: {report['claim_boundary']}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = generate()
        validate(report)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(report))
    else:
        report = json.loads(REPORT.read_text())
        validate(report)
        if DOC.read_text() != markdown(report):
            raise RuntimeError("markdown drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
