#!/usr/bin/env python3
"""Replay complete 8bpc Non-Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker_orchestration"


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/emulation/test_olmblur_worker_orchestration.py", "--export"],
        cwd=ROOT,
        check=True,
    )
    with tempfile.TemporaryDirectory(prefix="olmblur-worker-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_helper.cpp", "core/olmblur_worker_orchestration.cpp",
                "tools/emulation/replay_olmblur_worker_orchestration.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 8bpc Non-Legacy worker matches 2 complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
