#!/usr/bin/env python3
"""Fail-closed rerun gate for the standalone v1 run5 PF16 callback crash.

Run5 used a 32bpc AE project, but the standalone Windows/Mac v1 dispatcher has
no PF32 lane: AE host conversion reached the PF16 callback.  Keeping the 32bpc
request is therefore required to reproduce the crashed host context; this
runner does not relabel the request as a native-PF16 project/render oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMSmoother.plugin"
MACHO = INSTALLED / "Contents/MacOS/OLMSmoother"
BASE_RUNNER = ROOT / "scripts/run_olmsmoother_v1_32bpc_mac_validation_20260730.py"
PROBE = ROOT / "tools/emulation/probe_olmsmoother_v1_pf16_mainkernel_boundary_20260731.py"

EXPECTED = {
    ROOT / "mac/OLMSmoother/Mac/OLMSmoother_port.cpp": "417056110abb4e2515851c697b0d1ae7e565dc0f27bbb2acd129761c19739b67",
    ROOT / "mac/OLMSmoother/OLMSmoother_Strings.cpp": "ce4ed37933a67172f6cba6570a55a5f2ea592284e8a9f48cd852bf4fcf1484e7",
    ROOT / "refs/mac_validation_requests/olmsmoother_v1_32bpc_mac_validation_20260730.json": "0be8a7385ca6e6db61571459709eda1bfa3edbf515423058235266db2294b5ad",
    PROBE: "91a62a226fff1e742d8a9c3dab34ce986a54975de66eb9ec9e57d3d9d4053fb1",
    BASE_RUNNER: "57b006dcd34c76ffe755c2f3f7eeb0f0def93959a6c3ecbc6b77714ac3d63e52",
}
EXPECTED_INSTALLED_SHA256 = "5027d527bf67bedc94f784cbe9d6fcc16aea3a7eee07dfa210ed68596212b0e6"
RUN5_DUMP = ROOT / "refs/mac_validation_runs/olmsmoother_v1_32bpc_20260731_run5/crash_evidence/af0e9ca2-fd49-4729-b153-2e46a6f52b67.dmp"
RUN5_DUMP_SHA256 = "9095691989c52a95d1d9106aa728b308ac33b61cb2e630bb0fba0fd86d4d629c"
REQUEST = ROOT / "refs/mac_validation_requests/olmsmoother_v1_32bpc_mac_validation_20260730.json"
RUN5_CASE_ID = "final_random10_olm_smoother_01"
RUN5_PARAMS = [
    {"name": "Use Color Key", "match_name": "OLM Smoother-0001", "property_index": 1, "value": 1},
    {"name": "Color Key", "match_name": "OLM Smoother-0002", "property_index": 2, "value": [0.79379999637604, 0.7335000038147, 0.90140002965927, 1]},
    {"name": "Do Smooth Range", "match_name": "OLM Smoother-0003", "property_index": 3, "value": 33},
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapped_smoother(pid: int) -> list[str]:
    result = subprocess.run(["vmmap", str(pid)], text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(f"vmmap failed for AE pid {pid}")
    paths = set()
    for line in result.stdout.splitlines():
        if "OLMSmoother.plugin/Contents/MacOS/OLMSmoother" in line:
            start = line.find("/")
            if start >= 0:
                paths.add(line[start:].split("   ", 1)[0].strip())
    return sorted(paths)


def preflight() -> tuple[dict[str, object], bool]:
    checks: dict[str, object] = {}
    for path, expected in EXPECTED.items():
        observed = digest(path.resolve(strict=True))
        checks[str(path.relative_to(ROOT))] = {"expected": expected, "observed": observed, "pass": observed == expected}

    checks["installed_bundle"] = {
        "path": str(INSTALLED),
        "macho_sha256": digest(MACHO.resolve(strict=True)),
        "expected_macho_sha256": EXPECTED_INSTALLED_SHA256,
    }
    checks["installed_bundle"]["pass"] = checks["installed_bundle"]["macho_sha256"] == EXPECTED_INSTALLED_SHA256

    request = json.loads(REQUEST.read_text())
    case = request.get("cases", [{}])[0]
    checks["run5_host_context"] = {
        "project_bits_per_channel": request.get("common_setup", {}).get("bits_per_channel"),
        "callback_depth": "PF16 via classic host conversion; grounded by the pinned run5 dump/probe",
        "case_id": case.get("id"),
        "params": case.get("params"),
        "dump_sha256": digest(RUN5_DUMP.resolve(strict=True)),
    }
    checks["run5_host_context"]["pass"] = (
        checks["run5_host_context"]["project_bits_per_channel"] == 32
        and case.get("id") == RUN5_CASE_ID
        and case.get("params") == RUN5_PARAMS
        and checks["run5_host_context"]["dump_sha256"] == RUN5_DUMP_SHA256
    )

    probe = subprocess.run([sys.executable, str(PROBE)], text=True, capture_output=True, check=False)
    try:
        probe_json = json.loads(probe.stdout)
    except json.JSONDecodeError:
        probe_json = {}
    checks["pf16_boundary_probe"] = {
        "returncode": probe.returncode,
        "status": probe_json.get("status"),
        "source_tables_match_windows": probe_json.get("source_tables_match_windows"),
        "pass": probe.returncode == 0 and probe_json.get("status") == "pass" and probe_json.get("source_tables_match_windows") is True,
    }

    pgrep = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, check=False)
    pids = [int(value) for value in pgrep.stdout.split()]
    mappings = {str(pid): mapped_smoother(pid) for pid in pids}
    exact = str(MACHO.resolve(strict=True))
    host_ready = len(pids) == 1 and mappings == {str(pids[0]): [exact]}
    checks["ae_process_binding"] = {
        "pids": pids,
        "mappings": mappings,
        "required": "one AE PID with exactly the installed hash-bound Mach-O mapped",
        "pass": host_ready,
    }
    identity_ready = all(bool(value.get("pass")) for value in checks.values() if isinstance(value, dict) and "pass" in value and value is not checks["ae_process_binding"])
    return {
        "schema_version": 2,
        "scope": "OLMSmoother v1 run5: reproduce the 32bpc AE host context that reached the PF16 callback",
        "claim_boundary": "This is not a native-PF16 project fixture and does not substitute 32bpc FLOAT output for PF16 callback evidence.",
        "checks": checks,
    }, identity_ready and host_ready


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        report, ready = preflight()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "fail_closed", "error": str(exc)}, indent=2))
        return 1
    report["status"] = "ready" if ready else "restart_required"
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ready:
        return 2
    if not args.run:
        return 0
    if args.output_dir is None:
        print("[FAIL_CLOSED] --run requires --output-dir", file=sys.stderr)
        return 1
    return subprocess.call([
        sys.executable, str(BASE_RUNNER), "--execute", "--plugin-path", str(INSTALLED),
        "--output-dir", str(args.output_dir),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
