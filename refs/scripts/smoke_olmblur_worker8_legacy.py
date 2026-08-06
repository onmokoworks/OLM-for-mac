#!/usr/bin/env python3
"""Replay retained complete 8bpc Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker8_legacy"
MANIFEST_SHA256 = "144d0f8bfdccc6d8d6aa48344addb4dc9b10b280cbdfd585059c35d9f2bf4fa1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-fixtures", action="store_true")
    args = parser.parse_args()
    if args.refresh_fixtures:
        subprocess.run([sys.executable, "tools/emulation/test_olmblur_worker8_legacy.py", "--export"], cwd=ROOT, check=True)
    manifest_path = FIXTURES / "manifest.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["binary_sha256"] == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    assert len(manifest["cases"]) == 8
    by_id = {row["id"]: row for row in manifest["cases"]}
    smoothness = by_id["8bpc_legacy_smoothness43_75_byte_boundaries"]
    assert (smoothness["width"], smoothness["height"],
            smoothness["blur_amount"], smoothness["smoothness"],
            smoothness["repeat"], smoothness["bias_direction"]) == (
            19, 13, 9.0, 43.75, 3, 2)
    assert smoothness["pattern"] == "byte_boundaries"
    assert smoothness["partial_alpha_values"] == [1, 127, 128, 254]
    assert smoothness["coverage_gap"].startswith("first retained PF8 fixture")
    assert "no AE-host" in smoothness["claim_boundary"]
    for row in manifest["cases"]:
        directory = FIXTURES / row["id"]
        assert hashlib.sha256((directory / "source_argb.bin").read_bytes()).hexdigest() == row["source_sha256"]
        assert hashlib.sha256((directory / "expected_argb.bin").read_bytes()).hexdigest() == row["expected_sha256"]
    with tempfile.TemporaryDirectory(prefix="olmblur-worker8-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run([
            "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
            "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker8_legacy.cpp",
            "tools/emulation/replay_olmblur_worker8_legacy.cpp", "-o", str(binary),
        ], cwd=ROOT, check=True)
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 8bpc Legacy production worker matches 8 retained complete AEX fixtures, including non-default Smoothness byte boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
