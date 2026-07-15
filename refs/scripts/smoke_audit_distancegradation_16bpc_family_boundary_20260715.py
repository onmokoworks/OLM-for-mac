#!/usr/bin/env python3
"""Smoke-test the DG 16bpc family boundary audit."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmdg_family_boundary_") as temp:
        out_json = Path(temp) / "audit.json"
        out_md = Path(temp) / "audit.md"
        subprocess.run(
            [sys.executable, "scripts/audit_distancegradation_16bpc_family_boundary_20260715.py", "--output-json", str(out_json), "--output-md", str(out_md)],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmdistancegradation_16bpc_family_boundary_audit"
        assert len(report["FACT"]["case_0026_store_checks"]) == 4
        assert all(row["store_matches"] for row in report["FACT"]["case_0026_store_checks"])
        assert not any(row["field_raw_words_present"] for row in report["FACT"]["case_0026_store_checks"])
        assert "PNG" in out_json.read_text(encoding="utf-8")
        assert "FACT" in out_md.read_text(encoding="utf-8")
        assert "INFERENCE" in out_md.read_text(encoding="utf-8")
    print("[OK] DG 16bpc family boundary audit smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
