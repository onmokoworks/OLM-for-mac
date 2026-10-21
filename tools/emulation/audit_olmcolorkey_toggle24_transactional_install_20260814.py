#!/usr/bin/env python3
"""Audit the installed OLMColorKey 60-cell transactional update without AE."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmcolorkey_toggle24_incremental_20260814.py"
REPORT = ROOT / "refs/conformance/olmcolorkey_toggle24_transactional_install_20260814.json"
DOC = REPORT.with_suffix(".md")
POST_IDENTITY_SHA256 = "9d7402a37c9e4e5204860b0bcff7efed00708cb469e26a9d422a0c3401775bcd"
DEPENDENCIES = {
    "production_source": ROOT / "mac/OLMColorKey/OLMColorKey.cpp",
    "project": ROOT / "mac/OLMColorKey/Mac/OLMColorKey.xcodeproj/project.pbxproj",
    "installer": INSTALLER,
    "candidate_build_identity": ROOT / "handoffs/olmcolorkey_toggle24_universal_candidate_20260814/build_identity.json",
    "source_closure": ROOT / "refs/conformance/olmcolorkey_public_source_bound_closure_20260813.json",
    "installed_closure": ROOT / "refs/conformance/olmcolorkey_current_installed_public_closure_20260813.json",
    "all10_preflight": ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py",
}
EXPECTED = {
    "production_source": "7c66240d5813e240663d06fe342d45b73b9b2ce2f2d8b0852ffe7f73351e4001",
    "project": "b5b77f24dec0a1ec9d426c20d68384f03d3381145f1494fec59c491bcec2d72b",
    "installer": "781635d12b48f2e3e8c9961c014bc73f023c33dbe306429a96a2e2dd831a6d93",
    "candidate_build_identity": "f768e6b3413e4b6ebaee285ea478040a26311c7a6ff8e3b33b0d2dacf728bdec",
    "source_closure": "f27a0d9157a0bf9a53f5a87f7207555b3679561360e35600c6eaf9b51668e607",
    "installed_closure": "fbc71bb938d127a430f37665234728468b00e6053312e25239725d1cb14d65a6",
    "all10_preflight": "1065dfabbde20bff12fe6e2bcdce638905bf13e726635c7d7bf617fcfa5f9d96",
}
CLAIMS_NOT_MADE = [
    "No After Effects or aerender launch",
    "No native-AE numerical claim",
    "No numerical generalization beyond the source/tuple/geometry-bound 60 cells",
    "No Developer ID, notarization, or distribution acceptance claim",
]
TOP_KEYS = {
    "schema", "status", "claim_boundary", "authorities", "installed_predecessor",
    "installed_candidate", "identity_transition", "transaction", "all10_preflight",
    "after_effects_processes", "claims_not_made",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("colorkey_toggle24_installer", INSTALLER)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load installer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def authorities() -> dict[str, str]:
    observed = {name: sha(path) for name, path in DEPENDENCIES.items()}
    if observed != EXPECTED:
        raise RuntimeError(f"authority drift: {observed}")
    return observed


def run_all10_preflight() -> dict[str, object]:
    command = [sys.executable, str(DEPENDENCIES["all10_preflight"])]
    results = [subprocess.run(command, cwd=ROOT, capture_output=True) for _ in range(2)]
    if any(result.returncode != 2 for result in results) or results[0].stdout != results[1].stdout:
        raise RuntimeError("all-ten preflight is not two-pass exact")
    payload = json.loads(results[0].stdout)
    if payload.get("status") != "ae_not_running" or payload.get("after_effects") != []:
        raise RuntimeError("all-ten AE state drift")
    bundles = payload.get("bundles", [])
    if len(bundles) != 10 or any(
        row.get("bundle_count") != 1
        or row.get("sha256_exact") is not True
        or row.get("universal_exact") is not True
        or row.get("codesign_exact") is not True
        for row in bundles
    ):
        raise RuntimeError("all-ten identity drift")
    target = [row for row in bundles if row.get("name") == "OLMColorKey"]
    if len(target) != 1 or target[0].get("sha256") != "701ae9192e19d3e97dd33450e37ae97d90d9be5803ab663405507ed5e3659ca7":
        raise RuntimeError("ColorKey all-ten identity drift")
    return {
        "passes": 2,
        "returncode": 2,
        "status": "ae_not_running",
        "bundle_count": 10,
        "byte_identical": True,
        "stdout_sha256": hashlib.sha256(results[0].stdout).hexdigest(),
    }


def generate() -> dict[str, Any]:
    auth = authorities()
    installer = load_installer()
    if sha(installer.POST_IDENTITY_COPY) != POST_IDENTITY_SHA256 or installer.ae_pids():
        raise RuntimeError("retained post-install identity or AE state drift")
    if installer.STAGED.exists() or installer.FAILED_NEW.exists():
        raise RuntimeError("staged or failed-new residue exists")
    candidate = installer.verify_bundle(installer.CANDIDATE, installer.EXPECTED_NEW, True)
    installed = installer.verify_bundle(installer.INSTALLED, installer.EXPECTED_NEW, True)
    if candidate["manifest"] != installed["manifest"]:
        raise RuntimeError("candidate/installed inventory mismatch")
    old_rows = [
        installer.verify_bundle(path, installer.EXPECTED_OLD, False)
        for path in (installer.BACKUP, installer.PRE_SWAP, installer.MOVED_OLD)
    ]
    if not all(row["manifest"] == old_rows[0]["manifest"] for row in old_rows[1:]):
        raise RuntimeError("predecessor inventory mismatch")
    before = json.loads(installer.PRE_IDENTITY.read_text())
    after = json.loads(installer.POST_IDENTITY_COPY.read_text())
    transition = installer.transition(before, after)
    expected_transition = {
        "changed_plugins": ["OLMColorKey"],
        "changed_fields": {"OLMColorKey": ["sha256", "source_bundle", "source_sha256"]},
        "unchanged_plugins": sorted(installer.PLUGINS - {"OLMColorKey"}),
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "other_nine_rows_exact": True,
    }
    if transition != expected_transition:
        raise RuntimeError("identity transition drift")
    current = json.loads(installer.IDENTITY.read_text())
    retained_rows = [row for row in after.get("plugins", []) if row.get("plugin") == "OLMColorKey"]
    current_rows = [row for row in current.get("plugins", []) if row.get("plugin") == "OLMColorKey"]
    if len(retained_rows) != 1 or current_rows != retained_rows:
        raise RuntimeError("current accepted ColorKey row differs from retained post-install row")
    transaction = json.loads(installer.TRANSACTION.read_text())
    if transaction.get("status") != "installed_ae_not_launched" or transaction.get("post_identity_sha256") != POST_IDENTITY_SHA256:
        raise RuntimeError("transaction record drift")
    return {
        "schema": "olmcolorkey.toggle24-transactional-install-audit/1",
        "status": "installed_identity_closed_ae_deferred",
        "claim_boundary": "Current workspace and exact on-disk bundle identities; hostless public60 replay; AE deferred to a later batch",
        "authorities": auth,
        "installed_predecessor": {
            "binary_sha256": installer.EXPECTED_OLD,
            "retained_full_bundle_copies": 3,
            "full_inventories_exact": True,
            "full_inventory": old_rows[0]["manifest"],
        },
        "installed_candidate": {
            "binary_sha256": installer.EXPECTED_NEW,
            "candidate_installed_full_inventory_exact": True,
            "architectures": installed["architectures"],
            "strict_codesign": installed["strict_codesign"],
            "signing_kind": installed["signing_kind"],
            "minimum_versions": installed["macho_slice_minimum_versions"],
            "required_exports": installed["required_exports"],
            "full_inventory": installed["manifest"],
        },
        "identity_transition": transition,
        "transaction": {
            "sha256": sha(installer.TRANSACTION),
            "post_identity_sha256": POST_IDENTITY_SHA256,
            "same_volume_atomic_exchange": transaction.get("atomic_exchange", {}).get("method") == "renameatx_np(RENAME_SWAP)",
            "rollback_bundle_retained": True,
        },
        "all10_preflight": run_all10_preflight(),
        "after_effects_processes": [],
        "claims_not_made": CLAIMS_NOT_MADE,
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != TOP_KEYS:
        raise RuntimeError("top-level schema drift")
    if report != generate():
        raise RuntimeError("saved report differs from live audit")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMColorKey toggle24 transactional install audit\n\n"
        f"Status: `{report['status']}`.\n\n"
        "The Universal public60 candidate and installed bundle are inventory-exact. "
        "Three exact predecessor bundles and the ColorKey-only identity transition are retained. "
        "All-ten installed preflight is byte-identical across two passes with AE stopped. "
        "AE remains deferred to a later batched checkpoint.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(live))
    if not REPORT.is_file() or not DOC.is_file():
        raise RuntimeError("canonical report absent; use --write intentionally")
    saved = json.loads(REPORT.read_text())
    validate(saved)
    if DOC.read_text() != markdown(saved):
        raise RuntimeError("markdown drift")
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
