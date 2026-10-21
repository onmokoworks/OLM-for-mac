#!/usr/bin/env python3
"""Prepare or atomically install the source-bound ColorKeep complete union."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/install_colorkeep_count9_incremental_20260813.py"


def load_base():
    spec = importlib.util.spec_from_file_location("colorkeep_base_installer", BASE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


base = load_base()
HANDOFF = ROOT / "handoffs/colorkeep_source_bound_complete_union_install_20260813"
CANDIDATE = ROOT / "handoffs/colorkeep_source_bound_complete_union_candidate_20260813/Product/ColorKeep.plugin"
EXPECTED_SOURCE = "d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3"
EXPECTED_OLD = "fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77"
EXPECTED_NEW = "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d"
EXPECTED_PRE_IDENTITY = "e17dddbd8f26b1ac6caf65b43179689b8fa821f2cd9fe1ff23290afe29023431"

base.HANDOFF = HANDOFF
base.CANDIDATE = CANDIDATE
base.BACKUP = HANDOFF / "installed_backup/ColorKeep.plugin"
base.PRE_SWAP = HANDOFF / "pre_swap_original/ColorKeep.plugin"
base.MOVED_OLD = HANDOFF / "moved_old/ColorKeep.plugin"
base.PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
base.POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
base.TRANSACTION = HANDOFF / "install_transaction.json"
base.PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
base.EXPECTED_SOURCE = EXPECTED_SOURCE
base.EXPECTED_OLD = EXPECTED_OLD
base.EXPECTED_NEW = EXPECTED_NEW
base.EXPECTED_PRE_IDENTITY = EXPECTED_PRE_IDENTITY


def accepted_identity():
    before = json.loads(base.PRE_IDENTITY.read_text())
    if base.sha(base.PRE_IDENTITY) != EXPECTED_PRE_IDENTITY or base.sha(base.IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("pre-install identity manifest drift")
    after = json.loads(json.dumps(before))
    rows = {row["plugin"]: row for row in after["plugins"]}
    if set(rows) != base.PLUGINS or rows["ColorKeep"]["sha256"] != EXPECTED_OLD:
        raise RuntimeError("pre-install plugin identity drift")
    rows["ColorKeep"].update({
        "sha256": EXPECTED_NEW,
        "source_bundle": "handoffs/colorkeep_source_bound_complete_union_candidate_20260813/Product/ColorKeep.plugin",
        "source_sha256": EXPECTED_NEW,
        "source_installed_exact": True,
        "installed_bundle_count": 1,
        "architectures": ["x86_64", "arm64"],
        "universal_exact": True,
        "codesign_exact": True,
    })
    now = datetime.now(timezone.utc).isoformat()
    after["accepted_at"] = now
    after["installed_after"] = now
    return before, after


base.accepted_identity = accepted_identity
original_atomic_write_json = base.atomic_write_json


def scoped_atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    value = json.loads(json.dumps(payload))
    if path == base.TRANSACTION:
        value["schema"] = "colorkeep.source-bound-complete-union-install-transaction/1"
    original_atomic_write_json(path, value)


base.atomic_write_json = scoped_atomic_write_json


def prepare() -> int:
    if base.ae_pids():
        raise RuntimeError("After Effects is running")
    if base.sha(base.SOURCE) != EXPECTED_SOURCE or base.sha(base.IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("source or accepted identity drift")
    base.verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    base.verify_bundle(base.INSTALLED, EXPECTED_OLD, True)
    if base.TRANSACTION.exists() or base.MOVED_OLD.exists():
        raise RuntimeError("install transaction already exists")
    HANDOFF.mkdir(parents=True, exist_ok=True)
    if not base.PRE_IDENTITY.exists():
        shutil.copy2(base.IDENTITY, base.PRE_IDENTITY)
    for destination in (base.BACKUP, base.PRE_SWAP):
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ditto", str(base.INSTALLED), str(destination)], check=True)
        base.verify_bundle(destination, EXPECTED_OLD, True)
    saved_argv = sys.argv
    try:
        sys.argv = [str(Path(__file__)), "--preflight"]
        return base.main()
    finally:
        sys.argv = saved_argv


def install() -> int:
    saved_argv = sys.argv
    try:
        sys.argv = [str(Path(__file__))]
        return base.main()
    finally:
        sys.argv = saved_argv


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--install", action="store_true")
    args = parser.parse_args()
    return prepare() if args.prepare else install()


if __name__ == "__main__":
    raise SystemExit(main())
