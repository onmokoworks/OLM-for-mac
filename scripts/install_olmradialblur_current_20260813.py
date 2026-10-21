#!/usr/bin/env python3
"""Two-phase transactional installer for the current OLMRadialBlur candidate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/install_olm_hostless_batch4_20260813.py"
SPEC = importlib.util.spec_from_file_location("olm_install_base", BASE_PATH)
assert SPEC and SPEC.loader
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

NAME = "OLMRadialBlur"
HANDOFF = ROOT / "handoffs/olmradialblur_current_install_20260813"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
EXPECTED_PRE_IDENTITY = "40cd982cb90bb31d206aa5770dee476094217dc69fb325f708ace72fbd074363"
PRE_IDENTITY = HANDOFF / "olm_installed_identity_manifest_before.json"
POST_IDENTITY = HANDOFF / "olm_installed_identity_manifest_after.json"
PREPARED = HANDOFF / "prepared_transaction.json"
TRANSACTION = HANDOFF / "install_transaction.json"
CANDIDATE = ROOT / "handoffs/olmradialblur_type3_all_depth_universal_candidate_20260813/product/Debug/OLMRadialBlur.plugin"
AUTHORITY = ROOT / "handoffs/olmradialblur_type3_all_depth_universal_candidate_20260813/build_identity.json"
AUTHORITY_SHA256 = "c3e0db105c0bf0b967ccd3ccd788d66ff779671d492c408ad306dabe9259ed70"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
SOURCE_SHA256 = "0aac085aaca6d5057ceebfdc4b7a21d5d4290b0c9d2ebf472a9262c60f26cb26"
OLD_SHA256 = "1bd0d6eeebc646272b0d1c13a963609dd458eea269df133d49978b6f3a66baa6"
NEW_SHA256 = "da72af556cad862abf8eaa2c5388d82455b1f8d073cb739c97c357e0f1beb859"


def paths() -> dict[str, Path]:
    return {
        "installed": base.MEDIA_CORE / f"{NAME}.plugin",
        "backup": HANDOFF / "installed_backup" / f"{NAME}.plugin",
        "pre_swap": HANDOFF / "pre_swap_original" / f"{NAME}.plugin",
        "moved_old": HANDOFF / "moved_old" / f"{NAME}.plugin",
        "failed_new": HANDOFF / "failed_new" / f"{NAME}.plugin",
        "stage": base.MEDIA_CORE / ".OLMRadialBlur.current-stage-20260813",
    }


def artifact_state() -> str:
    p = paths()
    material = [x for key, x in p.items() if key != "installed" and x.exists()]
    material += [x for x in (PRE_IDENTITY, POST_IDENTITY, PREPARED, TRANSACTION) if x.exists()]
    if not material:
        return "clean"
    if PREPARED.exists() and PRE_IDENTITY.exists() and p["backup"].exists() and p["pre_swap"].exists() and not any(p[k].exists() for k in ("moved_old", "failed_new", "stage")) and not TRANSACTION.exists() and not POST_IDENTITY.exists():
        return "prepared"
    if TRANSACTION.exists() and POST_IDENTITY.exists() and p["moved_old"].exists():
        return "installed"
    return "partial"


def authority() -> dict[str, object]:
    if base.sha256(AUTHORITY) != AUTHORITY_SHA256 or base.sha256(SOURCE) != SOURCE_SHA256:
        raise RuntimeError("current candidate authority drift")
    candidate = base.verify_bundle(NAME, CANDIDATE, NEW_SHA256, require_macos11=True)
    symbols = set(base.run("nm", "-gjU", str(base.executable(CANDIDATE, NAME))).stdout.splitlines())
    if not {"_EffectMain", "_PluginDataEntryFunction2"}.issubset(symbols):
        raise RuntimeError("entry exports missing")
    return {"authority_path": str(AUTHORITY.relative_to(ROOT)), "authority_sha256": AUTHORITY_SHA256,
            "source_path": str(SOURCE.relative_to(ROOT)), "source_sha256": SOURCE_SHA256,
            "candidate": candidate}


def collect_preflight() -> dict[str, object]:
    if base.sha256(IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("accepted pre-install identity drift")
    if base.ae_pids():
        raise RuntimeError("After Effects is running")
    installed = base.verify_bundle(NAME, paths()["installed"], OLD_SHA256, require_macos11=False)
    return {"schema": "olmradialblur.current-install-preflight/1", "accepted_identity_sha256": EXPECTED_PRE_IDENTITY,
            "after_effects_processes": [], "plugin": {**authority(), "installed_before": installed}}


def cleanup_prepare() -> None:
    p = paths()
    for key in ("backup", "pre_swap", "stage"):
        if p[key].is_dir():
            shutil.rmtree(p[key])
    PRE_IDENTITY.unlink(missing_ok=True)
    PREPARED.unlink(missing_ok=True)


def prepare(preflight: dict[str, object]) -> dict[str, object]:
    if artifact_state() != "clean":
        raise RuntimeError("transaction artifacts are not clean")
    before = base.inventory(paths()["installed"])
    try:
        base.atomic_write(PRE_IDENTITY, IDENTITY.read_bytes())
        for key in ("backup", "pre_swap"):
            base.copy_bundle(paths()["installed"], paths()[key])
            copied = base.verify_bundle(NAME, paths()[key], OLD_SHA256, require_macos11=False)
            if copied["manifest"] != before:
                raise RuntimeError(f"backup inventory mismatch: {key}")
        result = {"schema": "olmradialblur.current-prepared-transaction/1",
                  "status": "prepared_install_ready_no_mediacore_or_identity_mutation",
                  "preflight": preflight, "pre_identity_sha256": base.sha256(PRE_IDENTITY),
                  "backup_copies": 2}
        base.atomic_json(PREPARED, result)
        if base.sha256(IDENTITY) != EXPECTED_PRE_IDENTITY or base.inventory(paths()["installed"]) != before:
            raise RuntimeError("prepare mutated live state")
        return result
    except BaseException:
        cleanup_prepare()
        raise


def validate_prepared(preflight: dict[str, object]) -> None:
    if artifact_state() != "prepared" or base.sha256(PRE_IDENTITY) != EXPECTED_PRE_IDENTITY:
        raise RuntimeError("prepared state incomplete")
    if json.loads(PREPARED.read_text())["preflight"] != preflight:
        raise RuntimeError("prepared preflight drift")
    live = base.verify_bundle(NAME, paths()["installed"], OLD_SHA256, require_macos11=False)
    for key in ("backup", "pre_swap"):
        copied = base.verify_bundle(NAME, paths()[key], OLD_SHA256, require_macos11=False)
        if copied["manifest"] != live["manifest"]:
            raise RuntimeError(f"prepared copy drift: {key}")


def accepted_after() -> dict[str, object]:
    before = json.loads(PRE_IDENTITY.read_text())
    after = json.loads(json.dumps(before))
    rows = {row["plugin"]: row for row in after["plugins"]}
    if rows[NAME]["sha256"] != OLD_SHA256:
        raise RuntimeError("old identity row drift")
    rows[NAME].update({"sha256": NEW_SHA256, "source_bundle": str(CANDIDATE.relative_to(ROOT)),
                       "source_sha256": NEW_SHA256, "source_installed_exact": True,
                       "installed_bundle_count": 1, "architectures": ["x86_64", "arm64"],
                       "universal_exact": True, "codesign_exact": True})
    now = datetime.now(timezone.utc).isoformat()
    after["accepted_at"] = now
    after["installed_after"] = now
    return after


def install(preflight: dict[str, object]) -> dict[str, object]:
    validate_prepared(preflight)
    identity_bytes = PRE_IDENTITY.read_bytes()
    p = paths()
    swapped = False
    moved = False
    try:
        base.copy_bundle(CANDIDATE, p["stage"])
        staged = base.verify_bundle(NAME, p["stage"], NEW_SHA256, require_macos11=True)
        if staged["manifest"] != preflight["plugin"]["candidate"]["manifest"]:
            raise RuntimeError("staged inventory drift")
        base.atomic_exchange(p["installed"], p["stage"])
        swapped = True
        new = base.verify_bundle(NAME, p["installed"], NEW_SHA256, require_macos11=True)
        old = base.verify_bundle(NAME, p["stage"], OLD_SHA256, require_macos11=False)
        if new["manifest"] != staged["manifest"] or old["manifest"] != preflight["plugin"]["installed_before"]["manifest"]:
            raise RuntimeError("post-swap inventory drift")
        p["moved_old"].parent.mkdir(parents=True, exist_ok=True)
        p["stage"].replace(p["moved_old"])
        moved = True
        base.atomic_json(IDENTITY, accepted_after())
        shutil.copy2(IDENTITY, POST_IDENTITY)
        if base.ae_pids():
            raise RuntimeError("After Effects appeared during install")
        result = {"schema": "olmradialblur.current-install-transaction/1",
                  "status": "installed_pending_deferred_batched_ae_checkpoint",
                  "old": OLD_SHA256, "new": NEW_SHA256,
                  "pre_identity_sha256": EXPECTED_PRE_IDENTITY,
                  "post_identity_sha256": base.sha256(IDENTITY),
                  "same_volume_atomic_exchange": True, "after_effects_processes": []}
        base.atomic_json(TRANSACTION, result)
        return result
    except BaseException:
        if moved and p["moved_old"].exists():
            p["moved_old"].replace(p["stage"])
        if swapped and p["stage"].exists():
            base.atomic_exchange(p["installed"], p["stage"])
        base.atomic_write(IDENTITY, identity_bytes)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--install", action="store_true")
    args = parser.parse_args()
    state = artifact_state()
    if state == "installed":
        transaction = json.loads(TRANSACTION.read_text())
        if base.sha256(IDENTITY) != transaction["post_identity_sha256"] or base.ae_pids():
            raise RuntimeError("installed transaction drift")
        print(json.dumps({"status": "installed_pending_deferred_batched_ae_checkpoint_no_mutation",
                          "after_effects_processes": []}, sort_keys=True))
        return 0
    preflight = collect_preflight()
    if args.prepare:
        print(json.dumps(prepare(preflight), sort_keys=True)); return 0
    if args.install:
        print(json.dumps(install(preflight), sort_keys=True)); return 0
    if state == "prepared":
        validate_prepared(preflight)
    elif state != "clean":
        raise RuntimeError(f"unsafe transaction artifact state: {state}")
    print(json.dumps({"status": "dry_run_install_ready_no_mutation" if state == "prepared" else "dry_run_prepare_ready_no_mutation",
                      "after_effects_processes": []}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
