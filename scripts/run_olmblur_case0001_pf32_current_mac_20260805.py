#!/usr/bin/env python3
"""Hash-bound OLMBlur case_0001 PF32 Mac AE gate for the current binary.

Preflight happens before the existing render runner is invoked.  In
particular, an AE process that has not mapped the pinned Mach-O produces a
restart_required record and no render side effect.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_olmblur_32bpc_mac_candidates import compare as compare_float_exr

DELEGATE = ROOT / "scripts/run_olmblur_32bpc_mac_validation_20260718.py"
REQUEST = ROOT / "refs/mac_validation_requests/olmblur_32bpc_mac_validation_repeat1_20260718.json"
INPUT = ROOT / "refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur/case_0001_before_effects.png"
DEFAULT_PLUGIN = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin"
PINNED_BINARY_SHA256 = "dd64362e6071cfd93e92f3a4853782752aeb023c54671773bfedb0c496e8afc7"
FORMAL_MATRIX = ROOT / "refs/conformance/olmblur_pf32_formal_worker_matrix_20260805.json"
PINNED_FORMAL_MATRIX_SHA256 = "fcf8795793ebfecc0bc61d997504ec3ddcfd9e67355e553a49b13db54bb3b560"
INSTALL_IDENTITY = ROOT / "refs/conformance/olmblur_current_universal_install_20260805.json"
PINNED_INSTALL_IDENTITY_SHA256 = "de40690db4fca843720e92a55a3152f69d1563da0d8df147bf6eda59d2caa20e"
PINNED_REQUEST_SHA256 = "d2e197155d36b5c99689683c865b8577920053a390b466fffcd35b3f70ff693f"
PINNED_INPUT_SHA256 = "cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4"
AUTHORITATIVE_RECORD = ROOT / "refs/conformance/olmblur_32bpc_case0001_ae_exact_20260727.json"
PINNED_AUTHORITATIVE_RECORD_SHA256 = "bfc16951adcc91fe9e1fbbdcbfd24ff3c7a0962a018fde9423463610382c0fbd"
AUTHORITATIVE_MAC_CONTROL_SHA256 = "528489da7e8d40810833dfeb60d55acf82eb6856b199e1539a099467de4af5fb"
AUTHORITATIVE_MAC_EFFECT_SHA256 = "9fd050776bec978510763dcae12df43e906f9df1dfd5713b2eeb1d0c3ccef5aa"
AUTHORITATIVE_WINDOWS_CONTROL_SHA256 = "98483e6d26127e0e4b89d655715ee81b564a534675bbe3b16b14321f29e48631"
AUTHORITATIVE_WINDOWS_EFFECT_SHA256 = "16d1702eb9b702f280c2d05e3f0b19032da76ce4fb5eb425e2f8e867dbf50cc2"
EXPECTED_PARAMS = [
    ("OLM OLM Blur-0005", 1, 129.399993896484),
    ("OLM OLM Blur-0006", 2, 100),
    ("OLM OLM Blur-0003", 3, 1),
    ("OLM OLM Blur-0004", 4, 1),
    ("OLM OLM Blur-0007", 5, 0),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_pids() -> list[int]:
    result = subprocess.run(["pgrep", "-x", "After Effects"], text=True, capture_output=True, check=False)
    return [int(item) for item in result.stdout.split() if item.isdigit()]


def exact_mapping(pid: int, binary: Path) -> bool:
    result = subprocess.run(["vmmap", str(pid)], text=True, capture_output=True, check=False, timeout=120)
    resolved = str(binary.resolve())
    return result.returncode == 0 and any(
        re.search(r"\s" + re.escape(resolved) + r"$", line)
        for line in result.stdout.splitlines()
    )


def universal_architectures(binary: Path) -> bool:
    if not binary.is_file():
        return False
    result = subprocess.run(["lipo", "-archs", str(binary)], text=True,
                            capture_output=True, check=False)
    return result.returncode == 0 and set(result.stdout.split()) == {"arm64", "x86_64"}


def same_number(left: object, right: object) -> bool:
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    return struct.pack("<f", float(left)) == struct.pack("<f", float(right))


def parameter_contract_exact() -> bool:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    record = json.loads(AUTHORITATIVE_RECORD.read_text(encoding="utf-8"))
    request_params = request["case"]["effect"]["params"][:5]
    named = record.get("contract", {}).get("params", {})
    reference_params = [named.get(name) for name in (
        "Blur Amount", "Blur Smoothness", "Number of Repeat", "Bias Direction", "Legacy")]
    if len(request_params) != 5 or any(value is None for value in reference_params):
        return False
    for requested, reference, (match_name, index, value) in zip(request_params, reference_params, EXPECTED_PARAMS):
        if requested.get("match_name") != match_name or requested.get("property_index") != index:
            return False
        if not same_number(requested.get("value"), value) or not same_number(reference, value):
            return False
    return True


def authoritative_record_exact() -> bool:
    record = json.loads(AUTHORITATIVE_RECORD.read_text(encoding="utf-8"))
    return (
        record.get("ae_exact_claim") is True
        and record.get("case_id") == "OLMBlur/case_0001"
        and record.get("windows", {}).get("loaded_plugin_proof", {}).get("aex_sha256")
        == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
        and record.get("comparison", {}).get("effect_on", {}).get("mismatched_values") == 0
        and record.get("comparison", {}).get("no_effect_control", {}).get("mismatched_values") == 0
    )


def locate_authoritative_artifacts() -> dict[str, Path]:
    wanted = {
        "mac_control": AUTHORITATIVE_MAC_CONTROL_SHA256,
        "mac_effect": AUTHORITATIVE_MAC_EFFECT_SHA256,
        "windows_control": AUTHORITATIVE_WINDOWS_CONTROL_SHA256,
        "windows_effect": AUTHORITATIVE_WINDOWS_EFFECT_SHA256,
    }
    found: dict[str, Path] = {}
    reverse = {digest: label for label, digest in wanted.items()}
    for path in (ROOT / "refs").rglob("*.exr"):
        digest = sha256(path)
        if digest in reverse:
            found[reverse[digest]] = path
    return found


def write_preflight(path: Path, *, status: str, plugin: Path, binary: Path,
                    pids: list[int], checks: dict[str, bool], reason: str | None) -> None:
    record = {
        "kind": "olmblur_case0001_pf32_current_mac_preflight",
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "status": status,
        "ae_exact_claim": False,
        "case_id": "olmblur__case_0001",
        "contract": {
            "ae": "26.3",
            "bits_per_channel": 32,
            "renderer": "SOFTWARE",
            "working_space": "None",
            "linear_blending": False,
            "outputs": ["no_effect", "effect_on"],
            "comparison": "raw FLOAT32 words against retained Windows control/effect",
        },
        "identity": {
            "plugin_bundle": str(plugin.resolve()),
            "binary": str(binary.resolve()),
            "binary_sha256_expected": PINNED_BINARY_SHA256,
            "binary_sha256_actual": sha256(binary) if binary.is_file() else None,
            "required_architectures": ["arm64", "x86_64"],
            "formal_worker_matrix": str(FORMAL_MATRIX.relative_to(ROOT)),
            "formal_worker_matrix_sha256_expected": PINNED_FORMAL_MATRIX_SHA256,
            "install_identity": str(INSTALL_IDENTITY.relative_to(ROOT)),
            "install_identity_sha256_expected": PINNED_INSTALL_IDENTITY_SHA256,
            "request": str(REQUEST.relative_to(ROOT)),
            "request_sha256_expected": PINNED_REQUEST_SHA256,
            "request_sha256_actual": sha256(REQUEST) if REQUEST.is_file() else None,
            "input": str(INPUT.relative_to(ROOT)),
            "input_sha256_expected": PINNED_INPUT_SHA256,
            "input_sha256_actual": sha256(INPUT) if INPUT.is_file() else None,
            "authoritative_record": str(AUTHORITATIVE_RECORD.relative_to(ROOT)),
            "authoritative_record_sha256_expected": PINNED_AUTHORITATIVE_RECORD_SHA256,
            "authoritative_artifact_sha256_expected": {
                "mac_control": AUTHORITATIVE_MAC_CONTROL_SHA256,
                "mac_effect": AUTHORITATIVE_MAC_EFFECT_SHA256,
                "windows_control": AUTHORITATIVE_WINDOWS_CONTROL_SHA256,
                "windows_effect": AUTHORITATIVE_WINDOWS_EFFECT_SHA256,
            },
        },
        "after_effects": {"pids": pids, "exact_binary_mapping_required": True},
        "checks": checks,
        "reason": reason,
        "render_started": False,
        "expected_raw_comparison": {
            "decoder": "scripts/audit_olmblur_32bpc_mac_candidates.py:compare",
            "channels": ["A", "B", "G", "R"],
            "dimensions": [1920, 1080],
            "required_mismatched_values": 0,
            "required_max_raw_u32_delta": 0,
            "branches": {"no_effect": "authoritative_mac_control", "effect_on": "authoritative_mac_effect"},
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-path", type=Path, default=DEFAULT_PLUGIN)
    parser.add_argument("--support-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--result-json", type=Path, required=True)
    parser.add_argument("--provenance-json", type=Path, required=True)
    parser.add_argument("--preflight-json", type=Path, required=True)
    args = parser.parse_args()

    plugin = args.plugin_path.resolve()
    binary = plugin / "Contents/MacOS/OLMBlur"
    pids = ae_pids()
    authoritative_artifacts = locate_authoritative_artifacts()
    checks = {
        "bundle_shape": plugin.name == "OLMBlur.plugin" and plugin.is_dir() and binary.is_file(),
        "binary_hash": binary.is_file() and sha256(binary) == PINNED_BINARY_SHA256,
        "universal_architectures": universal_architectures(binary),
        "formal_worker_matrix_hash": FORMAL_MATRIX.is_file() and sha256(FORMAL_MATRIX) == PINNED_FORMAL_MATRIX_SHA256,
        "install_identity_hash": INSTALL_IDENTITY.is_file() and sha256(INSTALL_IDENTITY) == PINNED_INSTALL_IDENTITY_SHA256,
        "request_hash": REQUEST.is_file() and sha256(REQUEST) == PINNED_REQUEST_SHA256,
        "input_hash": INPUT.is_file() and sha256(INPUT) == PINNED_INPUT_SHA256,
        "authoritative_record_hash": AUTHORITATIVE_RECORD.is_file() and sha256(AUTHORITATIVE_RECORD) == PINNED_AUTHORITATIVE_RECORD_SHA256,
        "authoritative_record_exact": AUTHORITATIVE_RECORD.is_file() and authoritative_record_exact(),
        "parameter_contract": AUTHORITATIVE_RECORD.is_file() and REQUEST.is_file() and parameter_contract_exact(),
        "authoritative_artifacts_complete": len(authoritative_artifacts) == 4,
        "single_ae_process": len(pids) == 1,
        "exact_binary_mapped": len(pids) == 1 and exact_mapping(pids[0], binary),
    }
    identity_ok = all(checks[key] for key in (
        "bundle_shape", "binary_hash", "universal_architectures",
        "formal_worker_matrix_hash", "install_identity_hash", "request_hash", "input_hash",
        "authoritative_record_hash", "authoritative_record_exact",
        "parameter_contract",
    ))
    if not identity_ok:
        write_preflight(args.preflight_json, status="failed_identity", plugin=plugin, binary=binary,
                        pids=pids, checks=checks, reason="pinned artifact identity mismatch")
        print("[FAIL_CLOSED] pinned OLMBlur artifact identity mismatch")
        return 1
    if not checks["authoritative_artifacts_complete"]:
        missing = sorted({"mac_control", "mac_effect", "windows_control", "windows_effect"} - set(authoritative_artifacts))
        write_preflight(args.preflight_json, status="authoritative_recapture_required", plugin=plugin, binary=binary,
                        pids=pids, checks=checks,
                        reason="20260727 authoritative EXR artifacts are absent: " + ", ".join(missing))
        print("[AUTHORITATIVE_RECAPTURE_REQUIRED] 20260727 exact-contract EXRs are absent; no render started")
        return 3
    if not checks["single_ae_process"] or not checks["exact_binary_mapped"]:
        write_preflight(args.preflight_json, status="restart_required", plugin=plugin, binary=binary,
                        pids=pids, checks=checks, reason="restart AE so the pinned OLMBlur Mach-O is mapped")
        print("[RESTART_REQUIRED] pinned OLMBlur binary is not mapped; no render started")
        return 2

    write_preflight(args.preflight_json, status="ready", plugin=plugin, binary=binary,
                    pids=pids, checks=checks, reason=None)
    command = [
        sys.executable, str(DELEGATE),
        "--plugin-path", str(plugin),
        "--support-dir", str(args.support_dir),
        "--output-dir", str(args.output_dir),
        "--result-json", str(args.result_json),
        "--provenance-json", str(args.provenance_json),
    ]
    delegated = subprocess.run(command, check=False)
    if delegated.returncode != 0:
        return delegated.returncode

    returned = json.loads(args.result_json.read_text(encoding="utf-8"))
    cases = returned.get("cases", [])
    if len(cases) != 1 or cases[0].get("id") != "olmblur__case_0001":
        print("[FAIL_CLOSED] returned case identity mismatch")
        return 1
    readback = cases[0].get("params", [])[:5]
    if len(readback) != 5 or any(
        item.get("match_name") != match_name or item.get("property_index") != index
        or not same_number(item.get("value"), value)
        for item, (match_name, index, value) in zip(readback, EXPECTED_PARAMS)
    ):
        print("[FAIL_CLOSED] returned parameter readback mismatch")
        return 1

    outputs = cases[0].get("outputs", {})
    comparisons = {
        "no_effect": compare_float_exr(authoritative_artifacts["mac_control"], Path(outputs["no_effect"]["path"])),
        "effect_on": compare_float_exr(authoritative_artifacts["mac_effect"], Path(outputs["effect_on"]["path"])),
    }
    exact = all(
        row.get("mismatched_values") == 0 and row.get("max_raw_u32_delta") == 0
        for row in comparisons.values()
    )
    comparison_record = {
        "kind": "olmblur_case0001_pf32_current_binary_raw_comparison",
        "schema_version": 1,
        "status": "raw_float32_exact" if exact else "raw_float32_mismatch",
        "ae_exact_claim": exact,
        "binary_sha256": PINNED_BINARY_SHA256,
        "windows_aex_sha256": "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b",
        "authoritative_record": str(AUTHORITATIVE_RECORD.relative_to(ROOT)),
        "reference_artifacts": {key: str(path.relative_to(ROOT)) for key, path in authoritative_artifacts.items()},
        "comparisons": comparisons,
    }
    comparison_path = args.output_dir / "current_binary_raw_comparison.json"
    comparison_path.write_text(json.dumps(comparison_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not exact:
        print(f"[FAIL_CLOSED] raw FLOAT32 mismatch: {comparison_path}")
        return 1
    print(f"[OK] raw FLOAT32 exact: {comparison_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
