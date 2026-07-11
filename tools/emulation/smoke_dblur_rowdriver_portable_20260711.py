#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tools/emulation/test_dblur_rowdriver_portable_20260711.py"


def main() -> int:
    result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, text=True,
                            capture_output=True)
    output = result.stdout + result.stderr
    if result.returncode == 0:
        print(output, end="")
        print("[OK] dblur rowdriver portable leaf smoke is byte-exact")
        return 0
    print(output, end="")
    print("[FAIL] dblur rowdriver portable leaf smoke")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
