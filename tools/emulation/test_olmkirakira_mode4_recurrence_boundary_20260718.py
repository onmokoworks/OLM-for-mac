#!/usr/bin/env python3
"""Regression gate for the bounded Mode4 recurrence audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_mode4_recurrence_boundary_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_recurrence_boundary_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "PASS_MODE4_BOUNDED_RECURRENCE_GEOMETRY"
    assert report["production_edit"] is False
    assert all(report["checks"].values()), report["checks"]
    assert report["actual_aex"]["mode4_entry"]
    assert report["actual_aex"]["gain_boundary"]
    assert report["static"]["decomp"]["recurrence_factors"] is True
    assert report["static"]["asm"]["gain_boundary"] is True
    print("PASS_OLMKIRAKIRA_MODE4_RECURRENCE_BOUNDARY_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
