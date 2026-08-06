#!/usr/bin/env python3
"""Replay complete 32bpc Non-Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker32_nonlegacy"
MANIFEST_SHA256 = "03e9d5386c96c75f6173a438c629c47bfb30bef4ad40369dad3e1e032a03e2f8"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-fixtures", action="store_true")
    args = parser.parse_args()
    if args.refresh_fixtures:
        subprocess.run(
            [sys.executable, "tools/emulation/test_olmblur_worker32_nonlegacy.py", "--export"],
            cwd=ROOT, check=True,
        )
    manifest_path = FIXTURES / "manifest.json"
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST_SHA256
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["binary_sha256"] == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    assert len(manifest["cases"]) == 12
    formal4 = [row for row in manifest["cases"] if row.get("formal_case") == "case0004"]
    assert len(formal4) == 1
    assert formal4[0]["coverage_delta"].startswith("24x24 full buffer")
    tiny = next(row for row in manifest["cases"] if row["id"] == "32bpc_nonlegacy_amount1256_repeat4")
    assert [formal4[0]["width"], formal4[0]["height"]] != [tiny["width"], tiny["height"]]
    assert formal4[0]["expected_sha256"] != tiny["expected_sha256"]
    formal5 = [row for row in manifest["cases"] if row.get("formal_case") == "case0005"]
    assert len(formal5) == 1
    assert formal5[0]["coverage_delta"].startswith("24x24 full buffer")
    tiny5 = next(row for row in manifest["cases"] if row["id"] == "32bpc_nonlegacy_amount5_repeat2")
    assert [formal5[0]["width"], formal5[0]["height"]] != [tiny5["width"], tiny5["height"]]
    assert formal5[0]["expected_sha256"] != tiny5["expected_sha256"]
    formal6 = [row for row in manifest["cases"] if row.get("formal_case") == "case0006"]
    assert len(formal6) == 1
    assert formal6[0]["coverage_delta"].startswith("24x24 full buffer")
    tiny6 = next(row for row in manifest["cases"] if row["id"] == "32bpc_nonlegacy_amount5_repeat10")
    assert [formal6[0]["width"], formal6[0]["height"]] != [tiny6["width"], tiny6["height"]]
    assert formal6[0]["expected_sha256"] != tiny6["expected_sha256"]
    for row in manifest["cases"]:
        directory = FIXTURES / row["id"]
        assert hashlib.sha256((directory / "source_argb_f32.bin").read_bytes()).hexdigest() == row["source_sha256"]
        assert hashlib.sha256((directory / "expected_argb_f32.bin").read_bytes()).hexdigest() == row["expected_sha256"]
    with tempfile.TemporaryDirectory(prefix="olmblur-worker32-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_helper.cpp", "core/olmblur_worker32_nonlegacy.cpp",
                "tools/emulation/replay_olmblur_worker32_nonlegacy.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 32bpc Non-Legacy production worker matches 12 retained complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
