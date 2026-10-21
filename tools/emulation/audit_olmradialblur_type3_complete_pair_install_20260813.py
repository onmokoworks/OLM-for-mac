#!/usr/bin/env python3
"""Audit the installed 32-pair OLMRadialBlur transaction without launching AE."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmradialblur_type3_complete_pair_20260813.py"
INSTALLER_SHA = "a5e3d3c5d5565df814ae3584f55e08ef4a22304cf317604f28146552de737dde"
PREPARED_SHA = "78c22b71415f2d1e735dc1e343c79c01fb3550b2cd0c6f32ed22da623146323d"
TRANSACTION_SHA = "bc8c50a7b860598e7116657edff9558858817049d7e41c12acdadf32b7798566"
PRE_IDENTITY_SHA = "3722313db6f77ff1e8ba44ff13a95a66b4a46727f86275d0801b0576048b55ed"
POST_IDENTITY_SHA = "c6ebb4cdb39eeecb569f35a969df7e1bd1ff54e3bcfedef87fab9f16d2ec5850"
BUILD_IDENTITY_SHA = "0cea554c10ba54f2d18c70b528527be58625a4b29491893ce12db6853a5bc045"
CLOSURE_SHA = "ba9fbc18434dfa24e4507b9bd2bf9b8217e7795e0fd77bb588c250dc1f77e4e8"
REPORT = ROOT / "refs/conformance/olmradialblur_type3_complete_pair_install_20260813.json"
DOC = REPORT.with_suffix(".md")
STATUS = "PASS_RADIAL_TYPE3_32_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED"
DOC_TEXT = """# OLMRadialBlur Type 3 complete-pair incremental install

Verdict: `PASS_RADIAL_TYPE3_32_PAIR_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED`.

The signed Universal minOS 11 candidate `d50934aa...773e` is full-inventory
exact to the sole installed OLMRadialBlur bundle. The superseded
`2934d136...3083` bundle remains in three full-inventory-exact rollback copies.
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
    spec = importlib.util.spec_from_file_location("radial_type3_complete_installer", INSTALLER)
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
        "schema": "olmradialblur.type3-complete-pair-install/1",
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
    if not isinstance(value, dict) or set(value) != {"schema", "status", "authorities", "installed", "identity_change", "all10_preflight", "after_effects_processes", "scope"}:
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
