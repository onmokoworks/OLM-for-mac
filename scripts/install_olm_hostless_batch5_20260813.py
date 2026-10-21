#!/usr/bin/env python3
"""Transactional Blur/Directional/Radial installer; default is read-only."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/install_olm_hostless_batch4_20260813.py"
SPEC = importlib.util.spec_from_file_location("olm_batch4_base", BASE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load transactional installer base")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

HANDOFF = ROOT / "handoffs/olm_hostless_batch5_install_20260813"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPECTED_PRE_IDENTITY = "426dce713a9595157fe4c9fa3731c464e4ef10afd5db269335a12fa4b38beccc"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREPARED = HANDOFF / "prepared_transaction.json"
TRANSACTION = HANDOFF / "install_transaction.json"

PLUGINS = {
    "OLMBlur": {
        "candidate": ROOT / "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/product/Debug/OLMBlur.plugin",
        "authority": ROOT / "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/build_identity.json",
        "authority_sha256": "767ec979aa369a3c2417d2577bfc9d87a2f06d3f419a8a617993de25f839dbf5",
        "source": ROOT / "mac/OLMBlur/OLMBlur.cpp",
        "source_sha256": "22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7",
        "old": "5893faeaf19d55bb4db6f42eb4c21915c94ad8fe2b945e2002c890d79131c48b",
        "new": "ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d",
    },
    "OLMDirectionalBlur": {
        "candidate": ROOT / "handoffs/olmdirectionalblur_smart_cleanup_universal_candidate_20260813/Product/OLMDirectionalBlur.plugin",
        "authority": ROOT / "handoffs/olmdirectionalblur_smart_cleanup_universal_candidate_20260813/build_identity.json",
        "authority_sha256": "aa16e1cb0586f2192c730e98b50ab7cd3405690b92ade9acf318034891788398",
        "source": ROOT / "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "source_sha256": "6032c79b07f6181420b3ff699eb5f51e0d9adc5f63dc1beaed2c71a40d03ad47",
        "old": "1dd6c11889a261fadec2f6cd64440c8a3e7afcadcaa59631714e0ffc232ac3e4",
        "new": "371c3b624c42d81d67f0e140f14f75d23dcfba302fbca716407902046d2cd0f0",
    },
    "OLMRadialBlur": {
        "candidate": ROOT / "handoffs/olmradialblur_smart_cleanup_universal_candidate_20260813/candidate/OLMRadialBlur.plugin",
        "authority": ROOT / "handoffs/olmradialblur_smart_cleanup_universal_candidate_20260813/build_identity.json",
        "authority_sha256": "44fed698aecd0f8a71d4afc5bbe5f58a393037b3068ed44db05037c903e13abe",
        "source": ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp",
        "source_sha256": "8fde53eb08a001e7695d2aec87ecadf3cefcf391ee67a2557e170c0dda248c10",
        "old": "03e837e8a9ccebbc3e03479b4d8a66f65aa85cce1ac0be616b14dac82284d548",
        "new": "1bd0d6eeebc646272b0d1c13a963609dd458eea269df133d49978b6f3a66baa6",
    },
}


def paths(name: str) -> dict[str, Path]:
    return {
        "installed": base.MEDIA_CORE / f"{name}.plugin",
        "backup": HANDOFF / "installed_backup" / f"{name}.plugin",
        "pre_swap": HANDOFF / "pre_swap_original" / f"{name}.plugin",
        "moved_old": HANDOFF / "moved_old" / f"{name}.plugin",
        "failed_new": HANDOFF / "failed_new" / f"{name}.plugin",
        "stage": base.MEDIA_CORE / f".{name}.batch5-stage-20260813",
    }


base.HANDOFF = HANDOFF
base.IDENTITY = IDENTITY
base.EXPECTED_PRE_IDENTITY = EXPECTED_PRE_IDENTITY
base.PRE_IDENTITY = PRE_IDENTITY
base.POST_IDENTITY = POST_IDENTITY
base.PREPARED = PREPARED
base.TRANSACTION = TRANSACTION
base.PLUGINS = PLUGINS
base.paths = paths


def verify_authorities() -> dict[str, object]:
    rows = {}
    for name, item in PLUGINS.items():
        if base.sha256(item["authority"]) != item["authority_sha256"]:
            raise RuntimeError(f"authority drift: {name}")
        if base.sha256(item["source"]) != item["source_sha256"]:
            raise RuntimeError(f"source drift: {name}")
        candidate = base.verify_bundle(name, item["candidate"], item["new"], require_macos11=True)
        symbols = set(base.run("nm", "-gjU", str(base.executable(item["candidate"], name))).stdout.splitlines())
        if not {"_EffectMain", "_PluginDataEntryFunction2"}.issubset(symbols):
            raise RuntimeError(f"entry exports missing: {name}")
        rows[name] = {
            "authority_path": str(item["authority"].relative_to(ROOT)),
            "authority_sha256": item["authority_sha256"],
            "source_path": str(item["source"].relative_to(ROOT)),
            "source_sha256": item["source_sha256"],
            "candidate": candidate,
        }
    return rows


def collect_preflight() -> dict[str, object]:
    if base.sha256(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("accepted pre-install identity drift")
    if base.ae_pids():
        raise RuntimeError("After Effects is running")
    authorities = verify_authorities()
    plugins = {}
    for name, item in PLUGINS.items():
        installed = base.verify_bundle(name, paths(name)["installed"], item["old"], require_macos11=False)
        plugins[name] = {**authorities[name], "installed_before": installed}
    return {
        "schema": "olm.hostless-batch5-transaction-preflight/1",
        "accepted_identity_sha256": EXPECTED_PRE_IDENTITY,
        "after_effects_processes": [],
        "candidate_count": len(PLUGINS),
        "plugins": plugins,
    }


def prepare(preflight: dict[str, object]) -> dict[str, object]:
    if base.artifact_state() != "clean":
        raise RuntimeError("transaction artifacts are not clean")
    identity_bytes = IDENTITY.read_bytes()
    before = {name: base.inventory(paths(name)["installed"]) for name in PLUGINS}
    try:
        base.atomic_write(PRE_IDENTITY, identity_bytes)
        for name, item in PLUGINS.items():
            for key in ("backup", "pre_swap"):
                base.copy_bundle(paths(name)["installed"], paths(name)[key])
                copied = base.verify_bundle(name, paths(name)[key], item["old"], require_macos11=False)
                if copied["manifest"] != before[name]:
                    raise RuntimeError(f"backup inventory mismatch: {name}/{key}")
        result = {
            "schema": "olm.hostless-batch5-prepared-transaction/1",
            "status": "prepared_install_ready_no_mediacore_or_identity_mutation",
            "preflight": preflight,
            "pre_identity_sha256": base.sha256(PRE_IDENTITY),
            "candidate_count": len(PLUGINS),
            "backup_copies_per_plugin": 2,
        }
        base.atomic_json(PREPARED, result)
        if base.sha256(IDENTITY) != EXPECTED_PRE_IDENTITY:
            raise RuntimeError("prepare mutated identity")
        if any(base.inventory(paths(name)["installed"]) != before[name] for name in PLUGINS):
            raise RuntimeError("prepare mutated MediaCore")
        return result
    except BaseException:
        base.cleanup_prepare_artifacts()
        raise


def accepted_after() -> dict[str, object]:
    before = json.loads(PRE_IDENTITY.read_text())
    after = json.loads(json.dumps(before))
    rows = {row["plugin"]: row for row in after["plugins"]}
    for name, item in PLUGINS.items():
        if rows[name]["sha256"] != item["old"]:
            raise RuntimeError(f"identity old row drift: {name}")
        rows[name].update({
            "sha256": item["new"],
            "source_bundle": str(item["candidate"].relative_to(ROOT)),
            "source_sha256": item["new"],
            "source_installed_exact": True,
            "installed_bundle_count": 1,
            "architectures": ["x86_64", "arm64"],
            "universal_exact": True,
            "codesign_exact": True,
        })
    now = datetime.now(timezone.utc).isoformat()
    after["accepted_at"] = now
    after["installed_after"] = now
    return after


def install(preflight: dict[str, object]) -> dict[str, object]:
    base.validate_prepared(preflight)
    identity_bytes = PRE_IDENTITY.read_bytes()
    swapped: list[str] = []
    old_moved: list[str] = []
    try:
        for name, item in PLUGINS.items():
            stage = paths(name)["stage"]
            if stage.exists():
                raise RuntimeError(f"stage exists: {name}")
            base.copy_bundle(item["candidate"], stage)
            staged = base.verify_bundle(name, stage, item["new"], require_macos11=True)
            if staged["manifest"] != preflight["plugins"][name]["candidate"]["manifest"]:
                raise RuntimeError(f"staged inventory drift: {name}")
        for name, item in PLUGINS.items():
            p = paths(name)
            base.atomic_exchange(p["installed"], p["stage"])
            swapped.append(name)
            new = base.verify_bundle(name, p["installed"], item["new"], require_macos11=True)
            old = base.verify_bundle(name, p["stage"], item["old"], require_macos11=False)
            if new["manifest"] != preflight["plugins"][name]["candidate"]["manifest"]:
                raise RuntimeError(f"installed inventory drift: {name}")
            if old["manifest"] != preflight["plugins"][name]["installed_before"]["manifest"]:
                raise RuntimeError(f"old inventory drift: {name}")
            p["moved_old"].parent.mkdir(parents=True, exist_ok=True)
            p["stage"].replace(p["moved_old"])
            old_moved.append(name)
        base.atomic_json(IDENTITY, accepted_after())
        shutil.copy2(IDENTITY, POST_IDENTITY)
        if base.ae_pids():
            raise RuntimeError("After Effects appeared during install")
        result = {
            "schema": "olm.hostless-batch5-install-transaction/1",
            "status": "installed_pending_single_batched_ae_checkpoint",
            "plugins": {name: {"old": item["old"], "new": item["new"]} for name, item in PLUGINS.items()},
            "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
            "post_identity_sha256": base.sha256(IDENTITY),
            "same_volume_atomic_exchange_per_bundle": True,
            "after_effects_processes": [],
        }
        base.atomic_json(TRANSACTION, result)
        return result
    except BaseException:
        base.restore_after_failure(identity_bytes, swapped, old_moved)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--install", action="store_true")
    args = parser.parse_args()
    state = base.artifact_state()
    if state == "installed":
        if args.prepare or args.install:
            raise RuntimeError("batch transaction is already installed")
        transaction = json.loads(TRANSACTION.read_text())
        if base.sha256(IDENTITY) != transaction["post_identity_sha256"] or base.ae_pids():
            raise RuntimeError("installed transaction drift")
        print(json.dumps({"status": "installed_pending_single_batched_ae_checkpoint_no_mutation",
                          "candidate_count": len(PLUGINS), "after_effects_processes": []}, sort_keys=True))
        return 0
    preflight = collect_preflight()
    if args.prepare:
        if state != "clean":
            raise RuntimeError(f"cannot prepare from state {state}")
        print(json.dumps(prepare(preflight), sort_keys=True))
        return 0
    if args.install:
        if state != "prepared":
            raise RuntimeError(f"cannot install from state {state}")
        print(json.dumps(install(preflight), sort_keys=True))
        return 0
    if state == "prepared":
        base.validate_prepared(preflight)
    elif state != "clean":
        raise RuntimeError(f"unsafe transaction artifact state: {state}")
    print(json.dumps({"status": "dry_run_install_ready_no_mutation" if state == "prepared" else "dry_run_prepare_ready_no_mutation",
                      "candidate_count": len(PLUGINS), "after_effects_processes": []}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
