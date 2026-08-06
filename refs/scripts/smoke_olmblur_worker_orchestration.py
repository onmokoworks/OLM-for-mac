#!/usr/bin/env python3
"""Replay complete 8bpc Non-Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker_orchestration"
MANIFEST_SHA256 = "40b3225900bb679e03c1a675c1a3877df2335c5822731ae0fe7bed7edcee9b52"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-fixtures", action="store_true")
    args = parser.parse_args()
    if args.refresh_fixtures:
        subprocess.run(
            [sys.executable, "tools/emulation/test_olmblur_worker_orchestration.py", "--export"],
            cwd=ROOT, check=True,
        )
    manifest_path = FIXTURES / "manifest.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["binary_sha256"] == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    assert len(manifest["cases"]) == 4
    for row in manifest["cases"]:
        directory = FIXTURES / row["id"]
        assert hashlib.sha256((directory / "source_argb.bin").read_bytes()).hexdigest() == row["source_sha256"]
        assert hashlib.sha256((directory / "expected_argb.bin").read_bytes()).hexdigest() == row["expected_sha256"]
    with tempfile.TemporaryDirectory(prefix="olmblur-worker-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_helper.cpp", "core/olmblur_worker_orchestration.cpp",
                "tools/emulation/replay_olmblur_worker_orchestration.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 8bpc Non-Legacy production worker matches 4 retained complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
