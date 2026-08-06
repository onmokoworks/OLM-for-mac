#!/usr/bin/env python3
"""Verify and replay retained complete 16bpc Legacy OLMBlur fixtures."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker16_legacy"
MANIFEST_SHA256 = "11ac4c8600f41ce8e3dcbb6aa41999817a3d4dc4c089d563e8f3b1eeb30b53d6"
AEX_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-fixtures", action="store_true")
    args = parser.parse_args()
    if args.refresh_fixtures:
        subprocess.run([sys.executable,
                        "tools/emulation/test_olmblur_worker16_legacy.py",
                        "--export"], cwd=ROOT, check=True)
    manifest_path = FIXTURES / "manifest.json"
    assert sha256(manifest_path) == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["binary_sha256"] == AEX_SHA256
    assert len(manifest["cases"]) == 4
    by_id = {row["id"]: row for row in manifest["cases"]}
    smoothness = by_id["16bpc_legacy_smoothness62_5_word_boundaries"]
    assert (smoothness["width"], smoothness["height"],
            smoothness["blur_amount"], smoothness["smoothness"],
            smoothness["repeat"], smoothness["bias_direction"]) == (
            20, 16, 7.0, 62.5, 4, 1)
    assert smoothness["pattern"] == "word_boundaries"
    assert smoothness["coverage_gap"].startswith("first retained PF16 fixture")
    assert "no AE-host" in smoothness["claim_boundary"]
    for row in manifest["cases"]:
        directory = FIXTURES / row["id"]
        assert sha256(directory / "source_argb16.bin") == row["source_sha256"]
        assert sha256(directory / "expected_argb16.bin") == row["expected_sha256"]
    with tempfile.TemporaryDirectory(prefix="olmblur-worker16-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(["c++", "-std=c++17", "-O2", "-ffp-contract=off", "-fno-fast-math", "-Icore", "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker16_legacy.cpp", "tools/emulation/replay_olmblur_worker16_legacy.cpp", "-o", str(binary)], cwd=ROOT, check=True)
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 16bpc Legacy worker matches 4 retained complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
