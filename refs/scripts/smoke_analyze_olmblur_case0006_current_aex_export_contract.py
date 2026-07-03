#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_case0006_current_aex_export_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_case0006_current_aex_contract_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_case0006_current_aex_export_contract.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_case0006_current_aex_export_contract_audit"
        assert report["decision"]["status"] == "awaiting-windows-current-aex-export"
        assert report["parameters"]["Legacy"] == 0
        assert report["files"]["canonical_ref"]["sha256"] == "27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f"
        assert report["witness_points"][0]["xy"] == [314, 14]
        assert report["witness_points"][0]["canonical_ref"] == [2201, 2201, 2201, 65535]
        assert report["witness_points"][1]["mac_single_export"] == [727, 727, 727, 65535]
        assert len(report["required_windows_payload"]) == 6
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Current-AEX Export Contract Audit",
            "awaiting-windows-current-aex-export",
            "Required Windows Payload",
            "(314, 14)",
            "global 16bpc writer swap",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur case_0006 current-AEX export contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
