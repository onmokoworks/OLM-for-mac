#!/usr/bin/env python3
"""Verify grounded Mode-3 lengths use the AEX Gaussian at any geometry."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp"
CPP = ROOT / "tools/emulation/test_kirakira_mode3_nonwhitelist_geometry.cpp"


def main() -> int:
    production = SOURCE.read_text(encoding="utf-8")
    assert "const bool actual_aex_mode3_length = length == 3 || length == 5 || length == 7;" in production
    assert "if (blur_mode == 3 && actual_aex_mode3_length)" in production
    assert "exact_mode3_fixture" not in production
    assert "return RotatedAxisBoxBlur(seed, work_width, work_height, len, angle, passes, info.blur_mode);" in production
    assert "if (bitdepth == 8) return RenderTyped<PF_Pixel8>" in production
    assert "if (bitdepth == 16) return RenderTyped<PF_Pixel16>" in production
    assert "if (bitdepth == 32) return RenderTyped<PF_PixelFloat>" in production
    with tempfile.TemporaryDirectory(prefix="olmkira-mode3-general-") as td:
        exe = Path(td) / "mode3"
        subprocess.run([
            "c++", "-std=c++20", "-O2", "-ffp-contract=off",
            str(CPP), "-o", str(exe),
        ], cwd=ROOT, check=True)
        subprocess.run([str(exe)], cwd=ROOT, check=True)
    print("PASS_OLMKIRAKIRA_MODE3_NONWHITELIST_PRODUCTION_20260806 depths=3 padding=exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
