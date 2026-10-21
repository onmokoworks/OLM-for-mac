#!/usr/bin/env python3
"""Two-phase transactional install for the bounded Kira FP-contract candidate."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs/olmkirakira_fp_contract_incremental_install_20260813"
CANDIDATE = ROOT / "handoffs/olmkirakira_fp_contract_universal_candidate_20260813/product/OLMKiraKira.plugin"
BUILD_IDENTITY = ROOT / "handoffs/olmkirakira_fp_contract_universal_candidate_20260813/build_identity.json"
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
MEDIACORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
INSTALLED = MEDIACORE / "OLMKiraKira.plugin"
STAGED = MEDIACORE / ".OLMKiraKira.plugin.codex-fp-contract-stage"
FAILED_NEW = MEDIACORE / ".OLMKiraKira.plugin.codex-fp-contract-failed"
BACKUP = HANDOFF / "installed_backup/OLMKiraKira.plugin"
PRE_SWAP = HANDOFF / "pre_swap_original/OLMKiraKira.plugin"
MOVED_OLD = HANDOFF / "moved_old/OLMKiraKira.plugin"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREPARED = HANDOFF / "prepared_install.json"
TRANSACTION = HANDOFF / "install_transaction.json"

SOURCE_SHA = "8f3ccda261b525f58e9abb6d942986f5f71ce6c67758aa7edfecc50a557f3e8f"
OLD_SHA = "69da64666478b25957aa268f6bb6fbc869c3d50b61759f9ca00172045afb5194"
NEW_SHA = "260c2d5e635b38213adf88e01298510bf7f180b38bdb5e1d2b85a2906fbfbf18"
PRE_IDENTITY_SHA = "cc9cb7edd30c23aef06b6ef4aab819763f900a1d40938e5b5a2b66758bb566be"
BUILD_IDENTITY_SHA = "9bf6570d46ad6cc5e181b28c21ff4077a127c4e850fe29f7a9ef892b2404b2d5"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMKiraKira"


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if run.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed: {name}")
        found += [f"{name}:{pid}" for pid in run.stdout.split() if pid.isdigit()]
    return found


def inventory(bundle: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file():
            continue
        rows.append({
            "path": path.relative_to(bundle).as_posix(),
            "size": path.stat().st_size,
            "mode": stat.S_IMODE(path.stat().st_mode),
            "sha256": sha256(path),
        })
    return rows


def verify_bundle(bundle: Path, expected_sha: str) -> dict[str, Any]:
    if not bundle.is_dir() or sha256(binary(bundle)) != expected_sha:
        raise RuntimeError(f"bundle identity mismatch: {bundle}")
    archs = subprocess.check_output(["lipo", "-archs", str(binary(bundle))], text=True).strip().split()
    if archs != ["x86_64", "arm64"]:
        raise RuntimeError(f"bundle is not expected Universal order: {bundle}: {archs}")
    signed = subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle)],
        text=True, capture_output=True,
    )
    if signed.returncode:
        raise RuntimeError(f"codesign failure: {bundle}: {signed.stdout}{signed.stderr}")
    return {"binary_sha256": expected_sha, "architectures": archs, "strict_codesign": True, "inventory": inventory(bundle)}


def ditto(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise RuntimeError(f"refusing to overwrite durable path: {destination}")
    result = subprocess.run(["ditto", str(source), str(destination)], text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"ditto failed: {result.stdout}{result.stderr}")


def base_checks() -> tuple[dict[str, Any], dict[str, Any]]:
    if ae_processes():
        raise RuntimeError("After Effects must be stopped")
    if sha256(SOURCE) != SOURCE_SHA or sha256(BUILD_IDENTITY) != BUILD_IDENTITY_SHA:
        raise RuntimeError("source/build authority drift")
    if sha256(IDENTITY) != PRE_IDENTITY_SHA:
        raise RuntimeError("accepted identity changed from authorized pre-state")
    candidate = verify_bundle(CANDIDATE, NEW_SHA)
    current = verify_bundle(INSTALLED, OLD_SHA)
    identity = json.loads(IDENTITY.read_text())
    row = next(item for item in identity["plugins"] if item["plugin"] == "OLMKiraKira")
    if row["sha256"] != OLD_SHA or row["installed_bundle_count"] != 1:
        raise RuntimeError("current Kira identity row is not the authorized predecessor")
    return candidate, current


def prepare() -> None:
    if TRANSACTION.exists() or POST_IDENTITY.exists() or MOVED_OLD.exists():
        raise RuntimeError("transaction artifacts already exist")
    candidate, current = base_checks()
    HANDOFF.mkdir(parents=True, exist_ok=True)
    ditto(INSTALLED, BACKUP)
    ditto(INSTALLED, PRE_SWAP)
    shutil.copy2(IDENTITY, PRE_IDENTITY)
    if sha256(PRE_IDENTITY) != PRE_IDENTITY_SHA:
        raise RuntimeError("pre-identity copy mismatch")
    backup = verify_bundle(BACKUP, OLD_SHA)
    pre_swap = verify_bundle(PRE_SWAP, OLD_SHA)
    if backup["inventory"] != current["inventory"] or pre_swap["inventory"] != current["inventory"]:
        raise RuntimeError("durable predecessor inventories differ")
    report = {
        "schema": "olmkirakira.fp-contract-install-prepared/1",
        "status": "prepared_no_mediacore_or_identity_mutation",
        "source_sha256": SOURCE_SHA,
        "candidate": candidate,
        "installed_before": current,
        "backup": backup,
        "pre_swap_original": pre_swap,
        "pre_identity_sha256": PRE_IDENTITY_SHA,
        "after_effects_processes": [],
    }
    PREPARED.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("PASS_OLMKIRAKIRA_FP_CONTRACT_INSTALL_PREPARED_NO_MUTATION")


def rename_swap(first: Path, second: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    fn = libc.renameatx_np
    fn.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    fn.restype = ctypes.c_int
    if fn(-2, os.fsencode(first), -2, os.fsencode(second), 0x00000002) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".codex-kira-fp.tmp")
    if temporary.exists():
        temporary.unlink()
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def install() -> None:
    if not PREPARED.is_file() or TRANSACTION.exists() or POST_IDENTITY.exists() or MOVED_OLD.exists():
        raise RuntimeError("prepared state missing or transaction already consumed")
    candidate, current = base_checks()
    prepared = json.loads(PREPARED.read_text())
    if prepared["candidate"] != candidate or prepared["installed_before"] != current:
        raise RuntimeError("prepared state differs from live pre-install state")
    if verify_bundle(BACKUP, OLD_SHA)["inventory"] != current["inventory"] or verify_bundle(PRE_SWAP, OLD_SHA)["inventory"] != current["inventory"]:
        raise RuntimeError("prepared rollback bundles drifted")
    if STAGED.exists() or FAILED_NEW.exists():
        raise RuntimeError("staging or failed-new path already exists")
    ditto(CANDIDATE, STAGED)
    if verify_bundle(STAGED, NEW_SHA)["inventory"] != candidate["inventory"]:
        raise RuntimeError("staged candidate differs")
    swapped = False
    manifest_updated = False
    try:
        rename_swap(INSTALLED, STAGED)
        swapped = True
        installed_after = verify_bundle(INSTALLED, NEW_SHA)
        old_after = verify_bundle(STAGED, OLD_SHA)
        if installed_after["inventory"] != candidate["inventory"] or old_after["inventory"] != current["inventory"]:
            raise RuntimeError("post-swap inventory mismatch")
        ditto(STAGED, MOVED_OLD)
        if verify_bundle(MOVED_OLD, OLD_SHA)["inventory"] != current["inventory"]:
            raise RuntimeError("moved-old durable copy differs")
        identity = json.loads(IDENTITY.read_text())
        row = next(item for item in identity["plugins"] if item["plugin"] == "OLMKiraKira")
        row.update({
            "sha256": NEW_SHA,
            "source_bundle": str(CANDIDATE.relative_to(ROOT)),
            "source_sha256": NEW_SHA,
            "source_installed_exact": True,
            "universal_exact": True,
            "codesign_exact": True,
            "installed_bundle_count": 1,
        })
        now = datetime.now(timezone.utc).isoformat()
        identity["accepted_at"] = now
        identity["installed_after"] = now
        atomic_write_json(IDENTITY, identity)
        manifest_updated = True
        shutil.copy2(IDENTITY, POST_IDENTITY)
        transaction = {
            "schema": "olmkirakira.fp-contract-incremental-install/1",
            "status": "installed",
            "source_sha256": SOURCE_SHA,
            "old_binary_sha256": OLD_SHA,
            "new_binary_sha256": NEW_SHA,
            "pre_identity_sha256": PRE_IDENTITY_SHA,
            "post_identity_sha256": sha256(IDENTITY),
            "candidate_inventory": candidate["inventory"],
            "installed_inventory": installed_after["inventory"],
            "old_inventory": current["inventory"],
            "atomic_exchange_api": "renameatx_np(RENAME_SWAP)",
            "rollback_copy_count": 3,
            "after_effects_processes_before_after": [[], ae_processes()],
        }
        if transaction["after_effects_processes_before_after"] != [[], []]:
            raise RuntimeError("unexpected AE process after install")
        TRANSACTION.write_text(json.dumps(transaction, indent=2, sort_keys=True) + "\n")
    except Exception:
        if manifest_updated:
            shutil.copy2(PRE_IDENTITY, IDENTITY)
        if swapped:
            rename_swap(INSTALLED, STAGED)
        if STAGED.exists() and not FAILED_NEW.exists():
            os.replace(STAGED, FAILED_NEW)
        raise
    if STAGED.exists():
        shutil.rmtree(STAGED)
    print("PASS_OLMKIRAKIRA_FP_CONTRACT_INCREMENTAL_INSTALL_NO_AE")


def dry_run() -> None:
    candidate, current = base_checks()
    if PREPARED.exists():
        status = "prepared"
    else:
        status = "ready_to_prepare"
    print(json.dumps({"status": status, "candidate": candidate["binary_sha256"], "installed": current["binary_sha256"], "after_effects_processes": []}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--prepare", action="store_true")
    actions.add_argument("--install", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.install:
        install()
    else:
        dry_run()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_OLMKIRAKIRA_FP_CONTRACT_INSTALL: {exc}", file=sys.stderr)
        raise
