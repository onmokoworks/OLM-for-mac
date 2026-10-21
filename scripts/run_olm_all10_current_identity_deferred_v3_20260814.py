#!/usr/bin/env python3
"""Hostless-only current-identity contract for a future batched AE checkpoint.

This module deliberately has no executable AE path.  ``--run`` and the public
``execute_v3`` function fail before locks, receipts, subprocesses, or launch
calls.  A later live route requires a separate reviewed change and explicit
user approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
BASE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
BASE_PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
PAYLOAD = ROOT / "scripts/ae_host_all10_current_identity_deferred_v3_20260814.jsx"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
SOURCE_AUTHORITY = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.json"
FAILURE_METADATA = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_failure_metadata_20260813.json"
V2_CONTRACT = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_contract_20260813.json"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_current_identity_deferred_v3_contract_20260814.json"
FUTURE_RAW = ROOT / "refs/conformance/olm_all10_current_identity_v3_fresh_ae_smoke_raw_20260814.json"
FUTURE_SUMMARY = ROOT / "refs/conformance/olm_all10_current_identity_v3_fresh_ae_smoke_20260814.json"
FUTURE_ARTIFACT_DIR = ROOT / "handoffs/olm_all10_current_identity_v3_fresh_ae_smoke_20260814"
FUTURE_RECEIPT = ROOT / "handoffs/olm_all10_current_identity_v3_fresh_ae_smoke_20260814.invocation-receipt.json"

PINS = {
    "base_runner": "45997d4c756fb9d82afde2fbe8f3be503db5e66dff2b15eaaf9ba1e1219ce4b7",
    "base_payload": "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511",
    "identity": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
    "source_authority": "8138180651e805e352fdb6ffd2e91abd426803d7395d949a545e73c421f3e6f9",
    "failure_metadata": "849de8a7d26ec10866511d03a7ab2521e704d4f7e6d221b66987adf7861b31bf",
    "v2_contract": "8adaae1f6cce55889bad5eced7c3dc9a29a3bc4d81f19da9e1b0ac46fd60107c",
}
EXPECTED_PLUGINS = [
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]
ENABLED_GENERIC_HOST_FRAME = ["OLMBlur", "OLMDirectionalBlur"]
DISABLED_GENERIC_HOST_FRAME = sorted(set(EXPECTED_PLUGINS) - set(ENABLED_GENERIC_HOST_FRAME))
CLAIM_BOUNDARY = (
    "Current installed host load/add/enable-state and exact mapping for all ten; "
    "generic effect-enabled host-frame render only for OLMBlur and "
    "OLMDirectionalBlur. The other eight are disabled before generic "
    "saveFrameToPng. Numerical behavior is not assessed. No pixel-exact, "
    "Windows-equivalence, typed-plane, padding, admission, or public-owner "
    "numerical-exact claim."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def future_outputs_absent() -> bool:
    return not any(path.exists() for path in (
        FUTURE_RAW, FUTURE_SUMMARY, FUTURE_ARTIFACT_DIR, FUTURE_RECEIPT,
    ))


def live_dependencies() -> dict[str, Any]:
    paths = {
        "base_runner": BASE_RUNNER,
        "base_payload": BASE_PAYLOAD,
        "identity": IDENTITY,
        "source_authority": SOURCE_AUTHORITY,
        "failure_metadata": FAILURE_METADATA,
        "v2_contract": V2_CONTRACT,
    }
    observed = {key: sha256(path) for key, path in paths.items()}
    if observed != PINS:
        raise RuntimeError(f"v3 input drift: {observed}")
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    plugins = identity.get("plugins")
    if not isinstance(plugins, list) or sorted(row.get("plugin") for row in plugins) != EXPECTED_PLUGINS:
        raise RuntimeError("v3 accepted-identity plug-in set drift")
    for row in plugins:
        if row.get("sha256") != row.get("source_sha256"):
            raise RuntimeError(f"v3 accepted identity row is not exact: {row.get('plugin')}")
    return {
        key: {"path": str(paths[key].relative_to(ROOT)), "sha256": observed[key]}
        for key in sorted(paths)
    }


def contract() -> dict[str, Any]:
    return {
        "schema": "olm.all10-current-identity-deferred-v3-contract/1",
        "status": "AE_FORBIDDEN_HOSTLESS_VALIDATED_CURRENT_IDENTITY",
        "execution": {
            "live_entrypoint_present": False,
            "run_flag_behavior": "refuse_before_lock_receipt_subprocess_or_launch",
            "explicit_user_approval_required_for_future_live_route": True,
            "single_batched_session_required": True,
        },
        "current_identity": {
            "path": str(IDENTITY.relative_to(ROOT)),
            "sha256": PINS["identity"],
            "plugin_count": 10,
            "plugins": EXPECTED_PLUGINS,
        },
        "dependencies": {
            **live_dependencies(),
            "v3_runner": {"path": str(THIS.relative_to(ROOT)), "sha256": sha256(THIS)},
            "v3_payload": {"path": str(PAYLOAD.relative_to(ROOT)), "sha256": sha256(PAYLOAD)},
        },
        "future_paths": {
            "raw": str(FUTURE_RAW.relative_to(ROOT)),
            "summary": str(FUTURE_SUMMARY.relative_to(ROOT)),
            "artifact_dir": str(FUTURE_ARTIFACT_DIR.relative_to(ROOT)),
            "receipt": str(FUTURE_RECEIPT.relative_to(ROOT)),
            "all_absent": future_outputs_absent(),
        },
        "host_frame_policy": {
            "enabled": ENABLED_GENERIC_HOST_FRAME,
            "disabled": DISABLED_GENERIC_HOST_FRAME,
            "numerical_assessment": "not_assessed",
            "claim_boundary": CLAIM_BOUNDARY,
        },
        "readiness_policy": {
            "same_fresh_singleton_pid": True,
            "get_version_exact": "26.3.0",
            "nonce_bound_doscript_json_probes": 2,
            "receipt_after_readiness_only": True,
            "canonical_outputs_on_failure": "absent",
            "cache_or_registry_mutation": "forbidden_without_separate_evidence_and_approval",
        },
    }


def validate_contract(value: Any) -> bool:
    try:
        expected = contract()
        return (
            value == expected
            and value["status"] == "AE_FORBIDDEN_HOSTLESS_VALIDATED_CURRENT_IDENTITY"
            and value["execution"]["live_entrypoint_present"] is False
            and value["future_paths"]["all_absent"] is True
            and value["host_frame_policy"]["enabled"] == ENABLED_GENERIC_HOST_FRAME
            and value["host_frame_policy"]["disabled"] == DISABLED_GENERIC_HOST_FRAME
        )
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def execute_v3(*_args: Any, **_kwargs: Any) -> int:
    raise SystemExit("AE execution forbidden: current-identity v3 is hostless contract only")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--write-contract", action="store_true")
    args = parser.parse_args()
    value = contract()
    if not validate_contract(value):
        raise SystemExit("v3 contract validation failed")
    if args.run:
        return execute_v3()
    if args.write_contract:
        CONTRACT_REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("PASS_CURRENT_IDENTITY_V3_CONTRACT_WRITE_NO_AE")
        return 0
    if not CONTRACT_REPORT.is_file() or json.loads(CONTRACT_REPORT.read_text(encoding="utf-8")) != value:
        raise SystemExit("persisted v3 contract missing or drifted")
    print(json.dumps({
        "status": value["status"],
        "current_identity_valid": True,
        "future_outputs_absent": future_outputs_absent(),
        "after_effects_launched": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
