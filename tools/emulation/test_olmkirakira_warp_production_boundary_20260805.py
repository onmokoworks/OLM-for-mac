#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkira-warp-") as tmp:
        binary = Path(tmp) / "warp"
        subprocess.run(["c++", "-std=c++20", "-O2", "-ffp-contract=off",
                        str(ROOT / "tools/emulation/test_kirakira_warp.cpp"), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    production = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    assert "olm::kirakira::warp_get_rotation_matrix_2d(" in production
    print("PASS_OLMKIRAKIRA_WARP_PRODUCTION_BOUNDARY_20260805")
    return 0
if __name__ == "__main__": raise SystemExit(main())
