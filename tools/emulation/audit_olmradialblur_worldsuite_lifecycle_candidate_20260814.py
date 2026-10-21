#!/usr/bin/env python3
"""Validate the isolated Universal RadialBlur WorldSuite-lifecycle candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMRadialBlur/OLMRadialBlur.cpp"
HANDOFF = ROOT / "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814"
BUNDLE = HANDOFF / "Product/OLMRadialBlur.plugin"
EXE = BUNDLE / "Contents/MacOS/OLMRadialBlur"
REPORT = HANDOFF / "build_identity.json"
README = HANDOFF / "README.md"
SOURCE_SHA256 = "b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1"
BINARY_SHA256 = "9be59d18601dc2b031335f4fec8c8c6a1eb13a4888bf0f228efa65e2d5b676b5"
INVENTORY_SHA256 = "026c58d43c775a7be9a0e8f74ab9dfdd1dca7b4a96fe12b389ae2ac81b35f845"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def inventory() -> list[dict]:
    rows = []
    for path in sorted(p for p in BUNDLE.rglob("*") if p.is_file()):
        rows.append({"path": str(path.relative_to(BUNDLE)), "bytes": path.stat().st_size,
                     "sha256": sha(path)})
    return rows


def canonical_inventory(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def slice_info(arch: str) -> dict:
    load = run("otool", "-arch", arch, "-l", str(EXE))
    match = re.search(r"LC_BUILD_VERSION\s+cmdsize\s+\d+\s+platform\s+\d+\s+minos\s+([0-9.]+)\s+sdk\s+([0-9.]+)", load)
    if not match:
        raise RuntimeError(f"missing LC_BUILD_VERSION for {arch}")
    exports = sorted(line.strip() for line in run("nm", "-arch", arch, "-gU", str(EXE)).splitlines()
                     if line.strip().endswith((" _EffectMain", " _PluginDataEntryFunction2")))
    return {"arch": arch, "minos": match.group(1), "sdk": match.group(2), "exports": exports}


def build_report() -> dict:
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)], check=True,
                   capture_output=True, text=True)
    archs = run("lipo", "-archs", str(EXE)).split()
    plist = plistlib.loads((BUNDLE / "Contents/Info.plist").read_bytes())
    rows = inventory()
    return {
        "schema": "olm.radialblur-worldsuite-lifecycle-candidate/1",
        "status": "pass",
        "source": {"path": str(SOURCE.relative_to(ROOT)), "sha256": sha(SOURCE)},
        "bundle": {"path": str(BUNDLE.relative_to(ROOT)), "binary_sha256": sha(EXE),
                   "architectures": archs, "info_minimum_system": plist["LSMinimumSystemVersion"],
                   "inventory": rows, "inventory_sha256": canonical_inventory(rows)},
        "slices": [slice_info(arch) for arch in ("arm64", "x86_64")],
        "signature": {"strict_deep_valid": True, "kind": "ad-hoc", "developer_id": False,
                      "notarized": False},
        "scope": {"installed": False, "after_effects_launched": False,
                  "numerical_claim_owned_by_separate_closures": True},
    }


def validate(report: dict) -> None:
    assert set(report) == {"schema", "status", "source", "bundle", "slices", "signature", "scope"}
    assert report["schema"] == "olm.radialblur-worldsuite-lifecycle-candidate/1"
    assert report["status"] == "pass"
    assert report["source"] == {"path": "mac/OLMRadialBlur/OLMRadialBlur.cpp", "sha256": SOURCE_SHA256}
    assert sha(SOURCE) == SOURCE_SHA256
    bundle = report["bundle"]
    assert set(bundle) == {"path", "binary_sha256", "architectures", "info_minimum_system",
                           "inventory", "inventory_sha256"}
    assert bundle["path"] == "handoffs/olmradialblur_worldsuite_lifecycle_candidate_20260814/Product/OLMRadialBlur.plugin"
    assert bundle["binary_sha256"] == BINARY_SHA256 == sha(EXE)
    assert bundle["architectures"] == ["x86_64", "arm64"]
    assert bundle["info_minimum_system"] == "11.0"
    assert bundle["inventory"] == inventory()
    assert bundle["inventory_sha256"] == canonical_inventory(bundle["inventory"])
    if INVENTORY_SHA256 != "PENDING":
        assert bundle["inventory_sha256"] == INVENTORY_SHA256
    assert [row["arch"] for row in report["slices"]] == ["arm64", "x86_64"]
    for row in report["slices"]:
        assert row["minos"] == "11.0" and row["sdk"] == "26.2"
        assert len(row["exports"]) == 2
        assert {line.rsplit(" ", 1)[-1] for line in row["exports"]} == {
            "_EffectMain", "_PluginDataEntryFunction2"}
    assert report["signature"] == {"strict_deep_valid": True, "kind": "ad-hoc",
                                    "developer_id": False, "notarized": False}
    assert report["scope"] == {"installed": False, "after_effects_launched": False,
                                "numerical_claim_owned_by_separate_closures": True}
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(BUNDLE)], check=True,
                   capture_output=True, text=True)


def readme(report: dict) -> str:
    return f"""# OLMRadialBlur WorldSuite lifecycle candidate

Status: `{report['status']}`

- Source: `{SOURCE_SHA256}`
- Universal binary: `{BINARY_SHA256}`
- Architectures: `x86_64 arm64`
- Minimum system: `11.0` in Info.plist and both slices
- Signature: strict-valid ad-hoc only; no Developer ID or notarization claim

This candidate is not installed and After Effects was not launched. Numerical
claims remain owned by the separate Type1/Type3 raw-exact closures.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        report = build_report()
        validate(report)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        README.write_text(readme(report), encoding="utf-8")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    validate(report)
    assert README.read_text(encoding="utf-8") == readme(report)
    print(json.dumps({"status": report["status"], "binary_sha256": BINARY_SHA256}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
