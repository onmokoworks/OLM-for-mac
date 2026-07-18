#!/usr/bin/env python3
"""Regression gate for the DirectionalBlur angle-pair evidence."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/emulation/test_dblur_angle0_diagonal_actual_aex_port_differential_20260718.py"
REPORT = ROOT / "refs/conformance/olmdirectionalblur_angle0_diagonal_actual_aex_port_differential_20260718.json"


def main() -> int:
    subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, check=True)
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert set(payload["cases"]) == {"0", "45"}
    assert all(case["equal_output"] for case in payload["cases"].values())
    print("PASS directionalblur angle0/diagonal actual-AEX port differential")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
