#!/usr/bin/env python3
"""Smoke-test DistanceGradation Power-fix residual classification."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_powerfix_residuals_") as tmp:
        out_json = Path(tmp) / "summary.json"
        out_md = Path(tmp) / "summary.md"
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_distancegradation_powerfix_residuals.py",
                "--summary-json",
                str(out_json),
                "--summary-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmdistancegradation_16bpc_powerfix_residual_families"
        assert data["exact"] == 1
        assert data["fail"] == 15
        assert data["total"] == 16
        families = data["family_counts"]
        assert families.get("constant-bg-binary-sparse-full-color") == 4
        assert families.get("power-rgb-bg-boundary-quantization") == 1
        assert families.get("power-layer-bg-source-or-premultiply") == 2
        assert "Power-Fix Residual Families" in out_md.read_text(encoding="utf-8")
    print("[OK] DistanceGradation Power-fix residual family smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
