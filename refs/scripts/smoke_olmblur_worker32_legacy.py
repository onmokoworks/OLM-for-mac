#!/usr/bin/env python3
"""Replay the complete 32bpc Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tools/emulation/fixtures/olmblur_worker32_legacy"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmblur-worker32-legacy-") as temp:
        binary = Path(temp) / "replay"
        subprocess.run(
            [
                "c++", "-std=c++17", "-O2", "-ffp-contract=off", "-Icore",
                "core/olmblur_fullworker_helper.cpp",
                "core/olmblur_worker32_legacy.cpp",
                "tools/emulation/replay_olmblur_worker32_legacy.cpp",
                "-o", str(binary),
            ],
            cwd=ROOT,
            check=True,
        )
        subprocess.run(
            [str(binary), str(FIXTURES)], cwd=ROOT, check=True
        )
    print("[OK] OLMBlur 32bpc Legacy worker matches 5 complete AEX fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
