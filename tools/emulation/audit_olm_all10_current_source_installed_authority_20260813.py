#!/usr/bin/env python3
"""Audit the current production-source -> candidate -> installed chain for all 10 OLM plug-ins.

Default operation is read-only and validates both live state and the persisted report.
Use --write only when intentionally refreshing the canonical report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
IDENTITY = ROOT / "refs/conformance/olm_installed_identity_manifest_20260806.json"
REPORT = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.json"
MARKDOWN = ROOT / "refs/conformance/olm_all10_current_source_installed_authority_20260813.md"

EXPECTED_IDENTITY_SHA256 = "94c6a1eff87e11705a65be638953cb134ff64bd0d919e8501338601aab333650"
EXPECTED: dict[str, dict[str, str]] = {
    "OLMBlur": {
        "source": "mac/OLMBlur/OLMBlur.cpp",
        "source_sha256": "22eb712a2485e080d811d2c064fe78bd521ee25434ece9a290a2d9b7b6e1fdd7",
        "authority": "handoffs/olmblur_retained_public_universal_candidate_v4_20260813/build_identity.json",
        "binary_sha256": "ecdf3d93b4b38fe71f4b66f717079aa86b961205d0a3f1b5b7edbd29e353284d",
    },
    "ColorKeep": {
        "source": "mac/ColorKeep/ColorKeep.cpp",
        "source_sha256": "d1c443042998e466b021d6fd2351537a2be63fe95d3e79a2089d82f78217bac3",
        "authority": "refs/conformance/colorkeep_source_bound_complete_union_install_20260813.json",
        "binary_sha256": "dae59a6faf54ed18ac803ad042be2cdab688c5f814edf322d64c108d5247f46d",
    },
    "OLMColorKey": {
        "source": "mac/OLMColorKey/OLMColorKey.cpp",
        "source_sha256": "7c66240d5813e240663d06fe342d45b73b9b2ce2f2d8b0852ffe7f73351e4001",
        "authority": "refs/conformance/olmcolorkey_toggle24_transactional_install_20260814.json",
        "binary_sha256": "701ae9192e19d3e97dd33450e37ae97d90d9be5803ab663405507ed5e3659ca7",
    },
    "OLMDirectionalBlur": {
        "source": "mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp",
        "source_sha256": "494116880d037a0d44a48b0e0ebe0fc5358b4cd8892b90ca8c61ea8a7bb2e845",
        "authority": "handoffs/olmdirectionalblur_testseam_compat_candidate_20260814/build_identity.json",
        "binary_sha256": "856ab700df0881cfb039e9c9d0675bf46a7e92b56e8cb0e311d820fd719bc0de",
    },
    "OLMDistanceGradation": {
        "source": "mac/OLMDistanceGradation/OLMDistanceGradation.cpp",
        "source_sha256": "06ffc5b7a2af5cf54a2503d3bf03f9baf2269acbf1277f034937ac79c4a7aba5",
        "authority": "refs/conformance/olmdistancegradation_power_failclose_incremental_install_identity_20260812.json",
        "binary_sha256": "231421e4a0c1607a70947778d99d748baefe07078b7e1145f4a4700268116605",
    },
    "OLMKiraKira": {
        "source": "mac/OLMKiraKira/OLMKiraKira.cpp",
        "source_sha256": "f251b19150a0b490d58cf6bece4c40fe9403f9bd36849cfe8c89ffbd14fc96c2",
        "authority": "refs/conformance/olmkirakira_worldsuite_incremental_install_identity_20260814.json",
        "binary_sha256": "edd6953ff0a86efa550ffd8a5be050cb200342ad68427519c092bcac578596a7",
    },
    "OLMRadialBlur": {
        "source": "mac/OLMRadialBlur/OLMRadialBlur.cpp",
        "source_sha256": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
        "authority": "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/build_identity.json",
        "binary_sha256": "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5",
    },
    "OLMSmoother": {
        "source": "mac/OLMSmoother/Mac/OLMSmoother_port.cpp",
        "source_sha256": "c8c7b7728553ee4ccaadc7ef802be40e607d7e7a7b829958d4b8dfab80f633dc",
        "authority": "handoffs/olmsmoother_source_bound_atomic_universal_candidate_v3_20260813/build_identity.json",
        "binary_sha256": "f416579eeb61b73da683437d382f786781e6ecdf27d9c4fc52f3ad1d55577162",
    },
    "OLMSmoother2": {
        "source": "mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp",
        "source_sha256": "c710902f5928c67ae72e2e4ba445e801acd4a3f229f04d23ab6a1cd56cf73168",
        "authority": "refs/conformance/olmsmoother2_pf8_pf16_pf32_transactional_install_20260814.json",
        "binary_sha256": "c8ea1f0e7dbe7398006578b91e01adfcea975a8c8a3244657ea934eda587c53f",
    },
    "OLMToonDilate": {
        "source": "mac/OLMToonDilate/OLMToonDilate.cpp",
        "source_sha256": "ded9eaab6b660044c9035f3aa0d9660f86086ec2e451c97c9ee0c1115574464b",
        "authority": "refs/conformance/olmtoondilate_ded9_incremental_install_identity_20260813.json",
        "binary_sha256": "5bbe693106072ceff14a1c1ae5a0d64815cddde58356c57575d29e516479036e",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(bundle: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((p for p in bundle.rglob("*") if p.is_file()), key=lambda p: p.relative_to(bundle).as_posix()):
        rows.append({
            "path": path.relative_to(bundle).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return rows


def executable(bundle: Path) -> Path:
    info = json.loads(subprocess.check_output(
        ["plutil", "-convert", "json", "-o", "-", str(bundle / "Contents/Info.plist")],
        text=True,
    ))
    return bundle / "Contents/MacOS" / info["CFBundleExecutable"]


def run_ok(command: list[str]) -> bool:
    return subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def json_contains(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return value == needle
    if isinstance(value, list):
        return any(json_contains(item, needle) for item in value)
    if isinstance(value, dict):
        return any(json_contains(item, needle) for item in value.values())
    return False


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        result = subprocess.run(["pgrep", "-x", name], text=True, capture_output=True)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pgrep failed for {name}")
        found.extend(f"{name}:{pid}" for pid in result.stdout.split() if pid.isdigit())
    return found


def generate() -> dict[str, Any]:
    identity_sha = sha256(IDENTITY)
    if identity_sha != EXPECTED_IDENTITY_SHA256:
        raise RuntimeError(f"accepted identity drift: {identity_sha}")
    identity = json.loads(IDENTITY.read_text())
    rows = identity.get("plugins")
    if not isinstance(rows, list) or len(rows) != 10:
        raise RuntimeError("accepted identity must contain exactly ten plug-ins")
    by_name = {row["plugin"]: row for row in rows}
    if set(by_name) != set(EXPECTED):
        raise RuntimeError("accepted identity plug-in set drift")

    plugins: list[dict[str, Any]] = []
    for name in sorted(EXPECTED):
        expected = EXPECTED[name]
        row = by_name[name]
        source = ROOT / expected["source"]
        authority = ROOT / expected["authority"]
        candidate = Path(row["source_bundle"])
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        installed = Path(row["installed_bundle"])
        if not source.is_file() or not authority.is_file() or not candidate.is_dir() or not installed.is_dir():
            raise RuntimeError(f"missing authority input for {name}")
        source_sha = sha256(source)
        authority_json = json.loads(authority.read_text())
        candidate_exe = executable(candidate)
        installed_exe = executable(installed)
        candidate_sha = sha256(candidate_exe)
        installed_sha = sha256(installed_exe)
        candidate_inventory = inventory(candidate)
        installed_inventory = inventory(installed)
        archs = subprocess.check_output(["lipo", "-archs", str(installed_exe)], text=True).split()
        checks = {
            "source_sha_exact": source_sha == expected["source_sha256"],
            "authority_binds_source": json_contains(authority_json, expected["source_sha256"]),
            "authority_binds_binary": json_contains(authority_json, expected["binary_sha256"]),
            "manifest_binary_exact": row["sha256"] == expected["binary_sha256"] == row["source_sha256"],
            "candidate_binary_exact": candidate_sha == expected["binary_sha256"],
            "installed_binary_exact": installed_sha == expected["binary_sha256"],
            "candidate_installed_full_inventory_exact": candidate_inventory == installed_inventory,
            "installed_count_one": row["installed_bundle_count"] == 1,
            "universal_exact": sorted(archs) == ["arm64", "x86_64"],
            "codesign_strict": run_ok(["codesign", "--verify", "--deep", "--strict", str(installed)]),
        }
        if not all(checks.values()):
            raise RuntimeError(f"authority-chain failure for {name}: {checks}")
        plugins.append({
            "plugin": name,
            "source": expected["source"],
            "source_sha256": source_sha,
            "authority": expected["authority"],
            "authority_sha256": sha256(authority),
            "candidate_bundle": str(candidate.relative_to(ROOT)) if candidate.is_relative_to(ROOT) else str(candidate),
            "installed_bundle": str(installed),
            "binary_sha256": installed_sha,
            "architectures": archs,
            "inventory_file_count": len(installed_inventory),
            "checks": checks,
        })

    processes = ae_processes()
    if processes:
        raise RuntimeError(f"AE-family processes are running: {processes}")
    return {
        "schema": "olm.all10-current-source-installed-authority/1",
        "status": "pass_all10_current_source_candidate_installed_exact_ae_deferred",
        "accepted_identity": {
            "path": str(IDENTITY.relative_to(ROOT)),
            "sha256": identity_sha,
            "plugin_count": 10,
        },
        "plugins": plugins,
        "after_effects_processes": [],
        "scope": {
            "production_source_to_build_authority_bound": True,
            "candidate_to_installed_full_inventory_exact": True,
            "installed_universal_strict_codesign": True,
            "after_effects_launched": False,
            "after_effects_checkpoint_deferred": True,
            "numerical_claim_added": False,
            "developer_id_or_notarization_claimed": False,
        },
    }


def validate_schema(report: dict[str, Any]) -> None:
    if set(report) != {"schema", "status", "accepted_identity", "plugins", "after_effects_processes", "scope"}:
        raise RuntimeError("report top-level schema drift")
    if report["schema"] != "olm.all10-current-source-installed-authority/1":
        raise RuntimeError("report schema mismatch")
    if report["status"] != "pass_all10_current_source_candidate_installed_exact_ae_deferred":
        raise RuntimeError("report status mismatch")
    if len(report["plugins"]) != 10 or {row["plugin"] for row in report["plugins"]} != set(EXPECTED):
        raise RuntimeError("report plug-in set mismatch")
    expected_plugin_keys = {
        "plugin", "source", "source_sha256", "authority", "authority_sha256",
        "candidate_bundle", "installed_bundle", "binary_sha256", "architectures",
        "inventory_file_count", "checks",
    }
    expected_check_keys = {
        "source_sha_exact", "authority_binds_source", "authority_binds_binary",
        "manifest_binary_exact", "candidate_binary_exact", "installed_binary_exact",
        "candidate_installed_full_inventory_exact", "installed_count_one",
        "universal_exact", "codesign_strict",
    }
    for row in report["plugins"]:
        if set(row) != expected_plugin_keys or set(row["checks"]) != expected_check_keys:
            raise RuntimeError("report row schema drift")
        if not all(row["checks"].values()):
            raise RuntimeError("report contains failed check")
    if report["after_effects_processes"] != []:
        raise RuntimeError("report AE process boundary mismatch")
    expected_scope = {
        "production_source_to_build_authority_bound": True,
        "candidate_to_installed_full_inventory_exact": True,
        "installed_universal_strict_codesign": True,
        "after_effects_launched": False,
        "after_effects_checkpoint_deferred": True,
        "numerical_claim_added": False,
        "developer_id_or_notarization_claimed": False,
    }
    if report["scope"] != expected_scope:
        raise RuntimeError("report scope mismatch")


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OLM all-10 current source → installed authority (2026-08-13)",
        "",
        f"Status: `{report['status']}`",
        "",
        "Each current production source is bound by its plug-in-specific build/install authority to the exact candidate executable named by the accepted identity manifest. Candidate and installed full bundle inventories are identical for all ten plug-ins; every installed executable is arm64+x86_64 and passes strict/deep code-sign verification.",
        "",
        "| Plug-in | source SHA-256 | installed executable SHA-256 |",
        "|---|---|---|",
    ]
    for row in report["plugins"]:
        lines.append(f"| {row['plugin']} | `{row['source_sha256']}` | `{row['binary_sha256']}` |")
    lines += [
        "",
        "Boundary: this is a hostless identity/provenance audit. It launches no After Effects process, adds no numerical claim, and does not claim Developer ID signing or notarization. The current-identity AE checkpoint remains deliberately deferred for a later batched run.",
        "",
    ]
    return "\n".join(lines)


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
            raise RuntimeError("persisted authority report is missing; use --write intentionally")
        persisted = json.loads(REPORT.read_text())
        validate_schema(persisted)
        if persisted != live:
            raise RuntimeError("persisted authority report differs from live state")
        if MARKDOWN.read_text() != markdown(live):
            raise RuntimeError("persisted authority markdown differs from live state")
    print("PASS_ALL10_CURRENT_SOURCE_CANDIDATE_INSTALLED_EXACT_AE_DEFERRED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL_ALL10_CURRENT_SOURCE_AUTHORITY: {exc}", file=sys.stderr)
        raise
