#!/usr/bin/env python3
"""Atomically install the reviewed ColorKeep count9 candidate with rollback."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import plistlib
import re
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs/colorkeep_count9_incremental_install_20260813"
CANDIDATE = HANDOFF / "candidate/Product/ColorKeep.plugin"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/ColorKeep.plugin"
BACKUP = HANDOFF / "installed_backup/ColorKeep.plugin"
PRE_SWAP = HANDOFF / "pre_swap_original/ColorKeep.plugin"
MOVED_OLD = HANDOFF / "moved_old/ColorKeep.plugin"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
TRANSACTION = HANDOFF / "install_transaction.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
SOURCE = ROOT / "mac/ColorKeep/ColorKeep.cpp"
EXPECTED_SOURCE = "3ff3a4d4319f5b3b5519e517fcf591be417c97e4e9dd62117fe4e42f66ebdfd3"
EXPECTED_OLD = "262b73e656d4363dce0de6f0fe819fabf461e157ca7cedd98cad107c8db87fe8"
EXPECTED_NEW = "fcd501dae5e62aaa0bb8c022cc55c3a6735e3021d465b42b80c939f33624dd77"
EXPECTED_PRE_IDENTITY = "90e37eefd68f990e137d23d46212c7039ec49f03e86bfe076765cc350da3820a"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/ColorKeep"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def ae_pids() -> list[int]:
    result = run(
        "pgrep", "-f",
        r"^/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects( |$)",
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("could not observe After Effects processes")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def inventory(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise RuntimeError(f"bundle missing: {bundle}")
    rows: list[dict[str, object]] = []
    for path in sorted([bundle, *bundle.rglob("*")],
                       key=lambda item: item.relative_to(bundle).as_posix()):
        info = path.lstat()
        name = "." if path == bundle else path.relative_to(bundle).as_posix()
        row: dict[str, object] = {"path": name, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update(type="symlink", target=os.readlink(path))
        elif path.is_dir():
            row["type"] = "directory"
        elif path.is_file():
            row.update(type="file", bytes=info.st_size, sha256=sha(path))
        else:
            raise RuntimeError(f"unsupported bundle entry: {path}")
        rows.append(row)
    return rows


def verify_bundle(bundle: Path, expected: str, require_macos11: bool) -> dict[str, object]:
    binary = executable(bundle)
    if sha(binary) != expected:
        raise RuntimeError(f"bundle executable mismatch: {bundle}")
    archs = run("lipo", "-archs", str(binary)).stdout.split()
    if set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"bundle is not Universal: {bundle}")
    signature = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if signature.returncode:
        raise RuntimeError(f"invalid strict signature: {bundle}: {signature.stderr}")
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    minimums: dict[str, str] = {}
    exports: dict[str, int] = {}
    for arch in archs:
        otool = run("otool", "-arch", arch, "-l", str(binary))
        versions = re.findall(r"^\s+minos\s+(\S+)\s*$", otool.stdout, re.MULTILINE)
        if otool.returncode or len(versions) != 1:
            raise RuntimeError(f"cannot bind minos for {arch}")
        minimums[arch] = versions[0]
        nm = run("nm", "-arch", arch, "-gU", str(binary))
        exports[arch] = sum(line.rstrip().endswith(" _EffectMain") for line in nm.stdout.splitlines())
        if nm.returncode or exports[arch] != 1:
            raise RuntimeError(f"EffectMain export drift for {arch}")
    if require_macos11 and (
        info.get("LSMinimumSystemVersion") != "11.0"
        or set(minimums.values()) != {"11.0"}
    ):
        raise RuntimeError(f"deployment target is not 11.0: {bundle}")
    return {
        "binary_sha256": expected,
        "architectures": archs,
        "strict_codesign": True,
        "info_plist_minimum_system_version": info.get("LSMinimumSystemVersion"),
        "macho_slice_minimum_versions": minimums,
        "effect_main_exports": exports,
        "manifest": inventory(bundle),
    }


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_path = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temp = Path(raw_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def atomic_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameatx_np = libc.renameatx_np
    renameatx_np.argtypes = [ctypes.c_int, ctypes.c_char_p,
                             ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameatx_np.restype = ctypes.c_int
    at_fdcwd = -2
    rename_swap = 0x00000002
    result = renameatx_np(
        at_fdcwd, os.fsencode(left), at_fdcwd, os.fsencode(right), rename_swap,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def accepted_identity() -> tuple[dict[str, object], dict[str, object]]:
    before = json.loads(PRE_IDENTITY.read_text(encoding="utf-8"))
    if sha(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY or sha(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("pre-install identity manifest drift")
    after = json.loads(json.dumps(before))
    rows = {row["plugin"]: row for row in after["plugins"]}
    if set(rows) != PLUGINS:
        raise RuntimeError("identity plugin set drift")
    row = rows["ColorKeep"]
    if row["sha256"] != EXPECTED_OLD:
        raise RuntimeError("pre-install ColorKeep identity drift")
    row.update({
        "sha256": EXPECTED_NEW,
        "source_bundle": "handoffs/colorkeep_count9_incremental_install_20260813/candidate/Product/ColorKeep.plugin",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if TRANSACTION.exists() or MOVED_OLD.exists():
        raise RuntimeError("install transaction already completed or partially retained")
    if sha(SOURCE) != EXPECTED_SOURCE:
        raise RuntimeError("production source drift")
    ae_before = ae_pids()
    if ae_before:
        raise RuntimeError(f"After Effects is running: {ae_before}")
    candidate = verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    installed_before = verify_bundle(INSTALLED, EXPECTED_OLD, False)
    backup = verify_bundle(BACKUP, EXPECTED_OLD, False)
    pre_swap = verify_bundle(PRE_SWAP, EXPECTED_OLD, False)
    if not (installed_before["manifest"] == backup["manifest"] == pre_swap["manifest"]):
        raise RuntimeError("durable backup inventory mismatch")
    before_identity, after_identity = accepted_identity()
    preinstall = {
        "schema": "colorkeep.count9-preinstall-inventory/1",
        "production_source_sha256_before": EXPECTED_SOURCE,
        "production_source_sha256_after_preflight": sha(SOURCE),
        "ae_processes": ae_before,
        "pre_identity_sha256": sha(PRE_IDENTITY),
        "candidate": candidate,
        "installed_before": installed_before,
        "installed_backup": backup,
        "pre_swap_original": pre_swap,
        "durable_old_inventories_exact": True,
        "candidate_ready_for_staging": True,
    }
    if args.preflight:
        atomic_write_json(PREINSTALL, preinstall)
        print(json.dumps({"status": "preflight_complete", "manifest": str(PREINSTALL)}, sort_keys=True))
        return 0
    if not PREINSTALL.is_file() or json.loads(PREINSTALL.read_text(encoding="utf-8")) != preinstall:
        raise RuntimeError("preinstall inventory manifest missing or stale")

    staged = INSTALLED.with_name(".ColorKeep.count9-stage-20260813")
    if staged.exists():
        raise RuntimeError(f"unexpected staged path: {staged}")
    subprocess.run(["ditto", str(CANDIDATE), str(staged)], check=True)
    staged_live = verify_bundle(staged, EXPECTED_NEW, True)
    if staged_live["manifest"] != candidate["manifest"]:
        raise RuntimeError("staged candidate inventory mismatch")

    swapped = False
    old_retained = False
    identity_changed = False
    try:
        atomic_exchange(INSTALLED, staged)
        swapped = True
        installed_after = verify_bundle(INSTALLED, EXPECTED_NEW, True)
        staged_old = verify_bundle(staged, EXPECTED_OLD, False)
        if installed_after["manifest"] != candidate["manifest"]:
            raise RuntimeError("installed candidate inventory mismatch")
        if staged_old["manifest"] != installed_before["manifest"]:
            raise RuntimeError("atomic-swap original inventory mismatch")
        MOVED_OLD.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged, MOVED_OLD)
        old_retained = True
        atomic_write_json(IDENTITY, after_identity)
        identity_changed = True
        shutil.copy2(IDENTITY, POST_IDENTITY_COPY)
        ae_after = ae_pids()
        if ae_after:
            raise RuntimeError(f"After Effects appeared during install: {ae_after}")
        transaction = {
            "schema": "colorkeep.count9-incremental-install-transaction/1",
            "production_source_sha256_before": EXPECTED_SOURCE,
            "production_source_sha256_after": sha(SOURCE),
            "ae_processes_before": ae_before,
            "ae_processes_after": ae_after,
            "old_binary_sha256": EXPECTED_OLD,
            "new_binary_sha256": EXPECTED_NEW,
            "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
            "post_identity_sha256": sha(IDENTITY),
            "candidate_staged_verified_before_swap": True,
            "same_volume_atomic_bundle_exchange": True,
            "atomic_exchange_api": "renameatx_np(RENAME_SWAP)",
            "rollback_original": str(MOVED_OLD),
            "identity_top_level_changed_fields": ["accepted_at", "installed_after"],
            "identity_changed_plugins": ["ColorKeep"],
            "source_before_after_exact": True,
        }
        atomic_write_json(TRANSACTION, transaction)
    except BaseException:
        if identity_changed:
            atomic_write_json(IDENTITY, before_identity)
        if swapped and not old_retained and staged.exists() and INSTALLED.exists():
            atomic_exchange(INSTALLED, staged)
            swapped = False
        elif swapped and old_retained and MOVED_OLD.exists() and INSTALLED.exists():
            failed = HANDOFF / "failed_new/ColorKeep.plugin"
            failed.parent.mkdir(parents=True, exist_ok=True)
            os.replace(INSTALLED, failed)
            os.replace(MOVED_OLD, INSTALLED)
        staged.exists() and shutil.rmtree(staged)
        raise

    print(json.dumps({
        "status": "installed",
        "binary_sha256": EXPECTED_NEW,
        "identity_sha256": sha(IDENTITY),
        "handoff": str(HANDOFF),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
