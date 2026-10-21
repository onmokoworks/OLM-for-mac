#!/usr/bin/env python3
"""Read-only readiness gate for a future single batched AE checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_AUDIT = ROOT / "tools/emulation/audit_olm_all10_current_source_installed_authority_20260813.py"
SOURCE_REPORT = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.json"
PREFLIGHT = ROOT / "scripts/preflight_olm_all_universal_installs_20260805.py"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
RELEASE_STATUS = ROOT / "refs/conformance/olm_release_gate_status_20260806.json"
HOST_AUTOMATION_FAILURE = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_failure_metadata_20260813.json"
FORBIDDEN_CONTRACT = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_contract_20260813.json"
FORBIDDEN_RUNNER = ROOT / "scripts/run_olm_all10_post_toondilate_ded9_corrected_v2_20260813.py"
HISTORICAL_SUCCESS_RAW = ROOT / "refs/conformance/olm_all10_current_install_fresh_ae_smoke_raw_20260812.json"
V3_RUNNER = ROOT / "scripts/run_olm_all10_current_identity_deferred_v3_20260814.py"
V3_CONTRACT = ROOT / "refs/conformance/olm_all10_current_identity_deferred_v3_contract_20260814.json"
REPORT = ROOT / "refs/conformance/olm_deferred_batched_ae_readiness_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_deferred_batched_ae_readiness_20260813.md"
SCRIPTING_PLUGIN = Path("/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/Required/Expressions and Scripting Palette.plugin")
SCRIPTING_BINARY = SCRIPTING_PLUGIN / "Contents/MacOS/Expressions and Scripting Palette"
SCRIPTING_PLIST = SCRIPTING_PLUGIN / "Contents/Info.plist"
PLUGIN_LOADING_LOG = Path.home() / "Library/Preferences/Adobe/After Effects/26.3/Plugin Loading.log"

PINS = {
    "source_auditor": "265fbccfc875c96a9cff3149a8e1cf5eb070e6863f9f939fe2dfc30d14913b8b",
    "source_report": "8138180651e805e352fdb6ffd2e91abd426803d7395d949a545e73c421f3e6f9",
    "preflight": "1065dfabbde20bff12fe6e2bcdce638905bf13e726635c7d7bf617fcfa5f9d96",
    "identity": "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650",
    "host_automation_failure": "849de8a7d26ec10866511d03a7ab2521e704d4f7e6d221b66987adf7861b31bf",
    "forbidden_contract": "8adaae1f6cce55889bad5eced7c3dc9a29a3bc4d81f19da9e1b0ac46fd60107c",
    "forbidden_runner": "031dbde3c47e4fe95364616e004bbf6dece63788ab4c3b551be97af182eb66fd",
    "historical_success_raw": "6ee2e4fbeee23e578da2b508f7827f1cc1d38dd7fdf5da534993531e353ec2be",
    "v3_runner": "019e72afe8726c91a41e873690303b1771e133e71a1d35c081e68e2a324ab190",
    "v3_contract": "805feaf66b7796ea344b24ee40b69e07214dbb5162da31134705db6bf76b8df7",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_source_audit() -> str:
    result = subprocess.run([sys.executable, str(SOURCE_AUDIT)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0 or "PASS_ALL10_CURRENT_SOURCE_CANDIDATE_INSTALLED_EXACT_AE_DEFERRED" not in result.stdout:
        raise RuntimeError("all10 source authority audit failed: " + result.stdout + result.stderr)
    return result.stdout.strip()


def run_preflight() -> tuple[int, bytes, dict[str, Any]]:
    result = subprocess.run([sys.executable, str(PREFLIGHT)], cwd=ROOT, capture_output=True)
    if result.returncode != 2:
        raise RuntimeError(f"preflight expected rc2/ae_not_running, got {result.returncode}")
    try:
        parsed = json.loads(result.stdout)
    except Exception as exc:
        raise RuntimeError("preflight stdout is not JSON") from exc
    return result.returncode, result.stdout, parsed


def validate_preflight(data: dict[str, Any]) -> None:
    if set(data) != {"after_effects", "bundles", "claim_boundary", "installed_after", "status"}:
        raise RuntimeError("preflight schema drift")
    if data["status"] != "ae_not_running" or data["after_effects"] != []:
        raise RuntimeError("preflight AE state mismatch")
    bundles = data["bundles"]
    if not isinstance(bundles, list) or len(bundles) != 10:
        raise RuntimeError("preflight bundle count mismatch")
    names = {row["name"] for row in bundles}
    expected = {row["plugin"] for row in json.loads(IDENTITY.read_text())["plugins"]}
    if names != expected:
        raise RuntimeError("preflight plug-in set mismatch")
    for row in bundles:
        if row["bundle_count"] != 1 or not row["sha256_exact"] or not row["universal_exact"] or not row["codesign_exact"]:
            raise RuntimeError(f"preflight bundle failure: {row['name']}")


def inspect_scripting_plugin() -> dict[str, Any]:
    if not SCRIPTING_BINARY.is_file() or not SCRIPTING_PLIST.is_file():
        raise RuntimeError("AE scripting plug-in is absent from the expected Required path")
    plist = plistlib.loads(SCRIPTING_PLIST.read_bytes())
    lipo = subprocess.run(["lipo", "-archs", str(SCRIPTING_BINARY)], text=True, capture_output=True)
    if lipo.returncode != 0:
        raise RuntimeError("AE scripting plug-in lipo inspection failed")
    architectures = lipo.stdout.strip().split()
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(SCRIPTING_PLUGIN)], text=True, capture_output=True)
    if sign.returncode != 0:
        raise RuntimeError("AE scripting plug-in strict code-sign verification failed")
    if set(architectures) != {"arm64", "x86_64"}:
        raise RuntimeError(f"AE scripting plug-in architecture drift: {architectures}")
    if not PLUGIN_LOADING_LOG.is_file():
        raise RuntimeError("AE plug-in loading log is missing")
    loading_log = PLUGIN_LOADING_LOG.read_text(encoding="utf-8", errors="replace")
    loader_excerpt = "\n".join([
        f"Loading {SCRIPTING_PLUGIN}",
        "The registry tells us to cache so the plugin will be loaded from the cache.",
        "The plugin is marked as Ignore, so it will not be loaded.",
    ])
    if loader_excerpt not in loading_log:
        raise RuntimeError("AE scripting plug-in Ignore/load evidence drift")
    return {
        "path": str(SCRIPTING_PLUGIN),
        "on_disk_present": True,
        "bundle_identifier": plist.get("CFBundleIdentifier"),
        "bundle_version": plist.get("CFBundleVersion"),
        "minimum_macos": plist.get("LSMinimumSystemVersion"),
        "architectures": architectures,
        "binary_sha256": sha256(SCRIPTING_BINARY),
        "plist_sha256": sha256(SCRIPTING_PLIST),
        "codesign_deep_strict_valid": True,
        "loader_log": {
            "path": str(PLUGIN_LOADING_LOG),
            "sha256": sha256(PLUGIN_LOADING_LOG),
            "registry_cached": True,
            "marked_ignore": True,
            "loaded": False,
        },
    }


def inspect_forbidden_runner() -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(FORBIDDEN_RUNNER)], cwd=ROOT, text=True, capture_output=True)
    combined = result.stdout + result.stderr
    if result.returncode == 0 or "corrected smoke execution dependency identity drift" not in combined:
        raise RuntimeError("deferred v2 runner no longer exhibits the pinned current-identity drift boundary")
    return {
        "returncode": result.returncode,
        "dependency_valid": False,
        "failure": "corrected smoke execution dependency identity drift",
        "after_effects_reached": False,
    }


def inspect_v3_contract() -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(V3_RUNNER)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError("current-identity v3 hostless contract failed: " + result.stdout + result.stderr)
    parsed = json.loads(result.stdout)
    expected = {
        "status": "AE_FORBIDDEN_HOSTLESS_VALIDATED_CURRENT_IDENTITY",
        "current_identity_valid": True,
        "future_outputs_absent": True,
        "after_effects_launched": False,
    }
    if parsed != expected:
        raise RuntimeError(f"current-identity v3 hostless status drift: {parsed}")
    contract = json.loads(V3_CONTRACT.read_text(encoding="utf-8"))
    if contract.get("status") != expected["status"] or contract.get("execution", {}).get("live_entrypoint_present") is not False:
        raise RuntimeError("current-identity v3 contract boundary drift")
    return {
        "contract_valid": True,
        "current_identity_valid": True,
        "future_outputs_absent": True,
        "live_entrypoint_present": False,
        "after_effects_reached": False,
    }


def generate() -> dict[str, Any]:
    live_pins = {
        "source_auditor": sha256(SOURCE_AUDIT),
        "source_report": sha256(SOURCE_REPORT),
        "preflight": sha256(PREFLIGHT),
        "identity": sha256(IDENTITY),
        "host_automation_failure": sha256(HOST_AUTOMATION_FAILURE),
        "forbidden_contract": sha256(FORBIDDEN_CONTRACT),
        "forbidden_runner": sha256(FORBIDDEN_RUNNER),
        "historical_success_raw": sha256(HISTORICAL_SUCCESS_RAW),
        "v3_runner": sha256(V3_RUNNER),
        "v3_contract": sha256(V3_CONTRACT),
    }
    if live_pins != PINS:
        raise RuntimeError(f"readiness input drift: {live_pins}")
    source_marker = run_source_audit()
    rc1, stdout1, preflight1 = run_preflight()
    rc2, stdout2, preflight2 = run_preflight()
    validate_preflight(preflight1)
    validate_preflight(preflight2)
    if stdout1 != stdout2 or preflight1 != preflight2:
        raise RuntimeError("two-pass preflight is not byte-identical")
    release_status = json.loads(RELEASE_STATUS.read_text())
    if release_status.get("status") != "release_gate_pending_or_invalid" or release_status.get("releasable") is not False:
        raise RuntimeError("saved release state is not the expected fail-closed pending state")
    automation_failure = json.loads(HOST_AUTOMATION_FAILURE.read_text())
    error_dialog = automation_failure.get("crash_evidence", {}).get("do_script_error_dialog", {})
    if automation_failure.get("status") != "FAILURE_PRESERVED_NO_RETRY_FORMAL_GATE_BLOCKED":
        raise RuntimeError("host automation failure authority status drift")
    if error_dialog.get("category") != "AEErrorDialog" or error_dialog.get("stack_owner") != "AEDoScriptFileCommand performDefaultImplementation":
        raise RuntimeError("host automation failure authority classification drift")
    if "スクリプト機能のプラグインがインストールされていません" not in str(error_dialog.get("message_ja") or ""):
        raise RuntimeError("host automation failure authority message drift")
    forbidden_contract = json.loads(FORBIDDEN_CONTRACT.read_text())
    if forbidden_contract.get("status") != "AE_FORBIDDEN_DEFERRED_BATCH_CHECKPOINT":
        raise RuntimeError("deferred runner contract is not fail-closed")
    historical_success = json.loads(HISTORICAL_SUCCESS_RAW.read_text())
    historical_host = historical_success.get("host", {})
    if historical_success.get("status") != "pass" or historical_success.get("passed") is not True:
        raise RuntimeError("historical DoScriptFile success control status drift")
    if historical_host.get("script_invocation") != {"returncode": 0, "stderr": "", "stdout": "0\n"}:
        raise RuntimeError("historical DoScriptFile success control invocation drift")
    if not historical_host.get("scriptability_samples") or historical_host["scriptability_samples"][0].get("stdout") != "26.3.0":
        raise RuntimeError("historical DoScriptFile success control AE version drift")
    scripting_plugin = inspect_scripting_plugin()
    runner_state = inspect_forbidden_runner()
    v3_state = inspect_v3_contract()
    return {
        "schema": "olm.deferred-batched-ae-readiness/2",
        "status": "identity_ready_v3_hostless_contract_valid_ae_not_executed",
        "inputs": {
            "source_auditor": {"path": str(SOURCE_AUDIT.relative_to(ROOT)), "sha256": live_pins["source_auditor"]},
            "source_report": {"path": str(SOURCE_REPORT.relative_to(ROOT)), "sha256": live_pins["source_report"]},
            "installed_preflight": {"path": str(PREFLIGHT.relative_to(ROOT)), "sha256": live_pins["preflight"]},
            "accepted_identity": {"path": str(IDENTITY.relative_to(ROOT)), "sha256": live_pins["identity"]},
            "release_status": {"path": str(RELEASE_STATUS.relative_to(ROOT)), "sha256": sha256(RELEASE_STATUS)},
            "host_automation_failure": {"path": str(HOST_AUTOMATION_FAILURE.relative_to(ROOT)), "sha256": live_pins["host_automation_failure"]},
            "forbidden_contract": {"path": str(FORBIDDEN_CONTRACT.relative_to(ROOT)), "sha256": live_pins["forbidden_contract"]},
            "forbidden_runner": {"path": str(FORBIDDEN_RUNNER.relative_to(ROOT)), "sha256": live_pins["forbidden_runner"]},
            "historical_success_raw": {"path": str(HISTORICAL_SUCCESS_RAW.relative_to(ROOT)), "sha256": live_pins["historical_success_raw"]},
            "v3_runner": {"path": str(V3_RUNNER.relative_to(ROOT)), "sha256": live_pins["v3_runner"]},
            "v3_contract": {"path": str(V3_CONTRACT.relative_to(ROOT)), "sha256": live_pins["v3_contract"]},
        },
        "source_authority": {"marker": source_marker, "plugin_count": 10, "exact": True},
        "preflight": {
            "passes": 2,
            "returncode": rc1,
            "status": preflight1["status"],
            "stdout_sha256": hashlib.sha256(stdout1).hexdigest(),
            "byte_identical": True,
            "bundle_count": len(preflight1["bundles"]),
            "after_effects": [],
        },
        "release_boundary": {
            "saved_status": release_status["status"],
            "releasable": False,
            "formal_gate_executed": False,
        },
        "host_automation": {
            "available": False,
            "blocked_command": "DoScriptFile",
            "failure_category": error_dialog["category"],
            "failure_message_ja": error_dialog["message_ja"],
            "payload_observed": False,
            "retry_authorized": False,
            "current_runner_execution_forbidden": True,
            "current_runner_state": runner_state,
            "v3_hostless_state": v3_state,
            "scripting_plugin_on_disk": scripting_plugin,
            "historical_success_control": {
                "ae_version": "26.3.0",
                "status": "pass",
                "script_invocation_returncode": 0,
                "script_invocation_stdout": "0\n",
                "fresh_pid": historical_host["pid"],
            },
            "runtime_load_or_registration_status": "unresolved; the loader log's cached Ignore line is not a causal proof because a retained AE 26.3 fresh process completed DoScriptFile successfully",
            "next_required_host_action": "do not mutate the plug-in cache by inference; the current-identity v3 contract is hostlessly valid but intentionally has no live entrypoint, so a separate reviewed change and explicit approval are required before one minimal marker and the single aggregate session",
        },
        "scope": {
            "after_effects_launch_authorized": False,
            "after_effects_launched": False,
            "future_checkpoint_must_be_single_batched_run": True,
            "future_checkpoint_requires_new_host_automation_authority": True,
            "numerical_claim_added": False,
            "windows_oracle_return_received": False,
            "reason_for_deferral": "identity is ready and a current-identity v3 hostless contract is valid, but it intentionally has no live entrypoint; the latest one-shot DoScriptFile failure remains unresolved, v2 fails before AE, and no cache mutation or AE retry is authorized without a separate reviewed change and explicit approval",
        },
    }


def validate_schema(report: dict[str, Any]) -> None:
    if set(report) != {"schema", "status", "inputs", "source_authority", "preflight", "release_boundary", "host_automation", "scope"}:
        raise RuntimeError("readiness top-level schema drift")
    if report["schema"] != "olm.deferred-batched-ae-readiness/2" or report["status"] != "identity_ready_v3_hostless_contract_valid_ae_not_executed":
        raise RuntimeError("readiness status mismatch")
    if set(report["inputs"]) != {"source_auditor", "source_report", "installed_preflight", "accepted_identity", "release_status", "host_automation_failure", "forbidden_contract", "forbidden_runner", "historical_success_raw", "v3_runner", "v3_contract"}:
        raise RuntimeError("readiness input set drift")
    if report["source_authority"] != {
        "marker": "PASS_ALL10_CURRENT_SOURCE_CANDIDATE_INSTALLED_EXACT_AE_DEFERRED",
        "plugin_count": 10,
        "exact": True,
    }:
        raise RuntimeError("source authority claim drift")
    expected_preflight_keys = {"passes", "returncode", "status", "stdout_sha256", "byte_identical", "bundle_count", "after_effects"}
    if set(report["preflight"]) != expected_preflight_keys:
        raise RuntimeError("preflight report schema drift")
    if report["preflight"]["passes"] != 2 or report["preflight"]["returncode"] != 2 or report["preflight"]["status"] != "ae_not_running" or report["preflight"]["bundle_count"] != 10 or report["preflight"]["after_effects"] != [] or report["preflight"]["byte_identical"] is not True:
        raise RuntimeError("preflight report claim drift")
    if report["release_boundary"] != {"saved_status": "release_gate_pending_or_invalid", "releasable": False, "formal_gate_executed": False}:
        raise RuntimeError("release boundary drift")
    if report["host_automation"] != {
        "available": False,
        "blocked_command": "DoScriptFile",
        "failure_category": "AEErrorDialog",
        "failure_message_ja": "スクリプトファイルを実行できません。スクリプト機能のプラグインがインストールされていません。",
        "payload_observed": False,
        "retry_authorized": False,
        "current_runner_execution_forbidden": True,
        "current_runner_state": {
            "returncode": 1,
            "dependency_valid": False,
            "failure": "corrected smoke execution dependency identity drift",
            "after_effects_reached": False,
        },
        "v3_hostless_state": {
            "contract_valid": True,
            "current_identity_valid": True,
            "future_outputs_absent": True,
            "live_entrypoint_present": False,
            "after_effects_reached": False,
        },
        "scripting_plugin_on_disk": {
            "path": "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/Required/Expressions and Scripting Palette.plugin",
            "on_disk_present": True,
            "bundle_identifier": "com.adobe.ExpressionPal.plugin",
            "bundle_version": "26.3.0.87",
            "minimum_macos": "14.0",
            "architectures": ["x86_64", "arm64"],
            "binary_sha256": "81e1d6190d0368e3ca08746dbfa7646cdf54533047c2ecbedd097dbcf3bc3cb0",
            "plist_sha256": "cc32f6b93113d1bf192462858cd4337ed6483d5f43e077fe08decdf6646c2de8",
            "codesign_deep_strict_valid": True,
            "loader_log": {
                "path": "/Users/onmk/Library/Preferences/Adobe/After Effects/26.3/Plugin Loading.log",
                "sha256": "5300a093052148266546f1a51dd209b9605638a808aaf554d96fab8db4238971",
                "registry_cached": True,
                "marked_ignore": True,
                "loaded": False,
            },
        },
        "historical_success_control": {
            "ae_version": "26.3.0",
            "status": "pass",
            "script_invocation_returncode": 0,
            "script_invocation_stdout": "0\n",
            "fresh_pid": 71551,
        },
        "runtime_load_or_registration_status": "unresolved; the loader log's cached Ignore line is not a causal proof because a retained AE 26.3 fresh process completed DoScriptFile successfully",
        "next_required_host_action": "do not mutate the plug-in cache by inference; the current-identity v3 contract is hostlessly valid but intentionally has no live entrypoint, so a separate reviewed change and explicit approval are required before one minimal marker and the single aggregate session",
    }:
        raise RuntimeError("host automation boundary drift")
    if report["scope"] != {
        "after_effects_launch_authorized": False,
        "after_effects_launched": False,
        "future_checkpoint_must_be_single_batched_run": True,
        "future_checkpoint_requires_new_host_automation_authority": True,
        "numerical_claim_added": False,
        "windows_oracle_return_received": False,
        "reason_for_deferral": "identity is ready and a current-identity v3 hostless contract is valid, but it intentionally has no live entrypoint; the latest one-shot DoScriptFile failure remains unresolved, v2 fails before AE, and no cache mutation or AE retry is authorized without a separate reviewed change and explicit approval",
    }:
        raise RuntimeError("readiness scope drift")


def markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# OLM deferred batched AE checkpoint readiness (2026-08-13)",
        "",
        f"Status: `{report['status']}`",
        "",
        "The current production-source → candidate → installed authority chain is exact for all ten plug-ins. The installed preflight ran twice with byte-identical output: ten count-one Universal/code-sign/identity-exact bundles and no AE process.",
        "",
        "The installed identity is ready, but the AE execution route is not. The retained one-shot failure reached AEDoScriptFileCommand and reported that the scripting function was unavailable before the payload produced any result. Read-only inspection proves that `Expressions and Scripting Palette.plugin` is present, Universal, and strict-valid Adobe signed. The loader log contains a cached `Ignore` line, but this is not causal proof: a separately retained fresh AE 26.3 process completed DoScriptFile successfully. The deferred v2 runner is stale and fails before AE. A new current-identity v3 contract is hostlessly valid and output-free, but intentionally exposes no live entrypoint.",
        "",
        "This report does not authorize or launch After Effects, and it forbids speculative cache mutation. Before the future single batched checkpoint, the v3 contract must be converted by a separate reviewed change into a live route and receive explicit approval, followed by one minimal script-marker validation in that same authorized session. It adds no numerical or release claim; the formal release gate remains pending.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    live = generate()
    validate_schema(live)
    if args.write:
        REPORT.write_text(json.dumps(live, indent=2, sort_keys=True) + "\n")
        MARKDOWN.write_text(markdown(live))
    else:
        if not REPORT.is_file() or not MARKDOWN.is_file():
            raise RuntimeError("persisted readiness report missing")
        persisted = json.loads(REPORT.read_text())
        validate_schema(persisted)
        if persisted != live or MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("persisted readiness evidence differs from live state")
    print("PASS_DEFERRED_BATCHED_AE_READINESS_NO_LAUNCH")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_DEFERRED_BATCHED_AE_READINESS: {exc}", file=sys.stderr)
        raise
