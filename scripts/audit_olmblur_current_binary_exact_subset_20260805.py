#!/usr/bin/env python3
"""Fail-closed audit of the OLMBlur current-binary PF32 exact subset.

Only case_0004..case_0007 are admitted.  case_0001 remains a pending fresh
render in run_olmblur_case0001_pf32_current_mac_20260805.py; cases 0002/0003
also used different Mach-O hashes and are deliberately excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINARY = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMBlur.plugin/Contents/MacOS/OLMBlur"
CURRENT_SHA256 = "c6a9e54b1760fc2c916f4551367666b58c100520b2c6644ebd809d60e3d9d83e"
WINDOWS_AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
EVIDENCE_SHA256 = {
    4: "664ce93195accc624d96ae81d25d138d86a799592d95453b5053c5be181ae284",
    5: "cdb233198f44364c913fa1efbaf2b238918c087578b499fd2d89bceddbcf794b",
    6: "542fd65d9d3730dabd564ea1c486e4c437016f49c32becae34ecd4dbc3b31cd0",
    7: "04759826e849250c33b0bbcca66027a0755b32bb92115eaa81d614fd3f1760ec",
}
EXPECTED_PARAMS = {
    4: {"Blur Amount": 125.6, "Blur Amount readback": 125.599998474121,
        "Blur Smoothness": 100, "Number of Repeat": 4, "Bias Direction": 1, "Legacy": 0},
    5: {"Blur Amount": 5, "Blur Amount readback": 5, "Blur Smoothness": 100,
        "Number of Repeat": 2, "Bias Direction": 1, "Legacy": 0},
    6: {"Blur Amount": 5, "Blur Amount readback": 5, "Blur Smoothness": 100,
        "Number of Repeat": 10, "Bias Direction": 1, "Legacy": 0},
    7: {"Blur Amount": 5, "Blur Amount readback": 5, "Blur Smoothness": 100,
        "Number of Repeat": 1, "Bias Direction": 1, "Legacy": 1},
}
HASH = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(binary: Path) -> dict:
    checks: dict[str, bool] = {
        "installed_binary_present": binary.is_file(),
        "installed_binary_hash": binary.is_file() and sha256(binary) == CURRENT_SHA256,
        "declared_subset_exactly_0004_through_0007": set(EVIDENCE_SHA256) == {4, 5, 6, 7},
        "case0001_excluded_pending_fresh_current_binary_render": 1 not in EVIDENCE_SHA256,
    }
    rows = []
    for number, evidence_hash in EVIDENCE_SHA256.items():
        path = ROOT / f"refs/conformance/olmblur_32bpc_case{number:04d}_ae_exact_20260727.json"
        prefix = f"case{number:04d}"
        checks[f"{prefix}_evidence_hash"] = path.is_file() and sha256(path) == evidence_hash
        if not path.is_file():
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        contract = row.get("contract", {})
        mac = row.get("mac", {})
        windows = row.get("windows", {})
        comparisons = row.get("comparison", {})
        checks[f"{prefix}_claim"] = row.get("ae_exact_claim") is True and row.get("status") == "raw_float32_ae_exact"
        checks[f"{prefix}_scope"] = (
            row.get("case_id") == f"OLMBlur/case_{number:04d}"
            and row.get("ae_version") == "26.3x87"
            and contract.get("bits_per_channel") == 32
            and contract.get("renderer") == {"name": "SOFTWARE", "raw": 1816}
            and contract.get("working_space_raw") == "None"
            and contract.get("linear_blending") is False
        )
        checks[f"{prefix}_params"] = contract.get("params") == EXPECTED_PARAMS[number]
        checks[f"{prefix}_mac_module_hash"] = mac.get("loaded_plugin_proof", {}).get("module_sha256") == CURRENT_SHA256
        checks[f"{prefix}_windows_aex_hash"] = windows.get("loaded_plugin_proof", {}).get("aex_sha256") == WINDOWS_AEX_SHA256
        checks[f"{prefix}_reference_hashes"] = all(
            isinstance(branch.get("sha256"), str) and HASH.fullmatch(branch["sha256"])
            for side in (mac.get("outputs", {}), windows.get("outputs", {}))
            for branch in (side.get("no_effect_control", {}), side.get("effect_on", {}))
        )
        checks[f"{prefix}_raw_exact"] = all(
            comparisons.get(branch) == {
                "height": 1080, "max_raw_u32_delta": 0, "mismatched_values": 0,
                "total_values": 8294400, "width": 1920,
            }
            for branch in ("no_effect_control", "effect_on")
        )
        rows.append({
            "case_id": row.get("case_id"),
            "evidence": str(path.relative_to(ROOT)),
            "evidence_sha256": evidence_hash,
            "params": contract.get("params"),
            "mac_outputs": mac.get("outputs"),
            "windows_outputs": windows.get("outputs"),
        })
    exact = all(checks.values()) and len(rows) == 4
    return {
        "kind": "olmblur_current_binary_pf32_exact_subset_audit",
        "schema_version": 1,
        "status": "exact_retained_subset" if exact else "failed_closed",
        "ae_exact_claim": exact,
        "binary": {"path": str(binary.resolve()), "sha256_expected": CURRENT_SHA256,
                   "sha256_actual": sha256(binary) if binary.is_file() else None},
        "declared_exact_cases": ["case_0004", "case_0005", "case_0006", "case_0007"],
        "excluded": {
            "case_0001": "pending fresh current-binary hash-bound Mac AE render",
            "case_0002": "retained AE exact proof uses a different Mac module hash",
            "case_0003": "retained AE exact proof uses a different Mac module hash",
        },
        "checks": checks,
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.binary.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "exact_retained_subset" else 1


if __name__ == "__main__":
    raise SystemExit(main())
