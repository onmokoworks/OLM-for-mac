#!/usr/bin/env python3
"""Compatibility entry point for the closed Mode2 Rotation22 PF32 seam."""
from __future__ import annotations
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "tools/emulation/test_olmkirakira_mode2_rotation22_closure_20260812.py"

def main() -> int:
    return subprocess.run(["python3", str(CLOSURE)], cwd=ROOT).returncode
if __name__=="__main__": raise SystemExit(main())
