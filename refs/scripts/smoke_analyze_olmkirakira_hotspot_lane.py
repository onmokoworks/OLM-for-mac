#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmkirakira_hotspot_lane.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmkirakira_hotspot_lane_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmkirakira_hotspot_lane.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmkirakira_hotspot_lane_audit"
        assert report["witness_xy"] == [934, 118]
        assert report["agreement_checks"]["same_glow_after_opacity"] is True
        assert report["agreement_checks"]["same_compose_float"] is True
        assert report["agreement_checks"]["same_pre_writeback_float"] is True
        assert report["agreement_checks"]["same_final_writeback_or_png_rgba"] is True
        assert report["agreement_checks"]["writeback_minus_reference_rgba"] == [13, 13, 13, 0]
        assert report["decision"]["status"] == "hotspot-proof-shifted-to-reference-or-witness-placement"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMKiraKira Hotspot Lane Audit",
            "(934, 118)",
            "144",
            "131",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMKiraKira hotspot lane smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
