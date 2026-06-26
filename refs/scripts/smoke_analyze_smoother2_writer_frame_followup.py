#!/usr/bin/env python3
"""Smoke-test scripts/analyze_smoother2_writer_frame_followup.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmsmoother2_writer_frame_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "writer_frame_analysis.json"
        report_md = out_dir / "writer_frame_analysis.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_smoother2_writer_frame_followup.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olmsmoother2_writer_frame_followup_analysis"
        assert report["decision"] == "producer-upstream-of-writer-frame"
        cases = {row["case_id"]: row for row in report["cases"]}
        assert cases["legacy_case_0004_current_aex"]["raw_derived"]["expected_png_rgba_after_premultiply"] == [
            103,
            103,
            103,
            113,
        ]
        assert cases["legacy_case_0012_gamma5_red_blue_current_aex"]["raw_derived"][
            "expected_png_rgba_after_premultiply"
        ] == [0, 0, 0, 0]
        assert all(row["writer_explains_reference"] for row in cases.values())
        md = report_md.read_text(encoding="utf-8")
        assert "producer-upstream-of-writer-frame" in md
        assert "legacy_case_0004_current_aex" in md
        assert "legacy_case_0012_gamma5_red_blue_current_aex" in md
    print("[OK] Smoother2 writer-frame follow-up smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
