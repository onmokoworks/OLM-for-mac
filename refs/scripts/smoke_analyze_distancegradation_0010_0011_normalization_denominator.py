#!/usr/bin/env python3
"""Smoke test for analyze_distancegradation_0010_0011_normalization_denominator.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/analyze_distancegradation_0010_0011_normalization_denominator.py"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="olmdg_0010_norm_denom_") as tmp:
        tmp_path = Path(tmp)
        out_json = tmp_path / "audit.json"
        out_md = tmp_path / "audit.md"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=ROOT,
            check=True,
        )
        data = json.loads(out_json.read_text(encoding="utf-8"))
        assert data["kind"] == "olmdistancegradation_0010_0011_normalization_denominator_audit"
        assert data["decision"] == "mixed-actual-max-and-threshold-half-boundary"
        by_xy = {tuple(row["xy"]): row for row in data["witnesses"]}
        assert by_xy[(6, 40)]["normalization_denominator_kind"] == "actual_raw_max"
        assert by_xy[(901, 394)]["normalization_denominator_kind"] == "ui_threshold"
        assert by_xy[(915, 392)]["normalization_denominator_kind"] == "ui_threshold"
        assert abs(by_xy[(6, 40)]["mac_denominator_implied"] - 45.5411912019) < 1e-6
        text = out_md.read_text(encoding="utf-8")
        assert "normalization denominator audit" in text
        assert "Do not change final output rounding" in text
    print("[OK] DistanceGradation 0010/0011 normalization denominator smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
