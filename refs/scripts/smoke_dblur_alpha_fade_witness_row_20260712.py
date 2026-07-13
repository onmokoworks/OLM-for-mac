#!/usr/bin/env python3
"""Smoke the bounded actual-AEX Alpha Fade witness-row comparison."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "tools/emulation/test_dblur_alpha_fade_witness_row_20260712.py"
REPORT = ROOT / "refs/conformance/dblur_alpha_fade_witness_row_20260712.json"


def main() -> int:
    subprocess.run([sys.executable, str(TEST)], cwd=ROOT, check=True)
    result = json.loads(REPORT.read_text(encoding="utf-8"))
    assert result["status"] == "pass"
    assert result["scope"]["full_entry_rerun"] is False
    assert result["scope"]["rowdriver_rows"] == [755, 756]
    assert result["mapping"]["internal_witness"] == [747, 755]
    assert all(item["exact"] for item in result["comparisons"].values())
    assert result["downstream"]["normalization"]["exact"]
    assert result["downstream"]["rotateback"]["source_bits_preserved"]
    assert not result["downstream"]["pf_writer"]["actual_aex_vs_windows"]["exact"]
    print("[OK] DirectionalBlur Alpha Fade witness row matches actual AEX byte-for-byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
