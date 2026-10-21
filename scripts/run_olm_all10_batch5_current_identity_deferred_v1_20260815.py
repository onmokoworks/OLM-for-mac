#!/usr/bin/env python3
"""Hostless Batch5 AE contract; live execution is deliberately unavailable."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
BASE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
BASE_PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
PREDECESSOR_DEFERRED = ROOT / "scripts/run_olm_all10_current_identity_deferred_v3_20260814.py"
PREDECESSOR_LIVE = ROOT / "scripts/run_olm_all10_current_identity_final_v4_20260814.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_batch5_current_identity_deferred_v1_20260815.jsx"
PREDECESSOR_IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_deferred_v1_contract_20260815.json"

FUTURE_RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v1_fresh_ae_smoke_raw_20260815.json"
FUTURE_SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v1_fresh_ae_smoke_20260815.json"
FUTURE_ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_v1_fresh_ae_smoke_20260815"
FUTURE_RECEIPT = ROOT / "handoffs/olm_all10_batch5_current_identity_v1_fresh_ae_smoke_20260815.invocation-receipt.json"

PINS = {
    "base_runner": "45997d4c756fb9d82afde2fbe8f3be503db5e66dff2b15eaaf9ba1e1219ce4b7",
    "base_payload": "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511",
    "predecessor_deferred": "019e72afe8726c91a41e873690303b1771e133e71a1d35c081e68e2a324ab190",
    "predecessor_live": "94cb7d1d613b5fa88be190047ef8692854f07187381a211c96b6fb64ce7bda31",
    "predecessor_identity": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
}
EXPECTED_PLUGINS = [
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]
ENABLED_GENERIC_HOST_FRAME = ["OLMBlur", "OLMDirectionalBlur"]
DISABLED_GENERIC_HOST_FRAME = sorted(set(EXPECTED_PLUGINS) - set(ENABLED_GENERIC_HOST_FRAME))
CLAIM_BOUNDARY = (
    "Batch5 installed host load/add/enable-state and exact mapping for all ten; "
    "generic effect-enabled host-frame render only for OLMBlur and "
    "OLMDirectionalBlur. The other eight bounded effects are disabled before "
    "generic saveFrameToPng. Numerical behavior is not assessed. No pixel-exact, "
    "Windows-equivalence, typed-plane, padding, admission, or public-owner "
    "numerical-exact claim."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def future_outputs_absent() -> bool:
    return not any(path.exists() for path in (FUTURE_RAW, FUTURE_SUMMARY, FUTURE_ARTIFACT_DIR, FUTURE_RECEIPT))


def pinned_dependencies() -> dict[str, dict[str, str]]:
    paths = {
        "base_runner": BASE_RUNNER,
        "base_payload": BASE_PAYLOAD,
        "predecessor_deferred": PREDECESSOR_DEFERRED,
        "predecessor_live": PREDECESSOR_LIVE,
        "predecessor_identity": PREDECESSOR_IDENTITY,
    }
    observed = {key: sha256(path) for key, path in paths.items()}
    if observed != PINS:
        raise RuntimeError(f"Batch5 predecessor drift: {observed}")
    return {key: {"path": relative(path), "sha256": observed[key]} for key, path in sorted(paths.items())}


def validate_identity(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError("Batch5 identity is absent")
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != "olm.installed-identity-manifest/1":
        raise RuntimeError("Batch5 identity schema drift")
    rows = value.get("plugins")
    if not isinstance(rows, list) or len(rows) != 10:
        raise RuntimeError("Batch5 identity row count drift")
    if sorted(row.get("plugin") for row in rows if isinstance(row, dict)) != EXPECTED_PLUGINS:
        raise RuntimeError("Batch5 identity plug-in set drift")
    compact = []
    for row in rows:
        plugin = row.get("plugin")
        required = (
            row.get("sha256") == row.get("source_sha256")
            and row.get("source_installed_exact") is True
            and row.get("universal_exact") is True
            and row.get("codesign_exact") is True
            and row.get("installed_bundle_count") == 1
        )
        if not required:
            raise RuntimeError(f"Batch5 identity row not exact: {plugin}")
        compact.append({"plugin": plugin, "binary_sha256": row["sha256"], "installed_bundle": row.get("installed_bundle")})
    return {"path": relative(path), "sha256": sha256(path), "plugin_count": 10, "plugins": compact}


def contract(identity: Path | None = None) -> dict[str, Any]:
    retargeted = identity is not None
    target = validate_identity(identity) if identity is not None else None
    return {
        "schema": "olm.all10-batch5-current-identity-deferred-v1-contract/1",
        "status": "AE_FORBIDDEN_RETARGETED_IDENTITY_VALIDATED" if retargeted else "AE_FORBIDDEN_AWAITING_BATCH5_IDENTITY",
        "execution": {
            "live_entrypoint_present": False,
            "all_live_calls_refuse_before_lock_receipt_subprocess_or_launch": True,
            "separate_reviewed_live_adapter_required": True,
            "single_fresh_batched_session_required": True,
            "existing_artifact_overwrite_forbidden": True,
        },
        "identity_retarget": {
            "state": "validated" if retargeted else "awaiting_installer_and_identity",
            "target": target,
            "required_schema": "olm.installed-identity-manifest/1",
            "required_plugin_count": 10,
            "required_plugins": EXPECTED_PLUGINS,
            "required_row_gates": ["source_installed_exact", "universal_exact", "codesign_exact", "installed_bundle_count_one"],
            "emit_policy": "explicit --identity plus --emit-retargeted-contract to a new absent path only",
        },
        "dependencies": {
            **pinned_dependencies(),
            "batch5_runner": {"path": relative(THIS), "sha256": sha256(THIS)},
            "batch5_payload": {"path": relative(PAYLOAD), "sha256": sha256(PAYLOAD)},
        },
        "future_paths": {
            "raw": relative(FUTURE_RAW), "summary": relative(FUTURE_SUMMARY),
            "artifact_dir": relative(FUTURE_ARTIFACT_DIR), "receipt": relative(FUTURE_RECEIPT),
            "all_absent": future_outputs_absent(),
        },
        "host_frame_policy": {
            "enabled": ENABLED_GENERIC_HOST_FRAME,
            "disabled_after_load_add": DISABLED_GENERIC_HOST_FRAME,
            "numerical_assessment": "not_assessed",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        "readiness_policy": {
            "same_fresh_singleton_pid": True, "exact_owned_pid_cleanup": True,
            "get_version_exact": "26.3.0", "nonce_bound_doscript_json_probes": 2,
            "receipt_after_readiness_only": True, "canonical_outputs_on_failure": "absent",
            "one_live_attempt_no_retry": True,
            "cache_or_registry_mutation": "forbidden_without_separate_evidence_and_approval",
        },
    }


def validate_contract(value: Any, identity: Path | None = None) -> bool:
    try:
        expected = contract(identity)
        return (
            value == expected
            and value["execution"]["live_entrypoint_present"] is False
            and value["future_paths"]["all_absent"] is True
            and value["host_frame_policy"]["enabled"] == ENABLED_GENERIC_HOST_FRAME
            and value["host_frame_policy"]["disabled_after_load_add"] == DISABLED_GENERIC_HOST_FRAME
            and value["host_frame_policy"]["numerical_assessment"] == "not_assessed"
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, RuntimeError):
        return False


def execute_batch5(*_args: Any, **_kwargs: Any) -> int:
    raise SystemExit("AE execution forbidden: Batch5 v1 is a hostless retargetable contract only")


def write_new(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise RuntimeError("refusing to overwrite existing contract artifact")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--write-prepared-contract", action="store_true")
    parser.add_argument("--identity", type=Path)
    parser.add_argument("--emit-retargeted-contract", type=Path)
    args = parser.parse_args()
    if args.run:
        return execute_batch5()
    if bool(args.identity) != bool(args.emit_retargeted_contract):
        raise SystemExit("--identity and --emit-retargeted-contract must be supplied together")
    if args.identity:
        value = contract(args.identity)
        if not validate_contract(value, args.identity):
            raise SystemExit("retargeted Batch5 contract validation failed")
        write_new(args.emit_retargeted_contract, value)
        print("PASS_BATCH5_RETARGETED_CONTRACT_WRITE_NO_AE")
        return 0
    value = contract()
    if not validate_contract(value):
        raise SystemExit("prepared Batch5 contract validation failed")
    if args.write_prepared_contract:
        write_new(CONTRACT_REPORT, value)
        print("PASS_BATCH5_PREPARED_CONTRACT_WRITE_NO_AE")
        return 0
    if not CONTRACT_REPORT.is_file() or json.loads(CONTRACT_REPORT.read_text(encoding="utf-8")) != value:
        raise SystemExit("persisted Batch5 prepared contract missing or drifted")
    print(json.dumps({"status": value["status"], "future_outputs_absent": True, "after_effects_launched": False}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
