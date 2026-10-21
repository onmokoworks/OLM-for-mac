#!/usr/bin/env python3
"""Aggregate current installed Radial Type1 and Type3 public-entry closures."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TYPE1 = ROOT / "refs/conformance/olmradialblur_current_installed_type1_complete_union_20260814.json"
TYPE3 = ROOT / "refs/conformance/olmradialblur_current_installed_type3_all_depth_closure_20260813.json"
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
INSTALLED = Path.home() / "Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/OLMRadialBlur.plugin/Contents/MacOS/OLMRadialBlur"
REPORT = ROOT / "refs/conformance/olmradialblur_current_installed_complete_public_union_20260814.json"
NOTE = REPORT.with_suffix(".md")
PINS = {
    "production_source_sha256": "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1",
    "installed_binary_sha256": "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5",
    "type1_report_sha256": "58f02746c8e6d364fc4bec2f60329cf73168be5f2309ba2d80cef4720bb1c444",
    "type3_report_sha256": "2e06b303db9541789f2b9d88de38310968859e9d3d0e5bf03d5ce8c5c70e3c6f",
}
STATUS = "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_COMPLETE_TYPE1_TYPE3_PUBLIC_UNION_AE_FREE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ae_processes() -> list[str]:
    found: list[str] = []
    for name in ("After Effects", "AfterFX", "aerender"):
        run = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if run.returncode == 0:
            found.extend(f"{name}:{pid}" for pid in run.stdout.split())
    return found


def generate() -> dict[str, Any]:
    identities = {
        "production_source_sha256": sha256(SOURCE),
        "installed_binary_sha256": sha256(INSTALLED),
        "type1_report_sha256": sha256(TYPE1),
        "type3_report_sha256": sha256(TYPE3),
    }
    if identities != PINS:
        raise RuntimeError(f"Radial complete union authority drift: {identities}")
    type1 = json.loads(TYPE1.read_text())
    type3 = json.loads(TYPE3.read_text())
    if type1.get("status") != "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_TYPE1_COMPLETE_UNION_AE_FREE":
        raise RuntimeError("Type1 installed closure status drift")
    if type3.get("status") != "PASS_OLMRADIALBLUR_CURRENT_INSTALLED_TYPE3_ALL_DEPTH_PUBLIC_AE_FREE":
        raise RuntimeError("Type3 installed closure status drift")
    if type1.get("summary", {}).get("positive_cells_per_slice") != 106 or type3.get("summary", {}).get("public_exact_cells_per_slice") != 45:
        raise RuntimeError("Radial installed positive partition drift")
    if type1.get("after_effects_processes") != [] or type3.get("after_effects_processes") != []:
        raise RuntimeError("Radial source report AE boundary drift")
    processes = ae_processes()
    if processes:
        raise RuntimeError(f"After Effects must remain stopped: {processes}")
    return {
        "schema": "olmradialblur.current-installed-complete-public-union/1",
        "status": STATUS,
        "claim_boundary": (
            "Both installed Universal slices reproduce the complete currently admitted Type1 and "
            "Type3 fixed-fixture public union through Classic and Smart: 106 Type1 cells plus 45 "
            "Type3 source/Layer pairs per slice. This aggregate adds no source, tuple, geometry or "
            "native-AE generalization."
        ),
        "identities": identities,
        "closures": {
            "type1": str(TYPE1.relative_to(ROOT)),
            "type3": str(TYPE3.relative_to(ROOT)),
        },
        "summary": {
            "exact_public_cells_per_slice": 151,
            "exact_public_cells_total": 302,
            "type1_cells_per_slice": 106,
            "type3_cells_per_slice": 45,
            "type1_mutation_rejects_per_slice": 57,
            "type3_reject_control_sets_per_slice": 45,
            "classic_smart_padded_output_exact": True,
            "installed_architectures": ["arm64", "x86_64"],
        },
        "after_effects_processes": [],
        "scope": {
            "installed_arm64": True,
            "installed_x86_64": True,
            "native_after_effects": False,
            "arbitrary_type1_or_type3": False,
            "production_or_install_changed": False,
        },
    }


def validate(value: dict[str, Any]) -> bool:
    try:
        return value == generate()
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def markdown(report: dict[str, Any]) -> str:
    return f"""# OLMRadialBlur current installed complete public union

Status: `{report['status']}`

Both installed Universal slices replay the complete bounded public union:
106 exact-source Type1 cells and 45 exact source/Layer Type3 pairs per slice,
for 151 cells per slice and 302 total Classic/Smart paired relations.

This is AE-free installed-Mach-O evidence. Unlisted inputs remain fail-closed.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = generate()
    if args.write:
        REPORT.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
        NOTE.write_text(markdown(current))
    saved = json.loads(REPORT.read_text())
    if saved != current or NOTE.read_text() != markdown(saved):
        raise RuntimeError("persisted Radial complete union drift")
    print(STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
