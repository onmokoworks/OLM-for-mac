#!/usr/bin/env python3
"""Regression entry point for the retained 46-cell ColorKey Edge Blur proof."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tools/emulation/audit_olmcolorkey_edge_blur_complete_family_20260806.py"


def test_retained_edge_blur_family_is_full_argb_exact() -> None:
    run = subprocess.run(["python3", str(AUDIT)], cwd=ROOT, text=True, capture_output=True, timeout=180)
    assert run.returncode == 0, run.stderr or run.stdout


if __name__ == "__main__":
    test_retained_edge_blur_family_is_full_argb_exact()
    print("[OK] OLMColorKey retained 46-cell Edge Blur family")
