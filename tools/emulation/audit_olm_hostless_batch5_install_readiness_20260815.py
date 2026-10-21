#!/usr/bin/env python3
"""Read-only audit/generator for the 2026-08-15 five-plugin transaction."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install_olm_hostless_batch5_20260815.py"
OUTPUT = ROOT / "refs/conformance/olm_hostless_batch5_install_readiness_20260815.json"
SUPERSEDED_DISTANCE = "d138c75d7dbd4c9ca3643988eebd9d53b7581947b6e22aa0f424de6433e2f206"


def load_installer():
    spec = importlib.util.spec_from_file_location("batch5_installer", INSTALLER)
    module = importlib.util.module_from_spec(spec); assert spec.loader
    spec.loader.exec_module(module)
    return module


def file_sha(path: Path) -> str:
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h


def audit() -> dict[str, object]:
    m = load_installer()
    if m.EXPECTED_PRE_IDENTITY != file_sha(m.IDENTITY):
        raise RuntimeError("accepted identity drift")
    if m.ae_pids():
        raise RuntimeError("After Effects is running")
    if m.artifact_state() != "clean":
        raise RuntimeError("new batch5 transaction namespace is not clean")
    accepted = {r["plugin"]: r for r in json.loads(m.IDENTITY.read_text())["plugins"]}
    if set(accepted).intersection(m.PLUGINS) != set(m.PLUGINS) or len(m.PLUGINS) != 5:
        raise RuntimeError("exact five-plugin keyset drift")
    plugins = {}
    for name, s in m.PLUGINS.items():
        if not s["ready"] or not all(s.get(k) for k in ("candidate", "identity", "new")):
            raise RuntimeError(f"candidate not frozen: {name}")
        if s["new"] == SUPERSEDED_DISTANCE:
            raise RuntimeError("superseded minOS26.2 Distance candidate is forbidden")
        for key in ("identity", "source", "project"):
            if file_sha(s[key]) != s[f"{key}_sha256"]:
                raise RuntimeError(f"{key} authority drift: {name}")
        evidence_text = s["identity"].read_text()
        if s["new"] not in evidence_text or s["source_sha256"] not in evidence_text:
            raise RuntimeError(f"identity report does not bind source+binary: {name}")
        if accepted[name]["sha256"] != s["old"]:
            raise RuntimeError(f"accepted old row drift: {name}")
        matches = [p.resolve() for p in m.MEDIA_CORE.rglob(f"{name}.plugin")]
        if matches != [m.paths(name)["installed"].resolve()]:
            raise RuntimeError(f"recursive MediaCore bundle count/path drift: {name}")
        candidate = m.verify_bundle(name, s["candidate"], s["new"], macos11=True)
        installed = m.verify_bundle(name, m.paths(name)["installed"], s["old"], macos11=False)
        plugins[name] = {
            "candidate_bundle": str(s["candidate"].relative_to(ROOT)),
            "candidate_binary_sha256": s["new"],
            "candidate_identity": str(s["identity"].relative_to(ROOT)),
            "candidate_identity_sha256": s["identity_sha256"],
            "source": str(s["source"].relative_to(ROOT)),
            "source_sha256": s["source_sha256"],
            "project": str(s["project"].relative_to(ROOT)),
            "project_sha256": s["project_sha256"],
            "installed_bundle": str(m.paths(name)["installed"]),
            "installed_binary_sha256": s["old"],
            "required_exports": sorted(s["exports"]),
            "candidate_inventory": candidate["inventory"],
            "installed_inventory": installed["inventory"],
        }
    return {
        "schema": "olm.hostless-batch5-20260815-install-readiness/1",
        "status": "PASS_HOSTLESS_BATCH5_CANDIDATES_READY_FOR_TRANSACTIONAL_PREP_NOT_INSTALLED",
        "accepted_pre_identity_sha256": m.EXPECTED_PRE_IDENTITY,
        "after_effects_processes": [],
        "transaction_artifact_state": "clean",
        "candidate_count": 5,
        "superseded_distance_binary_explicitly_forbidden": SUPERSEDED_DISTANCE,
        "plugins": plugins,
        "scope": {"installer_executed": False, "prepared": False, "installed": False,
                  "after_effects_launched": False, "production_sources_changed": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--write", action="store_true"); args = parser.parse_args()
    report = audit()
    encoded = (json.dumps(report, indent=2) + "\n").encode()
    if args.write:
        if OUTPUT.exists() and OUTPUT.read_bytes() != encoded:
            raise RuntimeError(f"refusing to overwrite existing readiness: {OUTPUT}")
        OUTPUT.parent.mkdir(parents=True, exist_ok=True); OUTPUT.write_bytes(encoded)
    print(json.dumps({"status": report["status"], "candidate_count": 5,
                      "report_sha256": hashlib.sha256(encoded).hexdigest(), "written": args.write}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
