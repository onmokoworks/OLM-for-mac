#!/usr/bin/env python3
"""Audit the prepared OLMSmoother2 39-cell incremental installation."""

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
INSTALLER = ROOT / "scripts/install_olmsmoother2_pf8_pf16_pf32_incremental_20260814.py"
REPORT = ROOT / "refs/conformance/olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.json"
DOC = REPORT.with_suffix(".md")
DEPENDENCIES = {
    "production_source": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
    "project": ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj/project.pbxproj",
    "installer": INSTALLER,
    "candidate_build_identity": ROOT / "handoffs/olmsmoother2_pf8_pf16_pf32_public_smart_candidate_20260814/build_identity.json",
    "pf8_public_closure": ROOT / "refs/conformance/olmsmoother2_pf8_legacy12_public_closure_20260814.json",
    "pf16_public_closure": ROOT / "refs/conformance/olmsmoother2_case07_pf16_unique_public_closure_20260814.json",
    "pf32_public_closure": ROOT / "refs/conformance/olmsmoother2_case07_public_smart_closure_20260814.json",
    "base_public_guard": ROOT / "refs/conformance/olmsmoother_public_admission_guard_closure_20260812.json",
    "official_runner": ROOT / "scripts/run_olm_mac_fixed_fixture_regression_20260805.py",
    "all10_installed_preflight": ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py",
}
EXPECTED = {
    "production_source": "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
    "project": "8a5525814eb7917b4ee124c507caf6a085200decf6072b32d52779e38279b89a",
    "installer": "b85a68eb800491cef972c2aa149e6e89fda32a9596d97d03784b3e2fb0e263cb",
    "candidate_build_identity": "c0852db33833084681012fa4a854f21bd50f96d29b392deb784df0fa89a6bd0b",
    "pf8_public_closure": "f7053387b000cfcb61d555723b665af75266af039ea5c1e2ace81ebb8a7800d7",
    "pf16_public_closure": "3da92c902d05da8de59a020918429c8c7fa51a69b5495c66541a9204c6cc86d3",
    "pf32_public_closure": "19758a53a11cbbfd5aa192144570ebcaa87c5a0b3d207cf655fb3072d1d17dfe",
    "base_public_guard": "446e9db01b9bf16fd35a24693fb5fde81fd8f01573280d2c4ca299863e48c2a5",
    "official_runner": "d0c35f0a5d992068051bd255164450235bd904958d87fc336efa457e0dc7b1e4",
    "all10_installed_preflight": "1065dfabbde20bff12fe6e2bcdce638905bf13e726635c7d7bf617fcfa5f9d96",
}
REPORT_KEYS = {
    "schema", "status", "claim_boundary", "authorities", "installed_predecessor",
    "candidate", "identity_transition", "transaction_state", "prepared_evidence",
    "after_effects_processes", "all10_preflight", "claims_not_made",
}
CLAIMS_NOT_MADE = [
    "No After Effects or aerender launch",
    "No installed-new-binary claim until the explicit install transaction completes",
    "No numerical generalization beyond the 39 source/tuple/geometry-bound Smart cells",
    "No native Windows output-world memory claim for host-presentation transforms",
    "No Developer ID, notarization, or distribution acceptance claim",
]
POST_IDENTITY_SHA256 = "7212ca5c887826eeb7d7f33474c87aed79f37407fe39472e182639fcdb9f6f16"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("smoother2_transactional_installer", INSTALLER)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load installer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def authorities() -> dict[str, str]:
    values = {name: sha(path) for name, path in DEPENDENCIES.items()}
    if values != EXPECTED:
        raise RuntimeError(f"authority drift: {values}")
    return values


def all10_preflight() -> dict[str, object]:
    command = [sys.executable, str(DEPENDENCIES["all10_installed_preflight"])]
    results = [subprocess.run(command, cwd=ROOT, capture_output=True) for _ in range(2)]
    if any(result.returncode != 2 for result in results):
        raise RuntimeError("all-ten preflight return code drift")
    if results[0].stdout != results[1].stdout:
        raise RuntimeError("all-ten preflight output is not byte-identical")
    payload = json.loads(results[0].stdout)
    if payload.get("status") != "ae_not_running" or payload.get("after_effects") != []:
        raise RuntimeError("all-ten preflight AE state drift")
    bundles = payload.get("bundles", [])
    if len(bundles) != 10 or any(
        row.get("bundle_count") != 1
        or row.get("sha256_exact") is not True
        or row.get("universal_exact") is not True
        or row.get("codesign_exact") is not True
        for row in bundles
    ):
        raise RuntimeError("all-ten installed identity contract drift")
    smoother2 = [row for row in bundles if row.get("name") == "OLMSmoother2"]
    expected = "c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f"
    if len(smoother2) != 1 or smoother2[0].get("sha256") != expected:
        raise RuntimeError("all-ten preflight Smoother2 identity drift")
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
    installed_preflight = all10_preflight()
    installer = load_installer()
    identity_sha = sha(installer.IDENTITY)
    if identity_sha == installer.EXPECTED_PRE_IDENTITY:
        preflight = installer.collect_preflight("either")
        state = preflight["transaction_artifact_state"]
        prepared: dict[str, object] | None = None
        if state == "prepared":
            prepared = installer.validate_prepared(preflight)
        elif state != "clean":
            raise RuntimeError(f"unsupported transaction state: {state}")
        predecessor = preflight["installed_before"]
        candidate = preflight["candidate"]
        identity_change = preflight["identity_transition"]
        status = "install_ready_prepared_no_target_mutation" if state == "prepared" else "prepare_ready_no_target_mutation"
    elif identity_sha == POST_IDENTITY_SHA256:
        if installer.ae_pids():
            raise RuntimeError("After Effects is running")
        if installer.STAGED.exists() or installer.FAILED_NEW.exists():
            raise RuntimeError("staged or failed candidate residue exists")
        candidate = installer.verify_bundle(installer.CANDIDATE, installer.EXPECTED_NEW, True)
        installed = installer.verify_bundle(installer.INSTALLED, installer.EXPECTED_NEW, True)
        if candidate["manifest"] != installed["manifest"]:
            raise RuntimeError("candidate and installed inventories differ")
        predecessor_rows = [
            installer.verify_bundle(path, installer.EXPECTED_OLD, False)
            for path in (installer.BACKUP, installer.PRE_SWAP, installer.MOVED_OLD)
        ]
        if not all(row["manifest"] == predecessor_rows[0]["manifest"] for row in predecessor_rows[1:]):
            raise RuntimeError("retained predecessor inventories differ")
        before = json.loads(installer.PRE_IDENTITY.read_text())
        after = json.loads(installer.IDENTITY.read_text())
        identity_change = installer.transition(before, after)
        installer.expected_transition(before)
        if identity_change["changed_plugins"] != ["OLMSmoother2"] or not identity_change["other_nine_rows_exact"]:
            raise RuntimeError("post-install identity transition drift")
        transaction = json.loads(installer.TRANSACTION.read_text())
        if transaction.get("status") != "installed_ae_not_launched" or transaction.get("post_identity_sha256") != POST_IDENTITY_SHA256:
            raise RuntimeError("transaction evidence drift")
        predecessor = predecessor_rows[0]
        prepared = {
            "old_bundle_copy_count": 3,
            "old_bundle_full_inventories_exact": True,
            "candidate_installed_full_inventory_exact": True,
            "post_identity_sha256": POST_IDENTITY_SHA256,
            "transaction_sha256": sha(installer.TRANSACTION),
        }
        state = "installed"
        status = "installed_identity_closed_ae_deferred"
    else:
        raise RuntimeError(f"accepted identity is neither predecessor nor reviewed successor: {identity_sha}")
    return {
        "schema": "olmsmoother2.pf8-pf16-pf32-transactional-install-audit/1",
        "status": status,
        "claim_boundary": "Current workspace and on-disk predecessor/candidate identities; hostless numerical closure only; AE deferred to a later batch",
        "authorities": auth,
        "installed_predecessor": {
            "binary_sha256": installer.EXPECTED_OLD,
            "bundle_count": 1,
            "full_inventory": predecessor["manifest"],
        },
        "candidate": {
            "binary_sha256": installer.EXPECTED_NEW,
            "full_inventory": candidate["manifest"],
            "architectures": candidate["architectures"],
            "strict_codesign": candidate["strict_codesign"],
            "signing_kind": candidate["signing_kind"],
            "minimum_versions": candidate["macho_slice_minimum_versions"],
            "required_exports": candidate["required_exports"],
        },
        "identity_transition": identity_change,
        "transaction_state": state,
        "prepared_evidence": prepared,
        "after_effects_processes": [],
        "all10_preflight": installed_preflight,
        "claims_not_made": CLAIMS_NOT_MADE,
    }


def validate(report: dict[str, Any]) -> None:
    if set(report) != REPORT_KEYS:
        raise RuntimeError("top-level schema drift")
    live = generate()
    if report != live:
        raise RuntimeError("saved report differs from live audit")
    if report["after_effects_processes"] != []:
        raise RuntimeError("AE process claim drift")
    if report["candidate"]["binary_sha256"] != "c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f":
        raise RuntimeError("candidate identity drift")
    if report["installed_predecessor"]["binary_sha256"] != "55d138e2a25704ffa59d8bd08d20e2160525f8f8011b8e11c733ae23fddd795e":
        raise RuntimeError("predecessor identity drift")
    if report["identity_transition"]["changed_plugins"] != ["OLMSmoother2"]:
        raise RuntimeError("identity transition scope drift")


def markdown(report: dict[str, Any]) -> str:
    return (
        "# OLMSmoother2 PF8/PF16/PF32 transactional install readiness\n\n"
        f"Status: `{report['status']}`.\n\n"
        "The source-bound 39-cell Universal candidate is verified against the installed identity chain. "
        "The transaction retains three full exact predecessor bundles and the exact pre-install identity bytes. "
        "After Effects is intentionally not launched; live host smoke remains deferred to the batched acceptance cycle.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        DOC.write_text(markdown(live))
    if not REPORT.is_file() or not DOC.is_file():
        raise RuntimeError("canonical audit report is absent; run --write once")
    saved = json.loads(REPORT.read_text())
    validate(saved)
    if DOC.read_text() != markdown(saved):
        raise RuntimeError("audit markdown drift")
    print(saved["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
