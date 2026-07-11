#!/usr/bin/env python3
"""Materialize and replay complete 8bpc Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker8_legacy"


def main() -> int:
    subprocess.run([sys.executable, "tools/emulation/test_olmblur_worker8_legacy.py", "--export"], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="olmblur-worker8-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run([
            "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
            "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker8_legacy.cpp",
            "tools/emulation/replay_olmblur_worker8_legacy.cpp", "-o", str(binary),
        ], cwd=ROOT, check=True)
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 8bpc Legacy worker matches 4 complete AEX fixtures, including case0003 radius248 boundary gradient")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
