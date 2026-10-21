#!/usr/bin/env python3
"""Audit the installed 35-pair OLMRadialBlur transaction without launching AE."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmradialblur_type3_35_pair_20260813.py"
INSTALLER_SHA = "0007ef4ea2c8eb93363084934a5a457edaf83444a8bef06738d775c397d13c01"
PREPARED_SHA = "04308b07f8193d58ab098847b8902b144dba442f7d91b6ad71f817584e913081"
TRANSACTION_SHA = "c064d00eac5af9fdbb634f326084b23024af457fc6829b424276a096fc12a2ae"
PRE_IDENTITY_SHA = "c6ebb4cdb39eeecb569f35a969df7e1bd1ff54e3bcfedef87fab9f16d2ec5850"
POST_IDENTITY_SHA = "7be33d88077c3ba90f7d9eeb73c156b0de53ac173d6bb46b5a15d46b0155fce3"
BUILD_IDENTITY_SHA = "a083703f380503c82a7329ef3e101202d3fbb22f426a9f82b0e373dbb36b5300"
CLOSURE_SHA = "af36409c771ff524971980033fa05658aab6b8f5fdd01fac634e43318d03bac7"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_35_pair_install_20260813.json"
DOC = REPORT.with_suffix(".md")
STATUS = "PASS_RADIAL_TYPE3_35_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED"
DOC_TEXT = """# OLMRadialBlur Type 3 35-pair incremental install

Verdict: `PASS_RADIAL_TYPE3_35_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED`.

The signed Universal minOS 11 candidate `ce5b57e1...0e7a` is full-inventory
exact to the sole installed OLMRadialBlur bundle. The superseded
`d50934aa...773e` bundle remains in three full-inventory-exact rollback copies.
Only the Radial identity row and the two top-level timestamps changed.

Two all-ten preflights were byte-identical and observed no After Effects
process. This closes installed identity only. Native AE and the formal release
gate remain deferred to a later batched checkpoint.
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_installer():
    spec = importlib.util.spec_from_file_location("radial_type3_35_installer", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.installer


def generate() -> dict[str, object]:
    if sha(INSTALLER) != INSTALLER_SHA:
        raise RuntimeError("installer drift")
    installer = load_installer()
    if installer.artifact_state() != "installed":
        raise RuntimeError("transaction is not installed")
    expected = {
        installer.PREPARED: PREPARED_SHA,
        installer.TRANSACTION: TRANSACTION_SHA,
        installer.PRE_IDENTITY: PRE_IDENTITY_SHA,
        installer.POST_IDENTITY: POST_IDENTITY_SHA,
        installer.IDENTITY: POST_IDENTITY_SHA,
        installer.AUTHORITY: BUILD_IDENTITY_SHA,
        ROOT / "refs/conformance/olmradialblur_type3_all_depth_public_closure_20260813.json": CLOSURE_SHA,
    }
    for path, digest in expected.items():
        if sha(path) != digest:
            raise RuntimeError(f"authority drift: {path}")
    before = json.loads(installer.PRE_IDENTITY.read_text())
    after = json.loads(installer.IDENTITY.read_text())
    old_rows = {row["plugin"]: row for row in before["plugins"]}
    new_rows = {row["plugin"]: row for row in after["plugins"]}
    if {name for name in old_rows if old_rows[name] != new_rows[name]} != {installer.NAME}:
        raise RuntimeError("identity row partition")
    top = sorted(key for key in before if key != "plugins" and before[key] != after[key])
    if top != ["accepted_at", "installed_after"]:
        raise RuntimeError("identity top-level partition")
    candidate = installer.base.verify_bundle(installer.NAME, installer.CANDIDATE, installer.NEW_SHA256, require_macos11=True)
    installed = installer.base.verify_bundle(installer.NAME, installer.paths()["installed"], installer.NEW_SHA256, require_macos11=True)
    if candidate["manifest"] != installed["manifest"]:
        raise RuntimeError("candidate/installed inventory")
    old = installer.base.verify_bundle(installer.NAME, installer.paths()["backup"], installer.OLD_SHA256, require_macos11=False)
    copies = []
    for key in ("backup", "pre_swap", "moved_old"):
        item = installer.base.verify_bundle(installer.NAME, installer.paths()[key], installer.OLD_SHA256, require_macos11=False)
        if item["manifest"] != old["manifest"]:
            raise RuntimeError(f"rollback inventory: {key}")
        copies.append(key)
    command = [sys.executable, str(ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py")]
    outputs = []
    for _ in range(2):
        run = subprocess.run(command, cwd=ROOT, capture_output=True)
        if run.returncode != 2:
            raise RuntimeError("preflight return code")
        value = json.loads(run.stdout)
        if value["status"] != "ae_not_running" or value["after_effects"] or len(value["bundles"]) != 10:
            raise RuntimeError("preflight state")
        if not all(row["bundle_count"] == 1 and row["sha256_exact"] and row["universal_exact"] and row["codesign_exact"] for row in value["bundles"]):
            raise RuntimeError("preflight bundle relation")
        outputs.append(run.stdout)
    if outputs[0] != outputs[1] or installer.base.ae_pids():
        raise RuntimeError("preflight instability")
    return {
        "schema": "olmradialblur.type3-35-pair-install/1",
        "status": STATUS,
        "authorities": {
            "installer_sha256": INSTALLER_SHA,
            "prepared_sha256": PREPARED_SHA,
            "transaction_sha256": TRANSACTION_SHA,
            "pre_identity_sha256": PRE_IDENTITY_SHA,
            "post_identity_sha256": POST_IDENTITY_SHA,
            "build_identity_sha256": BUILD_IDENTITY_SHA,
            "closure_sha256": CLOSURE_SHA,
        },
        "installed": {
            "old_sha256": installer.OLD_SHA256,
            "new_sha256": installer.NEW_SHA256,
            "candidate_installed_full_inventory_exact": True,
            "old_full_inventory_exact_copies": copies,
        },
        "identity_change": {
            "target_plugins": [installer.NAME],
            "other_nine_rows_exact": True,
            "top_level_changed_fields": top,
        },
        "all10_preflight": {
            "passes": 2,
            "returncode": 2,
            "status": "ae_not_running",
            "stdout_sha256": hashlib.sha256(outputs[0]).hexdigest(),
            "byte_identical": True,
            "exact_bundles": 10,
        },
        "after_effects_processes": [],
        "scope": {
            "installed": True,
            "rollback_copies": 3,
            "after_effects_launched": False,
            "batched_ae_checkpoint_complete": False,
            "formal_gate_complete": False,
        },
    }


def validate(value: object) -> None:
    keys = {"schema", "status", "authorities", "installed", "identity_change", "all10_preflight", "after_effects_processes", "scope"}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("schema")
    if value != generate() or DOC.read_text() != DOC_TEXT:
        raise ValueError("live state or documentation drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    value = generate()
    if args.write:
        REPORT.write_bytes(canonical(value))
        DOC.write_text(DOC_TEXT)
    if not REPORT.exists() or not DOC.exists():
        raise SystemExit("missing report; use --write")
    before = REPORT.read_bytes()
    validate(json.loads(before))
    if before != canonical(value) or REPORT.read_bytes() != before:
        raise SystemExit("not canonical/read-only")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
