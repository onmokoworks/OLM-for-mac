#!/usr/bin/env python3
"""Hardened hostless Batch5 AE retarget contract; live execution is unavailable."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
BASE = ROOT / "scripts/run_olm_all10_batch5_current_identity_deferred_v1_20260815.py"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_deferred_v2_contract_20260815.json"
FUTURE_RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v2_fresh_ae_smoke_raw_20260815.json"
FUTURE_SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v2_fresh_ae_smoke_20260815.json"
FUTURE_ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_v2_fresh_ae_smoke_20260815"
FUTURE_RECEIPT = ROOT / "handoffs/olm_all10_batch5_current_identity_v2_fresh_ae_smoke_20260815.invocation-receipt.json"
MEDIA_CORE = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("olm_batch5_deferred_v1_base", BASE)
    if not spec or not spec.loader:
        raise RuntimeError("cannot load Batch5 v1 base")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE_MODULE = load_base()
BASE_CONTRACT = BASE_MODULE.contract
BASE_WRITE_NEW = BASE_MODULE.write_new


def executable(bundle: Path) -> Path:
    plist_path = bundle / "Contents/Info.plist"
    if not plist_path.is_file():
        raise RuntimeError(f"missing Info.plist: {bundle}")
    value = plistlib.loads(plist_path.read_bytes()).get("CFBundleExecutable")
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"missing CFBundleExecutable: {bundle}")
    path = bundle / "Contents/MacOS" / value
    if not path.is_file():
        raise RuntimeError(f"missing bundle executable: {path}")
    return path


def checked(command: list[str], label: str) -> str:
    value = subprocess.run(command, capture_output=True, text=True)
    if value.returncode:
        raise RuntimeError(f"{label} failed rc={value.returncode}: {value.stdout}{value.stderr}")
    return value.stdout + value.stderr


def validate_identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError("Batch5 identity is absent")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "olm.installed-identity-manifest/1":
        raise RuntimeError("Batch5 identity schema drift")
    rows = value.get("plugins")
    if not isinstance(rows, list) or len(rows) != 10:
        raise RuntimeError("Batch5 identity row count drift")
    expected = BASE_MODULE.EXPECTED_PLUGINS
    if sorted(row.get("plugin") for row in rows if isinstance(row, dict)) != expected:
        raise RuntimeError("Batch5 identity plug-in set drift")
    compact = []
    for row in rows:
        plugin = row.get("plugin")
        installed = Path(row.get("installed_bundle", "")).expanduser().resolve()
        expected_installed = (MEDIA_CORE / f"{plugin}.plugin").resolve()
        candidates = sorted(item.resolve() for item in MEDIA_CORE.glob(f"{plugin}.plugin"))
        source = (ROOT / str(row.get("source_bundle", ""))).resolve()
        if installed != expected_installed or candidates != [expected_installed] or not installed.is_dir():
            raise RuntimeError(f"Batch5 installed count/path mismatch: {plugin}")
        if not source.is_dir():
            raise RuntimeError(f"Batch5 source bundle absent: {plugin}")
        installed_executable = executable(installed)
        source_executable = executable(source)
        observed = sha256(installed_executable)
        required = (
            observed == sha256(source_executable) == row.get("sha256") == row.get("source_sha256")
            and row.get("source_installed_exact") is True
            and row.get("universal_exact") is True
            and row.get("codesign_exact") is True
            and row.get("installed_bundle_count") == 1
        )
        if not required:
            raise RuntimeError(f"Batch5 binary/identity mismatch: {plugin}")
        arches = checked(["lipo", "-archs", str(installed_executable)], f"lipo {plugin}").split()
        if len(arches) != 2 or set(arches) != {"arm64", "x86_64"}:
            raise RuntimeError(f"Batch5 Universal mismatch: {plugin}")
        checked(["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(installed)], f"codesign {plugin}")
        compact.append({"plugin": plugin, "binary_sha256": observed, "installed_bundle": str(installed),
                        "source_bundle": str(source), "architectures": sorted(arches),
                        "installed_count_one": True, "strict_codesign_valid": True})
    return {"path": BASE_MODULE.relative(path), "sha256": sha256(path), "plugin_count": 10, "plugins": compact,
            "actual_installed_and_source_bundles_verified": True}


def contract(identity: Path | None = None) -> dict[str, Any]:
    value = BASE_CONTRACT(identity)
    value["schema"] = "olm.all10-batch5-current-identity-deferred-v2-contract/1"
    value["dependencies"]["batch5_v1_runner"] = value["dependencies"].pop("batch5_runner")
    value["dependencies"]["batch5_v2_runner"] = {"path": BASE_MODULE.relative(THIS), "sha256": sha256(THIS)}
    value["future_paths"] = {
        "raw": BASE_MODULE.relative(FUTURE_RAW), "summary": BASE_MODULE.relative(FUTURE_SUMMARY),
        "artifact_dir": BASE_MODULE.relative(FUTURE_ARTIFACT_DIR), "receipt": BASE_MODULE.relative(FUTURE_RECEIPT),
        "all_absent": future_outputs_absent(),
    }
    value["identity_retarget"]["actual_artifact_checks"] = [
        "installed_path_and_count_one", "source_bundle_present", "installed_source_binary_sha256_equal",
        "manifest_binary_sha256_equal", "arm64_x86_64_exact", "codesign_deep_strict",
    ]
    value["identity_retarget"]["emit_policy"] = (
        "explicit --identity plus --emit-retargeted-contract to a new absent non-reserved path only"
    )
    return value


def future_outputs_absent() -> bool:
    return not any(path.exists() for path in (FUTURE_RAW, FUTURE_SUMMARY, FUTURE_ARTIFACT_DIR, FUTURE_RECEIPT))


def validate_contract(value: Any, identity: Path | None = None) -> bool:
    try:
        expected = contract(identity)
        return value == expected and value["execution"]["live_entrypoint_present"] is False and future_outputs_absent()
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, RuntimeError):
        return False


def is_reserved(path: Path) -> bool:
    target = path.resolve()
    exact = {FUTURE_RAW.resolve(), FUTURE_SUMMARY.resolve(), FUTURE_RECEIPT.resolve(), FUTURE_ARTIFACT_DIR.resolve()}
    if target in exact:
        return True
    try:
        target.relative_to(FUTURE_ARTIFACT_DIR.resolve())
        return True
    except ValueError:
        return False


def write_new(path: Path, value: dict[str, Any]) -> None:
    if is_reserved(path):
        raise RuntimeError("refusing reserved Batch5 live-output path")
    BASE_WRITE_NEW(path, value)


def configure() -> None:
    BASE_MODULE.CONTRACT_REPORT = CONTRACT_REPORT
    BASE_MODULE.FUTURE_RAW = FUTURE_RAW
    BASE_MODULE.FUTURE_SUMMARY = FUTURE_SUMMARY
    BASE_MODULE.FUTURE_ARTIFACT_DIR = FUTURE_ARTIFACT_DIR
    BASE_MODULE.FUTURE_RECEIPT = FUTURE_RECEIPT
    BASE_MODULE.validate_identity = validate_identity
    BASE_MODULE.contract = contract
    BASE_MODULE.future_outputs_absent = future_outputs_absent
    BASE_MODULE.validate_contract = validate_contract
    BASE_MODULE.write_new = write_new


def main() -> int:
    configure()
    return BASE_MODULE.main()


if __name__ == "__main__":
    raise SystemExit(main())
