#!/usr/bin/env python3
"""Smoke-test scripts/analyze_distancegradation_debug_points.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="dg_debug_points_") as tmp:
        tmp_path = Path(tmp)
        debug_log = tmp_path / "field_debug.txt"
        debug_log.write_text(
            "\n".join(
                [
                    "OLMDistanceGradation debug dump",
                    "w=1920 h=1080 pixel_size=8 invert=0 in_out=3 inside=36 outside=0 render_mode=1 use_bg=1 interp=1 power=1 blur_mode=1 blur_size=0 ds_x=1 ds_y=1",
                    "point x=1699 y=7 alpha=0.00393676758 d_alpha=1 field_x=0 raw_inside=1 raw_outside=0 inside_x=0 outside_x=1 both_x=1 winner=outside inside_t=36 outside_t=0 inside_constant_binary=0 outside_constant_binary=1 compose_input_x=0",
                    "point x=1700 y=7 alpha=0 d_alpha=0 field_x=1 raw_inside=0 raw_outside=1",
                    "point x=415 y=393 alpha=1 d_alpha=1 field_x=1 raw_inside=36.0138855 raw_outside=0",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        subprocess.run(
            [
                py,
                str(root / "scripts" / "analyze_distancegradation_debug_points.py"),
                "--debug-log",
                str(debug_log),
                "--output-json",
                str(out_json),
                "--output-md",
                str(out_md),
            ],
            cwd=root,
            check=True,
        )
        report = json.loads(out_json.read_text(encoding="utf-8"))
        assert report["class_counts"]["inside_edge_1px"] == 1
        assert report["class_counts"]["outside_neighbor"] == 1
        assert report["class_counts"]["inside_threshold_plateau"] == 1
        point0 = report["points"][0]
        assert point0["inside_x"] == 0.0
        assert point0["outside_x"] == 1.0
        assert point0["winner"] == "outside"
        assert point0["compose_input_x"] == 0.0
        md = out_md.read_text(encoding="utf-8")
        assert "OLMDistanceGradation Debug Point Report" in md
        assert "compose_input_x" in md
    print("[OK] analyze_distancegradation_debug_points smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
