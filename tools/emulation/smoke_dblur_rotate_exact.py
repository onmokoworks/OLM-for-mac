#!/usr/bin/env python3
"""Smoke the bounded rotate replay and record its current exactness gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tools/emulation/test_dblur_rotate_exact.py"


def main() -> int:
    result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, text=True, capture_output=True)
    combined = result.stdout + result.stderr
    if result.returncode == 0:
        print("[OK] dblur rotate exact replay is byte-exact")
        return 0
    print(combined, end="")
    print("[FAIL] dblur rotate exact replay")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
