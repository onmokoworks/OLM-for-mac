#!/usr/bin/env python3
"""Read-only post-install closure for the 2026-08-15 five-plugin swap."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260815.py"
OUTPUT = ROOT / "refs/conformance/olm_hostless_batch5_postinstall_transaction_audit_20260815.json"


def load_installer():
    spec = importlib.util.spec_from_file_location("batch5_postinstall", INSTALLER)
    module = importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(module); return module


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory_digest(rows: list[dict[str, object]]) -> str:
    return digest_bytes(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())


def changed_paths(before: dict, after: dict) -> set[tuple[str, ...]]:
    changes: set[tuple[str, ...]] = set()
    for key in before:
        if key == "plugins": continue
        if before[key] != after[key]: changes.add((key,))
    old_rows = {r["plugin"]: r for r in before["plugins"]}
    new_rows = {r["plugin"]: r for r in after["plugins"]}
    if set(old_rows) != set(new_rows): raise RuntimeError("identity plugin keyset changed")
    for name, old in old_rows.items():
        if set(old) != set(new_rows[name]): raise RuntimeError(f"identity row shape changed: {name}")
        for key, value in old.items():
            if value != new_rows[name][key]: changes.add((name, key))
    return changes


def audit() -> dict[str, object]:
    m = load_installer()
    if m.artifact_state() != "installed": raise RuntimeError("transaction is not exactly installed")
    if m.ae_pids(): raise RuntimeError("After Effects or aerender is running")
    if m.ROLLBACK.exists(): raise RuntimeError("rollback receipt unexpectedly exists")
    prepared = json.loads(m.PREPARED.read_text()); transaction = json.loads(m.TRANSACTION.read_text())
    before_bytes = m.PRE_IDENTITY.read_bytes(); after_bytes = m.POST_IDENTITY.read_bytes()
    if m.IDENTITY.read_bytes() != after_bytes: raise RuntimeError("live and post identity differ")
    if digest_bytes(before_bytes) != m.EXPECTED_PRE_IDENTITY: raise RuntimeError("pre identity drift")
    if digest_bytes(after_bytes) != transaction["post_identity_sha256"]: raise RuntimeError("post identity drift")
    if transaction["pre_identity_sha256"] != m.EXPECTED_PRE_IDENTITY: raise RuntimeError("receipt pre identity drift")
    if transaction.get("same_volume_renameatx_np_swap") is not True: raise RuntimeError("swap method not recorded")

    before = json.loads(before_bytes); after = json.loads(after_bytes)
    allowed = {("accepted_at",), ("installed_after",)} | {
        (name, key) for name in m.PLUGINS for key in ("sha256", "source_bundle", "source_sha256")
    }
    actual = changed_paths(before, after)
    if actual != allowed: raise RuntimeError(f"identity allowlist mismatch: {actual ^ allowed}")
    old_rows = {r["plugin"]: r for r in before["plugins"]}; new_rows = {r["plugin"]: r for r in after["plugins"]}

    plugin_rows = {}
    for name, s in m.PLUGINS.items():
        if old_rows[name]["sha256"] != s["old"]: raise RuntimeError(f"old row mismatch: {name}")
        expected_new = {"sha256": s["new"], "source_bundle": str(s["candidate"].relative_to(ROOT)),
                        "source_sha256": s["new"]}
        if any(new_rows[name][key] != value for key, value in expected_new.items()):
            raise RuntimeError(f"new row mismatch: {name}")
        if new_rows[name].get("source_installed_exact") is not True: raise RuntimeError(f"installed-exact flag drift: {name}")
        preflight = prepared["preflight"]["plugins"][name]
        installed = m.verify_bundle(name, m.paths(name)["installed"], s["new"], macos11=True)
        if installed["inventory"] != preflight["candidate"]["inventory"]: raise RuntimeError(f"installed candidate inventory drift: {name}")
        old_digest = inventory_digest(preflight["installed_before"]["inventory"])
        copies = {}
        for key in ("backup", "pre_swap", "moved_old"):
            verified = m.verify_bundle(name, m.paths(name)[key], s["old"], macos11=False)
            if verified["inventory"] != preflight["installed_before"]["inventory"]:
                raise RuntimeError(f"old-copy inventory drift: {name}/{key}")
            copies[key] = {"path": str(m.paths(name)[key]), "binary_sha256": s["old"],
                           "inventory_sha256": old_digest, "node_count": len(verified["inventory"])}
        if m.paths(name)["stage"].exists() or m.paths(name)["failed_new"].exists():
            raise RuntimeError(f"residual stage/quarantine: {name}")
        matches = [p.resolve() for p in m.MEDIA_CORE.rglob(f"{name}.plugin")]
        if matches != [m.paths(name)["installed"].resolve()]: raise RuntimeError(f"MediaCore singleton drift: {name}")
        plugin_rows[name] = {
            "installed": {"path": str(m.paths(name)["installed"]), "binary_sha256": s["new"],
                          "inventory_sha256": inventory_digest(installed["inventory"]),
                          "node_count": len(installed["inventory"])},
            "old_exact_copies": copies,
            "identity_changed_fields": ["sha256", "source_bundle", "source_sha256"],
            "production_source_sha256": s["source_sha256"],
            "candidate_identity_sha256": s["identity_sha256"],
        }
    expected_receipt = {name: {"old": s["old"], "new": s["new"]} for name, s in m.PLUGINS.items()}
    if transaction["plugins"] != expected_receipt: raise RuntimeError("transaction plugin receipt drift")
    return {
        "schema": "olm.hostless-batch5-20260815-postinstall-audit/1",
        "status": "PASS_BATCH5_INSTALLED_TRANSACTION_OLD3_IDENTITY_ALLOWLIST_AE_PENDING",
        "installer_sha256": m.sha256(INSTALLER),
        "readiness_sha256": m.READINESS_SHA256,
        "prepared_receipt_sha256": m.sha256(m.PREPARED),
        "transaction_receipt_sha256": m.sha256(m.TRANSACTION),
        "pre_identity_sha256": m.EXPECTED_PRE_IDENTITY,
        "post_identity_sha256": digest_bytes(after_bytes),
        "after_effects_and_aerender_processes": [],
        "identity_exact_changed_paths": [list(p) for p in sorted(actual)],
        "plugins": plugin_rows,
        "scope": {"installed": True, "after_effects_smoke_completed": False, "release_gate_changed": False,
                  "mediacore_changed_by_auditor": False, "identity_changed_by_auditor": False,
                  "after_effects_launched_by_auditor": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    report = audit(); encoded = (json.dumps(report, indent=2) + "\n").encode()
    if args.write:
        if OUTPUT.exists() and OUTPUT.read_bytes() != encoded: raise RuntimeError(f"refusing overwrite: {OUTPUT}")
        OUTPUT.write_bytes(encoded)
    print(json.dumps({"status": report["status"], "plugins": len(report["plugins"]),
                      "report_sha256": digest_bytes(encoded), "written": args.write}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
