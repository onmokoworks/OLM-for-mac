#!/usr/bin/env python3
"""Post-install identity and rollback audit for the three-plugin hostless batch."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260813.py"
INSTALLER_SHA = "3f90a3fb811ebf42951d7a33033a792ad08cb152bac416da623f0a78e9df8221"
INSTALLER_UNIT = ROOT / "tests/test_olm_hostless_batch5_transactional_installer_20260813.py"
INSTALLER_UNIT_SHA = "1f3c8685aba58bfb9ed9192e94d65aa9ec2e704b04ae38b70e249fff5395ccae"
POST_IDENTITY_SHA = "40cd982cb90bb31d206aa5770dee476094217dc69fb325f708ace72fbd074363"
TRANSACTION_SHA = "97a93a1ee0e37cbc2d3f5ffa9538f59d897d3e26b146a541afcab05d83374b77"
REPORT = ROOT / "refs/conformance/olm_hostless_batch5_incremental_install_20260813.json"
DOC = REPORT.with_suffix(".md")
DOC_TEXT = """# Three-plugin hostless batch incremental install

Verdict: `PASS_BATCH5_INSTALLED_IDENTITY_AND_ROLLBACK_CLOSED_AE_DEFERRED`.

OLMBlur, OLMDirectionalBlur, and OLMRadialBlur are installed from the reviewed Universal macOS 11 candidates. Candidate and installed full bundle inventories are exact. For every plugin the previous bundle remains available in three inventory-exact copies: `installed_backup`, `pre_swap_original`, and `moved_old`.

Only those three identity rows and the two top-level timestamps changed; the other seven rows are exact. Two all-ten preflights are byte-identical, report one Universal strictly signed bundle per plugin, and observe no After Effects process. This is an installed identity closure only. Per the batched-checkpoint policy, After Effects was not launched and the formal release gate remains pending.
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def load_installer():
    spec = importlib.util.spec_from_file_location("batch5_post_installer", INSTALLER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate() -> dict[str, object]:
    if sha(INSTALLER) != INSTALLER_SHA or sha(INSTALLER_UNIT) != INSTALLER_UNIT_SHA:
        raise RuntimeError("installer authority drift")
    module = load_installer()
    if module.base.artifact_state() != "installed":
        raise RuntimeError("transaction is not installed")
    if sha(module.IDENTITY) != POST_IDENTITY_SHA or sha(module.TRANSACTION) != TRANSACTION_SHA:
        raise RuntimeError("installed transaction drift")
    before = json.loads(module.PRE_IDENTITY.read_text())
    after = json.loads(module.IDENTITY.read_text())
    old_rows = {row["plugin"]: row for row in before["plugins"]}
    new_rows = {row["plugin"]: row for row in after["plugins"]}
    targets = set(module.PLUGINS)
    if {name for name in old_rows if old_rows[name] != new_rows[name]} != targets:
        raise RuntimeError("identity target row set drift")
    top = {key for key in before if key != "plugins" and before[key] != after[key]}
    if top != {"accepted_at", "installed_after"}:
        raise RuntimeError(f"top identity drift: {top}")
    plugins = {}
    for name, item in module.PLUGINS.items():
        candidate = module.base.verify_bundle(name, item["candidate"], item["new"], require_macos11=True)
        installed = module.base.verify_bundle(name, module.paths(name)["installed"], item["new"], require_macos11=True)
        if installed["manifest"] != candidate["manifest"]:
            raise RuntimeError(f"candidate/install drift: {name}")
        reference = module.base.verify_bundle(name, module.paths(name)["backup"], item["old"], require_macos11=False)
        old_copies = []
        for key in ("backup", "pre_swap", "moved_old"):
            copy = module.base.verify_bundle(name, module.paths(name)[key], item["old"], require_macos11=False)
            if copy["manifest"] != reference["manifest"]:
                raise RuntimeError(f"old copy drift: {name}/{key}")
            old_copies.append(key)
        plugins[name] = {
            "old_sha256": item["old"],
            "new_sha256": item["new"],
            "candidate_installed_full_inventory_exact": True,
            "old_full_inventory_exact_copies": old_copies,
        }
    command = [sys.executable, str(ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py")]
    outputs = []
    for _ in range(2):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 2:
            raise RuntimeError(f"preflight rc: {result.returncode}")
        data = json.loads(result.stdout)
        if data["status"] != "ae_not_running" or data["after_effects"] or len(data["bundles"]) != 10:
            raise RuntimeError("preflight state")
        if not all(row["bundle_count"] == 1 and row["sha256_exact"] and row["universal_exact"] and row["codesign_exact"] for row in data["bundles"]):
            raise RuntimeError("preflight identity contract")
        outputs.append(result.stdout.encode())
    if outputs[0] != outputs[1]:
        raise RuntimeError("preflight passes differ")
    if module.base.ae_pids():
        raise RuntimeError("After Effects is running")
    return {
        "schema": "olm.hostless-batch5-incremental-install/1",
        "status": "PASS_BATCH5_INSTALLED_IDENTITY_AND_ROLLBACK_CLOSED_AE_DEFERRED",
        "authorities": {
            "installer_sha256": INSTALLER_SHA,
            "installer_unit_sha256": INSTALLER_UNIT_SHA,
            "transaction_sha256": TRANSACTION_SHA,
            "pre_identity_sha256": module.EXPECTED_PRE_IDENTITY,
            "post_identity_sha256": POST_IDENTITY_SHA,
        },
        "plugins": plugins,
        "identity_change": {
            "target_plugins": sorted(targets),
            "other_seven_rows_exact": True,
            "top_level_changed_fields": sorted(top),
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
            "rollback_copies_per_plugin": 3,
            "after_effects_launched": False,
            "batched_ae_checkpoint_complete": False,
            "formal_gate_complete": False,
        },
    }


def validate(data: object) -> None:
    keys = {"schema", "status", "authorities", "plugins", "identity_change", "all10_preflight", "after_effects_processes", "scope"}
    if not isinstance(data, dict) or set(data) != keys:
        raise ValueError("schema")
    if data != generate():
        raise ValueError("live state drift")
    if DOC.read_text() != DOC_TEXT:
        raise ValueError("doc")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = generate()
    if args.write:
        REPORT.write_bytes(canonical(data))
        DOC.write_text(DOC_TEXT)
    if not REPORT.is_file() or not DOC.is_file():
        raise SystemExit("missing report; use --write")
    before = REPORT.read_bytes()
    validate(json.loads(before))
    if before != canonical(data) or REPORT.read_bytes() != before:
        raise SystemExit("report is not read-only exact")
    print(data["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
