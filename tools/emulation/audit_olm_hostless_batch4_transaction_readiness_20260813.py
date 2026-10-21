#!/usr/bin/env python3
"""Final read-only gate before any four-plugin backup preparation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "refs/conformance/olm_hostless_batch4_transaction_readiness_20260813.json"
DOC = REPORT.with_suffix(".md")
FILES = {
    "readiness_auditor": (ROOT / "tools/emulation/audit_olm_hostless_batch4_install_readiness_20260813.py", "8fae1cf657a881dbf2b3eda41d6abfab1ac98aa1d12bfb72590a4259f0a96e0e"),
    "readiness_report": (ROOT / "refs/conformance/olm_hostless_batch4_install_readiness_20260813.json", "62def0d8d85a70b78266ba74ae1197f1abe918872546b526655cd329082f2093"),
    "readiness_unit": (ROOT / "tests/test_olm_hostless_batch4_install_readiness_20260813.py", "e2b4aa4284385dfc442766f578652c3df7363974a7c8f70ed17f21a421cf4bb2"),
    "installer": (ROOT / "scripts/install_olm_hostless_batch4_20260813.py", "8b6062619105ca64739790374beee844cb909ef062d34c85fb410f84d9bf0d8b"),
    "installer_unit": (ROOT / "tests/test_olm_hostless_batch4_transactional_installer_20260813.py", "388468e7d2523c3fc582b90316fa194a3b1efdbf49d39ebbceff8d22c439ed8b"),
    "accepted_identity": (ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json", "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"),
}
DOC_TEXT = """# Four-plugin transactional-preparation readiness

Verdict: `PASS_BATCH4_TRANSACTIONAL_PREP_READY_NO_MUTATION`.

The four source/closure-bound macOS 11 Universal candidates and the current installed identities validate live. The batch installer defaults to a read-only dry run. Its sandbox tests prove two exact backup copies per plugin, prepare-time MediaCore/identity immutability, cleanup after partial backup failure, rejection of partial transaction state, and restoration of all four old bundles plus the exact identity after an injected third-swap failure.

No backup preparation, plugin installation, identity update, After Effects launch, smoke, or formal release gate has occurred. This report authorizes only a later explicit `--prepare`; the user-requested batch policy still defers that mutation until the checkpoint is chosen.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def load_installer():
    path = FILES["installer"][0]
    spec = importlib.util.spec_from_file_location("batch4_installer_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate() -> dict[str, object]:
    identities = {}
    for name, (path, expected) in FILES.items():
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"identity drift: {name}: {actual}")
        identities[name] = {"path": str(path.relative_to(ROOT)), "sha256": actual}
    installer = load_installer()
    state = installer.artifact_state()
    if state != "clean":
        raise RuntimeError(f"transaction artifacts are not clean: {state}")
    watched = {"identity": sha256(installer.IDENTITY)}
    for name, spec in installer.PLUGINS.items():
        watched[f"candidate:{name}"] = sha256(installer.executable(spec["candidate"], name))
        watched[f"installed:{name}"] = sha256(installer.executable(installer.paths(name)["installed"], name))
    result = subprocess.run([sys.executable, str(FILES["installer"][0])], cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    dry = json.loads(result.stdout)
    if dry != {"after_effects_processes": [], "candidate_count": 4,
               "status": "dry_run_prepare_ready_no_mutation", "transaction_artifact_state": "clean"}:
        raise RuntimeError(f"unexpected dry-run output: {dry}")
    after = {"identity": sha256(installer.IDENTITY)}
    for name, spec in installer.PLUGINS.items():
        after[f"candidate:{name}"] = sha256(installer.executable(spec["candidate"], name))
        after[f"installed:{name}"] = sha256(installer.executable(installer.paths(name)["installed"], name))
    if watched != after:
        raise RuntimeError("dry run mutated bound bytes")
    return {
        "schema": "olm.hostless-batch4-transaction-readiness/1",
        "status": "PASS_BATCH4_TRANSACTIONAL_PREP_READY_NO_MUTATION",
        "identities": identities,
        "dry_run": dry,
        "bound_bytes_before_after_exact": True,
        "sandbox_proof": {
            "tests": 5, "two_backups_per_plugin": True,
            "prepare_media_and_identity_unchanged": True,
            "partial_backup_cleanup": True, "partial_state_rejected": True,
            "third_swap_failure_restores_all_four_and_identity": True,
        },
        "scope": {
            "prepared": False, "installed": False, "identity_updated": False,
            "after_effects_launched": False, "post_install_smoke_complete": False,
            "formal_release_gate_complete": False, "next_allowed_action": "explicit_batch_prepare",
        },
    }


def validate(data: object) -> None:
    if not isinstance(data, dict) or set(data) != {"schema", "status", "identities", "dry_run", "bound_bytes_before_after_exact", "sandbox_proof", "scope"}:
        raise ValueError("top-level schema")
    if data != generate():
        raise ValueError("saved transaction readiness differs from live state")
    if data["scope"] != {"prepared": False, "installed": False, "identity_updated": False,
                         "after_effects_launched": False, "post_install_smoke_complete": False,
                         "formal_release_gate_complete": False, "next_allowed_action": "explicit_batch_prepare"}:
        raise ValueError("scope")
    if DOC.read_text() != DOC_TEXT:
        raise ValueError("documentation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    generated = generate()
    if args.write:
        REPORT.write_bytes(canonical(generated)); DOC.write_text(DOC_TEXT)
    if not REPORT.is_file() or not DOC.is_file():
        raise SystemExit("transaction readiness missing; use --write")
    before = REPORT.read_bytes()
    validate(json.loads(before))
    if before != canonical(generated) or REPORT.read_bytes() != before:
        raise SystemExit("transaction readiness is not canonical/read-only exact")
    print(generated["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
