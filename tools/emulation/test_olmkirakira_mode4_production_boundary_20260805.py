#!/usr/bin/env python3
"""Build and run the shared Mode4 scalar recurrence against actual-AEX bits."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkirakira-mode4-") as tmp:
        binary = Path(tmp) / "mode4"
        subprocess.run([
            "c++", "-std=c++20", "-O2", "-ffp-contract=off",
            str(ROOT / "tools/emulation/test_kirakira_mode4.cpp"),
            "-o", str(binary),
        ], cwd=ROOT, check=True)
        subprocess.run([str(binary)], cwd=ROOT, check=True)
    source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    assert '#include "../../core/kirakira_mode4.h"' in source
    assert "mode4_rotated_scalar_chain(" in source
    print("PASS_OLMKIRAKIRA_MODE4_PRODUCTION_BOUNDARY_20260805")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
