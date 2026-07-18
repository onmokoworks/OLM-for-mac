#!/usr/bin/env python3
"""Regression gate for the bounded Mode4 edge/pass audit."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/audit_olmkirakira_mode4_edge_passes_20260718.py"
REPORT = ROOT / "refs/conformance/olmkirakira_mode4_edge_passes_20260718.json"


def main() -> int:
    subprocess.run(["python3", str(AUDIT)], cwd=ROOT, check=True)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["status"] == "PASS_MODE4_EDGE_FORWARD_BACKWARD_PASSES"
    assert report["production_edit"] is False
    assert report["ae_exact_claim"] is False
    assert all(report["checks"].values()), report["checks"]
    assert len(report["actual_aex"]["hits"]["forward_step"]) == 56
    hits = report["actual_aex"]["hits"]
    assert 4 * len(hits["backward_vector_step"]) + len(hits["backward_step"]) == 56
    print("PASS_OLMKIRAKIRA_MODE4_EDGE_FORWARD_BACKWARD_PASSES_20260718")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
