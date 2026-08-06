#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmkira-premultiply-") as temp:
        binary = Path(temp) / "premultiply"
        subprocess.run([
            "clang++", "-std=c++17", "-O0",
            str(ROOT / "tools/emulation/test_kirakira_premultiply.cpp"),
            "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)
    source = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text(encoding="utf-8")
    assert "info.blur_mode == 1 || info.blur_mode == 2 || info.blur_mode == 4" in source
    assert "ComposePremultiplyPixel(" in source
    print("PASS_OLMKIRAKIRA_MODE4_HIGHLIGHT_PREMULTIPLY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
