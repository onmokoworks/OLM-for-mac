#!/usr/bin/env python3
"""Read-only state auditor for the batch5 transaction namespace."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260815.py"


def load():
    spec = importlib.util.spec_from_file_location("batch5", INSTALLER)
    module = importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(module); return module


def audit() -> dict[str, object]:
    m = load(); state = m.artifact_state()
    if m.ae_pids(): raise RuntimeError("After Effects or aerender is running")
    if state == "clean":
        preflight = m.collect_preflight()
        return {"status": "PASS_BATCH5_CLEAN_READY_NO_MUTATION", "state": state,
                "candidate_count": len(preflight["plugins"]), "identity_sha256": m.sha256(m.IDENTITY)}
    if state == "prepared":
        preflight = m.collect_preflight(); m.validate_prepared(preflight)
        return {"status": "PASS_BATCH5_PREPARED_NO_INSTALL", "state": state, "candidate_count": 5}
    if state == "installed":
        receipt = json.loads(m.TRANSACTION.read_text())
        if m.sha256(m.IDENTITY) != receipt["post_identity_sha256"]: raise RuntimeError("post identity drift")
        for name, s in m.PLUGINS.items():
            m.verify_bundle(name, m.paths(name)["installed"], s["new"], macos11=True)
            m.verify_bundle(name, m.paths(name)["moved_old"], s["old"], macos11=False)
        return {"status": "PASS_BATCH5_INSTALLED_PENDING_AE", "state": state, "candidate_count": 5}
    if state == "rolled_back":
        if m.sha256(m.IDENTITY) != m.EXPECTED_PRE_IDENTITY: raise RuntimeError("rollback identity drift")
        for name, s in m.PLUGINS.items():
            m.verify_bundle(name, m.paths(name)["installed"], s["old"], macos11=False)
            m.verify_bundle(name, m.paths(name)["failed_new"], s["new"], macos11=True)
        return {"status": "PASS_BATCH5_ROLLED_BACK", "state": state, "candidate_count": 5}
    raise RuntimeError(f"unsafe partial transaction state: {state}")


if __name__ == "__main__": print(json.dumps(audit(), sort_keys=True))
