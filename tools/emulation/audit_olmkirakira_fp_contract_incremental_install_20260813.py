#!/usr/bin/env python3
"""Post-install identity closure for the Kira FP-contract correction."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmkirakira_fp_contract_incremental_20260813.py"
HANDOFF = ROOT / "handoffs/olmkirakira_fp_contract_incremental_install_20260813"
BUILD_IDENTITY = ROOT / "handoffs/olmkirakira_fp_contract_universal_candidate_20260813/build_identity.json"
PREPARED = HANDOFF / "prepared_install.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
REPORT = ROOT / "refs/conformance/olmkirakira_fp_contract_incremental_install_identity_20260813.json"
MARKDOWN = REPORT.with_suffix(".md")

PINS = {
    "source": "8f3ccda261b525f58e9abb6d942986f5f71ce6c67758aa7edfecc50a557f3e8f",
    "old_binary": "69da64666478b25957aa268f6bb6fbc869c3d50b61759f9ca00172045afb5194",
    "new_binary": "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18",
    "installer": "064402415674c46e39cdf00365a0ba3528525cbf1d3179767bd173296222f237",
    "build_identity": "9bf6570d46ad6cc5e181b28c21ff4077a127c4e850fe29f7a9ef892b2404b2d5",
    "prepared": "46f43e1cc06a6451cc17d83004e3a3b35df9bc8d7d82eb108966ecb7623ce0c8",
    "transaction": "0e8aef11b524e39041b32a3a4a5b453ea2dc004fbd804e86cad322a894b5c559",
    "pre_identity": "cc9cb7edd30c23aef06b6ef4aab819763f900a1d40938e5b5a2b66758bb566be",
    "post_identity": "e17dddbd8f26b1ac6caf65b43179689b8fa821f2cd9fe1ff23290afe29023431",
}
STATUS = "PASS_OLMKIRAKIRA_FP_CONTRACT_INCREMENTAL_INSTALL_IDENTITY_NO_AE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("kira_fp_installer_for_audit", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed: {name}")
        found += [f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit()]
    return found


def identity_transition(pre: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    pre_rows = {row["plugin"]: row for row in pre["plugins"]}
    post_rows = {row["plugin"]: row for row in post["plugins"]}
    if set(pre_rows) != set(post_rows) or len(pre_rows) != 10:
        raise RuntimeError("identity plugin set drift")
    changed = {}
    for name in sorted(pre_rows):
        fields = sorted(key for key in set(pre_rows[name]) | set(post_rows[name]) if pre_rows[name].get(key) != post_rows[name].get(key))
        if fields:
            changed[name] = fields
    top = sorted(key for key in set(pre) | set(post) if key != "plugins" and pre.get(key) != post.get(key))
    expected = {"OLMKiraKira": ["sha256", "source_bundle", "source_sha256"]}
    if changed != expected or top != ["accepted_at", "installed_after"]:
        raise RuntimeError(f"identity transition is not Kira-only: {changed}, {top}")
    return {
        "changed_plugins_and_fields": changed,
        "top_level_changed_fields": top,
        "other_nine_rows_exact": all(pre_rows[name] == post_rows[name] for name in pre_rows if name != "OLMKiraKira"),
        "old_binary_sha256": pre_rows["OLMKiraKira"]["sha256"],
        "new_binary_sha256": post_rows["OLMKiraKira"]["sha256"],
    }


def generate() -> dict[str, Any]:
    installer = load_installer()
    live = {
        "source": sha256(installer.SOURCE),
        "old_binary": installer.OLD_SHA,
        "new_binary": installer.NEW_SHA,
        "installer": sha256(INSTALLER),
        "build_identity": sha256(BUILD_IDENTITY),
        "prepared": sha256(PREPARED),
        "transaction": sha256(TRANSACTION),
        "pre_identity": sha256(PRE_IDENTITY),
        "post_identity": sha256(POST_IDENTITY),
    }
    if live != PINS:
        raise RuntimeError(f"install authority drift: {live}")
    if ae_processes():
        raise RuntimeError("AE process present during post-install audit")
    candidate = installer.verify_bundle(installer.CANDIDATE, installer.NEW_SHA)
    installed = installer.verify_bundle(installer.INSTALLED, installer.NEW_SHA)
    old = {
        "installed_backup": installer.verify_bundle(installer.BACKUP, installer.OLD_SHA),
        "pre_swap_original": installer.verify_bundle(installer.PRE_SWAP, installer.OLD_SHA),
        "moved_old": installer.verify_bundle(installer.MOVED_OLD, installer.OLD_SHA),
    }
    if candidate["inventory"] != installed["inventory"]:
        raise RuntimeError("candidate and installed inventories differ")
    if len({json.dumps(value["inventory"], sort_keys=True) for value in old.values()}) != 1:
        raise RuntimeError("old rollback inventories differ")
    pre = json.loads(PRE_IDENTITY.read_text())
    post = json.loads(POST_IDENTITY.read_text())
    current = json.loads(IDENTITY.read_text())
    post_rows = [row for row in post.get("plugins", []) if row.get("plugin") == "OLMKiraKira"]
    current_rows = [row for row in current.get("plugins", []) if row.get("plugin") == "OLMKiraKira"]
    if len(post_rows) != 1 or len(current_rows) != 1 or post_rows[0] != current_rows[0]:
        raise RuntimeError("current accepted Kira row differs from retained post-install row")
    current_names = [row.get("plugin") for row in current.get("plugins", [])]
    if len(current_names) != 10 or len(set(current_names)) != 10:
        raise RuntimeError("current accepted identity is not an exact ten-plugin manifest")
    transition = identity_transition(pre, post)
    transaction = json.loads(TRANSACTION.read_text())
    if transaction["status"] != "installed" or transaction["after_effects_processes_before_after"] != [[], []]:
        raise RuntimeError("transaction status/process boundary drift")
    return {
        "schema": "olmkirakira.fp-contract-incremental-install-identity/1",
        "status": STATUS,
        "claim_boundary": "Observed Kira-only atomic install identity and rollback closure. No AE launch, native-AE numerical, Developer ID, notarization, distribution, or release claim.",
        "authorities": live,
        "after_effects_processes": [],
        "candidate_installed_full_inventory_exact": True,
        "old_rollback_copy_count": 3,
        "old_rollback_full_inventories_exact": True,
        "candidate": candidate,
        "installed": installed,
        "old_copies": old,
        "identity_transition": transition,
        "transaction": transaction,
        "scope": {
            "installed": True,
            "after_effects_launched": False,
            "native_after_effects": False,
            "developer_id_or_notarization": False,
        },
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != {
        "schema", "status", "claim_boundary", "authorities", "after_effects_processes",
        "candidate_installed_full_inventory_exact", "old_rollback_copy_count",
        "old_rollback_full_inventories_exact", "candidate", "installed", "old_copies",
        "identity_transition", "transaction", "scope",
    }:
        raise RuntimeError("install report schema drift")
    if report["schema"] != "olmkirakira.fp-contract-incremental-install-identity/1" or report["status"] != STATUS or report["authorities"] != PINS:
        raise RuntimeError("install report identity drift")
    if report["after_effects_processes"] != [] or not report["candidate_installed_full_inventory_exact"]:
        raise RuntimeError("install/process relation drift")
    if report["old_rollback_copy_count"] != 3 or not report["old_rollback_full_inventories_exact"]:
        raise RuntimeError("rollback relation drift")
    if report["candidate"]["inventory"] != report["installed"]["inventory"]:
        raise RuntimeError("persisted candidate/installed inventory mismatch")
    if report["candidate"]["binary_sha256"] != PINS["new_binary"] or report["installed"]["binary_sha256"] != PINS["new_binary"]:
        raise RuntimeError("new binary identity drift")
    old_inventories = [value["inventory"] for value in report["old_copies"].values()]
    if set(report["old_copies"]) != {"installed_backup", "pre_swap_original", "moved_old"} or len({json.dumps(value, sort_keys=True) for value in old_inventories}) != 1:
        raise RuntimeError("rollback copy schema/inventory drift")
    if any(value["binary_sha256"] != PINS["old_binary"] for value in report["old_copies"].values()):
        raise RuntimeError("rollback binary identity drift")
    if report["identity_transition"] != {
        "changed_plugins_and_fields": {"OLMKiraKira": ["sha256", "source_bundle", "source_sha256"]},
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "other_nine_rows_exact": True,
        "old_binary_sha256": PINS["old_binary"],
        "new_binary_sha256": PINS["new_binary"],
    }:
        raise RuntimeError("identity transition drift")
    if report["transaction"]["post_identity_sha256"] != PINS["post_identity"]:
        raise RuntimeError("transaction post identity drift")
    if report["scope"] != {"installed": True, "after_effects_launched": False, "native_after_effects": False, "developer_id_or_notarization": False}:
        raise RuntimeError("install scope escalation")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMKiraKira FP-contract incremental install identity (2026-08-13)\n\n"
        f"Status: `{report['status']}`\n\n"
        f"Candidate and installed executable are exact at `{PINS['new_binary']}` with full "
        "bundle-inventory equality. Three independently retained predecessor copies are exact "
        f"at `{PINS['old_binary']}`. The accepted identity transition changes only Kira's "
        "three binary/source fields plus the two top-level timestamps; the other nine rows are exact.\n\n"
        "Boundary: no After Effects process was launched. This is install identity evidence, not "
        "native-AE, Developer ID, notarization, distribution, or release evidence.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    validate(live)
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(live))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("post-install report missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("post-install report differs from live state")
    print(STATUS)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_FP_CONTRACT_INSTALL_IDENTITY: {exc}", file=sys.stderr)
        raise
