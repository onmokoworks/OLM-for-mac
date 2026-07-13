#!/usr/bin/env python3
"""Guard the runtime-proven Channel=2 BT.709 seed coefficients."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = "0.2126f + g * 0.7152f + b * 0.0722f"
MAC_EXPECTED = "0.2126f + p.g * 0.7152f + p.b * 0.0722f"


def main() -> int:
    cli = (ROOT / "cli/OLMKiraKira/main.cpp").read_text()
    mac = (ROOT / "mac/OLMKiraKira/OLMKiraKira.cpp").read_text()
    assert EXPECTED in cli
    assert MAC_EXPECTED in mac

    r, g, b = (230 / 255, 210 / 255, 60 / 255)
    bt709 = r * 0.2126 + g * 0.7152 + b * 0.0722
    windows_trace = 0.79773343
    assert abs(bt709 - windows_trace) < 1e-7
    print("[OK] OLMKiraKira Channel=2 uses runtime-proven BT.709 seed luma")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
