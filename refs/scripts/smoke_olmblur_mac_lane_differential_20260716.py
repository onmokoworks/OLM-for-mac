#!/usr/bin/env python3
"""Smoke-test the dated OLMBlur Mac-lane differential."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/test_olmblur_mac_lane_differential_20260716.py"


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)], cwd=ROOT, check=True, capture_output=True, text=True
    )
    report = json.loads(completed.stdout)
    assert report["status"] == "pass"
    assert report["repeat_coverage"] == {"16bpc": [2, 3], "32bpc": [2, 3, 4, 10]}
    assert report["32bpc_repeat2_vs_repeat10_expected_sha256_differ"]
    assert report["smokes"]["8bpc_guard"].startswith("PASS existing 8bpc CLI smoke")
    print("[OK] OLMBlur Mac-lane actual-AEX/portable differential")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
