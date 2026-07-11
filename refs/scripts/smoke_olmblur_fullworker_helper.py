#!/usr/bin/env python3
"""Replay the actual-AEX OLMBlur full-worker helper fixtures."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_fullworker_helper"


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/emulation/test_olmblur_fullworker_helper.py", "--export"],
        cwd=ROOT,
        check=True,
    )
    with tempfile.TemporaryDirectory(prefix="olmblur-fullworker-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_fullworker_helper.cpp",
                "tools/emulation/replay_olmblur_fullworker_helper.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur full-worker helper matches 8 actual-AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
