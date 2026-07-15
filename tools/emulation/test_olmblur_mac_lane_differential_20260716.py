#!/usr/bin/env python3
"""Bounded Mac-only OLMBlur actual-AEX versus portable differential."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AEX = ROOT / "plugins_2025" / "OLMBlur.aex"
EXPECTED_SHA256 = "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"


def run_json(script: str) -> dict:
    completed = subprocess.run(
        [sys.executable, script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def run_smoke(script: str) -> str:
    completed = subprocess.run(
        [sys.executable, script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    if script.endswith("smoke_olmblur_cli.py"):
        assert "fail=0" in completed.stdout and "missing=0" in completed.stdout
        return "PASS existing 8bpc CLI smoke (fail=0, missing=0)"
    return completed.stdout.strip().splitlines()[-1]


def main() -> int:
    actual_hash = hashlib.sha256(AEX.read_bytes()).hexdigest()
    assert actual_hash == EXPECTED_SHA256, "fixture/AEX hash drift"

    writer = run_json("tools/emulation/test_olmblur_writer16_half_ties_20260713.py")
    assert writer["stored_agrb16"] == [32768, 1101, 1102, 32768]
    assert writer["add_half_then_truncate_rgb"] == [1101, 1102, 32768]
    assert writer["nearest_even_rgb"] == [1100, 1102, 32768]

    smoke16 = run_smoke("refs/scripts/smoke_olmblur_worker16_nonlegacy.py")
    smoke32 = run_smoke("refs/scripts/smoke_olmblur_worker32_nonlegacy.py")
    smoke8 = run_smoke("refs/scripts/smoke_olmblur_cli.py")

    manifest16 = json.loads(
        (ROOT / "tools/emulation/fixtures/olmblur_worker16_nonlegacy/manifest.json").read_text()
    )
    manifest32 = json.loads(
        (ROOT / "tools/emulation/fixtures/olmblur_worker32_nonlegacy/manifest.json").read_text()
    )
    repeats16 = sorted({case["repeat"] for case in manifest16["cases"]})
    repeats32 = sorted({case["repeat"] for case in manifest32["cases"]})
    assert repeats16 == [2, 3]
    assert repeats32 == [2, 3, 4, 10]
    repeat_hashes32 = {
        case["repeat"]: case["expected_sha256"]
        for case in manifest32["cases"]
        if case["id"].startswith("32bpc_nonlegacy_amount5_repeat")
    }
    assert len(repeat_hashes32) == 2 and len(set(repeat_hashes32.values())) == 2

    print(json.dumps({
        "schema": "olmblur.mac-lane-differential/1",
        "date": "2026-07-16",
        "aex_sha256": actual_hash,
        "writer": {
            "actual_aex": writer["stored_agrb16"],
            "portable_add_half_truncate": writer["add_half_then_truncate_rgb"],
            "portable_nearest_even": writer["nearest_even_rgb"],
        },
        "repeat_coverage": {"16bpc": repeats16, "32bpc": repeats32},
        "32bpc_repeat2_vs_repeat10_expected_sha256_differ": True,
        "smokes": {"16bpc": smoke16, "32bpc": smoke32, "8bpc_guard": smoke8},
        "status": "pass",
        "scope": "Mac-local actual-AEX CPU boundary versus portable worker; no AE or Windows claim",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
