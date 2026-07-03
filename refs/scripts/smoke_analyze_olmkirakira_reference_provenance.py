#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmkirakira_reference_provenance.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_reference_provenance_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmkirakira_reference_provenance.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_reference_provenance_audit"
        assert report["hotspot_xy"] == [934, 118]
        assert report["artifacts"]["canonical_reference_png"]["hotspot_rgba"] == [131, 131, 131, 255]
        assert report["artifacts"]["archived_bt709_candidate_png"]["hotspot_rgba"] == [145, 145, 145, 255]
        assert report["artifacts"]["current_mac_compose_witness"]["hotspot_rgba"] == [144, 144, 144, 255]
        assert report["artifacts"]["windows_traced_hotspot"]["hotspot_rgba"] == [144, 144, 144, 255]
        assert report["pairwise_deltas"]["archived_candidate_minus_reference"] == [14, 14, 14, 0]
        assert report["pairwise_deltas"]["windows_traced_minus_reference"] == [13, 13, 13, 0]
        assert report["pairwise_deltas"]["archived_candidate_minus_windows_traced"] == [1, 1, 1, 0]
        assert report["role_matrix"]["windows_traced_vs_mac_witness"] is True
        assert report["role_matrix"]["windows_traced_vs_archived_candidate"] is False
        assert report["decision"]["status"] == "reference-export-or-witness-placement-pending"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMKiraKira Reference Provenance Audit",
            "(934, 118)",
            "131",
            "144",
            "145",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira reference provenance smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
