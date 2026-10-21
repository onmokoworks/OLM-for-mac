#!/usr/bin/env python3
"""Transactional four-plugin installer; default is a read-only readiness check."""

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
HANDOFF = ROOT / "handoffs/olm_hostless_batch4_install_20260813"
READINESS = ROOT / "refs/conformance/olm_hostless_batch4_install_readiness_20260813.json"
READINESS_SHA256 = "62def0d8d85a70b78266ba74ae1197f1abe918872546b526655cd329082f2093"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPECTED_PRE_IDENTITY = "ef7bf31f4f8907af8d047276296b16c4d918433a94173938ca98b2874c61c368"
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREPARED = HANDOFF / "prepared_transaction.json"
TRANSACTION = HANDOFF / "install_transaction.json"

PLUGINS = {
    "OLMBlur": {
        "candidate": ROOT / "handoffs/olmblur_smart_public_admission_macos11_project_20260813/product/Debug/OLMBlur.plugin",
        "old": "21b629849011847784aba3b5311f42706504aded3b2c70e0dd3a241427e9ecf6",
        "new": "5893faeaf19d55bb4db6f42eb4c21915c94ad8fe2b945e2002c890d79131c48b",
    },
    "OLMSmoother": {
        "candidate": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/candidates/OLMSmoother.plugin",
        "old": "1d24d89fe1511d3cc69ca46498dc9e76ed7a088a163cd5f79d3e87f70a34de5e",
        "new": "f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162",
    },
    "OLMSmoother2": {
        "candidate": ROOT / "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/candidates/OLMSmoother2.plugin",
        "old": "b8e399a215ffb43d6332593391995daf12bd2e2770ab8757c3ca822993ced69c",
        "new": "55d138e2a25704ffa59d8bd08d20e2160525f8f8011b8e11c733ae23fddd795e",
    },
    "OLMColorKey": {
        "candidate": ROOT / "handoffs/olmcolorkey_public_source_bound_universal_candidate_20260813T234500JST/product/Debug/OLMColorKey.plugin",
        "old": "2e7a090b73cb08af50003768ca2a72784368104f3aad215ad2531e14bd491258",
        "new": "030e87c5b88c7312e35ecf5998446fb605a522b8a062f1ab798348b3dbf722c4",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def executable(bundle: Path, name: str) -> Path:
    return bundle / "Contents/MacOS" / name


def run(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, capture_output=True, text=True)


def ae_pids() -> list[int]:
    result = run("pgrep", "-f", r"^/Applications/Adobe After Effects .*\.app/Contents/MacOS/After Effects( |$)")
    if result.returncode not in (0, 1):
        raise RuntimeError("cannot observe After Effects")
    return sorted(int(value) for value in result.stdout.split() if value.isdigit())


def inventory(bundle: Path) -> list[dict[str, object]]:
    if not bundle.is_dir():
        raise RuntimeError(f"bundle missing: {bundle}")
    rows = []
    for path in sorted([bundle, *bundle.rglob("*")], key=lambda p: p.relative_to(bundle).as_posix()):
        info = path.lstat()
        relative = "." if path == bundle else path.relative_to(bundle).as_posix()
        row: dict[str, object] = {"path": relative, "mode": stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update(type="symlink", target=os.readlink(path))
        elif path.is_dir():
            row["type"] = "directory"
        elif path.is_file():
            row.update(type="file", bytes=info.st_size, sha256=sha256(path))
        else:
            raise RuntimeError(f"unsupported entry: {path}")
        rows.append(row)
    return rows


def verify_bundle(name: str, bundle: Path, expected: str, *, require_macos11: bool) -> dict[str, object]:
    binary = executable(bundle, name)
    if sha256(binary) != expected:
        raise RuntimeError(f"binary mismatch: {name}/{bundle}")
    lipo = run("lipo", "-archs", str(binary))
    archs = lipo.stdout.split()
    if lipo.returncode or set(archs) != {"arm64", "x86_64"}:
        raise RuntimeError(f"Universal check failed: {name}")
    signature = run("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
    if signature.returncode:
        raise RuntimeError(f"signature failed: {name}: {signature.stderr}")
    info_min = plistlib.loads((bundle / "Contents/Info.plist").read_bytes()).get("LSMinimumSystemVersion")
    minos = {}
    for arch in archs:
        commands = run("otool", "-arch", arch, "-l", str(binary))
        values = re.findall(r"^\s+minos\s+(\S+)\s*$", commands.stdout, re.MULTILINE)
        if commands.returncode or len(values) != 1:
            raise RuntimeError(f"minos unavailable: {name}/{arch}")
        minos[arch] = values[0]
    if require_macos11 and (info_min != "11.0" or set(minos.values()) != {"11.0"}):
        raise RuntimeError(f"candidate minOS drift: {name}")
    return {"binary_sha256": expected, "architectures": archs, "info_minimum_system_version": info_min,
            "slice_minos": minos, "strict_codesign": True, "manifest": inventory(bundle)}


def paths(name: str) -> dict[str, Path]:
    return {
        "installed": MEDIA_CORE / f"{name}.plugin",
        "backup": HANDOFF / "installed_backup" / f"{name}.plugin",
        "pre_swap": HANDOFF / "pre_swap_original" / f"{name}.plugin",
        "moved_old": HANDOFF / "moved_old" / f"{name}.plugin",
        "failed_new": HANDOFF / "failed_new" / f"{name}.plugin",
        "stage": MEDIA_CORE / f".{name}.batch4-stage-20260813",
    }


def copy_bundle(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ditto", str(source), str(destination)], check=True)


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    temporary = Path(raw)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_json(path: Path, value: object) -> None:
    atomic_write(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def atomic_exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    function = libc.renameatx_np
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(-2, os.fsencode(left), -2, os.fsencode(right), 0x2) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), f"{left} <-> {right}")


def artifact_state() -> str:
    material = []
    for name in PLUGINS:
        material.extend(path for key, path in paths(name).items() if key != "installed" and path.exists())
    material.extend(path for path in (PRE_IDENTITY, POST_IDENTITY, PREPARED, TRANSACTION) if path.exists())
    if not material:
        return "clean"
    prepared = PREPARED.exists() and PRE_IDENTITY.exists() and all(paths(name)[key].exists() for name in PLUGINS for key in ("backup", "pre_swap"))
    if prepared and not TRANSACTION.exists() and not POST_IDENTITY.exists() and all(not paths(name)[key].exists() for name in PLUGINS for key in ("moved_old", "failed_new", "stage")):
        return "prepared"
    if TRANSACTION.exists() and POST_IDENTITY.exists() and all(paths(name)["moved_old"].exists() for name in PLUGINS):
        return "installed"
    return "partial"


def readiness() -> dict[str, object]:
    if sha256(READINESS) != READINESS_SHA256:
        raise RuntimeError("batch readiness drift")
    data = json.loads(READINESS.read_text())
    if data["status"] != "PASS_HOSTLESS_BATCH4_CANDIDATES_READY_FOR_TRANSACTIONAL_PREP_NOT_INSTALLED":
        raise RuntimeError("batch readiness is not green")
    return data


def collect_preflight() -> dict[str, object]:
    if sha256(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("accepted pre-install identity drift")
    if ae_pids():
        raise RuntimeError("After Effects is running")
    bound = readiness()
    plugins = {}
    for name, spec in PLUGINS.items():
        p = paths(name)
        candidate = verify_bundle(name, spec["candidate"], spec["new"], require_macos11=True)
        installed = verify_bundle(name, p["installed"], spec["old"], require_macos11=False)
        if candidate["manifest"] != bound["candidates"][name]["bundle"]["inventory"]:
            # The readiness inventory omits directories/mode integer format, so bind its executable
            # and separately preserve this installer's complete manifest.
            if candidate["binary_sha256"] != bound["candidates"][name]["bundle"]["binary_sha256"]:
                raise RuntimeError(f"readiness candidate drift: {name}")
        plugins[name] = {"candidate": candidate, "installed_before": installed}
    return {"schema": "olm.hostless-batch4-transaction-preflight/1", "readiness_sha256": READINESS_SHA256,
            "accepted_identity_sha256": EXPECTED_PRE_IDENTITY, "after_effects_processes": [],
            # This preflight describes the clean-state inputs captured before preparation.
            # main() validates the live transaction state separately.
            "transaction_artifact_state": "clean", "plugins": plugins}


def cleanup_prepare_artifacts() -> None:
    for name in PLUGINS:
        for key in ("backup", "pre_swap", "stage"):
            path = paths(name)[key]
            if path.is_dir():
                shutil.rmtree(path)
    for path in (PRE_IDENTITY, PREPARED):
        path.unlink(missing_ok=True)


def prepare_transaction(preflight: dict[str, object], identity_bytes: bytes) -> dict[str, object]:
    if artifact_state() != "clean":
        raise RuntimeError("transaction artifacts are not clean")
    installed_before = {name: inventory(paths(name)["installed"]) for name in PLUGINS}
    try:
        atomic_write(PRE_IDENTITY, identity_bytes)
        for name, spec in PLUGINS.items():
            p = paths(name)
            copy_bundle(p["installed"], p["backup"])
            copy_bundle(p["installed"], p["pre_swap"])
            for key in ("backup", "pre_swap"):
                verified = verify_bundle(name, p[key], spec["old"], require_macos11=False)
                if verified["manifest"] != preflight["plugins"][name]["installed_before"]["manifest"]:
                    raise RuntimeError(f"backup inventory mismatch: {name}/{key}")
        prepared = {
            "schema": "olm.hostless-batch4-prepared-transaction/1",
            "status": "prepared_install_ready_no_mediacore_or_identity_mutation",
            "preflight": preflight, "pre_identity_sha256": sha256(PRE_IDENTITY),
            "candidate_count": 4, "backup_copies_per_plugin": 2,
        }
        atomic_json(PREPARED, prepared)
        if sha256(IDENTITY) != EXPECTED_PRE_IDENTITY or any(inventory(paths(name)["installed"]) != installed_before[name] for name in PLUGINS):
            raise RuntimeError("prepare mutated identity or MediaCore")
        return prepared
    except BaseException:
        cleanup_prepare_artifacts()
        raise


def validate_prepared(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "prepared" or sha256(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("prepared transaction incomplete")
    if json.loads(PREPARED.read_text())["preflight"] != preflight:
        raise RuntimeError("prepared preflight drift")
    for name, spec in PLUGINS.items():
        p = paths(name)
        live = verify_bundle(name, p["installed"], spec["old"], require_macos11=False)
        for key in ("backup", "pre_swap"):
            copy = verify_bundle(name, p[key], spec["old"], require_macos11=False)
            if copy["manifest"] != live["manifest"]:
                raise RuntimeError(f"prepared old copy drift: {name}/{key}")
    return {"old_bundle_full_inventories_exact": True, "identity_exact": True}


def accepted_after() -> dict[str, object]:
    before = json.loads(PRE_IDENTITY.read_text())
    after = json.loads(json.dumps(before))
    rows = {row["plugin"]: row for row in after["plugins"]}
    for name, spec in PLUGINS.items():
        if rows[name]["sha256"] != spec["old"]:
            raise RuntimeError(f"identity old row drift: {name}")
        rows[name].update({"sha256": spec["new"], "source_bundle": str(spec["candidate"].relative_to(ROOT)),
                           "source_sha256": spec["new"], "source_installed_exact": True,
                           "installed_bundle_count": 1, "architectures": ["x86_64", "arm64"],
                           "universal_exact": True, "codesign_exact": True})
    now = datetime.now(timezone.utc).isoformat()
    after["accepted_at"] = now
    after["installed_after"] = now
    return after


def restore_after_failure(identity_bytes: bytes, swapped: list[str], old_moved: list[str]) -> None:
    for name in reversed(list(PLUGINS)):
        p = paths(name)
        if name in old_moved and p["moved_old"].exists():
            if p["installed"].exists():
                p["failed_new"].parent.mkdir(parents=True, exist_ok=True)
                if p["failed_new"].exists(): shutil.rmtree(p["failed_new"])
                os.replace(p["installed"], p["failed_new"])
            os.replace(p["moved_old"], p["installed"])
        elif name in swapped and p["stage"].exists() and p["installed"].exists():
            atomic_exchange(p["installed"], p["stage"])
        if p["stage"].exists(): shutil.rmtree(p["stage"])
    atomic_write(IDENTITY, identity_bytes)
    POST_IDENTITY.unlink(missing_ok=True)


def install(preflight: dict[str, object]) -> dict[str, object]:
    validate_prepared(preflight)
    identity_bytes = PRE_IDENTITY.read_bytes()
    swapped: list[str] = []
    old_moved: list[str] = []
    try:
        for name, spec in PLUGINS.items():
            p = paths(name)
            if p["stage"].exists(): raise RuntimeError(f"stage exists: {name}")
            copy_bundle(spec["candidate"], p["stage"])
            staged = verify_bundle(name, p["stage"], spec["new"], require_macos11=True)
            if staged["manifest"] != preflight["plugins"][name]["candidate"]["manifest"]:
                raise RuntimeError(f"staged inventory drift: {name}")
        for name, spec in PLUGINS.items():
            p = paths(name)
            atomic_exchange(p["installed"], p["stage"]); swapped.append(name)
            new = verify_bundle(name, p["installed"], spec["new"], require_macos11=True)
            old = verify_bundle(name, p["stage"], spec["old"], require_macos11=False)
            if new["manifest"] != preflight["plugins"][name]["candidate"]["manifest"] or old["manifest"] != preflight["plugins"][name]["installed_before"]["manifest"]:
                raise RuntimeError(f"post-swap inventory drift: {name}")
            p["moved_old"].parent.mkdir(parents=True, exist_ok=True)
            os.replace(p["stage"], p["moved_old"]); old_moved.append(name)
        atomic_json(IDENTITY, accepted_after())
        shutil.copy2(IDENTITY, POST_IDENTITY)
        if ae_pids(): raise RuntimeError("After Effects appeared during install")
        transaction = {"schema": "olm.hostless-batch4-install-transaction/1", "status": "installed_pending_batched_ae_smoke",
                       "plugins": {name: {"old": PLUGINS[name]["old"], "new": PLUGINS[name]["new"]} for name in PLUGINS},
                       "pre_identity_sha256": EXPECTED_PRE_IDENTITY, "post_identity_sha256": sha256(IDENTITY),
                       "same_volume_atomic_exchange_per_bundle": True, "after_effects_processes": []}
        atomic_json(TRANSACTION, transaction)
        return transaction
    except BaseException:
        restore_after_failure(identity_bytes, swapped, old_moved)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--install", action="store_true")
    args = parser.parse_args()
    state = artifact_state()
    if state == "installed":
        if args.prepare or args.install:
            raise RuntimeError("batch transaction is already installed")
        transaction = json.loads(TRANSACTION.read_text())
        if sha256(IDENTITY) != transaction["post_identity_sha256"] or ae_pids():
            raise RuntimeError("installed transaction identity/process drift")
        for name, spec in PLUGINS.items():
            verify_bundle(name, paths(name)["installed"], spec["new"], require_macos11=True)
            verify_bundle(name, paths(name)["moved_old"], spec["old"], require_macos11=False)
        print(json.dumps({"status": "installed_pending_batched_ae_smoke_no_mutation",
                          "transaction_artifact_state": state, "candidate_count": 4,
                          "after_effects_processes": []}, sort_keys=True))
        return 0
    preflight = collect_preflight()
    if args.prepare:
        if state != "clean": raise RuntimeError(f"cannot prepare from state {state}")
        print(json.dumps(prepare_transaction(preflight, IDENTITY.read_bytes()), sort_keys=True)); return 0
    if args.install:
        if state != "prepared": raise RuntimeError(f"cannot install from state {state}")
        print(json.dumps(install(preflight), sort_keys=True)); return 0
    if state not in {"clean", "prepared"}:
        raise RuntimeError(f"unsafe transaction artifact state: {state}")
    if state == "prepared": validate_prepared(preflight)
    print(json.dumps({"status": "dry_run_install_ready_no_mutation" if state == "prepared" else "dry_run_prepare_ready_no_mutation",
                      "transaction_artifact_state": state, "candidate_count": 4, "after_effects_processes": []}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
