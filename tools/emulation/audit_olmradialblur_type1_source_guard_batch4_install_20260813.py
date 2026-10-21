#!/usr/bin/env python3
"""Audit the installed RadialBlur Type1 source-guard batch 4 transaction."""

from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olmradialblur_type1_source_guard_batch4_20260813.py"
INSTALLER_SHA = "ef4b382244538d5d4cbbf30ddb5ad1a455045ccc3508693c37cff59dd5f33ad3"
TRANSACTION_SHA = "86d6db1f425f7f1b5b394835383492e3cdc3b1a0fee9af76dd8e09192e14c41d"
POST_IDENTITY_SHA = "3722313db6f77ff1e8ba44ff13a95a66b4a46727f86275d0801b0576048b55ed"
REPORT = ROOT / "refs/conformance/olmradialblur_type1_source_guard_batch4_install_20260813.json"
DOC = REPORT.with_suffix(".md")
STATUS = "PASS_RADIAL_TYPE1_SOURCE_GUARD_BATCH4_INSTALLED_ROLLBACK_CLOSED_AE_DEFERRED"

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(value: object) -> bytes: return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()

def load_installer():
    spec = importlib.util.spec_from_file_location("radial_batch4_installer", INSTALLER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module.installer

def generate() -> dict:
    if sha(INSTALLER) != INSTALLER_SHA: raise RuntimeError("installer drift")
    module = load_installer()
    if module.artifact_state() != "installed" or sha(module.TRANSACTION) != TRANSACTION_SHA or sha(module.IDENTITY) != POST_IDENTITY_SHA:
        raise RuntimeError("transaction drift")
    before = json.loads(module.PRE_IDENTITY.read_text()); after = json.loads(module.IDENTITY.read_text())
    old_rows = {row["plugin"]: row for row in before["plugins"]}; new_rows = {row["plugin"]: row for row in after["plugins"]}
    if [name for name in old_rows if old_rows[name] != new_rows[name]] != [module.NAME]: raise RuntimeError("row partition")
    top = sorted(key for key in before if key != "plugins" and before[key] != after[key])
    if top != ["accepted_at", "installed_after"]: raise RuntimeError("top partition")
    candidate = module.base.verify_bundle(module.NAME, module.CANDIDATE, module.NEW_SHA256, require_macos11=True)
    installed = module.base.verify_bundle(module.NAME, module.paths()["installed"], module.NEW_SHA256, require_macos11=True)
    if candidate["manifest"] != installed["manifest"]: raise RuntimeError("new inventory")
    old = module.base.verify_bundle(module.NAME, module.paths()["backup"], module.OLD_SHA256, require_macos11=False)
    copies = []
    for key in ("backup", "pre_swap", "moved_old"):
        value = module.base.verify_bundle(module.NAME, module.paths()[key], module.OLD_SHA256, require_macos11=False)
        if value["manifest"] != old["manifest"]: raise RuntimeError("old inventory")
        copies.append(key)
    outputs = []
    command = [sys.executable, str(ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py")]
    for _ in range(2):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 2: raise RuntimeError("preflight return")
        value = json.loads(result.stdout)
        if value["status"] != "ae_not_running" or value["after_effects"] or len(value["bundles"]) != 10: raise RuntimeError("preflight state")
        if not all(row["bundle_count"] == 1 and row["sha256_exact"] and row["universal_exact"] and row["codesign_exact"] for row in value["bundles"]): raise RuntimeError("preflight bundle")
        outputs.append(result.stdout.encode())
    if outputs[0] != outputs[1] or module.base.ae_pids(): raise RuntimeError("preflight instability")
    return {"schema": "olmradialblur.type1-source-guard-batch4-install/1", "status": STATUS,
            "authorities": {"installer_sha256": INSTALLER_SHA, "transaction_sha256": TRANSACTION_SHA,
                "pre_identity_sha256": module.EXPECTED_PRE_IDENTITY, "post_identity_sha256": POST_IDENTITY_SHA,
                "candidate_authority_sha256": module.AUTHORITY_SHA256},
            "installed": {"old_sha256": module.OLD_SHA256, "new_sha256": module.NEW_SHA256,
                "candidate_installed_full_inventory_exact": True, "old_full_inventory_exact_copies": copies},
            "identity_change": {"target_plugins": [module.NAME], "other_nine_rows_exact": True, "top_level_changed_fields": top},
            "all10_preflight": {"passes": 2, "returncode": 2, "status": "ae_not_running",
                "stdout_sha256": hashlib.sha256(outputs[0]).hexdigest(), "byte_identical": True, "exact_bundles": 10},
            "after_effects_processes": [],
            "scope": {"installed": True, "rollback_copies": 3, "after_effects_launched": False,
                "batched_ae_checkpoint_complete": False, "formal_gate_complete": False}}

def markdown(_: dict) -> str:
    return ("# OLMRadialBlur Type1 source-guard batch 4 install\n\n"
            f"Verdict: `{STATUS}`.\n\nThe `44f1e7f9…c5acb` source candidate `2934d136…3083` is full-inventory exact to the sole installed bundle. "
            "Three exact rollback copies retain predecessor `da72af55…b859`. Only the Radial identity row and two top-level timestamps changed. "
            "Two all-ten preflights are byte-identical. AE remains deferred.\n")

def validate(value: dict) -> None:
    if set(value) != {"schema", "status", "authorities", "installed", "identity_change", "all10_preflight", "after_effects_processes", "scope"}: raise RuntimeError("schema")
    if value != generate() or DOC.read_text() != markdown(value): raise RuntimeError("live drift")

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args(); fresh = generate()
    if args.write: REPORT.write_bytes(canonical(fresh)); DOC.write_text(markdown(fresh))
    saved = json.loads(REPORT.read_text()); validate(saved)
    if REPORT.read_bytes() != canonical(fresh): raise RuntimeError("canonical drift")
    print(STATUS); return 0

if __name__ == "__main__": raise SystemExit(main())
