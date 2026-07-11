#!/usr/bin/env python3
"""Regression check for the deliberately incomplete OLM release scope."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_release_scope_") as temp_dir:
        report = Path(temp_dir) / "report.json"
        command = [
            sys.executable,
            str(ROOT / "scripts/check_olm_release_scope.py"),
            "--report-json",
            str(report),
        ]
        subprocess.run(command, cwd=ROOT, check=True)
        data = json.loads(report.read_text(encoding="utf-8"))

    assert data["complete"] is False
    assert data["plugin_count"] == 9
    assert data["depth_cells"] == 27
    assert data["ae_exact_depth_cells"] == 1
    assert data["open_gate_count"] > 0
    print("[OK] OLM release scope remains explicit and incomplete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
