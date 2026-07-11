#!/usr/bin/env python3
"""Smoke test for the OLMDistanceGradation case_0023 reference export audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    out_json = ROOT / "refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.json"
    out_md = ROOT / "refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/materialize_distancegradation_case0023_reference_export_audit.py",
            "--stamp",
            "20260707",
        ],
        cwd=ROOT,
        check=True,
    )
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["kind"] == "olmdistancegradation_case0023_reference_export_audit"
    assert data["reference_exact"] is True
    for key in [
        "packaged_vs_current_win_20260703",
        "packaged_vs_current_win_20260706",
        "current_win_20260703_vs_20260706",
    ]:
        comparison = data["comparisons"][key]
        assert comparison["status"] == "compared"
        assert comparison["nonzero_px"] == 0
        assert comparison["max_diff"] == 0
    md = out_md.read_text(encoding="utf-8")
    assert "Reference exact: `True`" in md
    assert "packaged_vs_current_win_20260706" in md
    print("ok: OLMDistanceGradation case_0023 reference export audit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
