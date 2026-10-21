#!/usr/bin/env python3
"""Post-install identity and rollback audit for current OLMRadialBlur."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmradialblur_current_20260813.py"
INSTALLER_SHA = "716f4c9ec3eeb72a0b90b2d206f296b24224cf03668fae1d96fdaf3f193578c1"
TRANSACTION_SHA = "d775a03d15383f1ec262eaab0a26a0e0b3cdba46c07d11e20ef225e1617b8c83"
POST_IDENTITY_SHA = "cc9cb7edd30c23aef06b6ef4aab819763f900a1d40938e5b5a2b66758bb566be"
REPORT = ROOT / "refs/conformance/olmradialblur_current_incremental_install_20260813.json"
DOC = REPORT.with_suffix(".md")
DOC_TEXT = """# OLMRadialBlur current-source incremental install

Verdict: `PASS_RADIAL_CURRENT_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED`.

The current `0aac...` source candidate is byte-identical to the sole installed
OLMRadialBlur bundle. The superseded batch5 `8fde...` bundle remains in three
full-inventory-exact rollback copies. Only the Radial identity row and the two
top-level timestamps changed; the other nine rows are exact.

Two all-ten preflights are byte-identical and observe no After Effects process.
This is an installed identity closure only. The next AE smoke remains deferred
to a later batched checkpoint.
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def installer():
    spec = importlib.util.spec_from_file_location("radial_current_installer", INSTALLER)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def generate() -> dict[str, object]:
    if sha(INSTALLER) != INSTALLER_SHA:
        raise RuntimeError("installer drift")
    module = installer()
    if module.artifact_state() != "installed" or sha(module.TRANSACTION) != TRANSACTION_SHA or sha(module.IDENTITY) != POST_IDENTITY_SHA:
        raise RuntimeError("installed transaction drift")
    before = json.loads(module.PRE_IDENTITY.read_text())
    after = json.loads(module.IDENTITY.read_text())
    old_rows = {x["plugin"]: x for x in before["plugins"]}
    new_rows = {x["plugin"]: x for x in after["plugins"]}
    changed = {name for name in old_rows if old_rows[name] != new_rows[name]}
    if changed != {module.NAME}:
        raise RuntimeError("identity row partition")
    top = {key for key in before if key != "plugins" and before[key] != after[key]}
    if top != {"accepted_at", "installed_after"}:
        raise RuntimeError("top identity partition")
    candidate = module.base.verify_bundle(module.NAME, module.CANDIDATE, module.NEW_SHA256, require_macos11=True)
    installed = module.base.verify_bundle(module.NAME, module.paths()["installed"], module.NEW_SHA256, require_macos11=True)
    if candidate["manifest"] != installed["manifest"]:
        raise RuntimeError("candidate/install inventory")
    old_reference = module.base.verify_bundle(module.NAME, module.paths()["backup"], module.OLD_SHA256, require_macos11=False)
    copies = []
    for key in ("backup", "pre_swap", "moved_old"):
        copy = module.base.verify_bundle(module.NAME, module.paths()[key], module.OLD_SHA256, require_macos11=False)
        if copy["manifest"] != old_reference["manifest"]:
            raise RuntimeError(f"rollback inventory: {key}")
        copies.append(key)
    command = [sys.executable, str(ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py")]
    outputs = []
    for _ in range(2):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 2:
            raise RuntimeError("preflight return code")
        data = json.loads(result.stdout)
        if data["status"] != "ae_not_running" or data["after_effects"] or len(data["bundles"]) != 10:
            raise RuntimeError("preflight state")
        if not all(x["bundle_count"] == 1 and x["sha256_exact"] and x["universal_exact"] and x["codesign_exact"] for x in data["bundles"]):
            raise RuntimeError("preflight bundle contract")
        outputs.append(result.stdout.encode())
    if outputs[0] != outputs[1] or module.base.ae_pids():
        raise RuntimeError("preflight instability")
    return {
        "schema": "olmradialblur.current-incremental-install/1",
        "status": "PASS_RADIAL_CURRENT_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED",
        "authorities": {"installer_sha256": INSTALLER_SHA, "transaction_sha256": TRANSACTION_SHA,
                        "pre_identity_sha256": module.EXPECTED_PRE_IDENTITY, "post_identity_sha256": POST_IDENTITY_SHA,
                        "candidate_authority_sha256": module.AUTHORITY_SHA256},
        "installed": {"old_sha256": module.OLD_SHA256, "new_sha256": module.NEW_SHA256,
                      "candidate_installed_full_inventory_exact": True,
                      "old_full_inventory_exact_copies": copies},
        "identity_change": {"target_plugins": [module.NAME], "other_nine_rows_exact": True,
                            "top_level_changed_fields": sorted(top)},
        "all10_preflight": {"passes": 2, "returncode": 2, "status": "ae_not_running",
                            "stdout_sha256": hashlib.sha256(outputs[0]).hexdigest(),
                            "byte_identical": True, "exact_bundles": 10},
        "after_effects_processes": [],
        "scope": {"installed": True, "rollback_copies": 3, "after_effects_launched": False,
                  "batched_ae_checkpoint_complete": False, "formal_gate_complete": False},
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
    data = generate()
    if args.write:
        REPORT.write_bytes(canonical(data))
        DOC.write_text(DOC_TEXT)
    if not REPORT.exists() or not DOC.exists():
        raise SystemExit("missing report; use --write")
    before = REPORT.read_bytes()
    validate(json.loads(before))
    if before != canonical(data) or REPORT.read_bytes() != before:
        raise SystemExit("not canonical/read-only")
    print(data["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
