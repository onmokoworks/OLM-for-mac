#!/usr/bin/env python3
"""Transactionally install the frozen OLMToonDilate ded9 candidate.

The default invocation is a read-only dry run.  Bundle or identity mutation is
only reachable through the explicit ``--install`` flag.
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
HANDOFF = ROOT / "handoffs/olmtoondilate_ded9_incremental_install_20260813"
CANDIDATE = HANDOFF / "candidate/Product/OLMToonDilate.plugin"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin"
BACKUP = HANDOFF / "installed_backup/OLMToonDilate.plugin"
PRE_SWAP = HANDOFF / "pre_swap_original/OLMToonDilate.plugin"
MOVED_OLD = HANDOFF / "moved_old/OLMToonDilate.plugin"
FAILED_NEW = HANDOFF / "failed_new/OLMToonDilate.plugin"
STAGED = INSTALLED.with_name(".OLMToonDilate.ded9-stage-20260813")
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
PROJECT = ROOT / "mac/OLMToonDilate/Mac/OLMToonDilate.xcodeproj/project.pbxproj"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY_COPY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREINSTALL = HANDOFF / "preinstall_inventory_manifest.json"
TRANSACTION = HANDOFF / "install_transaction.json"

EXPECTED_SOURCE = "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b"
EXPECTED_PROJECT = "eba3266a1dba3f50b217463c5bb077e9976b22febe70bfb7c5d05c6bdaca8abc"
EXPECTED_OLD = "fe0a4959a677eb495f290fc384d93a2da4b66119f07bd8d1e5dac0847f95c5e9"
EXPECTED_NEW = "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e"
EXPECTED_PRE_IDENTITY = "869a5e88ab34b3b26cc4a3786edb6de93f0e10c88b69c33f6e8d7afb6f18da90"
PLUGINS = {
    "OLMBlur", "ColorKeep", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur",
    "OLMSmoother", "OLMSmoother2", "OLMToonDilate",
}
REQUIRED_EXPORTS = ("_EffectMain", "_PluginDataEntryFunction2")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def executable(bundle: Path) -> Path:
    return bundle / "Contents/MacOS/OLMToonDilate"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True)


def ae_pids() -> list[int]:
    pattern = (
        r"(/Adobe After Effects [^/]+\.app/Contents/MacOS/After Effects( |$)"
        r"|/AfterFX( |$)|/aerender( |$))"
    )
    result = run("pgrep", "-f", pattern)
    if result.returncode not in (0, 1):
        raise RuntimeError("could not observe After Effects processes")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def inventory(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise RuntimeError(f"bundle missing: {bundle}")
    rows: list[dict[str, object]] = []
    paths = sorted(
        [bundle, *bundle.rglob("*")],
        key=lambda item: item.relative_to(bundle).as_posix(),
    )
    for path in paths:
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
    archs = lipo.stdout.split()
    if lipo.returncode or set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"bundle is not exactly Universal: {bundle}")
    signature = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if signature.returncode:
        raise RuntimeError(f"invalid strict signature: {bundle}: {signature.stderr}")
    detail = run("codesign", "-dv", "--verbose=4", str(bundle))
    detail_text = detail.stdout + detail.stderr
    signing_kind = (
        "ad-hoc"
        if detail.returncode == 0 and "Signature=adhoc" in detail_text
        and "TeamIdentifier=not set" in detail_text
        else "other"
    )
    with (bundle / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    minimums: dict[str, str] = {}
    exports: dict[str, dict[str, int]] = {}
    for arch in ("x86_64", "arm64"):
        otool = run("otool", "-arch", arch, "-l", str(binary))
        versions = re.findall(r"^\s+minos\s+(\S+)\s*$", otool.stdout, re.MULTILINE)
        if otool.returncode or len(versions) != 1:
            raise RuntimeError(f"cannot bind minimum OS for {arch}: {bundle}")
        minimums[arch] = versions[0]
        nm = run("nm", "-arch", arch, "-gU", str(binary))
        exports[arch] = {
            symbol: sum(line.rstrip().endswith(" " + symbol) for line in nm.stdout.splitlines())
            for symbol in REQUIRED_EXPORTS
        }
        if nm.returncode or any(count != 1 for count in exports[arch].values()):
            raise RuntimeError(f"required export drift for {arch}: {bundle}")
    if require_macos11 and (
        info.get("LSMinimumSystemVersion") != "11.0"
        or set(minimums.values()) != {"11.0"}
    ):
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
    toon = rows["OLMToonDilate"]
    if toon.get("sha256") != EXPECTED_OLD or toon.get("source_sha256") != EXPECTED_OLD:
        raise RuntimeError("accepted identity Toon row is not the expected predecessor")
    toon.update({
        "sha256": EXPECTED_NEW,
        "source_bundle": "handoffs/olmtoondilate_ded9_incremental_install_20260813/candidate/Product/OLMToonDilate.plugin",
        "source_sha256": EXPECTED_NEW,
    })
    after["accepted_at"] = timestamp
    after["installed_after"] = timestamp
    return after


def changed_identity_fields(before: dict[str, Any], after: dict[str, Any]) -> dict[str, object]:
    pre_rows = {row["plugin"]: row for row in before["plugins"]}
    post_rows = {row["plugin"]: row for row in after["plugins"]}
    changed: dict[str, list[str]] = {}
    for name in sorted(PLUGINS):
        fields = sorted(
            key for key in set(pre_rows[name]) | set(post_rows[name])
            if pre_rows[name].get(key) != post_rows[name].get(key)
        )
        if fields:
            changed[name] = fields
    top = sorted(
        key for key in set(before) | set(after)
        if key != "plugins" and before.get(key) != after.get(key)
    )
    return {
        "changed_plugins": sorted(changed),
        "changed_fields": changed,
        "unchanged_plugins": sorted(PLUGINS - set(changed)),
        "top_level_changed_fields": top,
        "other_nine_rows_exact": all(
            pre_rows[name] == post_rows[name] for name in PLUGINS - {"OLMToonDilate"}
        ),
    }


def prepared_artifacts() -> tuple[Path, ...]:
    return BACKUP, PRE_SWAP, PRE_IDENTITY, PREINSTALL


def post_prepare_artifacts() -> tuple[Path, ...]:
    return MOVED_OLD, FAILED_NEW, STAGED, POST_IDENTITY_COPY, TRANSACTION


def transaction_artifacts() -> tuple[Path, ...]:
    return prepared_artifacts() + post_prepare_artifacts()


def artifact_state() -> str:
    prepared = [path.exists() for path in prepared_artifacts()]
    post = [path.exists() for path in post_prepare_artifacts()]
    if not any(prepared) and not any(post):
        return "clean"
    if all(prepared) and not any(post):
        return "prepared"
    return "partial_or_completed"


def collect_preflight(require_state: str = "either") -> dict[str, object]:
    if sha(SOURCE) != EXPECTED_SOURCE:
        raise RuntimeError("production source drift")
    if sha(PROJECT) != EXPECTED_PROJECT:
        raise RuntimeError("Xcode project drift")
    if sha(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("accepted pre-install identity manifest drift")
    processes = ae_pids()
    if processes:
        raise RuntimeError(f"After Effects is running: {processes}")
    candidate = verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    installed = verify_bundle(INSTALLED, EXPECTED_OLD, False)
    if len(list(INSTALLED.parent.glob("OLMToonDilate.plugin"))) != 1:
        raise RuntimeError("installed OLMToonDilate bundle count is not one")
    existing = [str(path) for path in transaction_artifacts() if path.exists()]
    state = artifact_state()
    if require_state not in {"either", "clean", "prepared"}:
        raise ValueError(f"unsupported required artifact state: {require_state}")
    if require_state != "either" and state != require_state:
        raise RuntimeError(f"transaction artifact state is {state}, expected {require_state}: {existing}")
    if require_state == "either" and state == "partial_or_completed":
        raise RuntimeError(f"transaction artifact state is partial or completed: {existing}")
    if INSTALLED.parent.stat().st_dev != HANDOFF.stat().st_dev:
        raise RuntimeError("MediaCore and handoff are not on the same volume")
    before = json.loads(IDENTITY.read_text(encoding="utf-8"))
    preview = identity_projection(before, "<assigned-on-install-utc>")
    transition = changed_identity_fields(before, preview)
    expected_transition = {
        "changed_plugins": ["OLMToonDilate"],
        "changed_fields": {
            "OLMToonDilate": ["sha256", "source_bundle", "source_sha256"],
        },
        "unchanged_plugins": sorted(PLUGINS - {"OLMToonDilate"}),
        "top_level_changed_fields": ["accepted_at", "installed_after"],
        "other_nine_rows_exact": True,
    }
    if transition != expected_transition:
        raise RuntimeError(f"projected identity transition drift: {transition}")
    return {
        "schema": "olmtoondilate.ded9-transactional-install-preflight/1",
        "status": (
            "dry_run_install_ready_prepared_no_mutation"
            if state == "prepared"
            else "dry_run_prepare_ready_no_mutation"
        ),
        "production_source_sha256": EXPECTED_SOURCE,
        "project_sha256": EXPECTED_PROJECT,
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "old_binary_sha256": EXPECTED_OLD,
        "new_binary_sha256": EXPECTED_NEW,
        "after_effects_processes": processes,
        "installed_bundle_count": 1,
        "same_volume_stage_and_handoff": True,
        "candidate": candidate,
        "installed_before": installed,
        "identity_transition": transition,
        "transaction_artifact_state": state,
        "transaction_artifacts_absent": state == "clean",
        "transaction_artifact_paths": [str(path) for path in transaction_artifacts()],
    }


def _atomic_temp(path: Path) -> tuple[int, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temp = Path(raw)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    os.fchmod(fd, mode)
    return fd, temp


def atomic_write_bytes(path: Path, data: bytes) -> None:
    fd, temp = _atomic_temp(path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write_bytes(path, data)


def atomic_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameatx_np = libc.renameatx_np
    renameatx_np.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    ]
    renameatx_np.restype = ctypes.c_int
    result = renameatx_np(
        -2, os.fsencode(left), -2, os.fsencode(right), 0x00000002,
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def copy_bundle(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    result = run("ditto", str(source), str(destination))
    if result.returncode:
        raise RuntimeError(f"ditto failed: {source} -> {destination}: {result.stderr}")


def remove_bundle(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists() or path.is_symlink():
        path.unlink()


def cleanup_prepare_artifacts() -> None:
    """Remove only pre-swap preparation outputs; never remove post-swap evidence."""
    if any(path.exists() for path in post_prepare_artifacts()):
        raise RuntimeError("refusing prepare cleanup while post-prepare artifacts exist")
    if sha(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("refusing prepare cleanup after accepted identity changed")
    verify_bundle(INSTALLED, EXPECTED_OLD, False)
    for path in prepared_artifacts():
        if path.exists() or path.is_symlink():
            remove_bundle(path)


def prepare_transaction(preflight: dict[str, object], pre_identity_bytes: bytes) -> dict[str, object]:
    if any(path.exists() for path in transaction_artifacts()):
        raise RuntimeError("transaction artifacts appeared after preflight")
    atomic_write_bytes(PRE_IDENTITY, pre_identity_bytes)
    if sha(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("pre-identity durable copy mismatch")
    copy_bundle(INSTALLED, BACKUP)
    copy_bundle(INSTALLED, PRE_SWAP)
    backup = verify_bundle(BACKUP, EXPECTED_OLD, False)
    pre_swap = verify_bundle(PRE_SWAP, EXPECTED_OLD, False)
    installed = preflight["installed_before"]
    if not (backup["manifest"] == pre_swap["manifest"] == installed["manifest"]):
        raise RuntimeError("old bundle durable copy inventory mismatch")
    manifest = {
        "schema": "olmtoondilate.ded9-preinstall-inventory/1",
        "source_sha256": EXPECTED_SOURCE,
        "project_sha256": EXPECTED_PROJECT,
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "after_effects_processes": [],
        "candidate": preflight["candidate"],
        "installed_before": installed,
        "installed_backup": backup,
        "pre_swap_original": pre_swap,
        "old_bundle_full_inventories_exact": True,
        "same_volume_stage_and_handoff": True,
    }
    atomic_write_json(PREINSTALL, manifest)
    validated = validate_prepared(preflight)
    return {
        "status": "prepared_install_ready_no_mediacore_or_identity_mutation",
        "pre_identity_sha256": sha(PRE_IDENTITY),
        "preinstall_manifest_sha256": sha(PREINSTALL),
        "old_binary_sha256": EXPECTED_OLD,
        "new_binary_sha256": EXPECTED_NEW,
        "prepared": validated,
    }


def validate_prepared(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "prepared":
        raise RuntimeError(f"transaction is not in exact prepared state: {artifact_state()}")
    if sha(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("prepared pre-identity mismatch")
    if PRE_IDENTITY.read_bytes() != IDENTITY.read_bytes():
        raise RuntimeError("accepted identity changed after prepare")
    backup = verify_bundle(BACKUP, EXPECTED_OLD, False)
    pre_swap = verify_bundle(PRE_SWAP, EXPECTED_OLD, False)
    installed = verify_bundle(INSTALLED, EXPECTED_OLD, False)
    candidate = verify_bundle(CANDIDATE, EXPECTED_NEW, True)
    if not (
        backup["manifest"] == pre_swap["manifest"]
        == installed["manifest"] == preflight["installed_before"]["manifest"]
    ):
        raise RuntimeError("prepared predecessor inventories are not exact")
    if candidate["manifest"] != preflight["candidate"]["manifest"]:
        raise RuntimeError("candidate changed after prepare")
    expected_manifest = {
        "schema": "olmtoondilate.ded9-preinstall-inventory/1",
        "source_sha256": EXPECTED_SOURCE,
        "project_sha256": EXPECTED_PROJECT,
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "after_effects_processes": [],
        "candidate": preflight["candidate"],
        "installed_before": preflight["installed_before"],
        "installed_backup": backup,
        "pre_swap_original": pre_swap,
        "old_bundle_full_inventories_exact": True,
        "same_volume_stage_and_handoff": True,
    }
    if json.loads(PREINSTALL.read_text(encoding="utf-8")) != expected_manifest:
        raise RuntimeError("prepared preinstall inventory manifest mismatch")
    return {
        "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
        "old_bundle_copy_count_before_swap": 2,
        "old_bundle_full_inventories_exact": True,
        "candidate_reverified_exact": True,
        "installed_predecessor_reverified_exact": True,
        "accepted_identity_unchanged_since_prepare": True,
        "post_prepare_artifacts_absent": True,
    }


def restore_after_failure(pre_identity_bytes: bytes, swapped: bool, old_moved: bool) -> None:
    if swapped and not old_moved and INSTALLED.exists() and STAGED.exists():
        atomic_exchange(INSTALLED, STAGED)
        swapped = False
    elif swapped and old_moved and INSTALLED.exists() and MOVED_OLD.exists():
        atomic_exchange(INSTALLED, MOVED_OLD)
        swapped = False
        FAILED_NEW.parent.mkdir(parents=True, exist_ok=True)
        if FAILED_NEW.exists():
            raise RuntimeError(f"cannot retain failed candidate; path exists: {FAILED_NEW}")
        os.replace(MOVED_OLD, FAILED_NEW)
        copy_bundle(BACKUP, MOVED_OLD)
    if sha(IDENTITY) != EXPECTED_PRE_IDENTITY:
        atomic_write_bytes(IDENTITY, pre_identity_bytes)
    if POST_IDENTITY_COPY.exists():
        POST_IDENTITY_COPY.unlink()
    if STAGED.exists():
        remove_bundle(STAGED)
    if sha(executable(INSTALLED)) != EXPECTED_OLD:
        raise RuntimeError("rollback did not restore the predecessor executable")
    if IDENTITY.read_bytes() != pre_identity_bytes:
        raise RuntimeError("rollback did not restore the exact pre-identity bytes")


def perform_install(preflight: dict[str, object]) -> dict[str, object]:
    pre_identity_bytes = IDENTITY.read_bytes()
    validate_prepared(preflight)
    copy_bundle(CANDIDATE, STAGED)
    staged_new = verify_bundle(STAGED, EXPECTED_NEW, True)
    if staged_new["manifest"] != preflight["candidate"]["manifest"]:
        raise RuntimeError("same-volume staged candidate inventory mismatch")
    if STAGED.stat().st_dev != INSTALLED.stat().st_dev:
        raise RuntimeError("staged bundle is not on the installed bundle volume")

    swapped = False
    old_moved = False
    try:
        atomic_exchange(INSTALLED, STAGED)
        swapped = True
        installed_after = verify_bundle(INSTALLED, EXPECTED_NEW, True)
        staged_old = verify_bundle(STAGED, EXPECTED_OLD, False)
        if installed_after["manifest"] != preflight["candidate"]["manifest"]:
            raise RuntimeError("installed candidate inventory mismatch")
        if staged_old["manifest"] != preflight["installed_before"]["manifest"]:
            raise RuntimeError("atomic-exchange predecessor inventory mismatch")
        MOVED_OLD.parent.mkdir(parents=True, exist_ok=True)
        os.replace(STAGED, MOVED_OLD)
        old_moved = True
        retained = verify_bundle(MOVED_OLD, EXPECTED_OLD, False)
        if retained["manifest"] != preflight["installed_before"]["manifest"]:
            raise RuntimeError("retained moved-old inventory mismatch")
        if ae_pids():
            raise RuntimeError("After Effects appeared during the bundle transaction")

        before = json.loads(pre_identity_bytes.decode("utf-8"))
        timestamp = datetime.now(timezone.utc).isoformat()
        after = identity_projection(before, timestamp)
        atomic_write_json(IDENTITY, after)
        identity_sha = sha(IDENTITY)
        shutil.copy2(IDENTITY, POST_IDENTITY_COPY)
        if sha(SOURCE) != EXPECTED_SOURCE or sha(PROJECT) != EXPECTED_PROJECT:
            raise RuntimeError("source or project changed during install")
        processes_after = ae_pids()
        if processes_after:
            raise RuntimeError(f"After Effects appeared during identity update: {processes_after}")
        transaction = {
            "schema": "olmtoondilate.ded9-incremental-install-transaction/1",
            "status": "installed",
            "source_sha256_before_after": EXPECTED_SOURCE,
            "project_sha256_before_after": EXPECTED_PROJECT,
            "old_binary_sha256": EXPECTED_OLD,
            "new_binary_sha256": EXPECTED_NEW,
            "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
            "post_identity_sha256": identity_sha,
            "after_effects_processes_before": [],
            "after_effects_processes_after": processes_after,
            "candidate_staged_verified_before_swap": True,
            "same_volume_atomic_bundle_exchange": True,
            "atomic_exchange_api": "renameatx_np(RENAME_SWAP)",
            "rollback_original": str(MOVED_OLD),
            "old_bundle_copy_count": 3,
            "old_bundle_full_inventories_exact": True,
            "identity_changed_plugins": ["OLMToonDilate"],
            "identity_top_level_changed_fields": ["accepted_at", "installed_after"],
            "other_nine_identity_rows_exact": True,
        }
        atomic_write_json(TRANSACTION, transaction)
        return {
            "status": "installed",
            "binary_sha256": EXPECTED_NEW,
            "identity_sha256": identity_sha,
            "transaction": str(TRANSACTION),
        }
    except BaseException:
        restore_after_failure(pre_identity_bytes, swapped, old_moved)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run by default; pass --install to perform the reviewed transaction.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="validate only (the default)")
    mode.add_argument(
        "--prepare", action="store_true",
        help="create and verify rollback artifacts without changing MediaCore or accepted identity",
    )
    mode.add_argument(
        "--cleanup-prepare", action="store_true",
        help="remove only pre-swap preparation artifacts after verifying installed/identity predecessor",
    )
    mode.add_argument("--install", action="store_true", help="perform the bundle and identity transaction")
    args = parser.parse_args()
    if args.cleanup_prepare:
        cleanup_prepare_artifacts()
        print(json.dumps({"status": "prepare_artifacts_cleaned_no_mediacore_or_identity_mutation"}))
        return 0
    required_state = "prepared" if args.install else "either"
    preflight = collect_preflight(require_state=required_state)
    if args.prepare:
        if preflight["transaction_artifact_state"] == "prepared":
            print(json.dumps({
                "status": "already_prepared_install_ready_no_mutation",
                "prepared": validate_prepared(preflight),
            }, indent=2, sort_keys=True))
            return 0
        identity_before = IDENTITY.read_bytes()
        installed_before = inventory(INSTALLED)
        try:
            result = prepare_transaction(preflight, identity_before)
        except BaseException:
            cleanup_prepare_artifacts()
            if IDENTITY.read_bytes() != identity_before or inventory(INSTALLED) != installed_before:
                raise RuntimeError("prepare failure changed MediaCore or accepted identity")
            raise
        if IDENTITY.read_bytes() != identity_before or inventory(INSTALLED) != installed_before:
            raise RuntimeError("prepare changed MediaCore or accepted identity")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if not args.install:
        print(json.dumps(preflight, indent=2, sort_keys=True))
        return 0
    result = perform_install(preflight)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
