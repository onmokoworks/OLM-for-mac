#!/usr/bin/env python3
"""One-shot Batch5 fresh-AE runner, pinned to the accepted new identity.

Default execution is read-only readiness validation. Exactly one explicit
``--run`` dispatches the reviewed base producer with fixed, versioned output
paths. No caller-supplied output path is accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
BASE_RUNNER = ROOT / "scripts/run_olm_all10_current_install_fresh_ae_smoke_20260812.py"
BASE_PAYLOAD = ROOT / "scripts/ae_host_all10_current_install_fresh_validation_20260812.jsx"
DEFERRED_V2 = ROOT / "scripts/run_olm_all10_batch5_current_identity_deferred_v2_20260815.py"
PAYLOAD = ROOT / "scripts/ae_host_all10_batch5_current_identity_live_v3_20260815.jsx"
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_batch5_current_identity_live_v3_contract_20260815.json"
RAW = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_raw_20260815.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815.json"
ARTIFACT_DIR = ROOT / "handoffs/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815"
RECEIPT = ROOT / "handoffs/olm_all10_batch5_current_identity_v3_fresh_ae_smoke_20260815.invocation-receipt.json"

IDENTITY_SHA256 = "ede4857b810e9f2901561ee8a3a9179c4c508dc2ee058525aa3f46dff4164079"
PINS = {
    "base_runner": "45997d4c756fb9d82afde2fbe8f3be503db5e66dff2b15eaaf9ba1e1219ce4b7",
    "base_payload": "ef0477d30d30b1b5c587ebcc511864bd4692ae0ef9cc2d656975a209df4ad511",
    "deferred_v2": "d4875e4218138f247e9b6a2ee3179e9578c7f5ebe30c207f89fdbde006092138",
    "payload": "7343ff97e79b1881d32b75f7ec390b900884a40700dc3aea8df30aa7266df404",
    "identity": IDENTITY_SHA256,
}
EXPECTED_PLUGINS = [
    "ColorKeep", "OLMBlur", "OLMColorKey", "OLMDirectionalBlur",
    "OLMDistanceGradation", "OLMKiraKira", "OLMRadialBlur", "OLMSmoother",
    "OLMSmoother2", "OLMToonDilate",
]
ENABLED = ["OLMBlur", "OLMDirectionalBlur"]
DISABLED = sorted(set(EXPECTED_PLUGINS) - set(ENABLED))
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


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


BASE_MODULE = load(BASE_RUNNER, "olm_batch5_live_v3_base")
DEFERRED_MODULE = load(DEFERRED_V2, "olm_batch5_live_v3_identity_validator")


def ae_or_aerender_processes() -> list[str]:
    value = subprocess.run(["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True, check=True)
    return sorted(line.strip() for line in value.stdout.splitlines()
                  if "/Adobe After Effects 2026.app/Contents/MacOS/After Effects" in line
                  or "/Adobe After Effects 2026.app/Contents/MacOS/aerender" in line)


def outputs_absent() -> bool:
    return not any(path.exists() for path in (RAW, SUMMARY, ARTIFACT_DIR, RECEIPT))


def dependencies() -> dict[str, dict[str, str]]:
    paths = {"base_runner":BASE_RUNNER, "base_payload":BASE_PAYLOAD, "deferred_v2":DEFERRED_V2,
             "payload":PAYLOAD, "identity":IDENTITY}
    observed = {key:sha256(path) for key,path in paths.items()}
    if observed != PINS:
        raise RuntimeError(f"Batch5 live v3 dependency drift: {observed}")
    return {key:{"path":str(path.relative_to(ROOT)),"sha256":observed[key]} for key,path in sorted(paths.items())}


def contract() -> dict[str, Any]:
    identity = DEFERRED_MODULE.validate_identity(IDENTITY)
    processes = ae_or_aerender_processes()
    return {
        "schema":"olm.all10-batch5-current-identity-live-v3-contract/1",
        "status":"AE_RUN_READY_NEW_IDENTITY_EXPLICIT_RUN_REQUIRED",
        "execution": {
            "live_entrypoint_present":True, "exact_flag":"--run", "default_is_read_only":True,
            "single_attempt_no_retry":True, "fresh_singleton_required":True,
            "ae_and_aerender_process_count_required_before_run":0,
            "o_excl_receipt_before_launch":True, "exact_owned_pid_cleanup":True,
            "caller_supplied_output_paths_forbidden":True,
        },
        "accepted_identity": {**identity, "required_sha256":IDENTITY_SHA256,
                              "exact_hash":identity["sha256"]==IDENTITY_SHA256},
        "dependencies": {**dependencies(), "live_v3_runner":{"path":str(THIS.relative_to(ROOT)),"sha256":sha256(THIS)}},
        "fixed_outputs": {"raw":str(RAW.relative_to(ROOT)), "summary":str(SUMMARY.relative_to(ROOT)),
                          "artifact_dir":str(ARTIFACT_DIR.relative_to(ROOT)), "receipt":str(RECEIPT.relative_to(ROOT)),
                          "all_absent":outputs_absent()},
        "preflight": {"ae_and_aerender_processes":processes, "process_count":len(processes),
                      "identity_actual_artifacts_verified":identity["actual_installed_and_source_bundles_verified"],
                      "plugin_count":identity["plugin_count"], "outputs_absent":outputs_absent()},
        "host_frame_policy": {"enabled":ENABLED, "disabled_after_load_add":DISABLED,
                              "numerical_assessment":"not_assessed", "claim_boundary":CLAIM_BOUNDARY},
        "readiness_policy": {"same_fresh_singleton_pid":True, "get_version_exact":"26.3.0",
                             "nonce_bound_doscript_json_probes":2,
                             "receipt_created_with_o_excl_before_any_live_launch":True,
                             "canonical_outputs_on_failure":"fail_closed_durable_after_receipt",
                             "cache_or_registry_mutation":"forbidden"},
        "exact_run_command": f"python3 {THIS.relative_to(ROOT)} --run",
    }


def validate_contract(value: Any) -> bool:
    try:
        expected=contract()
        return (value==expected and value["accepted_identity"]["exact_hash"] is True
                and value["accepted_identity"]["plugin_count"]==10
                and value["preflight"]["process_count"]==0
                and value["fixed_outputs"]["all_absent"] is True
                and value["host_frame_policy"]["enabled"]==ENABLED
                and value["host_frame_policy"]["disabled_after_load_add"]==DISABLED
                and value["host_frame_policy"]["numerical_assessment"]=="not_assessed")
    except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,RuntimeError,subprocess.SubprocessError):
        return False


def configure_base() -> None:
    BASE_MODULE.RUNNER=THIS; BASE_MODULE.PAYLOAD=PAYLOAD; BASE_MODULE.IDENTITY=IDENTITY
    BASE_MODULE.ENABLED_HOST_FRAME_PLUGINS=set(ENABLED); BASE_MODULE.CLAIM_BOUNDARY=CLAIM_BOUNDARY


def execute_once() -> int:
    if not CONTRACT_REPORT.is_file():
        raise SystemExit("Batch5 live v3 contract absent")
    saved=json.loads(CONTRACT_REPORT.read_text(encoding="utf-8"))
    if not validate_contract(saved):
        raise SystemExit("Batch5 live v3 preflight/contract is not GO")
    configure_base()
    original=sys.argv
    sys.argv=[str(BASE_RUNNER), "--raw-report", str(RAW), "--summary", str(SUMMARY),
              "--artifact-dir", str(ARTIFACT_DIR), "--timeout", "900"]
    try:
        return BASE_MODULE.main()
    finally:
        sys.argv=original


def write_contract() -> None:
    if CONTRACT_REPORT.exists():
        raise RuntimeError("refusing to overwrite existing Batch5 live v3 contract")
    value=contract()
    if not validate_contract(value):
        raise RuntimeError("Batch5 live v3 contract is not GO")
    CONTRACT_REPORT.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8")


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--run",action="store_true");parser.add_argument("--write-contract",action="store_true");args=parser.parse_args()
    if args.run and args.write_contract:
        raise SystemExit("choose exactly one mode")
    if args.run:return execute_once()
    if args.write_contract:
        write_contract();print("PASS_BATCH5_LIVE_V3_CONTRACT_WRITE_NO_AE");return 0
    if not CONTRACT_REPORT.is_file():raise SystemExit("Batch5 live v3 contract absent")
    value=json.loads(CONTRACT_REPORT.read_text(encoding="utf-8"))
    if not validate_contract(value):raise SystemExit("Batch5 live v3 contract drift/not GO")
    print(json.dumps({"status":value["status"],"identity_sha256":IDENTITY_SHA256,"ae_run_executed":False,
                      "exact_run_command":value["exact_run_command"]},indent=2,sort_keys=True));return 0


if __name__=="__main__":raise SystemExit(main())
