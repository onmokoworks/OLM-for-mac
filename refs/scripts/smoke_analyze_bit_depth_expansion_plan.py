#!/usr/bin/env python3
"""Smoke-test the OLM bit-depth expansion plan report."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olm_bit_depth_plan_") as tmp:
        out_dir = Path(tmp)
        report_json = out_dir / "bit_depth_plan.json"
        report_md = out_dir / "bit_depth_plan.md"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts" / "analyze_bit_depth_expansion_plan.py"),
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            cwd=ROOT,
            check=True,
        )
        report = json.loads(report_json.read_text(encoding="utf-8"))
        assert report["kind"] == "olm_bit_depth_expansion_plan"
        assert report["decision"] == "request-16bpc-for-normalized-8bpc-exact-features"
        features = report["features"]
        groups = report["groups"]
        assert report["totals"]["feature_count"] == len(features)
        assert report["totals"]["plugin_count"] == len(groups)
        assert report["totals"]["case_count"] == sum(row["case_count"] for row in features)
        features = {row["name"]: row for row in report["features"]}
        assert set(features) == {
            "OLMBlur",
            "OLMColorKey",
            "OLMToonDilate",
            "OLMDistanceGradation basic",
            "OLMDistanceGradation extended",
            "OLMDistanceGradation blur",
        }
        assert features["OLMBlur"]["case_count"] == 7
        assert features["OLMColorKey"]["case_count"] == 9
        assert features["OLMToonDilate"]["case_count"] == 3
        assert features["OLMDistanceGradation basic"]["case_count"] == 12
        assert features["OLMDistanceGradation extended"]["case_count"] == 16
        assert features["OLMDistanceGradation blur"]["case_count"] == 1
        groups = {row["plugin"]: row for row in report["groups"]}
        assert set(groups) == {
            "OLMBlur",
            "OLMColorKey",
            "OLMToonDilate",
            "OLMDistanceGradation",
        }
        assert groups["OLMDistanceGradation"]["case_count"] == 29
        md = report_md.read_text(encoding="utf-8")
        for needle in (
            "OLM Bit-Depth Expansion Plan",
            "request-16bpc-for-normalized-8bpc-exact-features",
            "Do not claim all-bit-depth compatibility",
            "OLMDistanceGradation extended",
            "OLMToonDilate",
        ):
            assert needle in md
    print("[OK] bit-depth expansion plan smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
