#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tools/emulation/test_dblur_rowdriver_full_exact_20260711.py"


def main() -> int:
    result = subprocess.run([sys.executable, str(TEST)], cwd=ROOT, text=True,
                            capture_output=True)
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode == 0:
        print("[OK] dblur rowdriver full-entry gate is byte-exact")
        return 0
    print("[FAIL] dblur rowdriver full-entry candidate is known-red; exact is not claimed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
