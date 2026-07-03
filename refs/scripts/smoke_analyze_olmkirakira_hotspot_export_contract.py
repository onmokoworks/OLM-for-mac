#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmkirakira_hotspot_export_contract.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_hotspot_export_contract_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmkirakira_hotspot_export_contract.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_hotspot_export_contract_audit"
        assert report["decision"]["status"] == "awaiting-same-run-export-or-witness-placement-proof"
        assert report["artifacts"]["canonical_reference_png"]["hotspot_rgba"] == [131, 131, 131, 255]
        assert report["artifacts"]["current_mac_compose_witness"]["hotspot_rgba"] == [144, 144, 144, 255]
        assert report["artifacts"]["windows_traced_hotspot"]["hotspot_rgba"] == [144, 144, 144, 255]
        assert report["artifacts"]["archived_bt709_candidate_png"]["hotspot_rgba"] == [145, 145, 145, 255]
        assert len(report["required_windows_payload"]) == 6
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMKiraKira Hotspot Export Contract Audit",
            "awaiting-same-run-export-or-witness-placement-proof",
            "same-run Windows current export",
            "retune BT.709 seed",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira hotspot export contract smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
