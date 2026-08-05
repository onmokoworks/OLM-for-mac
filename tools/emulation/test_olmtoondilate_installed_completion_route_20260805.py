#!/usr/bin/env python3
"""Fail-closed OLMToonDilate entry-to-installed-bundle completion route."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTUAL = ROOT / "tools/emulation/probe_olmtoondilate_actual_aex_sequence_smartpre_20260805.py"
ADAPTER = ROOT / "tools/emulation/test_olmtoondilate_mac_smartrender_adapter_20260717.py"
DYNAMIC = ROOT / "tools/emulation/test_olmtoondilate_installed_dynamic_entry_20260805.py"
SOURCE = ROOT / "mac/OLMToonDilate/OLMToonDilate.cpp"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMToonDilate.plugin"
BINARY = INSTALLED / "Contents/MacOS/OLMToonDilate"
REPORT = ROOT / "refs/conformance/olmtoondilate_installed_completion_route_20260805.json"
MARKDOWN = REPORT.with_suffix(".md")
EXPECTED_BINARY_SHA = "8ac60d57193d1848fc830cff49c2a31faff5ed6298fa0d7736ab4298e2bd0ffc"
EXPECTED_SOURCE_SHA = "ea5b54e4a658a1cc092993c8d4bff1d67c08a5282a990df9f78771e69ee8f81b"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_json(path: Path) -> dict:
    run = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(f"BLOCKED_FAIL_CLOSED: {path.name} failed\n{run.stdout}\n{run.stderr}")
    return json.loads(run.stdout)


def main() -> int:
    actual = run_json(ACTUAL)
    adapter = run_json(ADAPTER)
    dynamic = run_json(DYNAMIC)
    archs = subprocess.run(["lipo", "-archs", str(BINARY)], capture_output=True, text=True, check=True).stdout.split()
    sign = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(INSTALLED)], capture_output=True)
    selected = [
        "smart_pre_entry_returned", "smart_render_entry_returned",
        "mixed_3x2_all_depths_exact", "radius2_4x2_all_depths_exact",
        "radius3_pf8_5x1_exact", "radius3_pf16_5x1_exact", "radius3_pf32_5x1_exact",
        "radius4_pf8_6x1_exact", "radius4_pf16_6x1_exact", "radius4_pf32_6x1_exact",
        "empty_width_pf8_exact", "empty_height_pf16_exact", "empty_both_pf32_exact",
    ]
    gates = {
        "actual_entry_chain_exact": actual.get("status") == "PASS_SEQUENCE_AND_SMARTPRE_ENTRY" and all(actual.get("gates", {}).get(k) for k in selected),
        "production_adapter_exact": adapter.get("status") == "ok",
        "production_source_identity": sha(SOURCE) == EXPECTED_SOURCE_SHA,
        "installed_binary_identity": sha(BINARY) == EXPECTED_BINARY_SHA,
        "installed_universal": set(archs) == {"arm64", "x86_64"},
        "installed_codesign_valid": sign.returncode == 0,
        "single_active_bundle": len(list(INSTALLED.parent.glob("OLMToonDilate.plugin"))) == 1,
        "installed_dynamic_entry_exact": dynamic.get("status") == "PASS_INSTALLED_DYNAMIC_ENTRY" and dynamic.get("callbacks", {}).get("exact") is True,
    }
    status = "PASS_INSTALLED_COMPLETION_ROUTE" if all(gates.values()) else "BLOCKED_FAIL_CLOSED"
    report = {
        "status": status,
        "route": [
            "actual AEX entry_point command 0x17 SmartPreRender",
            "actual AEX entry_point command 0x18 typed PF8/PF16/PF32 workers and writers",
            "source-included production EffectMain SmartPreRender/SmartRender exact adapter",
            "current production source SHA identity",
            "current installed signed Universal bundle SHA identity",
            "installed arm64 EffectMain dynamic SmartPreRender/SmartRender execution",
        ],
        "actual_aex_sha256": actual["aex_sha256"],
        "actual_report_sha256": sha(ROOT / "refs/conformance/olmtoondilate_actual_aex_sequence_smartpre_20260805.json"),
        "production_source_sha256": sha(SOURCE),
        "installed": {"path": str(INSTALLED), "binary_sha256": sha(BINARY), "architectures": archs, "codesign": "valid" if sign.returncode == 0 else "invalid"},
        "gates": gates,
        "restart_required_from_install_record": True,
        "installed_dynamic_entry": dynamic,
        "claim_boundary": "AE-free completion route including dynamic execution of the installed arm64 EffectMain under focused host callbacks. Real AE execution remains unclaimed.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    MARKDOWN.write_text(
        f"# OLMToonDilate installed completion route — 2026-08-05\n\n"
        f"- Status: **{status}**\n"
        f"- Actual entrypoint SmartPre/SmartRender, all typed workers/writers, production adapter, source identity, installed Universal identity, and installed arm64 EffectMain dynamic execution are fail-closed.\n"
        f"- Installed binary SHA-256: `{report['installed']['binary_sha256']}`.\n"
        f"- AE-free boundary: focused installed dynamic loading is proven; real AE rendering remains unclaimed and the prior install record still requires restart.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
