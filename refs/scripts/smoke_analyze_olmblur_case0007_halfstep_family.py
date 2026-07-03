#!/usr/bin/env python3
"""Smoke-test scripts/analyze_olmblur_case0007_halfstep_family.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="olmblur_case0007_halfstep_") as tmp:
        out_json = Path(tmp) / "report.json"
        out_md = Path(tmp) / "report.md"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "analyze_olmblur_case0007_halfstep_family.py"),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmblur_case0007_halfstep_family_audit"
        assert report["cases"]["16bpc"]["status"] == "resolved-as-pre-store-float-delta"
        assert report["cases"]["16bpc"]["windows_witness"]["target_channel_pre_store_float"] == 12544.498046875
        assert report["cases"]["8bpc_old_normalized"]["status"] == "still-needs-windows-pre-store-float"
        assert report["cases"]["8bpc_old_normalized"]["low_witness_xy"] == [488, 941]
        assert report["decision"]["status"] == "16bpc-resolved-8bpc-still-open-prestore-family"
        md = out_md.read_text(encoding="utf-8")
        for needle in (
            "OLMBlur case_0007 Half-Step Family Audit",
            "12544.498046875",
            "250.499985",
            "(488, 941)",
        ):
            if needle not in md:
                raise AssertionError(f"markdown missing {needle}")
    print("[OK] OLMBlur case_0007 half-step family smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
