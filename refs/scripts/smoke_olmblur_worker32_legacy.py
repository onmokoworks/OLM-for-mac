#!/usr/bin/env python3
"""Replay the complete 32bpc Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker32_legacy"
MANIFEST_SHA256 = "53b4f553c3ebc6ad81c4562f251c4624ff55383fcef89c8de4db1e4674227cf5"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_fixtures() -> None:
    manifest_path = FIXTURES / "manifest.json"
    if sha256(manifest_path) != MANIFEST_SHA256:
        raise RuntimeError("OLMBlur 32bpc Legacy manifest hash changed")
    manifest = json.loads(manifest_path.read_text())
    if manifest["binary_sha256"] != AEX_SHA256:
        raise RuntimeError("OLMBlur 32bpc Legacy fixture AEX hash changed")
    cases = manifest["cases"]
    if len(cases) != 8:
        raise RuntimeError(f"expected 8 fixtures, got {len(cases)}")
    by_id = {case["id"]: case for case in cases}
    formal = [case for case in cases if case.get("formal_case") == "case0007"]
    if len(formal) != 1:
        raise RuntimeError("expected exactly one formal case0007 fixture")
    case = formal[0]
    if (case["width"], case["height"], case["blur_amount"],
            case["smoothness"], case["repeat"], case["bias_direction"]) != (
            24, 24, 5.0, 100.0, 1, 1):
        raise RuntimeError("formal case0007 parameters changed")
    if not case.get("coverage_delta", "").startswith("24x24 complete buffer"):
        raise RuntimeError("formal case0007 coverage delta is missing")
    smaller = by_id["32bpc_legacy_declared_5_mixed_alpha"]
    if ((case["width"], case["height"], case["repeat"]) ==
            (smaller["width"], smaller["height"], smaller["repeat"])):
        raise RuntimeError("formal case0007 no longer expands small-fixture coverage")
    if case["expected_sha256"] == smaller["expected_sha256"]:
        raise RuntimeError("formal case0007 unexpectedly duplicates small fixture")
    formal3 = [case for case in cases if case.get("formal_case") == "case0003"]
    if len(formal3) != 1:
        raise RuntimeError("expected exactly one formal case0003 fixture")
    case3 = formal3[0]
    if (case3["width"], case3["height"], case3["blur_amount"],
            case3["smoothness"], case3["repeat"], case3["bias_direction"]) != (
            24, 24, 248.6, 100.0, 10, 1):
        raise RuntimeError("formal case0003 parameters changed")
    if not case3.get("coverage_delta", "").startswith("24x24 complete buffer"):
        raise RuntimeError("formal case0003 coverage delta is missing")
    smaller3 = by_id["32bpc_legacy_declared_248_6_red_boundary"]
    if [case3["width"], case3["height"]] == [smaller3["width"], smaller3["height"]]:
        raise RuntimeError("formal case0003 no longer expands small-fixture coverage")
    if case3["expected_sha256"] == smaller3["expected_sha256"]:
        raise RuntimeError("formal case0003 unexpectedly duplicates small fixture")
    smoothness = by_id["32bpc_legacy_smoothness37_5_full24"]
    if (smoothness["width"], smoothness["height"], smoothness["blur_amount"],
            smoothness["smoothness"], smoothness["repeat"],
            smoothness["bias_direction"]) != (24, 24, 11.0, 37.5, 3, 2):
        raise RuntimeError("non-default Smoothness parameter fixture changed")
    if not smoothness.get("coverage_gap", "").startswith("first retained PF32 fixture"):
        raise RuntimeError("non-default Smoothness coverage gap is missing")
    if "no AE-host" not in smoothness.get("claim_boundary", ""):
        raise RuntimeError("non-default Smoothness claim boundary is missing")
    for entry in cases:
        directory = FIXTURES / entry["id"]
        if sha256(directory / "source_argb_f32.bin") != entry["source_sha256"]:
            raise RuntimeError(f"source hash mismatch: {entry['id']}")
        if sha256(directory / "expected_argb_f32.bin") != entry["expected_sha256"]:
            raise RuntimeError(f"expected hash mismatch: {entry['id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-fixtures", action="store_true")
    args = parser.parse_args()
    if args.refresh_fixtures:
        subprocess.run(
            ["python3", "tools/emulation/test_olmblur_worker32_legacy.py",
             "--export"], cwd=ROOT, check=True
        )
    verify_fixtures()
    with tempfile.TemporaryDirectory(prefix="olmblur-worker32-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_fullworker_helper.cpp",
                "core/olmblur_worker32_legacy.cpp",
                "tools/emulation/replay_olmblur_worker32_legacy.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [str(binary), str(FIXTURES)], cwd=ROOT, check=True
        )
    print("[OK] OLMBlur 32bpc Legacy worker matches 8 retained complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
