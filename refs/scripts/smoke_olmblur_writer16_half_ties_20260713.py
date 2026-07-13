#!/usr/bin/env python3
"""Smoke-test the actual-AEX OLMBlur PF16 half-tie writer microfixture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/emulation/test_olmblur_writer16_half_ties_20260713.py"


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["status"] == "pass_actual_aex_distinguishes_half_ties"
    assert report["stored_agrb16"] == [32768, 1101, 1102, 32768]
    assert report["add_half_then_truncate_rgb"] == [1101, 1102, 32768]
    assert report["nearest_even_rgb"] == [1100, 1102, 32768]
    assert report["binary_sha256"] == "f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b"
    print("[OK] OLMBlur PF16 writer half-tie smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
