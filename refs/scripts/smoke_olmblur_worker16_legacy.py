#!/usr/bin/env python3
"""Replay complete 16bpc Legacy OLMBlur worker fixtures."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    subprocess.run(
        [sys.executable, "tools/emulation/smoke_olmblur_worker16_legacy.py"],
        cwd=ROOT,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
