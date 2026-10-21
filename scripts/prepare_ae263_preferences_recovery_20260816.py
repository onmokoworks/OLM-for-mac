#!/usr/bin/env python3
"""Prepare and optionally apply a reversible AE 26.3 preference reset.

Default mode is read-only. ``--prepare`` creates a byte-verified backup in the
workspace without changing Adobe preferences. ``--reset`` and ``--restore``
are intentionally separate, explicit mutations and are never implied by
``--prepare``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREFS = Path.home() / "Library/Preferences/Adobe/After Effects/26.3"
HANDOFF = ROOT / "handoffs/olm_ae263_preferences_recovery_20260816"
BACKUP = HANDOFF / "26.3_backup"
MANIFEST = HANDOFF / "pre_reset_manifest.json"
MOVED = PREFS.with_name("26.3.olm-pre-reset-20260816")
QUARANTINE = PREFS.with_name("26.3.olm-post-reset-quarantine-20260816")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ae_processes() -> list[str]:
    value = subprocess.run(
        ["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True, check=True
    )
    return sorted(
        line.strip() for line in value.stdout.splitlines()
        if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
        or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line
    )


def inventory(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError(f"expected canonical directory: {root}")
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            rows.append({"path": relative, "kind": "symlink", "target": os.readlink(path)})
        elif stat.S_ISDIR(info.st_mode):
            rows.append({"path": relative, "kind": "directory", "mode": stat.S_IMODE(info.st_mode)})
        elif stat.S_ISREG(info.st_mode):
            rows.append({
                "path": relative, "kind": "file", "size": info.st_size,
                "mode": stat.S_IMODE(info.st_mode), "sha256": sha256(path),
            })
        else:
            raise RuntimeError(f"unsupported preference node: {path}")
    return rows


def state() -> dict[str, Any]:
    processes = ae_processes()
    original_inventory = inventory(PREFS) if PREFS.is_dir() else None
    moved_inventory = inventory(MOVED) if MOVED.is_dir() else None
    backup_inventory = inventory(BACKUP) if BACKUP.is_dir() else None
    saved_inventory = None
    if MANIFEST.is_file():
        saved_inventory = json.loads(MANIFEST.read_text(encoding="utf-8")).get("inventory")
    prepared = backup_inventory is not None and backup_inventory == saved_inventory
    original_exact = original_inventory is not None and original_inventory == saved_inventory
    moved_exact = moved_inventory is not None and moved_inventory == saved_inventory
    return {
        "schema": "olm.ae263-preferences-recovery-state/1",
        "status": (
            "restored" if prepared and original_exact and QUARANTINE.is_dir() and not MOVED.exists()
            else "prepared_no_reset" if prepared and original_exact and not MOVED.exists()
            else "reset_applied_waiting_for_ae" if prepared and moved_exact and not PREFS.exists()
            else "reset_applied" if prepared and moved_exact and PREFS.is_dir()
            else "unprepared"
        ),
        "ae_or_aerender_processes": processes,
        "preferences_path": str(PREFS),
        "preferences_present": PREFS.is_dir(),
        "backup_path": str(BACKUP),
        "backup_present": BACKUP.is_dir(),
        "manifest_present": MANIFEST.is_file(),
        "moved_original_path": str(MOVED),
        "moved_original_present": MOVED.is_dir(),
        "quarantine_path": str(QUARANTINE),
        "quarantine_present": QUARANTINE.is_dir(),
        "prepared_exact": prepared,
        "node_count": len(original_inventory) if original_inventory is not None else None,
    }


def prepare() -> None:
    if ae_processes():
        raise RuntimeError("AE/aerender must not be running")
    if not PREFS.is_dir() or PREFS.is_symlink():
        raise RuntimeError("AE 26.3 preferences are absent or noncanonical")
    if HANDOFF.exists() or BACKUP.exists() or MANIFEST.exists():
        raise RuntimeError("refusing to overwrite recovery preparation")
    original = inventory(PREFS)
    HANDOFF.mkdir(parents=True, exist_ok=False)
    shutil.copytree(PREFS, BACKUP, symlinks=True, copy_function=shutil.copy2)
    copied = inventory(BACKUP)
    if copied != original:
        raise RuntimeError("preference backup inventory mismatch")
    value = {
        "schema": "olm.ae263-preferences-recovery-manifest/1",
        "status": "prepared_no_reset",
        "preferences_path": str(PREFS),
        "backup_path": str(BACKUP),
        "inventory": original,
        "claim_boundary": "Byte inventory only; no xattr/ACL claim. Adobe preferences were not changed.",
    }
    MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not state()["prepared_exact"]:
        raise RuntimeError("prepared state failed self-validation")


def reset() -> None:
    current = state()
    if current["ae_or_aerender_processes"]:
        raise RuntimeError("AE/aerender must not be running")
    if current["status"] != "prepared_no_reset" or not current["prepared_exact"]:
        raise RuntimeError("exact prepared backup is required")
    if MOVED.exists() or QUARANTINE.exists():
        raise RuntimeError("reset/restore target already exists")
    os.rename(PREFS, MOVED)


def restore() -> None:
    current = state()
    if current["ae_or_aerender_processes"]:
        raise RuntimeError("AE/aerender must not be running")
    if not MOVED.is_dir() or QUARANTINE.exists():
        raise RuntimeError("exact reset state is required for restore")
    saved = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if inventory(MOVED) != saved["inventory"]:
        raise RuntimeError("moved preference inventory mismatch")
    if not PREFS.exists():
        os.rename(MOVED, PREFS)
        return
    if not PREFS.is_dir():
        raise RuntimeError("new preferences path is noncanonical")
    os.rename(PREFS, QUARANTINE)
    try:
        os.rename(MOVED, PREFS)
    except BaseException:
        os.rename(QUARANTINE, PREFS)
        raise
    if inventory(PREFS) != saved["inventory"]:
        raise RuntimeError("restored preference inventory mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--reset", action="store_true")
    modes.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.reset:
        reset()
    elif args.restore:
        restore()
    print(json.dumps(state(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
