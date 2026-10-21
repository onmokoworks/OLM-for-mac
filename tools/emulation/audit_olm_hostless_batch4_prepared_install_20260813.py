#!/usr/bin/env python3
"""Read-only audit of the prepared four-plugin transaction."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch4_20260813.py"
INSTALLER_SHA256 = "8dec85c9249f5cea1bd8f56e40fe99850570d8c9c701ff0fc21acbd2d9abc39e"
INSTALLER_UNIT = ROOT / "tests/test_olm_hostless_batch4_transactional_installer_20260813.py"
INSTALLER_UNIT_SHA256 = "98436d78df368471ed1d75f56421a140f7a1e9796a202adb489055864c641ea2"
REPORT = ROOT / "refs/conformance/olm_hostless_batch4_prepared_install_20260813.json"
DOC = REPORT.with_suffix(".md")
PREPARED_SHA256 = "8526b36e79c1392abce5d9ba32b83c3c04a8d85f52faad42200c268ddc06da51"
DOC_TEXT = """# Prepared four-plugin transaction

Verdict: `PASS_BATCH4_PREPARED_INSTALL_READY_NO_MEDIACORE_OR_IDENTITY_MUTATION`.

Two complete copies of each old installed bundle are retained under the transaction handoff. All eight copies match the corresponding live installed bundle byte-for-byte by full inventory, the accepted identity remains `ef7bf31f…`, all four installed executables remain at their old hashes, and After Effects is not running.

The installer and its five sandbox tests are hash-bound. This prepared state authorizes the single four-bundle transaction. It is not an installation, AE smoke, or release claim.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def module():
    spec = importlib.util.spec_from_file_location("batch4_prepared_installer", INSTALLER)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def generate() -> dict[str, object]:
    if sha256(INSTALLER) != INSTALLER_SHA256 or sha256(INSTALLER_UNIT) != INSTALLER_UNIT_SHA256:
        raise RuntimeError("installer authority drift")
    install = module()
    if install.artifact_state() != "prepared" or sha256(install.PREPARED) != PREPARED_SHA256:
        raise RuntimeError("prepared transaction drift")
    preflight = install.collect_preflight()
    proof = install.validate_prepared(preflight)
    plugins = {}
    for name, spec in install.PLUGINS.items():
        p = install.paths(name)
        live = install.verify_bundle(name, p["installed"], spec["old"], require_macos11=False)
        backup = install.verify_bundle(name, p["backup"], spec["old"], require_macos11=False)
        pre_swap = install.verify_bundle(name, p["pre_swap"], spec["old"], require_macos11=False)
        if not (live["manifest"] == backup["manifest"] == pre_swap["manifest"]):
            raise RuntimeError(f"old inventory mismatch: {name}")
        plugins[name] = {"installed_old_sha256": spec["old"], "candidate_new_sha256": spec["new"],
                         "installed_backup_full_inventory_exact": True, "pre_swap_full_inventory_exact": True}
    return {
        "schema": "olm.hostless-batch4-prepared-install/1",
        "status": "PASS_BATCH4_PREPARED_INSTALL_READY_NO_MEDIACORE_OR_IDENTITY_MUTATION",
        "authorities": {"installer_sha256": INSTALLER_SHA256, "installer_unit_sha256": INSTALLER_UNIT_SHA256,
                        "prepared_transaction_sha256": PREPARED_SHA256,
                        "accepted_identity_sha256": sha256(install.IDENTITY)},
        "plugins": plugins, "prepared_validation": proof, "after_effects_processes": install.ae_pids(),
        "scope": {"backup_copies_per_plugin": 2, "installed": False, "identity_updated": False,
                  "after_effects_launched": False, "next_allowed_action": "single_batch4_install"},
    }


def validate(data: object) -> None:
    if not isinstance(data, dict) or set(data) != {"schema", "status", "authorities", "plugins", "prepared_validation", "after_effects_processes", "scope"}:
        raise ValueError("top-level schema")
    if data != generate(): raise ValueError("saved prepared audit differs from live state")
    if data["after_effects_processes"] != [] or data["scope"] != {"backup_copies_per_plugin": 2, "installed": False,
            "identity_updated": False, "after_effects_launched": False, "next_allowed_action": "single_batch4_install"}:
        raise ValueError("scope")
    if DOC.read_text() != DOC_TEXT: raise ValueError("documentation")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    current = generate()
    if args.write: REPORT.write_bytes(canonical(current)); DOC.write_text(DOC_TEXT)
    if not REPORT.is_file() or not DOC.is_file(): raise SystemExit("prepared audit missing; use --write")
    before = REPORT.read_bytes(); validate(json.loads(before))
    if before != canonical(current) or REPORT.read_bytes() != before: raise SystemExit("prepared audit not read-only exact")
    print(current["status"]); return 0


if __name__ == "__main__": raise SystemExit(main())
