#!/usr/bin/env python3
"""Read-only deferred v2 launcher contract; live AE execution is forbidden.

The v2 seam requires one successful version probe followed by two consecutive
exact, nonce-bound DoScript JSON readiness probes on the same fresh singleton
AE PID.  Only then is the canonical O_EXCL receipt created and DoScriptFile
allowed.  Readiness failure creates no canonical run outputs.
"""
from __future__ import annotations

import argparse
import atexit
import copy
import errno
import fcntl
import hashlib
import importlib.util
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()
V1_RUNNER = ROOT / "scripts/run_olm_all10_post_toondilate_ded9_corrected_20260813.py"
V1_PAYLOAD = ROOT / "scripts/ae_host_all10_post_toondilate_ded9_corrected_20260813.jsx"
PAYLOAD = ROOT / "scripts/ae_host_all10_post_toondilate_ded9_corrected_v2_20260813.jsx"
CONTRACT_REPORT = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_contract_20260813.json"
RAW = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_fresh_ae_smoke_raw_20260813.json"
SUMMARY = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_v2_fresh_ae_smoke_20260813.json"
ARTIFACT_DIR = ROOT / "handoffs/olm_all10_post_toondilate_ded9_corrected_v2_fresh_ae_smoke_20260813"
RECEIPT = ARTIFACT_DIR.with_name(ARTIFACT_DIR.name + ".invocation-receipt.json")

FAILURE1_RAW = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_raw_20260813.json"
FAILURE1_SUMMARY = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.json"
FAILURE1_RECEIPT = ROOT / "handoffs/olm_all10_post_toondilate_ded9_fresh_ae_smoke_20260813.invocation-receipt.json"
FAILURE2_RAW = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_raw_20260813.json"
FAILURE2_SUMMARY = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_20260813.json"
FAILURE2_RECEIPT = ROOT / "handoffs/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_20260813.invocation-receipt.json"
FAILURE2_METADATA = ROOT / "refs/conformance/olm_all10_post_toondilate_ded9_corrected_fresh_ae_smoke_failure_metadata_20260813.json"

V1_RUNNER_SHA256 = "7bbca21dc9a345e78dfeec909c6c5715d4100b71fb68bfd3d4b5b8147fdcef56"
V1_PAYLOAD_SHA256 = "95e75363743cd2537046bb7d2afa0d73586f772f77d34c72dfcd0386cb558fb8"
FAILURE1 = {
    "raw": (FAILURE1_RAW, "17a728f155c292a45b4c1ed83fcc9ba2e0f7d72785732c97eec8780a8f4d0e0e"),
    "summary": (FAILURE1_SUMMARY, "055820bf760d8c31d627e352c0fb87d11ecf263804f1bc3f8dcbc51c33c1972b"),
    "receipt": (FAILURE1_RECEIPT, "ed52902307f2e098c46dfb1343ac4105d3067657ac4d8a5a8001b2f71abaae7b"),
}
FAILURE2 = {
    "raw": (FAILURE2_RAW, "bfdafa52dd3912093eaaaea54507311bdb574ff66fba3b4ae033bd179c3a428f"),
    "summary": (FAILURE2_SUMMARY, "0d0fa68c29c7268a50a0b78ce493c9473d8afcecc022899b0e9e23ba0f81e90a"),
    "receipt": (FAILURE2_RECEIPT, "2bc516f728c4349029cc80b6179ea467ab5f623c58d32d5e3a2de4b9d3d260e8"),
    "failure_metadata": (FAILURE2_METADATA, "849de8a7d26ec10866511d03a7ab2521e704d4f7e6d221b66987adf7861b31bf"),
}
READINESS_SCHEMA = "olm.ae-doscript-readiness/1"
GET_VERSION = "26.3.0"
DOSCRIPT_APP_VERSION = "26.3x87"
READINESS_CONSECUTIVE = 2
LOCK = Path(tempfile.gettempdir()) / "olm-all10-toondilate-ded9-corrected-v2.lock"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


C = _load(V1_RUNNER, "olm_corrected_v1_for_v2")
B = C.base
B.RUNNER = THIS
B.PAYLOAD = PAYLOAD


def failure_authorities() -> dict[str, Any]:
    def rows(source: dict[str, tuple[Path, str]]) -> dict[str, Any]:
        return {key: {"path": str(path.relative_to(ROOT)), "sha256": digest}
                for key, (path, digest) in source.items()}
    return {
        "unsupported_generic_toon_frame_attempt": {
            "classification": "immutable_failure_owner_contract_mismatch",
            **rows(FAILURE1),
        },
        "pre_payload_doscriptfile_failure": {
            "classification": "immutable_failure_pre_payload_doscriptfile_error_not_plugin_crash",
            **rows(FAILURE2),
        },
    }


def validate_failures(value: Any) -> bool:
    try:
        return value == failure_authorities() and all(
            _sha(path) == digest
            for source in (FAILURE1, FAILURE2)
            for path, digest in source.values()
        )
    except (OSError, TypeError, ValueError):
        return False


def paths() -> dict[str, str]:
    return {
        "raw": str(RAW.relative_to(ROOT)),
        "summary": str(SUMMARY.relative_to(ROOT)),
        "artifact_dir": str(ARTIFACT_DIR.relative_to(ROOT)),
        "receipt": str(RECEIPT.relative_to(ROOT)),
    }


def dependencies() -> dict[str, Any]:
    return {
        "v1_runner": {"path": str(V1_RUNNER.relative_to(ROOT)), "sha256": V1_RUNNER_SHA256},
        "v1_payload": {"path": str(V1_PAYLOAD.relative_to(ROOT)), "sha256": V1_PAYLOAD_SHA256},
        "v2_runner": {"path": str(THIS.relative_to(ROOT)), "sha256": _sha(THIS)},
        "v2_payload": {"path": str(PAYLOAD.relative_to(ROOT)), "sha256": _sha(PAYLOAD)},
        "v1_contract": C.corrected_contract(),
    }


def contract() -> dict[str, Any]:
    return {
        "schema": "olm.all10-post-toondilate-ded9-corrected-v2-launch-contract/1",
        "status": "AE_FORBIDDEN_DEFERRED_BATCH_CHECKPOINT",
        "paths": paths(),
        "readiness": {
            "order": ["fresh_singleton_pid", "get_version", "doscript_exact_json_1", "doscript_exact_json_2", "o_excl_receipt", "doscriptfile"],
            "schema": READINESS_SCHEMA,
            "get_version": GET_VERSION,
            "doscript_app_version": DOSCRIPT_APP_VERSION,
            "consecutive_exact": READINESS_CONSECUTIVE,
            "same_fresh_pid_required": True,
            "receipt_before_readiness": False,
            "canonical_outputs_on_readiness_failure": "absent",
            "pre_receipt_concurrency_guard": "exclusive advisory flock",
        },
        "dependencies": dependencies(),
        "failure_authorities": failure_authorities(),
        "claim_boundary": C.CLAIM_BOUNDARY,
    }


def validate_contract(value: Any) -> bool:
    try:
        return (
            value == contract()
            and _sha(V1_RUNNER) == V1_RUNNER_SHA256
            and _sha(V1_PAYLOAD) == V1_PAYLOAD_SHA256
            and C.validate_contract(value["dependencies"]["v1_contract"])
            and validate_failures(value["failure_authorities"])
        )
    except (OSError, TypeError, ValueError, KeyError):
        return False


def outputs_absent() -> bool:
    return not any(path.exists() for path in (RAW, SUMMARY, ARTIFACT_DIR, RECEIPT))


def readiness_expected(nonce: str, probe_index: int) -> dict[str, Any]:
    return {"schema": READINESS_SCHEMA, "ready": True, "status": "ok", "version": DOSCRIPT_APP_VERSION, "nonce": nonce, "probe_index": probe_index}


def readiness_javascript(nonce: str, probe_index: int) -> str:
    # JSON text is emitted by AE; the nonce is JSON encoded before insertion.
    return (
        "JSON.stringify({schema:" + json.dumps(READINESS_SCHEMA) +
        ",ready:true,status:\"ok\",version:app.version,nonce:" + json.dumps(nonce) +
        ",probe_index:" + str(probe_index) + "})"
    )


def readiness_stdout(nonce: str, probe_index: int) -> str:
    return json.dumps(readiness_expected(nonce, probe_index), separators=(",", ":")) + "\n"


def readiness_probe_command(nonce: str, probe_index: int) -> list[str]:
    # Pass JavaScript as argv rather than interpolating it into AppleScript.
    apple = (
        "on run argv\n"
        "  with timeout of 30 seconds\n"
        '    tell application "Adobe After Effects 2026" to set observed to DoScript (item 1 of argv) with override\n'
        "  end timeout\n"
        "  return observed\n"
        "end run"
    )
    return ["osascript", "-e", apple, "--", readiness_javascript(nonce, probe_index)]


def exact_readiness_result(
    result: subprocess.CompletedProcess[str], pids: list[int], pid: int, nonce: str, probe_index: int,
) -> bool:
    return (
        result.returncode == 0
        and result.stderr == ""
        and result.stdout == readiness_stdout(nonce, probe_index)
        and pids == [pid]
    )


def has_two_consecutive_exact(samples: list[dict[str, Any]]) -> bool:
    return len(samples) >= 2 and samples[-1].get("exact") is True and samples[-2].get("exact") is True


def validate_v2_readiness(value: Any, host_pid: int) -> bool:
    try:
        if not isinstance(host_pid, int) or host_pid <= 0 or not isinstance(value, dict):
            return False
        if set(value) != {
            "schema", "same_fresh_pid", "version_probe", "samples",
            "post_probe_pids", "consecutive_exact", "receipt_created_after_readiness",
        }:
            return False
        if value["schema"] != READINESS_SCHEMA or value["same_fresh_pid"] != host_pid:
            return False
        if value["post_probe_pids"] != [host_pid] or value["consecutive_exact"] != 2:
            return False
        if value["receipt_created_after_readiness"] is not True:
            return False
        version = value["version_probe"]
        if set(version) != {"sampled_at", "returncode", "stdout", "stderr"}:
            return False
        C.base.parse_iso(version["sampled_at"])
        if version["returncode"] != 0 or version["stdout"] != GET_VERSION or version["stderr"] != "":
            return False
        samples = value["samples"]
        if not isinstance(samples, list) or not has_two_consecutive_exact(samples):
            return False
        nonces: set[str] = set()
        for index, row in enumerate(samples, 1):
            if set(row) != {"probe_index", "nonce", "returncode", "stdout", "stderr", "pids", "exact"}:
                return False
            nonce = row["nonce"]
            if not isinstance(nonce, str) or len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
                return False
            if nonce in nonces or row["probe_index"] != index:
                return False
            nonces.add(nonce)
            recomputed = exact_readiness_result(
                subprocess.CompletedProcess(["synthetic"], row["returncode"], row["stdout"], row["stderr"]),
                row["pids"], host_pid, nonce, index,
            )
            if row["exact"] is not recomputed:
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def validate_v2_outputs(summary: Any, raw: Any, raw_path: Path) -> bool:
    try:
        return (
            isinstance(summary, dict)
            and isinstance(raw, dict)
            and raw_path.resolve() == RAW
            and summary.get("raw_report", {}).get("path") == str(RAW.relative_to(ROOT))
            and raw.get("v2_contract") == contract()
            and summary.get("v2_contract") == contract()
            and summary.get("v2_launcher_readiness") == raw.get("v2_launcher_readiness")
            and validate_v2_readiness(raw.get("v2_launcher_readiness"), raw.get("host", {}).get("pid"))
        )
    except (OSError, TypeError, ValueError):
        return False


def poll_readiness(
    pid: int,
    executor: Callable[[list[str]], subprocess.CompletedProcess[str]],
    pid_reader: Callable[[], list[int]],
    *,
    timeout: float = 120.0,
) -> tuple[bool, list[dict[str, Any]]]:
    deadline = time.monotonic() + timeout
    consecutive = 0
    samples: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        probe_index = len(samples) + 1
        nonce = secrets.token_hex(16)
        pids = pid_reader()
        result = executor(readiness_probe_command(nonce, probe_index))
        exact = exact_readiness_result(result, pids, pid, nonce, probe_index)
        samples.append({
            "probe_index": probe_index,
            "nonce": nonce,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "pids": pids,
            "exact": exact,
        })
        consecutive = consecutive + 1 if exact else 0
        if consecutive == READINESS_CONSECUTIVE and has_two_consecutive_exact(samples):
            return True, samples
        time.sleep(0.25)
    return False, samples


def create_receipt_after_readiness(evidence: dict[str, Any], pid: int) -> None:
    if not validate_v2_readiness(evidence, pid):
        raise RuntimeError("receipt forbidden before two consecutive exact readiness samples")
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(RECEIPT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except OSError as error:
        if error.errno == errno.EEXIST:
            raise RuntimeError("refusing v2 receipt reuse") from error
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        # Preserve the producer validator's exact receipt schema.  The nonce-
        # bound samples are written into raw/summary by the v2 normalization.
        json.dump({"schema": "olm.all10-fresh-ae-invocation-receipt/1", "created_at": B.now_iso()}, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


LIVE_EXECUTION_ENABLED = False


def _execute_v2_locked(timeout: int) -> int:
    """Live path; v1 corrected semantics continue on the same ready PID."""
    if not LIVE_EXECUTION_ENABLED:
        raise RuntimeError("AE forbidden: deferred batch checkpoint")
    if not outputs_absent():
        raise SystemExit("refusing v2 path reuse")
    if not validate_contract(contract()):
        raise SystemExit("v2 dependency/authority drift")
    if B.ae_pids():
        raise SystemExit("AE process exists before v2 launch")
    # Verify accepted identity before any process or receipt mutation.
    B.verify_identity()
    launch = subprocess.run(["open", "-a", "Adobe After Effects 2026"], capture_output=True, text=True, timeout=30)
    if launch.returncode != 0:
        raise SystemExit("v2 open launch failed")
    pid, _ = B.wait_for_single_new_pid(set())
    owned = {pid} if pid is not None else set()
    try:
        if pid is None:
            raise RuntimeError("fresh singleton AE PID not observed")
        versions = B.wait_for_scriptable_ae()
        if not versions or versions[-1]["returncode"] != 0 or versions[-1]["stdout"] != GET_VERSION:
            raise RuntimeError("get-version readiness failed")
        ok, samples = poll_readiness(
            pid,
            lambda command: subprocess.run(command, capture_output=True, text=True, timeout=40),
            B.ae_pids,
        )
        if not ok:
            raise RuntimeError("two consecutive exact DoScript readiness probes not observed")
        post_probe_pids = B.ae_pids()
        # Close the pre-receipt TOCTOU window: identity, dependencies, exact
        # same PID and canonical path absence are all rechecked immediately.
        B.verify_identity()
        if post_probe_pids != [pid] or not validate_contract(contract()) or not outputs_absent():
            raise RuntimeError("v2 pre-receipt authority/PID/path recheck failed")
        readiness_evidence = {
            "schema": READINESS_SCHEMA,
            "same_fresh_pid": pid,
            "version_probe": versions[-1],
            "samples": samples,
            "post_probe_pids": post_probe_pids,
            "consecutive_exact": 2,
            "receipt_created_after_readiness": True,
        }
        create_receipt_after_readiness(readiness_evidence, pid)
        # Continue the frozen producer on the same process.  Its early receipt
        # is redirected to a private temporary file; the canonical receipt was
        # already created above after readiness.  Its apparent pre-launch AE
        # sample and PID discovery are adapted to the process owned here.
        original_os = B.os
        original_ae_pids = B.ae_pids
        original_wait = B.wait_for_single_new_pid
        original_normalize = B.normalize_raw_contract
        first_pid_read = True
        with tempfile.TemporaryDirectory(prefix="olm-toon-v2-receipt-") as temp_dir:
            shadow_receipt = Path(temp_dir) / "shadow-receipt.json"

            class OsProxy:
                def __getattr__(self, name: str):
                    return getattr(os, name)

                def open(self, path: Any, flags: int, mode: int = 0o777) -> int:
                    if Path(path).resolve() == RECEIPT:
                        return os.open(shadow_receipt, flags, mode)
                    return os.open(path, flags, mode)

            def adapted_pids() -> list[int]:
                nonlocal first_pid_read
                if first_pid_read:
                    first_pid_read = False
                    return []
                return original_ae_pids()

            def adapted_wait(_before: set[int], timeout: float = 240.0):
                return pid, [{"sampled_at": B.now_iso(), "pids": [pid], "v2_preowned": True}]

            def adapted_normalize(raw: dict[str, Any]) -> None:
                original_normalize(raw)
                raw["v2_contract"] = contract()
                raw["v2_launcher_readiness"] = copy.deepcopy(readiness_evidence)

            B.os = OsProxy()
            B.ae_pids = adapted_pids
            B.wait_for_single_new_pid = adapted_wait
            B.normalize_raw_contract = adapted_normalize
            original_build = B.build_summary
            original_persisted = B.validate_persisted_summary

            def adapted_build(raw: dict[str, Any], raw_path: Path) -> dict[str, Any]:
                value = original_build(raw, raw_path)
                value["v2_contract"] = contract()
                value["v2_launcher_readiness"] = copy.deepcopy(raw["v2_launcher_readiness"])
                return value

            def adapted_persisted(summary: dict[str, Any], raw: dict[str, Any], raw_path: Path) -> bool:
                # Preserve all semantic checks and exact v2 authority/readiness
                # checks. The frozen v1 validator's final path assertion is
                # intentionally replaced because it names the superseded path.
                saved_raw = C.RAW
                try:
                    C.RAW = RAW
                    return (
                        original_persisted(summary, raw, raw_path)
                        and validate_v2_outputs(summary, raw, raw_path)
                    )
                finally:
                    C.RAW = saved_raw

            B.build_summary = adapted_build
            B.validate_persisted_summary = adapted_persisted
            saved_argv = sys.argv[:]
            sys.argv = [
                str(THIS), "--raw-report", str(RAW), "--summary", str(SUMMARY),
                "--artifact-dir", str(ARTIFACT_DIR), "--timeout", str(timeout),
            ]
            try:
                return B.main()
            finally:
                B.os = original_os
                B.ae_pids = original_ae_pids
                B.wait_for_single_new_pid = original_wait
                B.normalize_raw_contract = original_normalize
                B.build_summary = original_build
                B.validate_persisted_summary = original_persisted
                sys.argv = saved_argv
    finally:
        if owned:
            B.stop_owned_ae(owned)


def execute_v2(timeout: int) -> int:
    if not LIVE_EXECUTION_ENABLED:
        raise RuntimeError("AE forbidden: deferred batch checkpoint")
    lock_fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise SystemExit("another v2 launcher owns the pre-receipt lock") from error
        return _execute_v2_locked(timeout)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--write-contract", action="store_true")
    args = parser.parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    value = contract()
    if not validate_contract(value):
        raise SystemExit("v2 contract validation failed")
    if args.write_contract:
        CONTRACT_REPORT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("PASS_V2_CONTRACT_WRITE")
        return 0
    try:
        saved = json.loads(CONTRACT_REPORT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit("v2 contract report missing or invalid") from error
    if saved != value:
        raise SystemExit("v2 contract report drift")
    if not args.run:
        print(json.dumps({"status": "ready_read_only" if outputs_absent() else "already_invoked_no_reuse", "outputs_absent": outputs_absent(), "contract": value}, indent=2, sort_keys=True))
        return 0
    raise SystemExit("AE forbidden: deferred batch checkpoint; live continuation is intentionally unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
