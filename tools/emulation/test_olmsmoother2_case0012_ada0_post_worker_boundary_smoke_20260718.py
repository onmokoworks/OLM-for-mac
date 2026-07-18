#!/usr/bin/env python3
"""Smoke test for the 20260718 ADA0 post-worker boundary report."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "tools/emulation/test_olmsmoother2_case0012_ada0_post_worker_boundary_20260718.py"


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        subprocess.run([sys.executable, str(AUDIT), "--output-json", str(output / "report.json"), "--output-md", str(output / "report.md")], cwd=ROOT, check=True)
        report = json.loads((output / "report.json").read_text(encoding="utf-8"))
        assert report["verdict"] == "PASS_NO_POST_WORKER_DIVERGENCE_IN_COMPARED_WINDOW"
        assert report["first_divergence"] is None
        assert report["runtime"]["worker_entries"] == 1
        assert report["runtime"]["classifier_entries"] == 256
        assert len(report["boundary"]["compared_window"]) == 12
        assert "No production source or ledger change." in (output / "report.md").read_text(encoding="utf-8")
    print("PASS: ADA0 post-worker boundary has no compared-byte divergence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
