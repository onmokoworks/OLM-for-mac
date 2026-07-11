#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_case0006_current_aex_export_contract.py."""

from __future__ import annotations

import json
import shutil
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
        assert report["decision"]["status"] in {
            "awaiting-windows-current-aex-export",
            "outcome-a-current-aex-matches-canonical",
        }
        assert report["parameters"]["Legacy"] == 0
        assert report["files"]["canonical_ref"]["sha256"] == "27d24c96a6f3c15d27d8884ede039e5fd97480d752324f04d8e3aa77acc8791f"
        assert report["witness_points"][0]["xy"] == [314, 14]
        assert report["witness_points"][0]["canonical_ref"] == [2201, 2201, 2201, 65535]
        assert report["witness_points"][1]["mac_single_export"] == [727, 727, 727, 65535]
        assert len(report["required_windows_payload"]) == 6
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "Current-AEX Export Contract Audit",
            "Required Windows Payload",
            "(314, 14)",
            "global 16bpc writer swap",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")

        out_json_pending = Path(tmp) / "report_pending.json"
        out_md_pending = Path(tmp) / "report_pending.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_case0006_current_aex_export_contract.py"),
                "--no-auto-find-windows-current-export",
                "--output-json",
                str(out_json_pending),
                "--output-md",
                str(out_md_pending),
            ],
            cwd=root,
            check=True,
        )
        report_pending = json.loads(out_json_pending.read_text(encoding="utf-8"))
        assert report_pending["decision"]["status"] == "awaiting-windows-current-aex-export"
        if "awaiting-windows-current-aex-export" not in out_md_pending.read_text(encoding="utf-8"):
            raise AssertionError("pending markdown missing awaiting status")

        canonical_copy = Path(tmp) / "current_aex_export.png"
        shutil.copy2(
            root
            / "refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/"
            / "olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0006.png",
            canonical_copy,
        )
        out_json2 = Path(tmp) / "report_with_export.json"
        out_md2 = Path(tmp) / "report_with_export.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_case0006_current_aex_export_contract.py"),
                "--windows-current-export",
                str(canonical_copy),
                "--output-json",
                str(out_json2),
                "--output-md",
                str(out_md2),
            ],
            cwd=root,
            check=True,
        )
        report_with_export = json.loads(out_json2.read_text(encoding="utf-8"))
        assert report_with_export["decision"]["status"] == "outcome-a-current-aex-matches-canonical"
        assert report_with_export["witness_points"][0]["windows_current_export"] == [2201, 2201, 2201, 65535]
    print("[OK] OLMBlur case_0006 current-AEX export contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
