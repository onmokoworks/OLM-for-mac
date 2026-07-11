#!/usr/bin/env python3
"""Materialize and replay complete 16bpc Legacy OLMBlur worker fixtures."""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker16_legacy"


def main() -> int:
    subprocess.run([sys.executable, "tools/emulation/test_olmblur_worker16_legacy.py", "--export"], cwd=ROOT, check=True)
    with tempfile.TemporaryDirectory(prefix="olmblur-worker16-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(["c++", "-std=c++17", "-O2", "-ffp-contract=off", "-fno-fast-math", "-Icore", "core/olmblur_fullworker_helper.cpp", "core/olmblur_worker16_legacy.cpp", "tools/emulation/replay_olmblur_worker16_legacy.cpp", "-o", str(binary)], cwd=ROOT, check=True)
        subprocess.run([str(binary), str(FIXTURES)], cwd=ROOT, check=True)
    print("[OK] OLMBlur 16bpc Legacy worker matches 3 complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
