#!/usr/bin/env python3
"""Smoke-test the AEX CPU emulation OpenCV detour gates.

This wrapper keeps the long command lines for the DistanceGradation emulator
checks discoverable from the normal refs/scripts smoke namespace. It does not
claim AE exactness; it only verifies that the local AEX CPU simulation can still
detour the OpenCV primitives used by the DG field-generation probe.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run(repo: Path, command: list[str]) -> int:
    proc = subprocess.run(command, cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(f"+ {' '.join(command)}")
    print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    return proc.returncode


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    py = repo / "tools" / "emulation" / ".venv" / "bin" / "python"
    if not py.exists():
        print(f"[SKIP] missing emulation venv: {py}")
        return 0

    commands = [
        [str(py), "tools/emulation/test_opencv_detour.py"],
        [str(py), "tools/emulation/test_dg_fieldgen_p1b.py", "--points", "8,5;7,5;9,5"],
    ]
    for command in commands:
        rc = run(repo, command)
        if rc != 0:
            return rc
    print("[OK] emulation OpenCV detour smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
