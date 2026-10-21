#!/usr/bin/env python3
"""Prepare or transactionally install the frozen OLMSmoother2 39-cell candidate.

The default invocation is read-only. ``--prepare`` creates two durable copies
of the installed predecessor and an exact pre-identity snapshot without
changing MediaCore. ``--install`` is accepted only from that prepared state.
"""

from __future__ import annotations

import argparse
import copy
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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_HANDOFF = ROOT / "handoffs/olmsmoother2_pf8_pf16_pf32_public_smart_candidate_20260814"
HANDOFF = ROOT / "handoffs/olmsmoother2_pf8_pf16_pf32_incremental_install_20260814"
CANDIDATE = CANDIDATE_HANDOFF / "product/OLMSmoother2.plugin"
MEDIACORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
INSTALLED = MEDIACORE / "OLMSmoother2.plugin"
BACKUP = HANDOFF / "installed_backup/OLMSmoother2.plugin"
PRE_SWAP = HANDOFF / "pre_swap_original/OLMSmoother2.plugin"
MOVED_OLD = HANDOFF / "moved_old/OLMSmoother2.plugin"
FAILED_NEW = HANDOFF / "failed_new/OLMSmoother2.plugin"
STAGED = MEDIACORE / ".OLMSmoother2.pf8-pf16-pf32-stage-20260814"
SOURCE = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp"
PROJECT = ROOT / "mac/OLMSmoother2/Mac/OLMSmoother2.xcodeproj/project.pbxproj"
BUILD_IDENTITY = CANDIDATE_HANDOFF / "build_identity.json"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
TRANSACTION = HANDOFF / "install_transaction.json"

EXPECTED_SOURCE = "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168"
EXPECTED_PROJECT = "8a5525814eb7917b4ee124c507caf6a085200decf6072b32d52779e38279b89a"
EXPECTED_BUILD_IDENTITY = "c0852db33833084681012fa4a854f21bd50f96d29b392deb784df0fa89a6bd0b"
EXPECTED_OLD = "55d138e2a25704ffa59d8bd08d20e2160525f8f8011b8e11c733ae23fddd795e"
EXPECTED_NEW = "c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f"
EXPECTED_PRE_IDENTITY = "24c4f71a46b4bf969226bd17204e116290048570f3515e953b7f72f3fed58aa9"
PLUGIN = "OLMSmoother2"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
REQUIRED_EXPORTS = ("_EffectMain",)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMSmoother2"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def ae_pids() -> list[int]:
    result = run("ps", "ax", "-o", "pid=,command=")
    if result.returncode:
        raise RuntimeError("could not observe After Effects processes")
    pattern = re.compile(r"/(?:Adobe After Effects[^/]*/Contents/MacOS/After Effects|AfterFX|aerender)(?:\s|$)")
    return sorted(
        int(line.strip().split(None, 1)[0])
        for line in result.stdout.splitlines()
        if line.strip() and pattern.search(line)
    )


def inventory(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise RuntimeError(f"bundle missing: {bundle}")
    rows: list[dict[str, object]] = []
    for path in sorted([bundle, *bundle.rglob("*")], key=lambda p: p.relative_to(bundle).as_posix()):
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
    if not binary.is_file() or sha(binary) != expected:
        raise RuntimeError(f"bundle executable mismatch: {bundle}")
    lipo = run("lipo", "-archs", str(binary))
    if lipo.returncode or set(lipo.stdout.split()) != {"arm64", "x86_64"}:
        raise RuntimeError(f"bundle is not exactly Universal: {bundle}")
    signature = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if signature.returncode:
        raise RuntimeError(f"invalid strict signature: {bundle}: {signature.stderr}")
    detail = run("codesign", "-dv", "--verbose=4", str(bundle))
    detail_text = detail.stdout + detail.stderr
    signing_kind = "ad-hoc" if "Signature=adhoc" in detail_text and "TeamIdentifier=not set" in detail_text else "other"
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    minimums: dict[str, str] = {}
    exports: dict[str, dict[str, int]] = {}
    for arch in ("x86_64", "arm64"):
        load = run("otool", "-arch", arch, "-l", str(binary))
        versions = re.findall(r"^\s+minos\s+(\S+)\s*$", load.stdout, re.MULTILINE)
        if load.returncode or len(versions) != 1:
            raise RuntimeError(f"cannot bind minimum OS for {arch}: {bundle}")
        minimums[arch] = versions[0]
        symbols = run("nm", "-arch", arch, "-gU", str(binary))
        exports[arch] = {
            symbol: sum(line.rstrip().endswith(" " + symbol) for line in symbols.stdout.splitlines())
            for symbol in REQUIRED_EXPORTS
        }
        if symbols.returncode or any(count != 1 for count in exports[arch].values()):
            raise RuntimeError(f"required export drift for {arch}: {bundle}")
    if require_macos11 and (info.get("LSMinimumSystemVersion") != "11.0" or set(minimums.values()) != {"11.0"}):
        raise RuntimeError(f"candidate deployment target is not macOS 11: {bundle}")
    return {
        "binary_sha256": expected,
        "architectures": ["x86_64", "arm64"],
        "strict_codesign": True,
        "signing_kind": signing_kind,
        "info_plist_minimum_system_version": info.get("LSMinimumSystemVersion"),
        "macho_slice_minimum_versions": minimums,
        "required_exports": exports,
        "bundle_identifier": info.get("CFBundleIdentifier"),
        "bundle_executable": info.get("CFBundleExecutable"),
        "manifest": inventory(bundle),
    }


def identity_projection(before: dict[str, Any], timestamp: str) -> dict[str, Any]:
    after = copy.deepcopy(before)
    rows = {row["plugin"]: row for row in after["plugins"]}
    if set(rows) != PLUGINS:
        raise RuntimeError("accepted identity plugin set drift")
    target = rows[PLUGIN]
    if target.get("sha256") != EXPECTED_OLD or target.get("source_sha256") != EXPECTED_OLD:
        raise RuntimeError("accepted identity Smoother2 row is not the expected predecessor")
    target.update({
        "sha256": EXPECTED_NEW,
        "source_bundle": "handoffs/olmsmoother2_pf8_pf16_pf32_public_smart_candidate_20260814/product/OLMSmoother2.plugin",
        "source_sha256": EXPECTED_NEW,
    })
    after["accepted_at"] = timestamp
    after["installed_after"] = timestamp
    return after


def transition(before: dict[str, Any], after: dict[str, Any]) -> dict[str, object]:
    pre = {row["plugin"]: row for row in before["plugins"]}
    post = {row["plugin"]: row for row in after["plugins"]}
    changed = {
        name: sorted(key for key in set(pre[name]) | set(post[name]) if pre[name].get(key) != post[name].get(key))
        for name in sorted(PLUGINS)
        if pre[name] != post[name]
    }
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "top_level_changed_fields": sorted(
            key for key in set(before) | set(after) if key != "plugins" and before.get(key) != after.get(key)
        ),
        "other_nine_rows_exact": all(pre[name] == post[name] for name in PLUGINS - {PLUGIN}),
    }


def prepared_artifacts() -> tuple[Path, ...]:
    return BACKUP, PRE_SWAP, PRE_IDENTITY, PREINSTALL


def post_artifacts() -> tuple[Path, ...]:
    return MOVED_OLD, FAILED_NEW, STAGED, POST_IDENTITY_COPY, TRANSACTION


def artifact_state() -> str:
    prepared = [path.exists() for path in prepared_artifacts()]
    post = [path.exists() for path in post_artifacts()]
    if not any(prepared) and not any(post):
        return "clean"
    if all(prepared) and not any(post):
        return "prepared"
    return "partial_or_completed"


def expected_transition(before: dict[str, Any]) -> dict[str, object]:
    result = transition(before, identity_projection(before, "<assigned-on-install-utc>"))
    expected = {
        "changed_plugins": [PLUGIN],
        "changed_fields": {PLUGIN: ["sha256", "source_bundle", "source_sha256"]},
        "unchanged_plugins": sorted(PLUGINS - {PLUGIN}),
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "other_nine_rows_exact": True,
    }
    if result != expected:
        raise RuntimeError(f"projected identity transition drift: {result}")
    return result


def collect_preflight(required_state: str = "either") -> dict[str, object]:
    if sha(SOURCE) != EXPECTED_SOURCE or sha(PROJECT) != EXPECTED_PROJECT:
        raise RuntimeError("source or project drift")
    if sha(BUILD_IDENTITY) != EXPECTED_BUILD_IDENTITY:
        raise RuntimeError("candidate build identity drift")
    if sha(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("accepted pre-install identity manifest drift")
    processes = ae_pids()
    if processes:
        raise RuntimeError(f"After Effects is running: {processes}")
    candidate = verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    installed = verify_bundle(INSTALLED, EXPECTED_OLD, False)
    if len(list(MEDIACORE.glob("OLMSmoother2.plugin"))) != 1:
        raise RuntimeError("installed OLMSmoother2 bundle count is not one")
    state = artifact_state()
    if required_state not in {"either", "clean", "prepared"}:
        raise ValueError(required_state)
    if required_state != "either" and state != required_state:
        raise RuntimeError(f"transaction state is {state}, expected {required_state}")
    if required_state == "either" and state == "partial_or_completed":
        raise RuntimeError("transaction artifacts are partial or completed")
    if MEDIACORE.stat().st_dev != CANDIDATE_HANDOFF.stat().st_dev:
        raise RuntimeError("MediaCore and handoff are not on the same volume")
    before = json.loads(IDENTITY.read_text())
    return {
        "schema": "olmsmoother2.pf8-pf16-pf32-transactional-preflight/1",
        "status": "dry_run_install_ready_prepared_no_mutation" if state == "prepared" else "dry_run_prepare_ready_no_mutation",
        "source_sha256": EXPECTED_SOURCE,
        "project_sha256": EXPECTED_PROJECT,
        "build_identity_sha256": EXPECTED_BUILD_IDENTITY,
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "old_binary_sha256": EXPECTED_OLD,
        "new_binary_sha256": EXPECTED_NEW,
        "after_effects_processes": [],
        "installed_bundle_count": 1,
        "same_volume": True,
        "candidate": candidate,
        "installed_before": installed,
        "identity_transition": expected_transition(before),
        "transaction_artifact_state": state,
    }


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temp = Path(raw)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def atomic_json(path: Path, payload: dict[str, object]) -> None:
    atomic_write(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode())


def copy_bundle(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = run("ditto", str(source), str(destination))
    if result.returncode:
        raise RuntimeError(f"ditto failed: {result.stderr}")


def remove(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def atomic_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    function = libc.renameatx_np
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(-2, os.fsencode(left), -2, os.fsencode(right), 0x00000002):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def validate_prepared(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "prepared" or sha(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("transaction is not exactly prepared")
    if PRE_IDENTITY.read_bytes() != IDENTITY.read_bytes():
        raise RuntimeError("accepted identity changed after prepare")
    backup = verify_bundle(BACKUP, EXPECTED_OLD, False)
    pre_swap = verify_bundle(PRE_SWAP, EXPECTED_OLD, False)
    installed = verify_bundle(INSTALLED, EXPECTED_OLD, False)
    candidate = verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    if not (backup["manifest"] == pre_swap["manifest"] == installed["manifest"] == preflight["installed_before"]["manifest"]):
        raise RuntimeError("predecessor inventories differ")
    if candidate["manifest"] != preflight["candidate"]["manifest"]:
        raise RuntimeError("candidate inventory changed")
    saved = json.loads(PREINSTALL.read_text())
    expected = {
        "schema": "olmsmoother2.pf8-pf16-pf32-preinstall-inventory/1",
        "source_sha256": EXPECTED_SOURCE,
        "project_sha256": EXPECTED_PROJECT,
        "build_identity_sha256": EXPECTED_BUILD_IDENTITY,
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "after_effects_processes": [],
        "candidate": preflight["candidate"],
        "installed_before": preflight["installed_before"],
        "installed_backup": backup,
        "pre_swap_original": pre_swap,
        "old_bundle_full_inventories_exact": True,
    }
    if saved != expected:
        raise RuntimeError("preinstall manifest mismatch")
    return {
        "old_bundle_copy_count": 2,
        "old_bundle_full_inventories_exact": True,
        "candidate_reverified_exact": True,
        "identity_unchanged": True,
    }


def prepare(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "clean":
        raise RuntimeError("prepare requires clean state")
    identity_before = IDENTITY.read_bytes()
    installed_before = inventory(INSTALLED)
    try:
        atomic_write(PRE_IDENTITY, identity_before)
        copy_bundle(INSTALLED, BACKUP)
        copy_bundle(INSTALLED, PRE_SWAP)
        backup = verify_bundle(BACKUP, EXPECTED_OLD, False)
        pre_swap = verify_bundle(PRE_SWAP, EXPECTED_OLD, False)
        payload = {
            "schema": "olmsmoother2.pf8-pf16-pf32-preinstall-inventory/1",
            "source_sha256": EXPECTED_SOURCE,
            "project_sha256": EXPECTED_PROJECT,
            "build_identity_sha256": EXPECTED_BUILD_IDENTITY,
            "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
            "after_effects_processes": [],
            "candidate": preflight["candidate"],
            "installed_before": preflight["installed_before"],
            "installed_backup": backup,
            "pre_swap_original": pre_swap,
            "old_bundle_full_inventories_exact": backup["manifest"] == pre_swap["manifest"] == installed_before,
        }
        if not payload["old_bundle_full_inventories_exact"]:
            raise RuntimeError("prepared predecessor inventories differ")
        atomic_json(PREINSTALL, payload)
        verified = validate_prepared(preflight)
    except BaseException:
        for path in prepared_artifacts():
            if path.exists():
                remove(path)
        if IDENTITY.read_bytes() != identity_before or inventory(INSTALLED) != installed_before:
            raise RuntimeError("prepare failure changed installed bundle or identity")
        raise
    return {"status": "prepared_no_mediacore_or_identity_mutation", "verified": verified}


def rollback(identity_before: bytes, swapped: bool, old_moved: bool) -> None:
    if swapped and not old_moved and INSTALLED.exists() and STAGED.exists():
        atomic_exchange(INSTALLED, STAGED)
    elif swapped and old_moved and INSTALLED.exists() and MOVED_OLD.exists():
        atomic_exchange(INSTALLED, MOVED_OLD)
        FAILED_NEW.parent.mkdir(parents=True, exist_ok=True)
        os.replace(MOVED_OLD, FAILED_NEW)
        copy_bundle(BACKUP, MOVED_OLD)
    if IDENTITY.read_bytes() != identity_before:
        atomic_write(IDENTITY, identity_before)
    POST_IDENTITY_COPY.unlink(missing_ok=True)
    if STAGED.exists():
        remove(STAGED)
    if sha(executable(INSTALLED)) != EXPECTED_OLD or IDENTITY.read_bytes() != identity_before:
        raise RuntimeError("rollback did not restore exact predecessor state")


def install(preflight: dict[str, object]) -> dict[str, object]:
    validate_prepared(preflight)
    identity_before = IDENTITY.read_bytes()
    copy_bundle(CANDIDATE, STAGED)
    staged = verify_bundle(STAGED, EXPECTED_NEW, True)
    if staged["manifest"] != preflight["candidate"]["manifest"] or STAGED.stat().st_dev != INSTALLED.stat().st_dev:
        raise RuntimeError("same-volume staged candidate mismatch")
    swapped = False
    old_moved = False
    try:
        atomic_exchange(INSTALLED, STAGED)
        swapped = True
        installed_after = verify_bundle(INSTALLED, EXPECTED_NEW, True)
        predecessor = verify_bundle(STAGED, EXPECTED_OLD, False)
        if installed_after["manifest"] != preflight["candidate"]["manifest"] or predecessor["manifest"] != preflight["installed_before"]["manifest"]:
            raise RuntimeError("atomic exchange inventory mismatch")
        MOVED_OLD.parent.mkdir(parents=True, exist_ok=True)
        os.replace(STAGED, MOVED_OLD)
        old_moved = True
        if verify_bundle(MOVED_OLD, EXPECTED_OLD, False)["manifest"] != preflight["installed_before"]["manifest"]:
            raise RuntimeError("retained predecessor mismatch")
        if ae_pids():
            raise RuntimeError("After Effects appeared during transaction")
        before = json.loads(identity_before)
        after = identity_projection(before, datetime.now(timezone.utc).isoformat())
        atomic_json(IDENTITY, after)
        shutil.copy2(IDENTITY, POST_IDENTITY_COPY)
        if sha(SOURCE) != EXPECTED_SOURCE or sha(PROJECT) != EXPECTED_PROJECT or ae_pids():
            raise RuntimeError("authority changed during identity update")
        identity_change = transition(before, after)
        expected_transition(before)
        transaction = {
            "schema": "olmsmoother2.pf8-pf16-pf32-incremental-install/1",
            "status": "installed_ae_not_launched",
            "source_sha256": EXPECTED_SOURCE,
            "project_sha256": EXPECTED_PROJECT,
            "build_identity_sha256": EXPECTED_BUILD_IDENTITY,
            "old_binary_sha256": EXPECTED_OLD,
            "new_binary_sha256": EXPECTED_NEW,
            "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
            "post_identity_sha256": sha(IDENTITY),
            "candidate_staged_verified_before_swap": True,
            "same_volume_atomic_exchange": "renameatx_np(RENAME_SWAP)",
            "old_bundle_copy_count": 3,
            "old_bundle_full_inventories_exact": True,
            "identity_transition": identity_change,
            "after_effects_processes_before_after": [[], []],
        }
        atomic_json(TRANSACTION, transaction)
        return {"status": transaction["status"], "binary_sha256": EXPECTED_NEW, "identity_sha256": sha(IDENTITY)}
    except BaseException:
        rollback(identity_before, swapped, old_moved)
        raise


def cleanup_prepare() -> None:
    if any(path.exists() for path in post_artifacts()):
        raise RuntimeError("refusing cleanup after transaction began")
    if sha(IDENTITY) != EXPECTED_PRE_IDENTITY or sha(executable(INSTALLED)) != EXPECTED_OLD:
        raise RuntimeError("refusing cleanup after predecessor changed")
    for path in prepared_artifacts():
        if path.exists():
            remove(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--cleanup-prepare", action="store_true")
    args = parser.parse_args()
    if args.cleanup_prepare:
        cleanup_prepare()
        print(json.dumps({"status": "prepared_artifacts_removed_no_target_mutation"}))
        return 0
    preflight = collect_preflight("prepared" if args.install else "either")
    if args.prepare:
        result = validate_prepared(preflight) if preflight["transaction_artifact_state"] == "prepared" else prepare(preflight)
    elif args.install:
        result = install(preflight)
    else:
        result = preflight
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
